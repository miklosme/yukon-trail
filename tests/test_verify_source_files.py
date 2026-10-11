"""Source verification with an independent, tiny tar container and known bytes."""

import hashlib
import io
import json
from pathlib import Path
import shutil
import tarfile
import tempfile
import unittest

from tools.verify_source_files import VerificationError, verify


@unittest.skipUnless(shutil.which("bsdtar"), "source comparisons require bsdtar")
class SourceVerificationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        # bsdtar reads this synthetic container; tests do not claim ISO parsing.
        self.disc = self.root / "fixture.tar"
        self.windows = self.root / "extracted"
        self.windows.mkdir()
        content = b"independent source bytes\x00\xff"
        with tarfile.open(self.disc, "w") as output:
            member = tarfile.TarInfo("SAMPLE.BIN")
            member.size = len(content)
            output.addfile(member, io.BytesIO(content))
        (self.windows / "SAMPLE.BIN").write_bytes(content)
        self.source = self.root / "source.json"
        self.extraction = self.root / "extraction.json"
        disc_hash = hashlib.sha256(self.disc.read_bytes()).hexdigest()
        self.source.write_text(json.dumps({"files": [{"role": "source_disc_image",
            "size_bytes": self.disc.stat().st_size, "sha256": disc_hash}]}))
        self.metadata = {"source_iso_sha256": disc_hash, "files": [{"path": "SAMPLE.BIN",
            "size_bytes": len(content), "sha256": hashlib.sha256(content).hexdigest()}]}
        self.write_metadata()

    def write_metadata(self):
        self.extraction.write_text(json.dumps(self.metadata))

    def run_verify(self):
        return verify(self.disc, self.windows, self.source, self.extraction)

    def test_independent_container_and_extraction_match(self):
        result = self.run_verify()
        self.assertEqual(result["verified_file_count"], 1)
        self.assertEqual(result["files"], self.metadata["files"])
        self.assertEqual(self.run_verify(), result)

    def test_changed_disc_identity(self):
        with self.disc.open("ab") as output:
            output.write(b"x")
        with self.assertRaisesRegex(VerificationError, "disc size/SHA-256"):
            self.run_verify()

    def test_changed_extraction(self):
        (self.windows / "SAMPLE.BIN").write_bytes(b"wrong bytes")
        with self.assertRaisesRegex(VerificationError, "extracted file differs"):
            self.run_verify()

    def test_source_entry_differs_even_when_local_metadata_agrees(self):
        data = b"different matching local bytes"
        (self.windows / "SAMPLE.BIN").write_bytes(data)
        self.metadata["files"][0].update(size_bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
        self.write_metadata()
        with self.assertRaisesRegex(VerificationError, "disc entry differs"):
            self.run_verify()

    def test_missing_disc_entry(self):
        (self.windows / "ABSENT.BIN").write_bytes((self.windows / "SAMPLE.BIN").read_bytes())
        self.metadata["files"][0]["path"] = "ABSENT.BIN"
        self.write_metadata()
        with self.assertRaisesRegex(VerificationError, "disc read failed"):
            self.run_verify()

    def test_different_source_metadata(self):
        self.metadata["source_iso_sha256"] = "0" * 64
        self.write_metadata()
        with self.assertRaisesRegex(VerificationError, "different disc"):
            self.run_verify()

    def test_reject_ambiguous_selected_paths(self):
        for name in ("../SAMPLE.BIN", "/SAMPLE.BIN", "./SAMPLE.BIN", "", "a//b"):
            with self.subTest(name=name):
                self.metadata["files"][0]["path"] = name
                self.write_metadata()
                with self.assertRaisesRegex(VerificationError, "selected-file path"):
                    self.run_verify()

    def test_reject_duplicate_selection(self):
        self.metadata["files"].append(self.metadata["files"][0].copy())
        self.write_metadata()
        with self.assertRaisesRegex(VerificationError, "duplicate selected-file"):
            self.run_verify()

    def test_reject_container_member_patterns(self):
        # Without an exact-name guard bsdtar concatenates both matches into AB.
        with tarfile.open(self.disc, "w") as output:
            for name, content in (("SAMPLE1.BIN", b"A"), ("SAMPLE2.BIN", b"B")):
                member = tarfile.TarInfo(name)
                member.size = len(content)
                output.addfile(member, io.BytesIO(content))
        self.source.write_text(json.dumps({"files": [{"role": "source_disc_image",
            "size_bytes": self.disc.stat().st_size,
            "sha256": hashlib.sha256(self.disc.read_bytes()).hexdigest()}]}))
        self.metadata["source_iso_sha256"] = hashlib.sha256(self.disc.read_bytes()).hexdigest()
        self.metadata["files"] = [{"path": "SAMPLE*.BIN", "size_bytes": 2,
            "sha256": hashlib.sha256(b"AB").hexdigest()}]
        (self.windows / "SAMPLE*.BIN").write_bytes(b"AB")
        self.write_metadata()
        with self.assertRaisesRegex(VerificationError, "selected-file path"):
            self.run_verify()

    def test_reject_glob_escape_and_nul_characters(self):
        for name in ("SAMPLE?.BIN", "SAMPLE[1].BIN", "SAMPLE].BIN", "SAMPLE\\1.BIN", "SAMPLE\0.BIN"):
            with self.subTest(name=name):
                self.metadata["files"][0]["path"] = name
                self.write_metadata()
                with self.assertRaisesRegex(VerificationError, "selected-file path"):
                    self.run_verify()


if __name__ == "__main__":
    unittest.main()
