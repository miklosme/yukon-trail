#!/usr/bin/env python3
"""Compare recovered bubble border pixels with a native RGB PNG capture.

Deliberately excludes indices 0 (exterior) and 159 (dialogue interior); those
areas can contain background, text and the mouse pointer. No automatic alignment.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import zlib

try:
    from .yukonbmp import decode, source_palette
    from .yukonres import read_index, verify_source, DEFAULT_SOURCE_MANIFEST
except ImportError:
    from yukonbmp import decode, source_palette
    from yukonres import read_index, verify_source, DEFAULT_SOURCE_MANIFEST


def read_rgb_capture(data):
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not PNG")
    position, compressed, dimensions = 8, bytearray(), None
    while position < len(data):
        if position + 12 > len(data):
            raise ValueError("truncated PNG chunk")
        size, kind = struct.unpack_from(">I4s", data, position)
        end = position + 12 + size
        if end > len(data):
            raise ValueError("truncated PNG payload")
        payload = data[position + 8:position + 8 + size]
        crc = struct.unpack_from(">I", data, end - 4)[0]
        if zlib.crc32(kind + payload) != crc:
            raise ValueError("bad PNG CRC")
        if kind == b"IHDR":
            width, height, depth, color, compression, filtering, interlace = struct.unpack(">IIBBBBB", payload)
            if not (0 < width <= 2048 and 0 < height <= 2048) or (depth, color, compression, filtering, interlace) != (8, 2, 0, 0, 0):
                raise ValueError("only bounded noninterlaced 8-bit RGB captures supported")
            dimensions = (width, height)
        elif kind == b"IDAT":
            compressed.extend(payload)
        elif kind == b"IEND":
            if payload or end != len(data):
                raise ValueError("unexpected PNG ending")
            break
        position = end
    else:
        raise ValueError("missing PNG ending")
    if dimensions is None:
        raise ValueError("missing PNG header")
    width, height = dimensions
    stride = width * 3
    inflater = zlib.decompressobj()
    raw = inflater.decompress(bytes(compressed), (stride + 1) * height + 1)
    if len(raw) != (stride + 1) * height or not inflater.eof or inflater.unused_data:
        raise ValueError("invalid decompressed PNG size")
    output = bytearray()
    previous = bytes(stride)
    for row in range(height):
        offset = row * (stride + 1)
        kind, encoded = raw[offset], raw[offset + 1:offset + 1 + stride]
        if kind > 4:
            raise ValueError("unknown PNG row filter")
        current = bytearray()
        for column, value in enumerate(encoded):
            left = current[column - 3] if column >= 3 else 0
            above = previous[column]
            corner = previous[column - 3] if column >= 3 else 0
            if kind == 1:
                value += left
            elif kind == 2:
                value += above
            elif kind == 3:
                value += (left + above) // 2
            elif kind == 4:
                prediction = left + above - corner
                distances = [abs(prediction - sample) for sample in (left, above, corner)]
                value += (left, above, corner)[distances.index(min(distances))]
            current.append(value & 255)
        output.extend(current)
        previous = current
    return width, height, bytes(output)


def compare(frame, palette, capture, x, y):
    width, height, pixels = capture
    if not (0 <= x <= width - frame.width and 0 <= y <= height - frame.height):
        raise ValueError("comparison rectangle outside capture")
    counts = {"border_pixels": 0, "mismatches": 0, "excluded_exterior": 0, "excluded_interior": 0}
    examples = []
    for position, index in enumerate(frame.pixels):
        if index in (0, 159):
            counts["excluded_exterior" if index == 0 else "excluded_interior"] += 1
            continue
        row, column = divmod(position, frame.width)
        expected = palette[index * 3:index * 3 + 3]
        # This comparison explicitly models the configured 6-bit VGA DAC:
        # discard two low bits, then replicate the high bits to RGB8.
        expected = bytes(((value >> 2) << 2) | (value >> 6) for value in expected)
        offset = ((y + row) * width + x + column) * 3
        actual = pixels[offset:offset + 3]
        counts["border_pixels"] += 1
        if actual != expected:
            counts["mismatches"] += 1
            if len(examples) < 5:
                examples.append({"x": column, "y": row, "index": index, "expected": list(expected), "actual": list(actual)})
    return {**counts, "examples": examples, "capture_origin": [x, y], "palette_conversion": "six-bit DAC, high-bit replication"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("executable", type=Path)
    parser.add_argument("capture", type=Path)
    parser.add_argument("report", type=Path)
    parser.add_argument("--id", type=int, required=True)
    parser.add_argument("--x", type=int, required=True)
    parser.add_argument("--y", type=int, required=True)
    args = parser.parse_args()
    palette = source_palette(args.executable.read_bytes())
    capture_bytes = args.capture.read_bytes()
    with args.archive.open("rb") as source:
        archive_hash = verify_source(source, DEFAULT_SOURCE_MANIFEST)
        resource = read_index(source).by_key()[f"CBMP:{args.id}"]
        source.seek(resource.offset)
        payload = source.read(resource.length)
        frame = decode(payload)[0]
    report = compare(frame, palette, read_rgb_capture(capture_bytes), args.x, args.y)
    report.update({"resource": resource.key, "payload_sha256": hashlib.sha256(payload).hexdigest(),
                   "archive_sha256": archive_hash, "capture_sha256": hashlib.sha256(capture_bytes).hexdigest()})
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report))
    if report["mismatches"] or not report["border_pixels"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
