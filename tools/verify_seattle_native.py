#!/usr/bin/env python3
"""Execute bounded original partner setters and money mutation with Unicorn2.1.4.

Only the optional rendering-cache lookup is stubbed to return no display object.
Does not execute dialogue selection, journal, date progression, or Windows APIs.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_CS, UC_X86_REG_DS, UC_X86_REG_ES, UC_X86_REG_SS, UC_X86_REG_SP, UC_X86_REG_IP, UC_X86_REG_AX, UC_X86_REG_DX

try:
    from .verify_bitmap_native import NativeReader
    from .yukonseattle import State, accept_linda, change_money_slot_zero
except ImportError:
    from verify_bitmap_native import NativeReader
    from yukonseattle import State, accept_linda, change_money_slot_zero


def transition(executable, cash, bank, delta, partner=4, blocked=0):
    reader = NativeReader(executable)
    m = reader.machine
    for start, end in [(0x9df8, 0x9e1c), (0xa184, 0xa27e), (0xa652, 0xa66e)]:
        m.mem_write(0x10000 + start, executable[0x460 + start:0x460 + end])
    state = bytearray(0x350)
    struct.pack_into('<HH', state, 0x2fa, cash, bank)
    struct.pack_into('<H', state, 0x334, blocked)
    m.mem_write(0x40000, bytes(state))
    # Synthetic DS holds a far pointer to the dirty-flag/display owner.
    m.mem_write(0x352fc, struct.pack('<HH', 0, 0x5000))
    stub_calls = []

    def hook(machine, address, size, user_data):
        if address == 0x1a1bd:
            # Caller pushed key dword and cache far pointer; original cache
            # convention RETF8 established at NE2:9dbf. No display exists here.
            stub_calls.append('NE1:a1bd optional display cache lookup -> null')
            machine.reg_write(UC_X86_REG_SP, machine.reg_read(UC_X86_REG_SP) + 8)
            machine.reg_write(UC_X86_REG_AX, 0)
            machine.reg_write(UC_X86_REG_DX, 0)
            machine.reg_write(UC_X86_REG_IP, 0xa1c1)

    m.hook_add(UC_HOOK_CODE, hook)

    def call(entry, arguments):
        for reg, value in [(UC_X86_REG_CS, 0x1000), (UC_X86_REG_DS, 0x3000), (UC_X86_REG_ES, 0x4000),
                           (UC_X86_REG_SS, 0x6000), (UC_X86_REG_SP, 0xf000)]:
            m.reg_write(reg, value)
        m.mem_write(0x6f000, struct.pack('<HHHH', 0xf100, 0x1000, 0, 0x4000) + arguments)
        m.emu_start(0x10000 + entry, 0x1f100, count=10000)
        if m.reg_read(UC_X86_REG_CS) != 0x1000 or m.reg_read(UC_X86_REG_IP) != 0xf100:
            raise ValueError('Native routine did not return within bound')
        return m.reg_read(UC_X86_REG_AX)

    call(0x9df8, struct.pack('<H', partner))
    call(0xa652, struct.pack('<H', 1))
    returned = call(0xa184, struct.pack('<iH', delta, 0))
    result = bytes(m.mem_read(0x40000, len(state)))
    return {'cash': struct.unpack_from('<H', result, 0x2fa)[0],
            'bank': struct.unpack_from('<H', result, 0x2fc)[0],
            'partner': struct.unpack_from('<H', result, 0x312)[0],
            'flag344': struct.unpack_from('<H', result, 0x344)[0],
            'dirty54': struct.unpack('<H', m.mem_read(0x50054, 2))[0],
            'money_return': returned, 'stub_calls': stub_calls}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('executable', type=Path)
    parser.add_argument('report', type=Path)
    args = parser.parse_args()
    exe = args.executable.read_bytes()
    instructions = [(2, 0x22d9, '2d0a00'), (2, 0x2361, '26ff7702'),
                    (2, 0x2365, '26ff7704'), (2, 0x23f7, '660fbf460a'),
                    (1, 0x9e09, '2689871203'), (1, 0xa65b, '2689874403'),
                    (1, 0xa228, '268980fa02'), (1, 0xa266, '26833800'),
                    (1, 0xa26a, '7d0a')]
    source_checks = []
    for segment, offset, expected in instructions:
        location = {1: 0x460, 2: 0xf2c0}[segment] + offset
        if exe[location:location + len(bytes.fromhex(expected))].hex() != expected:
            raise ValueError('Unexpected source routing bytes')
        source_checks.append({'ne': f'{segment:04x}:{offset:04x}',
                              'file_offset': location, 'bytes': expected})
    # Expected values are hand-calculated, independent of a new rule model.
    cases = [
        ('Linda +500', 350, 0, 500, 0, (850, 0, 4, 1, 1)),
        ('blocked mutation', 350, 0, 500, 1, (350, 0, 0, 1, 1)),
        ('cash subtraction', 850, 0, -60, 0, (790, 0, 4, 1, 1)),
        ('bank fallback', 20, 100, -60, 0, (0, 60, 4, 1, 1)),
        ('insufficient total', 20, 30, -60, 0, (20, 30, 4, 1, 0)),
        ('signed word overflow clamp', 32760, 0, 500, 0, (0, 0, 4, 1, 1)),
    ]
    results = []
    for name, cash, bank, delta, blocked, expected in cases:
        actual = transition(exe, cash, bank, delta, blocked=blocked)
        measured = tuple(actual[k] for k in ['cash', 'bank', 'partner', 'flag344', 'money_return'])
        if measured != expected:
            raise ValueError(f'{name}: {measured} != independently expected {expected}')
        before = State(cash, bank, 0, blocked, 0)
        if delta == 500:
            recovered, success = accept_linda(before)
        else:
            recovered, success = change_money_slot_zero(State(cash, bank, 4, blocked, 1), delta)
        translated = (recovered.cash_word, recovered.bank_word, recovered.partner_word,
                      recovered.flag344_word, int(success))
        if translated != measured:
            raise ValueError(f'{name}: recovered model differs from original execution')
        results.append({'name': name, 'before': {'cash': cash, 'bank': bank, 'delta': delta, 'flag334': blocked}, 'after': actual})
    matrix = []
    for cash in (0, 20, 32767, 32768, 65535):
        for bank in (0, 20, 32767, 32768, 65535):
            for delta in (-32768, -500, -60, -1, 0, 1, 500, 32767):
                for blocked in (0, 1):
                    actual = transition(exe, cash, bank, delta, blocked=blocked)
                    before = State(cash, bank, 0, blocked, 0)
                    if delta == 500:
                        recovered, success = accept_linda(before)
                    else:
                        prepared = State(cash, bank, 0 if blocked else 4, blocked, 1)
                        recovered, success = change_money_slot_zero(prepared, delta)
                    translated = (recovered.cash_word, recovered.bank_word, recovered.partner_word,
                                  recovered.flag344_word, int(success))
                    measured = tuple(actual[k] for k in ['cash', 'bank', 'partner', 'flag344', 'money_return'])
                    if translated != measured:
                        raise ValueError(f'Native matrix mismatch {cash}/{bank}/{delta}/{blocked}: {translated} != {measured}')
                    matrix.append([cash, bank, delta, blocked, *measured])
    report = {'source_sha256': hashlib.sha256(exe).hexdigest(), 'unicorn_version': '2.1.4',
              'native_routines': ['0001:9df8', '0001:a652', '0001:a184'],
              'source_instruction_checks': source_checks,
              'differential_boundary_matrix': {'cases': len(matrix),
                  'cash_words': [0, 20, 32767, 32768, 65535],
                  'bank_words': [0, 20, 32767, 32768, 65535],
                  'deltas': [-32768, -500, -60, -1, 0, 1, 500, 32767],
                  'flag334': [0, 1], 'mismatches': 0,
                  'rows_sha256': hashlib.sha256(json.dumps(matrix, separators=(',', ':')).encode()).hexdigest()},
              'scope': 'Original setters and money mutation composed with synthetic state; optional display cache lookup stubbed null. Not whole dialogue opcode or original live-state validation.',
              'cases': results, 'mismatches': 0}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
