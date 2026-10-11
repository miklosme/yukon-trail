#!/usr/bin/env python3
"""Inventory classic HFS catalog/fork metadata without mounting or extracting.

Supported subset: 512-byte Apple partition map, one HFS partition, 512-byte
B-tree nodes, catalog and forks entirely described by their inline extents,
and an empty extents-overflow tree. Unsupported structures fail explicitly.
"""

import argparse
from collections import Counter
import hashlib
import json
import mmap
from pathlib import Path
import struct
import sys


class InventoryError(ValueError):
    """Invalid or unsupported input; no partial inventory should be used."""


def require(condition, message):
    if not condition:
        raise InventoryError(message)


def read(data, offset, length):
    require(offset >= 0 and length >= 0 and offset + length <= len(data),
            f"source range outside image: {offset:#x}+{length:#x}")
    return data[offset:offset + length]


def u16(data, offset):
    return struct.unpack(">H", read(data, offset, 2))[0]


def u32(data, offset):
    return struct.unpack(">I", read(data, offset, 4))[0]


def i32(data, offset):
    return struct.unpack(">i", read(data, offset, 4))[0]


def digest(data, ranges):
    result = hashlib.sha256()
    for offset, length in ranges:
        while length:
            count = min(length, 1024 * 1024)
            result.update(read(data, offset, count))
            offset += count
            length -= count
    return result.hexdigest()


def inline_extents(data, offset, allocation):
    result = []
    ended = False
    for index in range(3):
        start = u16(data, offset + index * 4)
        count = u16(data, offset + index * 4 + 2)
        if count == 0:
            require(start == 0, "unused extent has nonzero start")
            ended = True
            continue
        require(not ended, "nonempty extent follows an unused extent")
        require(start + count <= allocation["block_count"],
                "extent outside HFS allocation area")
        require(all(start + count <= extent["allocation_block"] or
                    start >= extent["allocation_block"] + extent["block_count"]
                    for extent in result), "overlapping inline extents")
        result.append({
            "allocation_block": start,
            "block_count": count,
            "source_offset": allocation["source_offset"] + start * allocation["block_size"],
            "byte_length": count * allocation["block_size"],
        })
    return result


def ranges_for_fork(extents, size):
    require(size >= 0, "negative fork size")
    require(sum(e["byte_length"] for e in extents) >= size,
            "fork requires unsupported extents-overflow lookup")
    ranges = []
    remaining = size
    for extent in extents:
        count = min(remaining, extent["byte_length"])
        ranges.append((extent["source_offset"], count))
        remaining -= count
    return ranges


def special_file(data, mdb, size_offset, extent_offset, allocation):
    size = u32(mdb, size_offset)
    require(0 < size <= 64 * 1024 * 1024, "unsupported special-file size")
    extents = inline_extents(mdb, extent_offset, allocation)
    ranges = ranges_for_fork(extents, size)
    contents = b"".join(read(data, offset, length) for offset, length in ranges)
    return contents, {
        "logical_size": size,
        "extents": extents,
        "sha256": hashlib.sha256(contents).hexdigest(),
    }


def tree_header(tree):
    require(len(tree) >= 512, "truncated B-tree header")
    require(tree[8] == 1 and tree[9] == 0 and u16(tree, 10) == 3,
            "unsupported B-tree header-node descriptor")
    require(u16(tree, 32) == 512, "unsupported B-tree node size (requires 512)")
    header_start = u16(tree, 510)
    require(header_start == 14, "unsupported B-tree header record offset")
    total = u32(tree, 36)
    require(total > 0 and total * 512 == len(tree), "B-tree size/node count mismatch")
    return {
        "tree_depth": u16(tree, 14),
        "root_node": u32(tree, 16),
        "leaf_records": u32(tree, 20),
        "first_leaf": u32(tree, 24),
        "last_leaf": u32(tree, 28),
        "node_size": 512,
        "total_nodes": total,
    }


def file_fork(data, record, logical_offset, physical_offset, extent_offset, allocation):
    logical = i32(record, logical_offset)
    physical = i32(record, physical_offset)
    require(0 <= logical <= physical, "invalid fork logical/physical sizes")
    extents = inline_extents(record, extent_offset, allocation)
    require(sum(e["byte_length"] for e in extents) == physical,
            "fork physical size differs from inline extent capacity")
    ranges = ranges_for_fork(extents, logical)
    return {
        "logical_size": logical,
        "physical_size": physical,
        "extents": extents,
        "sha256": digest(data, ranges),
    }


