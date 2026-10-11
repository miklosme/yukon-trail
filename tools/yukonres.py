#!/usr/bin/env python3
"""Validate and inventory the supplied YUKONRES; optionally export raw records."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import struct
import sys
from typing import BinaryIO


HEADER_SIZE = 0x58
GROUP_SIZE = 8
RECORD_SIZE = 14
DEFAULT_SOURCE_MANIFEST = Path(__file__).resolve().parents[1] / "docs/source-manifest.json"


class ArchiveError(ValueError):
    """Malformed, unsupported, or incorrectly identified archive."""


@dataclass(frozen=True)
class Group:
    tag: str
    count: int
    first: int


@dataclass(frozen=True)
class Resource:
    tag: str
    resource_id: int
    length: int
    offset: int
    index: int
    entry_offset: int

    @property
    def key(self) -> str:
        return f"{self.tag}:{self.resource_id}"


@dataclass(frozen=True)
class ArchiveIndex:
    groups: tuple[Group, ...]
    resources: tuple[Resource, ...]
    index_end: int
    size: int

    def by_key(self) -> dict[str, Resource]:
        return {resource.key: resource for resource in self.resources}


def _tag(raw: bytes, location: int) -> str:
    if len(raw) != 4 or any(byte < 0x20 or byte > 0x7E for byte in raw):
        raise ArchiveError(f"invalid four-byte ASCII tag at 0x{location:x}")
    return raw.decode("ascii")


def _table_bounds(header: bytes, archive_size: int) -> tuple[int, int, int, int]:
    if len(header) < HEADER_SIZE or archive_size < HEADER_SIZE:
        raise ArchiveError("truncated archive header")
    if header[4:8] != b"MECC":
        raise ArchiveError("unsupported archive signature at 0x4")
    group_count, record_count = struct.unpack_from(">HH", header, 0x54)
    if group_count == 0 or record_count == 0:
        raise ArchiveError("empty group or resource table is unsupported")
    record_start = HEADER_SIZE + group_count * GROUP_SIZE
    index_end = record_start + record_count * RECORD_SIZE
    if index_end > archive_size:
        raise ArchiveError(f"index ends at 0x{index_end:x}, outside archive size 0x{archive_size:x}")
    return group_count, record_count, record_start, index_end


def parse_index(data: bytes, *, archive_size: int | None = None) -> ArchiveIndex:
    """Parse index bytes with an explicit full-file size when payloads are absent."""
    size = len(data) if archive_size is None else archive_size
    group_count, record_count, record_start, index_end = _table_bounds(data, size)
    if len(data) < index_end:
        raise ArchiveError(f"truncated index: need {index_end} bytes, got {len(data)}")
    groups = []
    tags = set()
    next_record = 0
    for index in range(group_count):
        location = HEADER_SIZE + index * GROUP_SIZE
        raw_tag, count, first = struct.unpack_from(">4sHH", data, location)
        tag = _tag(raw_tag, location)
        if tag in tags:
            raise ArchiveError(f"duplicate group {tag} at 0x{location:x}")
        tags.add(tag)
        if count == 0 or first != next_record or first + count > record_count:
            raise ArchiveError(f"invalid group coverage for {tag} at 0x{location:x}")
        next_record = first + count
        groups.append(Group(tag, count, first))
    if next_record != record_count:
        raise ArchiveError(f"groups cover {next_record} of {record_count} resources")

    resources = []
    keys = set()
    for group in groups:
        for index in range(group.first, group.first + group.count):
            location = record_start + index * RECORD_SIZE
            raw_tag, resource_id, length, offset = struct.unpack_from(">4sHII", data, location)
            tag = _tag(raw_tag, location)
            key = (tag, resource_id)
            if tag != group.tag:
                raise ArchiveError(f"group {group.tag} contains {tag}:{resource_id} at 0x{location:x}")
            if key in keys:
                raise ArchiveError(f"duplicate resource {tag}:{resource_id} at 0x{location:x}")
            keys.add(key)
            if offset < index_end or offset > size or length > size - offset:
                raise ArchiveError(f"{tag}:{resource_id} range 0x{offset:x}+0x{length:x} outside payload area")
            resources.append(Resource(tag, resource_id, length, offset, index, location))

    positive_ranges = sorted((r for r in resources if r.length), key=lambda r: r.offset)
    for previous, current in zip(positive_ranges, positive_ranges[1:]):
        if current.offset < previous.offset + previous.length:
            raise ArchiveError(f"unsupported payload overlap: {previous.key} and {current.key}")
    return ArchiveIndex(tuple(groups), tuple(resources), index_end, size)


def read_index(source: BinaryIO) -> ArchiveIndex:
    source.seek(0, 2)
    size = source.tell()
    source.seek(0)
    header = source.read(HEADER_SIZE)
    _, _, _, index_end = _table_bounds(header, size)
    return parse_index(header + source.read(index_end - HEADER_SIZE), archive_size=size)


def sha256_stream(source: BinaryIO) -> str:
    source.seek(0)
    digest = hashlib.sha256()
    while chunk := source.read(1024 * 1024):
        digest.update(chunk)
    return digest.hexdigest()


def verify_source(source: BinaryIO, manifest_path: Path) -> str:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    candidates = [item for item in manifest["files"] if item["role"] == "resource_archive"]
    if len(candidates) != 1:
        raise ArchiveError("source manifest must identify exactly one resource archive")
    expected = candidates[0]
    source.seek(0, 2)
    size = source.tell()
    if size != expected["size_bytes"]:
        raise ArchiveError(f"unsupported source size {size}; expected {expected['size_bytes']}")
    digest = sha256_stream(source)
    if digest != expected["sha256"]:
        raise ArchiveError(f"unsupported source SHA-256 {digest}")
    return digest


def manifest_for(index: ArchiveIndex, source_name: str, source_hash: str) -> dict:
    resources: dict[str, dict] = {}
    for resource in sorted(index.resources, key=lambda r: (r.tag, r.resource_id)):
        resources.setdefault(resource.tag, {})[str(resource.resource_id)] = {
            "index": resource.index,
            "entry_offset": resource.entry_offset,
            "offset": resource.offset,
            "length": resource.length,
        }
    return {
        "manifest_version": 1,
        "format": "YUKONRES-index-1.1",
        "source": {"name": source_name, "size_bytes": index.size, "sha256": source_hash},
        "index_end": index.index_end,
        "group_count": len(index.groups),
        "record_count": len(index.resources),
        "groups": [{"type": g.tag, "count": g.count, "first_record": g.first} for g in index.groups],
        "resources": resources,
        "raw_exports": {},
    }


def export_archive(source_path: Path, output_dir: Path, keys: list[str], source_manifest: Path) -> dict:
    """Validate before writing; refuse nonempty destinations and existing files."""
    with source_path.open("rb") as source:
        source_hash = verify_source(source, source_manifest)
        index = read_index(source)
        resources = index.by_key()
        if len(keys) != len(set(keys)):
            raise ArchiveError("duplicate --extract key")
        for key in keys:
            if key not in resources:
                raise ArchiveError(f"resource not found: {key}")
        if output_dir.exists() and (not output_dir.is_dir() or any(output_dir.iterdir())):
            raise ArchiveError(f"output directory must be new or empty: {output_dir}")
        # Tags are printable ASCII for inventory, but must be safe filenames for export.
        for key in keys:
            if any(not (char.isascii() and (char.isalnum() or char == "_")) for char in resources[key].tag):
                raise ArchiveError(f"resource tag is unsupported for filename export: {key}")
        report = manifest_for(index, source_path.name, source_hash)
        output_dir.mkdir(parents=True, exist_ok=True)
        for key in sorted(keys):
            resource = resources[key]
            source.seek(resource.offset)
            name = f"{resource.tag}-{resource.resource_id}.bin"
            digest = hashlib.sha256()
            remaining = resource.length
            with (output_dir / name).open("xb") as output:
                while remaining:
                    chunk = source.read(min(remaining, 1024 * 1024))
                    if not chunk:
                        raise ArchiveError(f"short payload read: {key}")
                    output.write(chunk)
                    digest.update(chunk)
                    remaining -= len(chunk)
            report["raw_exports"][key] = {"path": name, "sha256": digest.hexdigest()}
        with (output_dir / "manifest.json").open("x", encoding="utf-8") as output:
            json.dump(report, output, indent=2, sort_keys=True)
            output.write("\n")
        return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--extract", action="append", default=[], metavar="TYPE:ID")
    parser.add_argument("--source-manifest", type=Path, default=DEFAULT_SOURCE_MANIFEST)
    args = parser.parse_args(argv)
    try:
        report = export_archive(args.archive, args.output_dir, args.extract, args.source_manifest)
    except (ArchiveError, OSError, KeyError, TypeError, json.JSONDecodeError) as error:
        print(f"yukonres: {error}", file=sys.stderr)
        return 1
    print(f"Validated {report['record_count']} records in {report['group_count']} groups; wrote {args.output_dir / 'manifest.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
