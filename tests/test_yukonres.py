"""Synthetic index fixtures; no original game assets are required."""

import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest

from tools.yukonres import ArchiveError, export_archive, parse_index, read_index, verify_source


def fixture() -> bytes:
    # Handwritten big-endian bytes: two groups, three records, index end 0x92.
    header = bytearray(0x58)
    header[4:8] = b"MECC"
    header[0x54:0x58] = bytes.fromhex("0002 0003")
    return bytes(header) + bytes.fromhex(
        "494d4147 0002 0000"  # IMAG: records 0..1
        "54455854 0001 0002"  # TEXT: record 2
        "494d4147 0007 00000003 00000092"  # IMAG:7
        "494d4147 002a 00000000 00000095"  # IMAG:42, empty
        "54455854 0009 00000004 00000095"  # TEXT:9
    ) + b"\x00\xff\x01note"


def changed(data: bytes, offset: int, value: bytes) -> bytes:
    return data[:offset] + value + data[offset + len(value):]


class IndexTests(unittest.TestCase):
    def test_handwritten_index(self):
        index = parse_index(fixture())
        self.assertEqual(index.index_end, 0x92)
        self.assertEqual(index.size, 0x99)
        self.assertEqual([(g.tag, g.count, g.first) for g in index.groups], [("IMAG", 2, 0), ("TEXT", 1, 2)])
        self.assertEqual(
            [(r.key, r.offset, r.length, r.index, r.entry_offset) for r in index.resources],
            [("IMAG:7", 0x92, 3, 0, 0x68), ("IMAG:42", 0x95, 0, 1, 0x76), ("TEXT:9", 0x95, 4, 2, 0x84)],
        )

    def test_stream_reads_index_without_loading_payload(self):
        source = io.BytesIO(fixture())
        index = read_index(source)
        self.assertEqual(source.tell(), 0x92)
        self.assertEqual(index.by_key()["TEXT:9"].length, 4)

    def test_index_only_with_full_file_size(self):
        self.assertEqual(parse_index(fixture()[:0x92], archive_size=0x99), parse_index(fixture()))

    def test_truncation_at_every_byte(self):
        for size in range(len(fixture())):
            with self.subTest(size=size), self.assertRaises(ArchiveError):
                parse_index(fixture()[:size])

    def test_truncated_index_despite_claimed_full_size(self):
        with self.assertRaisesRegex(ArchiveError, "truncated index"):
            parse_index(fixture()[:0x91], archive_size=0x99)

    def test_bad_signature(self):
        with self.assertRaisesRegex(ArchiveError, "signature"):
            parse_index(changed(fixture(), 4, b"NOPE"))

    def test_count_bounds(self):
        for value in (bytes.fromhex("0000 0003"), bytes.fromhex("0002 0000"), bytes.fromhex("ffff ffff")):
            with self.subTest(value=value), self.assertRaises(ArchiveError):
                parse_index(changed(fixture(), 0x54, value))

    def test_group_coverage(self):
        # Out of range, overlapping, empty, or incomplete group coverage.
        for offset, value in ((0x64, b"\x00\x02"), (0x66, b"\x00\x01"), (0x64, b"\x00\x00"), (0x54, b"\x00\x01")):
            with self.subTest(offset=offset, value=value), self.assertRaisesRegex(ArchiveError, "coverage|cover"):
                parse_index(changed(fixture(), offset, value))

    def test_duplicate_group(self):
        with self.assertRaisesRegex(ArchiveError, "duplicate group"):
            parse_index(changed(fixture(), 0x60, b"IMAG"))

    def test_group_membership(self):
        with self.assertRaisesRegex(ArchiveError, "group IMAG contains TEXT"):
            parse_index(changed(fixture(), 0x76, b"TEXT"))

    def test_duplicate_resource(self):
        with self.assertRaisesRegex(ArchiveError, "duplicate resource IMAG:7"):
            parse_index(changed(fixture(), 0x7A, b"\x00\x07"))

    def test_invalid_tags(self):
        for offset in (0x58, 0x68):
            with self.subTest(offset=offset), self.assertRaisesRegex(ArchiveError, "ASCII tag"):
                parse_index(changed(fixture(), offset, b"\xffBAD"))

    def test_payload_bounds(self):
        for offset, value in ((0x72, bytes.fromhex("00000091")), (0x8E, bytes.fromhex("0000009a")), (0x8A, bytes.fromhex("00000005"))):
            with self.subTest(offset=offset), self.assertRaisesRegex(ArchiveError, "outside payload area"):
                parse_index(changed(fixture(), offset, value))

    def test_u32_end_does_not_wrap(self):
        data = changed(fixture(), 0x6E, bytes.fromhex("ffffffff fffffff0"))
        with self.assertRaisesRegex(ArchiveError, "outside payload area"):
            parse_index(data, archive_size=0x100000000)

    def test_positive_payload_overlap(self):
        with self.assertRaisesRegex(ArchiveError, "payload overlap"):
            parse_index(changed(fixture(), 0x8E, bytes.fromhex("00000094")))

    def test_zero_length_at_eof_is_preserved(self):
        index = parse_index(changed(fixture(), 0x80, bytes.fromhex("00000099")))
        self.assertEqual(index.by_key()["IMAG:42"].offset, 0x99)


class ExportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = self.root / "fixture.res"
        self.source.write_bytes(fixture())
        self.manifest = self.root / "source.json"
        self.manifest.write_text(json.dumps({"files": [{
            "role": "resource_archive", "size_bytes": 0x99,
            "sha256": hashlib.sha256(fixture()).hexdigest(),
        }]}), encoding="utf-8")

    def test_raw_export_preserves_bytes_and_provenance(self):
        output = self.root / "output"
        report = export_archive(self.source, output, ["IMAG:7", "IMAG:42", "TEXT:9"], self.manifest)
        self.assertEqual((output / "IMAG-7.bin").read_bytes(), b"\x00\xff\x01")
        self.assertEqual((output / "IMAG-42.bin").read_bytes(), b"")
        self.assertEqual((output / "TEXT-9.bin").read_bytes(), b"note")
        self.assertEqual(report["resources"]["TEXT"]["9"]["offset"], 0x95)
        self.assertEqual(report["raw_exports"]["TEXT:9"]["sha256"], hashlib.sha256(b"note").hexdigest())
        self.assertEqual(json.loads((output / "manifest.json").read_text()), report)

    def test_deterministic_manifest(self):
        first, second = self.root / "first", self.root / "second"
        export_archive(self.source, first, ["TEXT:9", "IMAG:7"], self.manifest)
        export_archive(self.source, second, ["IMAG:7", "TEXT:9"], self.manifest)
        self.assertEqual((first / "manifest.json").read_bytes(), (second / "manifest.json").read_bytes())

    def test_wrong_hash_creates_no_output(self):
        self.source.write_bytes(changed(fixture(), 0x98, b"x"))
        output = self.root / "output"
        with self.assertRaisesRegex(ArchiveError, "SHA-256"):
            export_archive(self.source, output, [], self.manifest)
        self.assertFalse(output.exists())

    def test_wrong_size(self):
        with self.source.open("ab") as source:
            source.write(b"x")
        with self.source.open("rb") as source, self.assertRaisesRegex(ArchiveError, "source size"):
            verify_source(source, self.manifest)

    def test_bad_index_creates_no_output(self):
        data = changed(fixture(), 0x7A, b"\x00\x07")
        self.source.write_bytes(data)
        metadata = json.loads(self.manifest.read_text())
        metadata["files"][0]["sha256"] = hashlib.sha256(data).hexdigest()
        self.manifest.write_text(json.dumps(metadata))
        output = self.root / "output"
        with self.assertRaisesRegex(ArchiveError, "duplicate resource"):
            export_archive(self.source, output, [], self.manifest)
        self.assertFalse(output.exists())

    def test_missing_or_repeated_key_creates_no_output(self):
        for keys in (["TEXT:10"], ["TEXT:9", "TEXT:9"]):
            output = self.root / "output"
            with self.subTest(keys=keys), self.assertRaises(ArchiveError):
                export_archive(self.source, output, keys, self.manifest)
            self.assertFalse(output.exists())

    def test_existing_output_is_preserved(self):
        output = self.root / "output"
        output.mkdir()
        sentinel = output / "manifest.json"
        sentinel.write_bytes(b"keep me")
        with self.assertRaisesRegex(ArchiveError, "new or empty"):
            export_archive(self.source, output, [], self.manifest)
        self.assertEqual(sentinel.read_bytes(), b"keep me")


if __name__ == "__main__":
    unittest.main()