def inventory(data, expected_sha256=None):
    source_hash = digest(data, [(0, len(data))])
    if expected_sha256 is not None:
        require(source_hash == expected_sha256.lower(), "source SHA-256 mismatch")
    if read(data, 0, 2) == b"ER":
        require(u16(data, 2) == 512, "unsupported Apple device block size")
    first = read(data, 512, 512)
    require(first[:2] == b"PM", "missing 512-byte Apple partition map")
    count = u32(first, 4)
    require(0 < count <= 4096, "unsupported Apple partition-map count")
    partitions = []
    for index in range(1, count + 1):
        entry = read(data, index * 512, 512)
        require(entry[:2] == b"PM" and u32(entry, 4) == count,
                "inconsistent Apple partition-map entry")
        start = u32(entry, 8)
        blocks = u32(entry, 12)
        require(blocks > 0 and (start + blocks) * 512 <= len(data),
                "partition outside source image")
        try:
            kind = entry[48:80].split(b"\0")[0].decode("ascii")
        except UnicodeDecodeError as error:
            raise InventoryError("non-ASCII partition type") from error
        partitions.append({
            "map_index": index,
            "map_source_offset": index * 512,
            "name": entry[16:48].split(b"\0")[0].decode("mac_roman"),
            "type": kind,
            "source_offset": start * 512,
            "byte_length": blocks * 512,
        })
    hfs = [p for p in partitions if p["type"] == "Apple_HFS"]
    require(len(hfs) == 1, "requires exactly one Apple_HFS partition")
    partition = hfs[0]
    require(partition["byte_length"] >= 1536, "truncated HFS partition")
    mdb_offset = partition["source_offset"] + 1024
    mdb = read(data, mdb_offset, 512)
    require(mdb[:2] == b"BD", "unsupported volume signature (requires classic HFS)")
    require(mdb[36] <= 27, "invalid HFS volume-name length")
    allocation = {
        "source_offset": partition["source_offset"] + u16(mdb, 28) * 512,
        "block_size": u32(mdb, 20),
        "block_count": u16(mdb, 18),
    }
    require(allocation["block_size"] >= 512 and allocation["block_size"] % 512 == 0,
            "invalid HFS allocation-block size")
    require(allocation["source_offset"] >= mdb_offset + 512 and
            allocation["source_offset"] + allocation["block_size"] * allocation["block_count"]
            <= partition["source_offset"] + partition["byte_length"],
            "HFS allocation area outside partition")
    overflow, overflow_info = special_file(data, mdb, 130, 134, allocation)
    overflow_info["header"] = tree_header(overflow)
    require(all(overflow_info["header"][key] == 0 for key in
                ("tree_depth", "root_node", "leaf_records", "first_leaf", "last_leaf")),
            "nonempty extents-overflow tree is unsupported")
    catalog, catalog_info = special_file(data, mdb, 146, 150, allocation)
    header = tree_header(catalog)
    catalog_info["header"] = header
    require(header["tree_depth"] > 0 and 0 < header["root_node"] < header["total_nodes"],
            "invalid catalog root")
    folders = {}
    files = []
    threads = []
    types = Counter()
    visited = set()
    previous = 0
    node_id = header["first_leaf"]
    while node_id:
        require(node_id not in visited and node_id < header["total_nodes"],
                "invalid or cyclic catalog leaf chain")
        visited.add(node_id)
        node = read(catalog, node_id * 512, 512)
        next_node = u32(node, 0)
        require(u32(node, 4) == previous and node[8] == 255 and node[9] == 1,
                "invalid catalog leaf descriptor/link")
        records = u16(node, 10)
        require(0 < records <= 248, "invalid leaf record count")
        offsets = [u16(node, 512 - 2 * (i + 1)) for i in range(records + 1)]
        require(offsets[0] >= 14 and offsets[-1] <= 512 - 2 * (records + 1)
                and all(a < b for a, b in zip(offsets, offsets[1:])),
                "invalid catalog record-offset table")
        for index, (start, end) in enumerate(zip(offsets, offsets[1:])):
            record = node[start:end]
            key_length = record[0]
            require(key_length >= 6 and key_length + 1 <= len(record),
                    "invalid catalog key length")
            name_length = record[6]
            require(name_length <= 31 and key_length in (6 + name_length, (6 + name_length) | 1),
                    "unsupported catalog name/key length")
            require(all(byte == 0 for byte in record[7 + name_length:key_length + 1]),
                    "nonzero catalog key padding")
            name_bytes = record[7:7 + name_length]
            parent = u32(record, 2)
            value = record[(key_length + 2) & ~1:]
            kind = u16(value, 0)
            types[kind] += 1
            location = {"catalog_node": node_id, "record_index": index,
                        "catalog_offset": node_id * 512 + start}
            common = {"parent_id": parent, "name": name_bytes.decode("mac_roman"),
                      "name_bytes_hex": name_bytes.hex(), "location": location,
                      "catalog_value_hex": value.hex()}
            if kind == 0x0100:
                require(len(value) == 70, "invalid folder record size")
                cnid = u32(value, 6)
                require(cnid not in folders, "duplicate folder CNID")
                folders[cnid] = {**common, "cnid": cnid}
            elif kind == 0x0200:
                require(len(value) == 102, "invalid file record size")
                files.append({
                    **common, "cnid": u32(value, 20),
                    "finder_type_hex": value[4:8].hex(),
                    "finder_creator_hex": value[8:12].hex(),
                    "data_fork": file_fork(data, value, 26, 30, 74, allocation),
                    "resource_fork": file_fork(data, value, 36, 40, 86, allocation),
                })
            elif kind in (0x0300, 0x0400):
                require(len(value) == 46 and name_length == 0,
                        "invalid thread record")
                threads.append({**common, "record_type": kind})
            else:
                raise InventoryError(f"unsupported catalog record type {kind:#x}")
        previous, node_id = node_id, next_node
    require(previous == header["last_leaf"] and sum(types.values()) == header["leaf_records"],
            "catalog leaf chain/count differs from header")
    require(len(files) == u32(mdb, 84) and len(folders) == u32(mdb, 88) + 1,
            "catalog file/folder counts differ from MDB")
    require(2 in folders and folders[2]["parent_id"] == 1, "missing HFS root folder")
    all_cnids = list(folders) + [file["cnid"] for file in files]
    require(len(all_cnids) == len(set(all_cnids)), "duplicate catalog CNID")
    for entry in list(folders.values()) + files:
        require(entry["cnid"] == 2 or entry["parent_id"] != 1,
                "non-root catalog entry uses reserved root-parent CNID")
        components = [entry["name"]]
        parent = entry["parent_id"]
        parents = {entry["cnid"]}
        while parent != 1:
            require(parent in folders and parent not in parents,
                    "missing or cyclic parent folder")
            parents.add(parent)
            components.insert(0, folders[parent]["name"])
            parent = folders[parent]["parent_id"]
        entry["path_components"] = components
    return {
        "inventory_version": 1,
        "source": {"size_bytes": len(data), "sha256": source_hash},
        "partitions": partitions,
        "volume": {"name": mdb[37:37 + mdb[36]].decode("mac_roman"),
                   "mdb_source_offset": mdb_offset, "mdb_bytes_hex": mdb.hex(),
                   "allocation": allocation},
        "extents_overflow": overflow_info,
        "catalog": {**catalog_info, "visited_leaf_nodes": len(visited),
                    "record_type_counts": {f"{key:#06x}": types[key] for key in sorted(types)}},
        "folders": sorted(folders.values(), key=lambda e: e["cnid"]),
        "files": sorted(files, key=lambda e: e["cnid"]),
        "threads": threads,
        "validation_scope": "APM/MDB bounds, inline fork extents and hashes, linked catalog leaves; "
                            "no mount, fork extraction, bitmap/index-node validation, or executable interpretation",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("--expect-sha256", help="fail before interpretation if source hash differs")
    arguments = parser.parse_args()
    try:
        with arguments.image.open("rb") as source:
            require(arguments.image.stat().st_size > 0, "empty source image")
            with mmap.mmap(source.fileno(), 0, access=mmap.ACCESS_READ) as data:
                result = inventory(data, arguments.expect_sha256)
        result["source"]["path"] = str(arguments.image)
    except (InventoryError, OSError) as error:
        print(f"hfs_inventory: {error}", file=sys.stderr)
        return 1
    json.dump(result, sys.stdout, indent=2, sort_keys=True, ensure_ascii=True)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
