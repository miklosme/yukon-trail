"""Small classic-HFS fixtures using Apple's published field offsets.

No original game bytes or extracted files are embedded in these tests.
"""

import hashlib
import struct
import unittest

from tools.hfs_inventory import InventoryError, inventory


PARTITION = 4 * 512
MDB = PARTITION + 1024
ALLOCATION = PARTITION + 3 * 512
CATALOG = ALLOCATION + 512
LEAF = CATALOG + 512


def put16(data, offset, value):
    struct.pack_into(">H", data, offset, value)


def put32(data, offset, value):
    struct.pack_into(">I", data, offset, value)


def header(nodes, records=0, leaf=0):
    data = bytearray(nodes * 512)
    data[8] = 1
    put16(data, 10, 3)
    put16(data, 14, 1 if leaf else 0)
    put32(data, 16, leaf)
    put32(data, 20, records)
    put32(data, 24, leaf)
    put32(data, 28, leaf)
    put16(data, 32, 512)
    put32(data, 36, nodes)
    put16(data, 510, 14)
    return data


def keyed(parent, name, value):
    # The observed Toast catalog includes a zero pad in keyLength for even
    # name lengths. The value starts on an even boundary.
    key_length = (6 + len(name)) | 1
    key = bytearray(key_length + 1)
    key[0] = key_length
    put32(key, 2, parent)
    key[6] = len(name)
    key[7:7 + len(name)] = name
    return key + value


def fixture():
    image = bytearray(32 * 512)
    image[:2] = b"ER"
    put16(image, 2, 512)
    for index, start, blocks, kind in [
        (1, 1, 2, b"Apple_partition_map"),
        (2, 4, 28, b"Apple_HFS"),
    ]:
        offset = index * 512
        image[offset:offset + 2] = b"PM"
        put32(image, offset + 4, 2)
        put32(image, offset + 8, start)
        put32(image, offset + 12, blocks)
        image[offset + 48:offset + 48 + len(kind)] = kind
    image[MDB:MDB + 2] = b"BD"
    put16(image, MDB + 18, 20)
    put32(image, MDB + 20, 512)
    put16(image, MDB + 28, 3)
    image[MDB + 36:MDB + 40] = b"\x03Vol"
    put32(image, MDB + 84, 1)
    put32(image, MDB + 88, 0)  # excludes root folder
    put32(image, MDB + 130, 512)
    put16(image, MDB + 134, 0)
    put16(image, MDB + 136, 1)
    put32(image, MDB + 146, 1024)
    put16(image, MDB + 150, 1)
    put16(image, MDB + 152, 2)
    image[ALLOCATION:ALLOCATION + 512] = header(1)
    image[CATALOG:CATALOG + 1024] = header(2, records=3, leaf=1)
    folder = bytearray(70)
    put16(folder, 0, 0x0100)
    put32(folder, 6, 2)
    file = bytearray(102)
    put16(file, 0, 0x0200)
    file[4:12] = b"TEXTTEST"
    put32(file, 20, 16)
    put32(file, 26, 5)
    put32(file, 30, 512)
    put32(file, 36, 5)
    put32(file, 40, 512)
    put16(file, 74, 3)
    put16(file, 76, 1)
    put16(file, 86, 4)
    put16(file, 88, 1)
    thread = bytearray(46)
    put16(thread, 0, 0x0300)
    put32(thread, 10, 1)
    thread[14:18] = b"\x03Vol"
    records = [keyed(1, b"Vol", folder), keyed(2, b"Icon\r", file), keyed(2, b"", thread)]
    image[LEAF + 8:LEAF + 10] = b"\xff\x01"
    put16(image, LEAF + 10, len(records))
    position = 14
    for index, record in enumerate(records):
        put16(image, LEAF + 510 - index * 2, position)
        image[LEAF + position:LEAF + position + len(record)] = record
        position += len(record)
    put16(image, LEAF + 510 - len(records) * 2, position)
    image[ALLOCATION + 3 * 512:ALLOCATION + 3 * 512 + 5] = b"DATA!"
    image[ALLOCATION + 4 * 512:ALLOCATION + 4 * 512 + 5] = b"RSRC?"
    return image


def file_value_offset(image):
    record = LEAF + struct.unpack_from(">H", image, LEAF + 508)[0]
    return record + ((image[record] + 2) & ~1)


