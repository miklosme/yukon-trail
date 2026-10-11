#!/usr/bin/env python3
"""Check the disassembly-derived lookup against physical source index ordinals.

This is a bounded static consistency check for the exact supplied archive, not
an emulator, payload decoder, or original-game behavioral fidelity test.
See docs/ARCHIVE-CONSUMERS.md and NE 0001:75fe / Ghidra 1000:75fe.
"""

import argparse
import hashlib
import json
from pathlib import Path
import struct


ARCHIVE_SHA256 = "438d729386cdb2effb120ed7652d14af00fb8a0e78f4426c12b17c934c3db8b6"
EXE_SHA256 = "9ca8f0a12f4798e762fbf27634f99afcb5c0c1a3836604bf0a4049a73227dd06"


def traced_lookup(groups, records, tag, resource_id):
    """Mirror checked compare/branch/arithmetic for this source's small counts."""
    for group_tag, count, start in groups:
        if group_tag == tag:
            break
    else:
        return -1
    end = start + count
    low, high = start, end
    middle = low + (end - low) // 2
    steps = 0
    while low < high and 0 < middle < end:
        steps += 1
        if steps > 32:
            raise ValueError("Search exceeded bounded source domain")
        current_id = records[middle][1]
        if current_id == resource_id:
            break
        if current_id > resource_id:  # unsigned ID CMP/JBE at 0001:76a1/76a7
            high = middle - 1
            middle = low + (middle - low) // 2
        else:
            low = middle + 1
            middle = middle + (high - middle + 1) // 2
    if middle < end and records[middle][1] == resource_id:
        return middle
    return -1


def verify(path):
    data = path.read_bytes()
    actual = hashlib.sha256(data).hexdigest()
    if actual != ARCHIVE_SHA256:
        raise ValueError(f"Unsupported archive identity: {actual}")
    group_count, record_count = struct.unpack_from(">HH", data, 0x54)
    if (group_count, record_count) != (21, 2522):
        raise ValueError("Unexpected bounded source domain")
    groups = [
        (data[0x58 + i * 8:0x5c + i * 8], *struct.unpack_from(">HH", data, 0x5c + i * 8))
        for i in range(group_count)
    ]
    records = [
        (data[0x100 + i * 14:0x104 + i * 14], *struct.unpack_from(">HII", data, 0x104 + i * 14))
        for i in range(record_count)
    ]
    # Expected ordinal comes from direct physical enumeration, independently of
    # the binary-search control flow and without importing tools/yukonres.py.
    expected = {(record[0], record[1]): i for i, record in enumerate(records)}
    if len(expected) != record_count:
        raise ValueError("Source keys are not unique")
    for key, wanted in expected.items():
        actual_index = traced_lookup(groups, records, *key)
        if actual_index != wanted:
            raise ValueError(f"Lookup mismatch {key!r}: {actual_index} != {wanted}")
    absent = [(b"NONE", 1)]
    for tag, count, start in groups:
        first_id = records[start][1]
        last_id = records[start + count - 1][1]
        if first_id:
            absent.append((tag, first_id - 1))
        if last_id < 65535:
            absent.append((tag, last_id + 1))
    for key in absent:
        if key in expected or traced_lookup(groups, records, *key) != -1:
            raise ValueError(f"Absent-key result mismatch {key!r}")
    samples = []
    for key in [(b"CBMP", 1), (b"PSND", 1), (b"TREE", 39)]:
        index = expected[key]
        tag, resource_id, length, offset = records[index]
        samples.append({"tag": tag.decode("ascii"), "id": resource_id,
                        "physical_index": index, "payload_length": length,
                        "payload_offset": offset})
    return {"source_sha256": ARCHIVE_SHA256, "executable_sha256": EXE_SHA256,
            "routine_ne": "0001:75fe", "routine_ghidra": "1000:75fe",
            "present_queries": record_count, "absent_queries": len(absent),
            "mismatches": 0, "samples": samples,
            "scope": "Static source consistency; original-game execution unverified"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.archive), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
