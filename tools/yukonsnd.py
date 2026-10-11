#!/usr/bin/env python3
"""Bounded sequential PSND:1 recovery; seeking/other sound variants unsupported."""
from dataclasses import dataclass
import argparse
import hashlib
import json
from pathlib import Path
import struct
import wave

try:
    from .yukonbmp import BitmapError, Bits, _block
    from .yukonres import read_index, verify_source, DEFAULT_SOURCE_MANIFEST
except ImportError:
    from yukonbmp import BitmapError, Bits, _block
    from yukonres import read_index, verify_source, DEFAULT_SOURCE_MANIFEST


class SoundError(ValueError):
    """Malformed or unsupported selected sound."""


@dataclass(frozen=True)
class Sound:
    channels: int
    sample_bits: int
    sample_rate: int
    order: int
    packed_bits: int
    encoded_values: bytes
    samples: bytes
    record_metadata: bytes
    chunk_metadata: bytes


def integrate(data: bytes, order: int, state: bytes = bytes([128]) * 4) -> tuple[bytes, bytes]:
    """NE3:9b34, byte-wrapping repeated integration, caller retains four bytes."""
    if order not in (1, 2, 3, 4) or len(state) != 4:
        raise SoundError("unsupported integration parameters")
    result, accumulators = bytearray(), bytearray(state)
    for value in data:
        for index in range(order - 1, -1, -1):
            accumulators[index] = (accumulators[index] + value + 128) & 255
            value = accumulators[index]
        result.append(value)
    return bytes(result), bytes(accumulators)


def decode(payload: bytes, trace=None) -> Sound:
    # Selected proof layout: header record, retained index record, data record.
    if len(payload) < 24 or payload[:6] != b"\x01\x81\x0c\x00\x00\x00":
        raise SoundError("unsupported PSND header record")
    channels, sample_bits, rate_code, order = payload[6], payload[7], payload[8], payload[10]
    if (channels, sample_bits, rate_code, order) != (1, 8, 22, 2):
        raise SoundError("only selected mono 8-bit rate-code22 order2 sound supported")
    position = 12
    if payload[position:position + 2] != b"\x02\x80":
        raise SoundError("unsupported PSND index record")
    index_length = struct.unpack_from("<I", payload, position + 2)[0]
    if index_length < 10 or position + index_length + 6 > len(payload):
        raise SoundError("invalid PSND index record length")
    metadata = payload[position:position + index_length]
    # NE3:b3cd reads a word at record+8 (not a dword at+6).
    index_count = struct.unpack_from("<H", metadata, 8)[0]
    if index_length != 10 + 8 * index_count:
        raise SoundError("PSND index count does not match record length")
    position += index_length
    if payload[position:position + 6] != b"\x00\x80\x06\x00\x00\x00":
        raise SoundError("unsupported PSND data record")
    position += 6
    chunk = payload[position:]
    if len(chunk) < 54:
        raise SoundError("truncated sound compression header")
    header_size, algorithm, flags, bit_count, expanded = struct.unpack_from("<HBBII", chunk)
    if (header_size, algorithm, flags) != (54, 3, 2):
        raise SoundError("unsupported sound compression header")
    if not expanded or expanded % 64 or expanded > 16 * 1024 * 1024:
        raise SoundError("invalid sound expanded size")
    # NE3:baae initializes these pairs; the local palette-control byte is zero.
    palette = bytes(128 + index // 2 if index % 2 == 0 else 127 - index // 2 for index in range(256))
    output = bytearray()
    try:
        reader = Bits(chunk[header_size:], bit_count)
        while len(output) < expanded:
            block, repeat = _block(reader, palette, trace, palette_control=False)
            if len(output) + 64 * (repeat + 1) > expanded:
                raise SoundError("sound block repeat exceeds expanded size")
            output.extend(block * (repeat + 1))
    except BitmapError as error:
        raise SoundError(str(error)) from error
    if reader.position != bit_count or (bit_count + 7) // 8 != len(reader.data):
        raise SoundError("sound bit consumption/length mismatch")
    encoded = bytes(output)
    samples, _ = integrate(encoded, order)
    # Source getter binding NE6:82c0+3c -> NE3:b226 -> object+20 -> byte8;
    # NE3:92dc maps22 to22050. Channels/depth similarly bind+34/+38.
    return Sound(channels, sample_bits, 22050, order, bit_count, encoded, samples, metadata, chunk[12:header_size])


def write_wav(sound: Sound, path: Path):
    with wave.open(str(path), "wb") as output:
        output.setnchannels(sound.channels)
        output.setsampwidth(sound.sample_bits // 8)
        output.setframerate(sound.sample_rate)
        output.writeframes(sound.samples)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    with args.archive.open("rb") as source:
        archive_hash = verify_source(source, DEFAULT_SOURCE_MANIFEST)
        resource = read_index(source).by_key()["PSND:1"]
        source.seek(resource.offset)
        payload = source.read(resource.length)
    sound = decode(payload)
    args.output.mkdir(parents=True, exist_ok=True)
    wav = args.output / "PSND-1.wav"
    write_wav(sound, wav)
    report = {"archive_sha256": archive_hash, "resource": "PSND:1", "offset": resource.offset,
              "length": resource.length, "payload_sha256": hashlib.sha256(payload).hexdigest(),
              "channels": sound.channels, "sample_bits": sound.sample_bits, "sample_rate": sound.sample_rate,
              "integration_order": sound.order, "sample_count": len(sound.samples), "packed_bits": sound.packed_bits,
              "encoded_values_sha256": hashlib.sha256(sound.encoded_values).hexdigest(),
              "pcm_sha256": hashlib.sha256(sound.samples).hexdigest(), "wav_sha256": hashlib.sha256(wav.read_bytes()).hexdigest(),
              "record_metadata_sha256": hashlib.sha256(sound.record_metadata).hexdigest(),
              "chunk_metadata_sha256": hashlib.sha256(sound.chunk_metadata).hexdigest(),
              "scope": "sequential PSND:1 only; index metadata retained, seek/loop semantics unimplemented"}
    (args.output / "sound-manifest.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
