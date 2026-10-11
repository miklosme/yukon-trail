#!/usr/bin/env python3
"""Bounded CBMP recovery probe; see docs/formats/CBMP.md for supported scope."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import struct
import zlib

try:
    from .yukonres import read_index, verify_source, DEFAULT_SOURCE_MANIFEST
except ImportError:
    from yukonres import read_index, verify_source, DEFAULT_SOURCE_MANIFEST

EXE_SHA256 = "9ca8f0a12f4798e762fbf27634f99afcb5c0c1a3836604bf0a4049a73227dd06"


class BitmapError(ValueError):
    """Unsupported or malformed image data."""


class Bits:
    def __init__(self, data: bytes, limit: int, position: int = 0):
        if not 0 <= position <= limit <= len(data) * 8:
            raise BitmapError("invalid bitstream bounds")
        self.data, self.limit, self.position = data, limit, position

    def get(self, count: int) -> int:
        if count < 0 or self.position + count > self.limit:
            raise BitmapError(f"truncated bitstream at bit {self.position}")
        value = 0
        for _ in range(count):
            value = value * 2 + ((self.data[self.position // 8] >> (7 - self.position % 8)) & 1)
            self.position += 1
        return value


def values(reader: Bits, base: int, extension: int, maximum: int, count: int,
           hybrid: bool = True, trace=None) -> bytes:
    """NE 0001:0062/0129: preserve byte masks and byte result arithmetic."""
    if not (1 <= base <= 8 and 1 <= extension <= 8 and 0 <= maximum <= 255 and 1 <= count <= 64):
        raise BitmapError("unsupported integer-reader parameters")
    start = reader.position
    result = bytearray()
    for _ in range(count):
        if hybrid and maximum >> base:
            small = base - 1
            low = (1 << small) & 255
            width = extension + small - 1
            # The original keeps these masks in bytes, but computes groups in BX.
            big_mask = ((2 << width) - 1) & 255
            groups = min(32, (((maximum - low - big_mask - 1) >> width) + 2) & 65535)
            limit = (groups - 1) & 255
            if reader.get(1):
                value = reader.get(small)
            else:
                group = 0
                while group < limit and not reader.get(1):
                    group += 1
                value = (low + (group << width) + reader.get(width if group < limit else width + 1)) & 255
        else:
            value = reader.get(base)
            if value == (1 << base) - 1:
                while value != maximum:
                    part = reader.get(extension)
                    value = (value + part) & 255
                    if part != (1 << extension) - 1:
                        break
        if value > maximum:
            raise BitmapError(f"palette value {value} exceeds {maximum}")
        result.append(value)
    output = bytes(result)
    if trace is not None:
        trace(reader.data, start, base, extension, maximum, count, hybrid, output, reader.position)
    return output


def _palette(reader: Bits, global_palette: bytes, trace) -> bytes:
    control = reader.get(2)
    if control == 0:
        return global_palette
    if control not in (1, 2):
        raise BitmapError(f"unsupported local palette control {control}")
    count, base, extension = reader.get(6), reader.get(3) + 1, reader.get(3) + 1
    tokens = values(reader, base, extension, len(global_palette) - 1, count, trace=trace)
    output = bytearray()
    index = 0
    cursor = 0
    while cursor < len(tokens):
        token = tokens[cursor]
        cursor += 1
        if control == 1:
            index += token
        elif cursor == 1:
            index = token
        elif token:
            index += token
        else:
            if cursor == len(tokens):
                raise BitmapError("local palette reset lacks its index")
            index = tokens[cursor]
            cursor += 1
        if index >= len(global_palette):
            raise BitmapError("local palette index outside global palette")
        output.append(global_palette[index])
        if control == 1:
            index += 1
    return bytes(output)


def _block(reader: Bits, palette: bytes, trace, active: tuple[int, ...] = (),
           palette_control: bool = True) -> tuple[bytes, int]:
    start = reader.position
    if start in active or len(active) >= 64:
        raise BitmapError("cyclic or excessively nested block reference")
    kind = reader.get(2)
    if kind < 2:
        local = _palette(reader, palette, trace) if palette_control else palette
        base, extension = reader.get(3) + 1, reader.get(3) + 1
        indices = values(reader, base, extension, len(local) - 1, 64, kind == 1, trace)
        return bytes(local[index] for index in indices), 0
    if kind == 2:
        position = reader.get(24)
        child = Bits(reader.data, reader.limit, position)
        output, _ = _block(child, palette, trace, active + (start,), palette_control)
        return output, 0
    value = reader.get(8)
    repeat = reader.get(16) if reader.get(1) else 0
    return bytes([value]) * 64, repeat


def unpack(chunk: bytes, expected_size: int, trace=None) -> bytes:
    if len(chunk) < 12:
        raise BitmapError("truncated compression header")
    header_size, algorithm, flags, bit_count, expanded = struct.unpack_from("<HBBII", chunk)
    if header_size != 12 or algorithm != 3 or flags != 1:
        raise BitmapError("only 12-byte algorithm-3, flags-1 image headers are supported")
    if expanded != expected_size or expanded % 64 or expanded > 16 * 1024 * 1024:
        raise BitmapError("expanded size does not match padded image geometry")
    if len(chunk) <= header_size:
        raise BitmapError("missing global palette")
    count = chunk[header_size] + 1
    end = header_size + 1 + count
    if end > len(chunk):
        raise BitmapError("truncated global palette")
    palette = chunk[header_size + 1:end]
    reader = Bits(chunk[end:], bit_count)
    output = bytearray()
    while len(output) < expanded:
        block, repeat = _block(reader, palette, trace)
        if len(output) + 64 * (repeat + 1) > expanded:
            raise BitmapError("block repeat exceeds expanded size")
        output.extend(block * (repeat + 1))
    if reader.position != bit_count:
        raise BitmapError(f"consumed {reader.position} of {bit_count} declared bits")
    if (bit_count + 7) // 8 != len(reader.data):
        raise BitmapError("unexpected bytes after compressed bitstream")
    return bytes(output)


@dataclass(frozen=True)
class Frame:
    width: int
    height: int
    offset: int
    length: int
    pixels: bytes


def decode(data: bytes, trace=None) -> tuple[Frame, ...]:
    if len(data) < 2:
        raise BitmapError("truncated frame count")
    count = struct.unpack_from("<H", data)[0]
    if not count or 2 + 12 * count > len(data):
        raise BitmapError("invalid frame table")
    frames = []
    for index in range(count):
        width, height, offset, length = struct.unpack_from("<HHII", data, 2 + 12 * index)
        if not (0 < width < 32768 and 0 < height < 32768):
            raise BitmapError("zero or signed frame dimensions are unsupported")
        if offset < 2 + 12 * count or length > len(data) - offset:
            raise BitmapError("frame range outside payload")
        columns, rows = (width + 7) // 8, (height + 7) // 8
        blocks = unpack(data[offset:offset + length], columns * rows * 64, trace)
        pixels = bytearray(width * height)
        for tile in range(columns * rows):
            left, top = (tile // rows) * 8, (tile % rows) * 8
            for y in range(min(8, height - top)):
                size = min(8, width - left)
                destination = (top + y) * width + left
                source = tile * 64 + y * 8
                pixels[destination:destination + size] = blocks[source:source + size]
        frames.append(Frame(width, height, offset, length, bytes(pixels)))
    return tuple(frames)


def source_palette(executable: bytes) -> bytes:
    if hashlib.sha256(executable).hexdigest() != EXE_SHA256:
        raise BitmapError("unsupported executable identity")
    # Observed custom NE type 2000, ID100, file offset 0x618e0; NE1:5eb4.
    resource = executable[0x618e0:0x618e0 + 1056]
    if resource[:4] != b"RIFF" or resource[8:16] != b"PAL data" or resource[20:24] != b"\x00\x03\x00\x01":
        raise BitmapError("unexpected executable palette header")
    return b"".join(resource[24 + 4 * i:27 + 4 * i] for i in range(256))


def png(frame: Frame, palette: bytes) -> bytes:
    if len(palette) != 768:
        raise BitmapError("palette must contain 256 RGB entries")
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))
    scanlines = b"".join(b"\0" + frame.pixels[y * frame.width:(y + 1) * frame.width] for y in range(frame.height))
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", frame.width, frame.height, 8, 3, 0, 0, 0))
            + chunk(b"PLTE", palette) + chunk(b"IDAT", zlib.compress(scanlines)) + chunk(b"IEND", b""))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("executable", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--id", type=int, action="append", required=True)
    args = parser.parse_args()
    palette = source_palette(args.executable.read_bytes())
    args.output.mkdir(parents=True, exist_ok=True)
    manifest = {"archive_sha256": None, "executable_sha256": EXE_SHA256,
                "palette_file_offset": "0x618e0", "palette_rgb_sha256": hashlib.sha256(palette).hexdigest(),
                "resources": {}}
    with args.archive.open("rb") as source:
        manifest["archive_sha256"] = verify_source(source, DEFAULT_SOURCE_MANIFEST)
        index = read_index(source).by_key()
        for resource_id in sorted(set(args.id)):
            key = f"CBMP:{resource_id}"
            if key not in index:
                raise BitmapError(f"missing {key}")
            resource = index[key]
            source.seek(resource.offset)
            payload = source.read(resource.length)
            records = []
            for number, frame in enumerate(decode(payload)):
                name = f"CBMP-{resource_id}-frame-{number}.png"
                output = png(frame, palette)
                (args.output / name).write_bytes(output)
                records.append({"frame": number, "width": frame.width, "height": frame.height,
                                "payload_offset": frame.offset, "compressed_length": frame.length,
                                "indices_sha256": hashlib.sha256(frame.pixels).hexdigest(),
                                "png": name, "png_sha256": hashlib.sha256(output).hexdigest()})
            manifest["resources"][key] = {"offset": resource.offset, "length": resource.length,
                                          "sha256": hashlib.sha256(payload).hexdigest(), "frames": records}
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"resources": len(manifest["resources"]), "output": str(args.output)}))


if __name__ == "__main__":
    main()
