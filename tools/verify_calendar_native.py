#!/usr/bin/env python3
"""Compare NE1:a0c2 unchanged original instructions to explicit date-word model."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
try:
    from .verify_journal_native import NativeJournal
    from .yukoncalendar import DateWords, advance_one_original_day, MONTH_LENGTHS
except ImportError:
    from verify_journal_native import NativeJournal
    from yukoncalendar import DateWords, advance_one_original_day, MONTH_LENGTHS


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('executable', type=Path)
    parser.add_argument('report', type=Path)
    args = parser.parse_args()
    executable = args.executable.read_bytes()
    native = NativeJournal(executable, b'\0\4one\0two\0three\0four\0')
    native.m.mem_write(0x352fc, struct.pack('<HH', 0x3000, 0x6000))
    rows = []
    for month, days in enumerate(MONTH_LENGTHS, 1):
        for day in range(1, days + 1):
            for elapsed, phase in ((0, 0), (32767, 5), (65535, 65535)):
                for gate in (0, 1):
                    before = DateWords(day, month, elapsed, phase, gate)
                    expected = advance_one_original_day(before)
                    state = bytearray([0x55] * 0x350)
                    for offset, value in [(0x28, day), (0x2a, month), (0x30e, elapsed),
                                          (0x310, phase), (0x334, gate)]:
                        struct.pack_into('<H', state, offset, value)
                    wanted = bytearray(state)
                    for offset, value in [(0x28, expected.day_word), (0x2a, expected.month_word),
                                          (0x30e, expected.elapsed_word), (0x310, expected.phase_word)]:
                        struct.pack_into('<H', wanted, offset, value)
                    native.m.mem_write(0x50000, bytes(state))
                    native.m.mem_write(0x63054, bytes(2))
                    native.call(0x1000, 0xa0c2, struct.pack('<HH', 0, 0x5000))
                    actual = bytes(native.m.mem_read(0x50000, len(state)))
                    dirty = int.from_bytes(native.m.mem_read(0x63054, 2), 'little')
                    if actual != wanted or dirty != (0 if gate else 1):
                        raise ValueError(f'Original date model differs at{before}')
                    rows.append([day, month, elapsed, phase, gate, hashlib.sha256(actual).hexdigest(), dirty])
    report = dict(executable_sha256=hashlib.sha256(executable).hexdigest(), native_ne='0001:a0c2',
                  ghidra_address='1000:a0c2', native_cases=len(rows), mismatches=0,
                  month_lengths=MONTH_LENGTHS,
                  matrix_sha256=hashlib.sha256(json.dumps(rows, separators=(',', ':')).encode()).hexdigest(),
                  scope='All365 valid fixed-calendar dates times3 rawword contexts times gate0/1. Original routine and dirty notification execute without behavior stubs; no scene caller or live navigation binding.')
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
