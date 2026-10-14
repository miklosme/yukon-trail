#!/usr/bin/env python3
"""Prepare source-derived selected journal vocabulary for browser rules, locally."""
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
try:
    from .yukonres import read_index, verify_source, DEFAULT_SOURCE_MANIFEST
    from .yukonjournal import source_vocabulary, linda_text_from_raw_cstr505, EXE_SHA256
except ImportError:
    from yukonres import read_index, verify_source, DEFAULT_SOURCE_MANIFEST
    from yukonjournal import source_vocabulary, linda_text_from_raw_cstr505, EXE_SHA256


def prepare(archive, executable, output):
    if output.exists():
        raise FileExistsError('Refusing to replace existing generated assets')
    vocabulary = source_vocabulary(executable.read_bytes())
    with archive.open('rb') as source:
        archive_hash = verify_source(source, DEFAULT_SOURCE_MANIFEST)
        record = read_index(source).by_key()['CSTR:505']
        source.seek(record.offset)
        raw = source.read(record.length)
    # Exact bounded parser; no fallback vocabulary or changed original prose.
    linda_text = linda_text_from_raw_cstr505(raw)
    strings = {k: ([v.decode('latin1') for v in value] if isinstance(value, tuple)
                   else value.decode('latin1')) for k, value in asdict(vocabulary).items()}
    data = {'schema': 'selected-linda-journal-v1', 'vocabulary': strings,
            'linda_text': linda_text.decode('latin1'), 'provenance': {
                'executable_sha256': EXE_SHA256, 'archive_sha256': archive_hash,
                'resource': record.key, 'offset': record.offset, 'length': record.length,
                'sha256': hashlib.sha256(raw).hexdigest(),
                'vocabulary_source': 'NE data13 strings; addresses in docs/SEATTLE-RULES.md',
                'encoding': 'one-byte Latin1 mapping; original font/rendering not inferred'}}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, indent=2, sort_keys=True) + '\n')
    return data['provenance']


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ('archive', 'executable', 'output'):
        parser.add_argument(arg, type=Path)
    args = parser.parse_args()
    print(json.dumps(prepare(args.archive, args.executable, args.output), sort_keys=True))
