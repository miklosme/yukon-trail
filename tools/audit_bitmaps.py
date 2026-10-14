#!/usr/bin/env python3
"""Inventory bounded decoder acceptance; this is not native rendering validation."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct

try:
    from .yukonbmp import BitmapError, decode
    from .yukonres import DEFAULT_SOURCE_MANIFEST, read_index, verify_source
except ImportError:
    from yukonbmp import BitmapError, decode
    from yukonres import DEFAULT_SOURCE_MANIFEST, read_index, verify_source


def inspect_payload(payload):
    """Retain frame geometry even if the bounded decoder rejects a later frame."""
    count = struct.unpack_from('<H', payload)[0] if len(payload) >= 2 else 0
    table = []
    if count and 2 + 12 * count <= len(payload):
        for i in range(count):
            width, height, offset, length = struct.unpack_from('<HHII', payload, 2 + 12 * i)
            header = None
            if offset >= 2 + 12 * count and length >= 12 and offset + length <= len(payload):
                header = list(struct.unpack_from('<HBBII', payload, offset))
            table.append(dict(frame=i, width=width, raw_height=height,
                              chunk_offset=offset, chunk_length=length, header=header))
    result = dict(declared_frames=count, table=table)
    try:
        frames = decode(payload)
    except BitmapError as error:
        result.update(status='unsupported_or_invalid', reason=str(error))
    else:
        result.update(status='decoded', frames=[dict(frame=i, width=f.width, height=f.height,
                      indices_sha256=hashlib.sha256(f.pixels).hexdigest()) for i, f in enumerate(frames)])
    return result


def audit(archive):
    with archive.open('rb') as source:
        source_hash = verify_source(source, DEFAULT_SOURCE_MANIFEST)
        index = read_index(source)
        resources = {}
        for resource in index.resources:
            if resource.tag != 'CBMP':
                continue
            source.seek(resource.offset)
            payload = source.read(resource.length)
            result = inspect_payload(payload)
            result.update(offset=resource.offset, length=resource.length,
                          payload_sha256=hashlib.sha256(payload).hexdigest())
            resources[resource.key] = result
    statuses = Counter(r['status'] for r in resources.values())
    return dict(schema_version=1, archive_sha256=source_hash,
                scope='bounded decoder acceptance only; no native rendering/compositing claim',
                summary=dict(resources=len(resources), declared_frames=sum(r['declared_frames'] for r in resources.values()),
                             decoded_frames=sum(len(r.get('frames', [])) for r in resources.values()),
                             statuses=dict(sorted(statuses.items()))), resources=resources)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('report', type=Path)
    args = parser.parse_args()
    if args.report.exists():
        parser.error('report already exists; use a fresh path')
    report = audit(args.archive)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    print(json.dumps(report['summary'], sort_keys=True))


if __name__ == '__main__':
    main()
