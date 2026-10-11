#!/usr/bin/env python3
"""Verify source identity and compare selected Windows files directly to the disc."""

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]


class VerificationError(ValueError):
    """Source identity or a selected-file comparison failed."""


def stream_identity(stream):
    digest = hashlib.sha256()
    size = 0
    while block := stream.read(1024 * 1024):
        size += len(block)
        digest.update(block)
    return size, digest.hexdigest()


def file_identity(path):
    with path.open("rb") as source:
        return stream_identity(source)


def disc_member_identity(iso, member):
    # Read the disc directly with the extraction reader; do not reuse the copy.
    environment = {**os.environ, "LC_ALL": "C"}
    with subprocess.Popen(
        ["bsdtar", "-xOf", str(iso), "--", member],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=environment,
    ) as process:
        identity = stream_identity(process.stdout)
        diagnostic = process.stderr.read().decode("utf-8", errors="replace").strip()
        if process.wait() != 0:
            raise VerificationError(f"disc read failed for {member}: {diagnostic}")
    return identity


def verify(iso, windows_dir, source_manifest, extraction_manifest):
    original = json.loads(source_manifest.read_text(encoding="utf-8"))
    extracted = json.loads(extraction_manifest.read_text(encoding="utf-8"))
    candidates = [entry for entry in original["files"] if entry["role"] == "source_disc_image"]
    if len(candidates) != 1:
        raise VerificationError("source manifest must identify exactly one disc image")
    expected_disc = candidates[0]
    disc_identity = file_identity(iso)
    if disc_identity != (expected_disc["size_bytes"], expected_disc["sha256"]):
        raise VerificationError("disc size/SHA-256 differs from the source manifest")
    if extracted["source_iso_sha256"] != expected_disc["sha256"]:
        raise VerificationError("extraction metadata refers to a different disc")
    if not extracted["files"]:
        raise VerificationError("extraction metadata has no selected files")
    seen = set()
    # Validate every entry name before starting container reads.
    for entry in extracted["files"]:
        name = entry["path"]
        path = PurePosixPath(name)
        if (not name or path.is_absolute() or ".." in path.parts or str(path) != name
                or any(char in name for char in "*?[]\\\0")):
            raise VerificationError(f"unsupported selected-file path: {name!r}")
        if name in seen:
            raise VerificationError(f"duplicate selected-file path: {name}")
        seen.add(name)
    verified = []
    for entry in extracted["files"]:
        member = entry["path"]
        expected = entry["size_bytes"], entry["sha256"]
        local = file_identity(windows_dir / member)
        if local != expected:
            raise VerificationError(f"extracted file differs from metadata: {member}")
        direct = disc_member_identity(iso, member)
        if direct != expected:
            raise VerificationError(f"disc entry differs from extraction metadata: {member}")
        verified.append({"path": member, "size_bytes": direct[0], "sha256": direct[1]})
    return {
        "verification_version": 1,
        "method": "bsdtar direct-disc stream versus extracted file and recorded identity",
        "source": {"size_bytes": disc_identity[0], "sha256": disc_identity[1]},
        "verified_file_count": len(verified),
        "files": verified,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iso", type=Path, default=REPO_ROOT / "original/iso/YUKONCD.ISO")
    parser.add_argument("--windows-dir", type=Path, default=REPO_ROOT / "original/extracted/windows")
    parser.add_argument("--source-manifest", type=Path, default=REPO_ROOT / "docs/source-manifest.json")
    parser.add_argument("--extraction-manifest", type=Path, default=REPO_ROOT / "docs/windows-extraction.json")
    args = parser.parse_args()
    try:
        result = verify(args.iso, args.windows_dir, args.source_manifest, args.extraction_manifest)
    except (VerificationError, OSError, KeyError, TypeError, json.JSONDecodeError) as error:
        print(f"verify_source_files: {error}", file=sys.stderr)
        return 1
    json.dump(result, sys.stdout, indent=2, sort_keys=True)
    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
