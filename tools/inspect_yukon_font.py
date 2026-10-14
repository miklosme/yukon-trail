#!/usr/bin/env python3
"""Source-verified SFNT/name inventory; no glyph decoding or rendering claim."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

EXPECTED = '6a2c8f3356a9affef9711a14070b5de1cac95c320799360d10c78d8df40f4f18'


def inspect(path):
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != EXPECTED:
        raise ValueError('Unsupported Yukon font source identity')
    if data[:4] != b'\x00\x01\x00\x00':
        raise ValueError('Unsupported SFNT version')
    count = struct.unpack_from('>H', data, 4)[0]
    if 12 + count * 16 > len(data):
        raise ValueError('Truncated SFNT directory')
    tables = {}
    for i in range(count):
        tag, checksum, offset, length = struct.unpack_from('>4sIII', data, 12 + i * 16)
        name = tag.decode('ascii')
        if name in tables or offset + length > len(data):
            raise ValueError('Duplicate/out-of-range table')
        tables[name] = {'offset': offset, 'length': length, 'declared_checksum': checksum}
    table = tables['name']; offset = table['offset']; end = offset + table['length']
    version, names_count, storage = struct.unpack_from('>3H', data, offset)
    if version != 0 or offset + 6 + names_count * 12 > end:
        raise ValueError('Unsupported/truncated naming table')
    names = []
    for i in range(names_count):
        platform, encoding, language, name_id, length, relative = struct.unpack_from('>6H', data, offset + 6 + i * 12)
        start = offset + storage + relative
        if start < offset + 6 + names_count * 12 or start + length > end:
            raise ValueError('Naming string outside storage')
        if name_id not in (1, 2, 4, 6):
            continue
        if platform in (0, 3):
            codec = 'utf-16-be'
        elif platform == 1 and encoding == 0:
            codec = 'mac_roman'
        else:
            raise ValueError('Unsupported selected name encoding')
        names.append({'platform': platform, 'encoding': encoding, 'language': language,
                      'name_id': name_id, 'file_offset': start, 'byte_length': length,
                      'text': data[start:start + length].decode(codec)})
    return {'source': str(path), 'sha256': EXPECTED, 'bytes': len(data),
            'tables': tables, 'selected_names': names,
            'scope': 'Directory bounds and selected naming strings only; no table checksum, glyph, hinting or browser rendering validation'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('font', type=Path)
    print(json.dumps(inspect(parser.parse_args().font), indent=2, sort_keys=True))
