#!/usr/bin/env python3
"""Check original memory-stream getter's independence from PSND record byte1."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from unicorn import UC_HOOK_MEM_READ
from unicorn.x86_const import UC_X86_REG_CS, UC_X86_REG_DS, UC_X86_REG_ES, UC_X86_REG_SS, UC_X86_REG_SP, UC_X86_REG_IP, UC_X86_REG_AX
try:
    from .verify_bitmap_native import NativeReader
except ImportError:
    from verify_bitmap_native import NativeReader


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('executable', type=Path)
    parser.add_argument('report', type=Path)
    args = parser.parse_args()
    exe = args.executable.read_bytes()
    native = NativeReader(exe)
    m = native.machine
    source = exe[0x2cac0 + 0xf4c:0x2cac0 + 0xfa8]
    m.mem_write(0x20f4c, source)
    payload_reads = []
    m.hook_add(UC_HOOK_MEM_READ, lambda machine, access, address, size, value, data:
               payload_reads.append([address, size]), begin=0x50000, end=0x5000b)
    rows = []
    for byte1 in range(256):
        payload = bytes([1, byte1, 12, 0, 0, 0, 1, 8, 22, 1, 1, 57])
        m.mem_write(0x50000, payload)
        for position in (0, 12):
            state = bytearray(0x1a)
            struct.pack_into('<HHII', state, 0xe, 0, 0x5000, len(payload), position)
            m.mem_write(0x40000, bytes(state))
            m.mem_write(0x60000, bytes(8))
            for register, value in [(UC_X86_REG_CS, 0x2000), (UC_X86_REG_DS, 0x3000),
                                    (UC_X86_REG_ES, 0x4000), (UC_X86_REG_SS, 0x7000),
                                    (UC_X86_REG_SP, 0xf000)]:
                m.reg_write(register, value)
            m.mem_write(0x7f000, struct.pack('<HHHHHHHH', 0x1100, 0x2000,
                                             0, 0x4000, 0, 0x6000, 4, 0x6000))
            m.emu_start(0x20f4c, 0x21100, count=1000)
            if m.reg_read(UC_X86_REG_CS) != 0x2000 or m.reg_read(UC_X86_REG_IP) != 0x1100:
                raise ValueError('Memory stream getter failed to return')
            actual = (m.reg_read(UC_X86_REG_AX), *struct.unpack('<IHH', m.mem_read(0x60000, 8)))
            expected = (0 if position == 0 else 1, 12 - position, position, 0x5000)
            if actual != expected:
                raise ValueError(f'Getter mismatch byte1={byte1},cursor={position}: {actual} != {expected}')
            rows.append([byte1, position, *actual])
    if payload_reads:
        raise ValueError('Original stream getter unexpectedly inspected payload bytes')
    report = {'source_sha256': hashlib.sha256(exe).hexdigest(), 'unicorn_version': '2.1.4',
              'routine': {'ne': '0004:0f4c', 'ghidra': '1018:0f4c', 'file_offset': 0x2cac0 + 0xf4c,
                          'code_sha256': hashlib.sha256(source).hexdigest()},
              'cases': len(rows), 'payload_reads': 0, 'byte1_values': 'all256',
              'cursor_values': [0, 12], 'mismatches': 0,
              'rows_sha256': hashlib.sha256(json.dumps(rows, separators=(',', ':')).encode()).hexdigest(),
              'scope': 'Original memory-stream raw pointer/remaining getter only; record processor byte1 omission checked statically. No file buffering or whole sound playback executed.'}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