class HFSInventoryTests(unittest.TestCase):
    def test_independent_forks_names_and_geometry(self):
        source = fixture()
        result = inventory(source, hashlib.sha256(source).hexdigest())
        self.assertEqual(result["volume"]["mdb_source_offset"], MDB)
        self.assertEqual(result["catalog"]["extents"][0]["source_offset"], CATALOG)
        self.assertEqual(result["catalog"]["header"]["leaf_records"], 3)
        self.assertEqual(result["catalog"]["visited_leaf_nodes"], 1)
        file = result["files"][0]
        self.assertEqual(file["cnid"], 16)
        self.assertEqual(file["path_components"], ["Vol", "Icon\r"])
        self.assertEqual(file["name_bytes_hex"], "49636f6e0d")
        self.assertEqual(file["data_fork"]["sha256"], hashlib.sha256(b"DATA!").hexdigest())
        self.assertEqual(file["resource_fork"]["sha256"], hashlib.sha256(b"RSRC?").hexdigest())
        self.assertEqual(file["resource_fork"]["logical_size"], 5)
        self.assertEqual(source, fixture())  # reader never changes input

    def reject(self, mutate, message):
        source = fixture()
        mutate(source)
        with self.assertRaisesRegex(InventoryError, message):
            inventory(source)

    def test_source_identity(self):
        with self.assertRaisesRegex(InventoryError, "SHA-256 mismatch"):
            inventory(fixture(), "0" * 64)

    def test_fork_with_two_inline_extents(self):
        source = fixture()
        value = file_value_offset(source)
        put32(source, value + 26, 600)
        put32(source, value + 30, 1024)
        put16(source, value + 78, 5)
        put16(source, value + 80, 1)
        source[ALLOCATION + 5 * 512:ALLOCATION + 5 * 512 + 6] = b"SECOND"
        result = inventory(source)["files"][0]["data_fork"]
        expected = b"DATA!" + bytes(507) + b"SECOND" + bytes(82)
        self.assertEqual(result["sha256"], hashlib.sha256(expected).hexdigest())
        self.assertEqual(len(result["extents"]), 2)

    def test_empty_resource_fork(self):
        source = fixture()
        value = file_value_offset(source)
        for offset in (36, 40):
            put32(source, value + offset, 0)
        put16(source, value + 86, 0)
        put16(source, value + 88, 0)
        result = inventory(source)["files"][0]["resource_fork"]
        self.assertEqual(result["extents"], [])
        self.assertEqual(result["sha256"], hashlib.sha256(b"").hexdigest())

    def test_unpadded_catalog_key_length(self):
        source = fixture()
        record = LEAF + struct.unpack_from(">H", source, LEAF + 508)[0]
        source[record] = 10
        source[record + 6:record + 12] = b"\x04Test\0"
        self.assertEqual(inventory(source)["files"][0]["name"], "Test")

    def test_truncated_source(self):
        with self.assertRaisesRegex(InventoryError, "outside source image"):
            inventory(fixture()[:-1])

    def test_multiple_hfs_partitions(self):
        def mutate(source):
            source[512 + 48:512 + 80] = b"Apple_HFS" + b"\0" * 23
        self.reject(mutate, "exactly one")

    def test_unsupported_hfs_plus(self):
        self.reject(lambda s: s.__setitem__(slice(MDB, MDB + 2), b"H+"), "classic HFS")

    def test_allocation_bounds(self):
        self.reject(lambda s: put16(s, MDB + 18, 100), "allocation area outside")

    def test_nonempty_overflow_tree(self):
        self.reject(lambda s: put32(s, ALLOCATION + 20, 1), "nonempty extents-overflow")

    def test_catalog_requires_overflow(self):
        self.reject(lambda s: put32(s, MDB + 146, 1536), "extents-overflow lookup")

    def test_cycle_in_leaf_chain(self):
        self.reject(lambda s: put32(s, LEAF, 1), "cyclic catalog leaf chain")

    def test_backward_link_mismatch(self):
        self.reject(lambda s: put32(s, LEAF + 4, 1), "leaf descriptor/link")

    def test_overlapping_record_offsets(self):
        self.reject(lambda s: put16(s, LEAF + 508, 14), "record-offset table")

    def test_catalog_count_mismatch(self):
        self.reject(lambda s: put32(s, MDB + 84, 2), "counts differ from MDB")

    def test_duplicate_cnid(self):
        self.reject(lambda s: put32(s, file_value_offset(s) + 20, 2), "duplicate catalog CNID")

    def test_negative_fork_length(self):
        self.reject(lambda s: put32(s, file_value_offset(s) + 36, 0xffffffff), "invalid fork")

    def test_fork_extent_outside_allocation(self):
        self.reject(lambda s: put16(s, file_value_offset(s) + 86, 20), "extent outside")

    def test_fork_capacity_mismatch(self):
        self.reject(lambda s: put32(s, file_value_offset(s) + 40, 1024), "physical size differs")

    def test_overlapping_inline_extents(self):
        def mutate(source):
            value = file_value_offset(source)
            put32(source, value + 30, 1024)
            put16(source, value + 78, 3)
            put16(source, value + 80, 1)
        self.reject(mutate, "overlapping inline extents")

    def test_non_root_entry_under_reserved_root_parent(self):
        def mutate(source):
            record = LEAF + struct.unpack_from(">H", source, LEAF + 508)[0]
            put32(source, record + 2, 1)
        self.reject(mutate, "reserved root-parent")

    def test_missing_parent(self):
        def mutate(source):
            record = LEAF + struct.unpack_from(">H", source, LEAF + 508)[0]
            put32(source, record + 2, 999)
        self.reject(mutate, "missing or cyclic parent")


if __name__ == "__main__":
    unittest.main()
