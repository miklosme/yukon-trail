#!/usr/bin/env python3
"""Compare every bounded CBMP integer-reader call with original x86 code.

Requires optional local Unicorn 2.1.4, not needed by the decoder/tests.
Executes only NE1:0000..02d0 from the source-verified executable; no OS calls.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from unicorn import Uc, UC_ARCH_X86, UC_MODE_16, __version__ as unicorn_version
from unicorn.x86_const import UC_X86_REG_CS, UC_X86_REG_DS, UC_X86_REG_ES, UC_X86_REG_SS, UC_X86_REG_SP, UC_X86_REG_IP, UC_X86_REG_AX, UC_X86_REG_DX

try:
    from .yukonbmp import EXE_SHA256, decode
    from .yukonres import read_index, verify_source, DEFAULT_SOURCE_MANIFEST
except ImportError:
    from yukonbmp import EXE_SHA256, decode
    from yukonres import read_index, verify_source, DEFAULT_SOURCE_MANIFEST


class NativeReader:
    def __init__(self, executable):
        if unicorn_version != "2.1.4":
            raise ValueError(f"unsupported native verifier version {unicorn_version}")
        if hashlib.sha256(executable).hexdigest() != EXE_SHA256:
            raise ValueError("unsupported executable identity")
        self.machine = Uc(UC_ARCH_X86, UC_MODE_16)
        self.machine.mem_map(0, 0x80000)
        self.machine.mem_write(0x10000, executable[0x460:0x460 + 0x2d1])
        self.calls, self.unique = 0, set()

    def run(self, data, start, base, extension, maximum, count, hybrid):
        if len(data) > 60000 or not 1 <= count <= 64:
            raise ValueError("native probe bounds exceeded")
        machine = self.machine
        machine.mem_write(0x40000, data + bytes(16))
        machine.mem_write(0x50000, bytes(64))
        for reg, value in [(UC_X86_REG_CS, 0x1000), (UC_X86_REG_DS, 0x4000), (UC_X86_REG_ES, 0x5000),
                           (UC_X86_REG_SS, 0x6000), (UC_X86_REG_SP, 0xf000)]:
            machine.reg_write(reg, value)
        machine.mem_write(0x6f000, struct.pack("<HHHHIHHHHHH", 0x400, 0x1000, 0, 0x4000,
                                             start, base, extension, maximum, count, 0, 0x5000))
        entry = 0x129 if hybrid else 0x62
        machine.emu_start(0x10000 + entry, 0x10400, count=50000)
        if machine.reg_read(UC_X86_REG_CS) != 0x1000 or machine.reg_read(UC_X86_REG_IP) != 0x400:
            raise ValueError("original reader did not return within instruction limit")
        end = machine.reg_read(UC_X86_REG_AX) | (machine.reg_read(UC_X86_REG_DX) << 16)
        return bytes(machine.mem_read(0x50000, count)), end

    def compare(self, data, start, base, extension, maximum, count, hybrid, expected, end):
        native, native_end = self.run(data, start, base, extension, maximum, count, hybrid)
        if (native, native_end) != (expected, end):
            raise ValueError(f"native mismatch at bit {start}, p/e/max/count={base}/{extension}/{maximum}/{count}, "
                             f"hybrid={hybrid}: end {native_end} != {end}; bytes {native.hex()} != {expected.hex()}")
        self.calls += 1
        self.unique.add((start, base, extension, maximum, count, hybrid, hashlib.sha256(data).digest()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("executable", type=Path)
    parser.add_argument("report", type=Path)
    parser.add_argument("--id", type=int, action="append", required=True)
    args = parser.parse_args()
    native = NativeReader(args.executable.read_bytes())
    results = {}
    with args.archive.open("rb") as source:
        archive_hash = verify_source(source, DEFAULT_SOURCE_MANIFEST)
        index = read_index(source).by_key()
        for resource_id in sorted(set(args.id)):
            key = f"CBMP:{resource_id}"
            resource = index[key]
            source.seek(resource.offset)
            payload = source.read(resource.length)
            before = native.calls
            frames = decode(payload, native.compare)
            results[key] = {"sha256": hashlib.sha256(payload).hexdigest(), "frames": len(frames),
                            "native_calls": native.calls - before}
    report = {"executable_sha256": EXE_SHA256, "archive_sha256": archive_hash,
              "native_code": "NE 0001:0062 and 0001:0129; file base 0x460", "unicorn_version": "2.1.4",
              "calls": native.calls, "unique_calls": len(native.unique), "mismatches": 0, "resources": results}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
