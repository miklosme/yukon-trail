#!/usr/bin/env python3
"""Export raw header facts for the verified Yukon 1.1 executable; no code semantics."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

EXPECTED_SHA256 = "9ca8f0a12f4798e762fbf27634f99afcb5c0c1a3836604bf0a4049a73227dd06"


def inspect(path: Path) -> dict:
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != EXPECTED_SHA256:
        raise ValueError(f"Unexpected executable SHA-256: {digest}")
    ne = struct.unpack_from("<I", data, 0x3C)[0]
    if data[:2] != b"MZ" or data[ne:ne + 2] != b"NE":
        raise ValueError("Expected MZ/NE signatures")
    segment_count, module_count = struct.unpack_from("<HH", data, ne + 0x1C)
    segment_table = ne + struct.unpack_from("<H", data, ne + 0x22)[0]
    module_table = ne + struct.unpack_from("<H", data, ne + 0x28)[0]
    imported_names = ne + struct.unpack_from("<H", data, ne + 0x2A)[0]
    alignment_shift = struct.unpack_from("<H", data, ne + 0x32)[0]
    entry_offset, entry_segment = struct.unpack_from("<HH", data, ne + 0x14)
    segments = []
    for i in range(segment_count):
        sector, length_word, flags, minimum_allocation_word = struct.unpack_from("<4H", data, segment_table + i * 8)
        segments.append({"ne_segment": i + 1, "table_file_offset": segment_table + i * 8,
                         "sector_word": sector, "length_word": length_word,
                         "flags_word": flags, "minimum_allocation_word": minimum_allocation_word,
                         "initialized_file_offset": sector << alignment_shift if sector else None})
    modules = []
    for i in range(module_count):
        relative_offset = struct.unpack_from("<H", data, module_table + i * 2)[0]
        offset = imported_names + relative_offset
        length = data[offset]
        modules.append({"module_index": i + 1, "name_file_offset": offset,
                        "name": data[offset + 1:offset + 1 + length].decode("ascii")})
    occurrences = []
    offset = 0
    while (offset := data.find(b"YUKONRES", offset)) != -1:
        occurrences.append(offset)
        offset += len(b"YUKONRES")
    return {"source": str(path), "sha256": digest, "ne_header_file_offset": ne,
            "segment_table_file_offset": segment_table, "alignment_shift": alignment_shift,
            "entry_segment": entry_segment, "entry_offset": entry_offset,
            "segments": segments, "modules": modules,
            "yukonres_string_file_offsets": occurrences}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("executable", type=Path)
    args = parser.parse_args()
    print(json.dumps(inspect(args.executable), indent=2))


if __name__ == "__main__":
    main()
