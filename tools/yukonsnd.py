#!/usr/bin/env python3
"""Bounded sequential mono8-bit PSND recovery; seek/loop unsupported."""
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
    header_record_metadata: bytes
    data_record_metadata: bytes
    block_padding: bytes
    consumed_bits: int
    terminal_unused_bits: int
    terminal_unused_value: int


def integrate(data: bytes, order: int, state: bytes = bytes([128]) * 4) -> tuple[bytes, bytes]:
    """NE3:9b34, byte-wrapping repeated integration, caller retains four bytes."""
    if order not in (0, 1, 2, 3, 4) or len(state) != 4:
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
    # NE4:0f4c returns raw stream bytes; NE3:acea never reads record byte1.
    # Retain that uninterpreted byte instead of assigning flag semantics.
    if len(payload) < 24 or payload[0] != 1 or payload[2:6] != b"\x0c\x00\x00\x00":
        raise SoundError("unsupported PSND header record")
    channels, sample_bits, rate_code, order = payload[6], payload[7], payload[8], payload[10]
    if (channels, sample_bits, rate_code) != (1, 8, 22) or order not in (0, 1, 2, 3, 4):
        raise SoundError("only mono 8-bit rate-code22 order0..4 sounds supported")
    position = 12
    if payload[position] != 2:
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
    data_record = payload[position:position + 6]
    if len(data_record) != 6 or data_record[0] != 0 or data_record[2:6] != b"\x06\x00\x00\x00":
        raise SoundError("unsupported PSND data record")
    position += 6
    chunk = payload[position:]
    if len(chunk) < 12:
        raise SoundError("truncated sound compression header")
    header_size, algorithm, flags, bit_count, expanded = struct.unpack_from("<HBBII", chunk)
    if algorithm != 3:
        raise SoundError("unsupported sound compression algorithm")
    if len(chunk) < header_size:
        raise SoundError("truncated sound compression metadata")
    # Native baae/bfd8 proof covers all871sourceheaders +count1..26 matrix.
    # flags0 has only12basebytes; flags2 appendscount plus8*count opaque bytes.
    if flags == 0:
        if header_size != 12:
            raise SoundError("unsupported unindexed sound compression header")
    elif flags == 2:
        if header_size < 14:
            raise SoundError("truncated sound checkpoint count")
        checkpoint_count = struct.unpack_from('<H', chunk, 12)[0]
        if not 1 <= checkpoint_count <= 26 or header_size != 14 + 8 * checkpoint_count:
            raise SoundError("unsupported sound checkpoint count/header size")
    else:
        raise SoundError("unsupported sound compression flags")
    if not expanded or expanded > 16 * 1024 * 1024:
        raise SoundError("invalid sound expanded size")
    # NE3:baae initializes these pairs; the local palette-control byte is zero.
    palette = bytes(128 + index // 2 if index % 2 == 0 else 127 - index // 2 for index in range(256))
    output = bytearray()
    try:
        reader = Bits(chunk[header_size:], (len(chunk)-header_size)*8)
        padded_size = (expanded + 63) // 64 * 64  # NE3:bb72..bb85
        while len(output) < padded_size:
            block, repeat = _block(reader, palette, trace, palette_control=False)
            if len(output) + 64 * (repeat + 1) > padded_size:
                raise SoundError("sound block repeat exceeds expanded size")
            output.extend(block * (repeat + 1))
    except BitmapError as error:
        raise SoundError(str(error)) from error
    consumed_bits = reader.position
    terminal_bits = len(reader.data)*8-consumed_bits
    # Originalbe0e exits onremaining outputblocks, notdeclaredheaderbits580.
    # Native9actualdiscrepancies prove finalwholeblock and0..7unusedphysicalbits.
    if not 0 <= terminal_bits <= 7:
        raise SoundError("unexpected bytes/bits after final sound block")
    terminal_value = reader.get(terminal_bits) if terminal_bits else 0
    # NE3:bbee clamps emitted bytes to expanded size; final block stays64.
    encoded, padding = bytes(output[:expanded]), bytes(output[expanded:])
    samples, _ = integrate(encoded, order)
    # Source getter binding NE6:82c0+3c -> NE3:b226 -> object+20 -> byte8;
    # NE3:92dc maps22 to22050. Channels/depth similarly bind+34/+38.
    return Sound(channels, sample_bits, 22050, order, bit_count, encoded, samples,
                 metadata, chunk[12:header_size], payload[:12], data_record, padding, consumed_bits, terminal_bits, terminal_value)


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
    parser.add_argument("--id", type=int, default=1)
    args = parser.parse_args()
    with args.archive.open("rb") as source:
        archive_hash = verify_source(source, DEFAULT_SOURCE_MANIFEST)
        key = f"PSND:{args.id}"
        resource = read_index(source).by_key()[key]
        source.seek(resource.offset)
        payload = source.read(resource.length)
    sound = decode(payload)
    args.output.mkdir(parents=True, exist_ok=True)
    wav = args.output / f"PSND-{args.id}.wav"
    write_wav(sound, wav)
    report = {"archive_sha256": archive_hash, "resource": key, "offset": resource.offset,
              "length": resource.length, "payload_sha256": hashlib.sha256(payload).hexdigest(),
              "channels": sound.channels, "sample_bits": sound.sample_bits, "sample_rate": sound.sample_rate,
              "integration_order": sound.order, "sample_count": len(sound.samples), "packed_bits": sound.packed_bits,
              "encoded_values_sha256": hashlib.sha256(sound.encoded_values).hexdigest(),
              "pcm_sha256": hashlib.sha256(sound.samples).hexdigest(), "wav_sha256": hashlib.sha256(wav.read_bytes()).hexdigest(),
              "record_metadata_sha256": hashlib.sha256(sound.record_metadata).hexdigest(),
              "chunk_metadata_sha256": hashlib.sha256(sound.chunk_metadata).hexdigest(),
              "header_record_metadata_sha256": hashlib.sha256(sound.header_record_metadata).hexdigest(),
              "data_record_metadata_sha256": hashlib.sha256(sound.data_record_metadata).hexdigest(),
              "final_block_padding_bytes": len(sound.block_padding),
              "consumed_bits": sound.consumed_bits, "terminal_unused_bits": sound.terminal_unused_bits,
              "terminal_unused_value": sound.terminal_unused_value,
              "scope": "selected mono8-bit rate22 order0..4 header12(flags0)/14+8*count1..26(flags2) sequential path; seek/loop unimplemented"}
    (args.output / "sound-manifest.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
