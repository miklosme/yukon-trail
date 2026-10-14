#!/usr/bin/env python3
"""Verify PSND:1 integer calls and all sample conversions against original x86."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from unicorn.x86_const import UC_X86_REG_CS, UC_X86_REG_DS, UC_X86_REG_ES, UC_X86_REG_SS, UC_X86_REG_SP, UC_X86_REG_IP

try:
    from .verify_bitmap_native import NativeReader
    from .yukonsnd import decode, integrate
    from .yukonres import read_index, verify_source, DEFAULT_SOURCE_MANIFEST
except ImportError:
    from verify_bitmap_native import NativeReader
    from yukonsnd import decode, integrate
    from yukonres import read_index, verify_source, DEFAULT_SOURCE_MANIFEST


class SoundNativeReader(NativeReader):
    def __init__(self, executable):
        super().__init__(executable)
        self.windowed_calls = 0

    def run(self, data, start, base, extension, maximum, count, hybrid):
        if len(data) <= 60000:
            return super().run(data, start, base, extension, maximum, count, hybrid)
        # Original integer helper operates on a supplied pointer/bitcursor.
        # Relocate a <=60000byte input window and its cursor together; retain
        # the absolute returned bit position. This avoids spilling input into
        # the synthetic output area and does not emulate Win16 huge buffers.
        origin = max(0, start // 8 - 256)
        window = data[origin:origin + 60000]
        actual, end = super().run(window, start - origin * 8, base, extension, maximum, count, hybrid)
        self.windowed_calls += 1
        return actual, end + origin * 8


def native_integrate(reader, executable, data, order):
    machine = reader.machine
    # Bounded pure converter, Code3 at synthetic selector2000. All branches
    # stay inside9b34..9c3f, and all data accesses are supplied far pointers.
    machine.mem_write(0x29b34, executable[0x1dde0 + 0x9b34:0x1dde0 + 0x9c40])
    machine.mem_write(0x40000, bytes([128]) * 4)
    output = bytearray()
    for start in range(0, len(data), 16384):
        part = data[start:start + 16384]
        machine.mem_write(0x50000, part)
        for reg, value in [(UC_X86_REG_CS, 0x2000), (UC_X86_REG_DS, 0x4000), (UC_X86_REG_ES, 0x5000),
                           (UC_X86_REG_SS, 0x6000), (UC_X86_REG_SP, 0xf000)]:
            machine.reg_write(reg, value)
        machine.mem_write(0x6f000, struct.pack("<HHHHIIHH", 0x9d00, 0x2000, 0, 0x4000, order, len(part), 0, 0x5000))
        machine.emu_start(0x29b34, 0x29d00, count=1000000)
        if machine.reg_read(UC_X86_REG_CS) != 0x2000 or machine.reg_read(UC_X86_REG_IP) != 0x9d00:
            raise ValueError("original converter did not return within instruction limit")
        output.extend(machine.mem_read(0x50000, len(part)))
    return bytes(output), bytes(machine.mem_read(0x40000, 4))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("executable", type=Path)
    parser.add_argument("report", type=Path)
    parser.add_argument("--id", type=int, default=1)
    args = parser.parse_args()
    executable = args.executable.read_bytes()
    native = SoundNativeReader(executable)
    with args.archive.open("rb") as source:
        archive_hash = verify_source(source, DEFAULT_SOURCE_MANIFEST)
        key = f"PSND:{args.id}"
        resource = read_index(source).by_key()[key]
        source.seek(resource.offset)
        payload = source.read(resource.length)
    sound = decode(payload, native.compare)
    actual = native_integrate(native, executable, sound.encoded_values, sound.order)
    expected = integrate(sound.encoded_values, sound.order)
    if actual != expected or actual[0] != sound.samples:
        raise ValueError("original sample conversion mismatch")
    # A separate input covers wraparound and every original integration branch.
    synthetic = bytes(range(256)) * 3
    for order in range(0, 5):
        if native_integrate(native, executable, synthetic, order) != integrate(synthetic, order):
            raise ValueError(f"synthetic conversion mismatch, order {order}")
    report = {"archive_sha256": archive_hash, "payload_sha256": hashlib.sha256(payload).hexdigest(),
              "executable_sha256": hashlib.sha256(executable).hexdigest(), "unicorn_version": "2.1.4",
              "resource": key, "integer_calls": native.calls, "integer_unique_calls": len(native.unique), "windowed_integer_calls": native.windowed_calls,
              "sample_bytes_compared": len(actual[0]), "native_pcm_sha256": hashlib.sha256(actual[0]).hexdigest(),
              "sample_rate": sound.sample_rate, "integration_order": sound.order,
              "final_block_padding_bytes": len(sound.block_padding),
              "declared_packed_bits": sound.packed_bits, "consumed_bits": sound.consumed_bits,
              "terminal_unused_bits": sound.terminal_unused_bits, "terminal_unused_value": sound.terminal_unused_value,
              "final_state": list(actual[1]), "synthetic_orders_checked": [0, 1, 2, 3, 4], "mismatches": 0,
              "scope": "original integer readers and NE3:9b34 converter; large inputs use bounded relocated bitcursor windows; not whole processor, Win16 huge buffers or live playback"}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
