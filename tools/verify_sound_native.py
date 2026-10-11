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
    args = parser.parse_args()
    executable = args.executable.read_bytes()
    native = NativeReader(executable)
    with args.archive.open("rb") as source:
        archive_hash = verify_source(source, DEFAULT_SOURCE_MANIFEST)
        resource = read_index(source).by_key()["PSND:1"]
        source.seek(resource.offset)
        payload = source.read(resource.length)
    sound = decode(payload, native.compare)
    actual = native_integrate(native, executable, sound.encoded_values, sound.order)
    expected = integrate(sound.encoded_values, sound.order)
    if actual != expected or actual[0] != sound.samples:
        raise ValueError("original sample conversion mismatch")
    # A separate input covers wraparound and every original integration branch.
    synthetic = bytes(range(256)) * 3
    for order in range(1, 5):
        if native_integrate(native, executable, synthetic, order) != integrate(synthetic, order):
            raise ValueError(f"synthetic conversion mismatch, order {order}")
    report = {"archive_sha256": archive_hash, "payload_sha256": hashlib.sha256(payload).hexdigest(),
              "executable_sha256": hashlib.sha256(executable).hexdigest(), "unicorn_version": "2.1.4",
              "resource": "PSND:1", "integer_calls": native.calls, "integer_unique_calls": len(native.unique),
              "sample_bytes_compared": len(actual[0]), "native_pcm_sha256": hashlib.sha256(actual[0]).hexdigest(),
              "final_state": list(actual[1]), "synthetic_orders_checked": [1, 2, 3, 4], "mismatches": 0,
              "scope": "original integer readers and NE3:9b34 converter; not whole processor or live playback"}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
