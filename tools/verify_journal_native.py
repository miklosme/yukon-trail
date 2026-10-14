#!/usr/bin/env python3
"""Execute original journal prefix/date/place and CSTR selection routines.

Far CALLF operands are routed to synthetic selectors using checked NE targets;
the actual source instructions and pure string functions execute unchanged.
No date transition, allocator, journal overflow, or UI loop is simulated.
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
    from .yukonres import verify_source, read_index, DEFAULT_SOURCE_MANIFEST
    from .yukonjournal import source_vocabulary, linda_entry, queue_linda_continuation
except ImportError:
    from verify_bitmap_native import NativeReader
    from yukonres import verify_source, read_index, DEFAULT_SOURCE_MANIFEST
    from yukonjournal import source_vocabulary, linda_entry, queue_linda_continuation


class NativeJournal:
    def __init__(self, exe, cstr):
        reader = NativeReader(exe)
        self.m = reader.machine
        self.m.mem_map(0x80000, 0x10000)
        self.m.mem_write(0x10000, exe[0x460:0x460 + 60176])
        self.m.mem_write(0x20000, exe[0x44fc0:0x44fc0 + 39822])
        self.m.mem_write(0x30000, exe[0x4f420:0x4f420 + 29314])
        self.m.mem_write(0x80000, exe[0xf2c0:0xf2c0 + 59610])
        self.m.mem_write(0x35308, struct.pack('<HH', 0, 0x5000))
        self.m.mem_write(0x35304, struct.pack('<HH', 0, 0x6000))
        self.m.mem_write(0x40004, struct.pack('<HH', 0x1000, 0x4000))
        self.m.mem_write(0x6000e, struct.pack('<HH', 0x1000, 0x6000))
        self.m.mem_write(0x60104, struct.pack('<HH', 0x2000, 0x6000))
        self.m.mem_write(0x62000, cstr)
        self.relocations = set()
        self.m.hook_add(UC_HOOK_CODE, self.route_far_call)

    def route_far_call(self, m, address, size, _):
        opcode = bytes(m.mem_read(address, size))
        if opcode[0] != 0x9a:
            return
        offset = int.from_bytes(opcode[1:3], 'little')
        # NE2:205e has an internal-entry relocation changing the offset too:
        # source9a861b0000, Ghidra CALLF1028:1f88. Preserve source bytes and
        # dispatch the checked relocated target, rather than its source chain.
        caller_cs, ip = m.reg_read(UC_X86_REG_CS), m.reg_read(UC_X86_REG_IP)
        if (caller_cs, ip) == (0x8000, 0x205e):
            if opcode != bytes.fromhex('9a861b0000'):
                raise ValueError('Unexpected internal-entry call fixup source')
            offset = 0x1f88
        targets = {0x1f88: 0x2000, 0x1ece: 0x2000, 0x1f22: 0x2000,
                   0x20f8: 0x2000, 0x28c0: 0x2000,
                   0xa68e: 0x1000, 0xa850: 0x1000, 0xa6f4: 0x1000,
                   0xa804: 0x1000, 0xa7f4: 0x1000}
        if offset not in targets:
            raise ValueError(f'Unrecovered native dependency at {address:x}: {opcode.hex()}')
        self.relocations.add((caller_cs, ip, targets[offset], offset))
        sp = (m.reg_read(UC_X86_REG_SP) - 4) & 65535
        m.mem_write(m.reg_read(UC_X86_REG_SS) * 16 + sp, struct.pack('<HH', ip + size, caller_cs))
        m.reg_write(UC_X86_REG_SP, sp)
        m.reg_write(UC_X86_REG_CS, targets[offset])
        m.reg_write(UC_X86_REG_IP, offset)

    def call(self, segment, offset, arguments, instruction_limit=100000):
        m = self.m
        for register, value in [(UC_X86_REG_CS, segment), (UC_X86_REG_DS, 0x3000),
                                (UC_X86_REG_ES, 0x4000), (UC_X86_REG_SS, 0x7000),
                                (UC_X86_REG_SP, 0xf000)]:
            m.reg_write(register, value)
        m.mem_write(0x7f000, struct.pack('<HH', 0xf100, 0x1000) + arguments)
        m.emu_start(segment * 16 + offset, 0x1f100, count=instruction_limit)
        if m.reg_read(UC_X86_REG_CS) != 0x1000 or m.reg_read(UC_X86_REG_IP) != 0xf100:
            raise ValueError('Journal routine did not return within bound')
        return m.reg_read(UC_X86_REG_AX), m.reg_read(UC_X86_REG_DX)

    def entry(self, day, month, phase, prior, location=(200,0,0)):
        m = self.m
        state = bytearray(0x350)
        struct.pack_into('<HH', state, 0x28, day, month)
        struct.pack_into('<HHH', state, 0x34, *location)  # explicit selected place tuple
        struct.pack_into('<H', state, 0x310, phase)
        m.mem_write(0x50000, bytes(state))
        m.mem_write(0x41000, bytes(255))
        m.mem_write(0x61000, prior + b'\0')
        args = struct.pack('<HH', 0, 0x4000)
        for offset in (0xd364, 0xcdae):
            self.call(0x1000, offset, args)
        self.call(0x1000, 0xcff8, args + struct.pack('<H', 0))
        text_offset, text_selector = self.call(0x8000, 0x2040, struct.pack('<HHH', 0x100, 0x6000, 3))
        text = bytes(m.mem_read(text_selector * 16 + text_offset, 255)).split(b'\0')[0]
        header = bytes(m.mem_read(0x41000, 255)).split(b'\0')[0]
        if len(header) + len(text) < 255:
            self.call(0x2000, 0x1ece, struct.pack('<HHHH', 0x1000, 0x4000, text_offset, text_selector))
        result = bytes(m.mem_read(0x41000, 255)).split(b'\0')[0]
        if bytes(m.mem_read(0x50000, len(state))) != bytes(state):
            raise ValueError('Journal formatting unexpectedly changed game state')
        self.call(0x2000, 0x1ece, struct.pack('<HHHH', 0x1000, 0x6000, 0x1000, 0x4000))
        committed = bytes(m.mem_read(0x61000, len(prior) + 255)).split(b'\0')[0]
        if committed != prior + result:
            raise ValueError('Original string append differs from bounded journal composition')
        return result

    def queue(self, manager):
        self.m.mem_write(0x50000, manager)
        self.m.mem_write(0x42000, struct.pack('<4H', 3, 0, 0, 0))
        self.call(0x1000, 0x4dba, struct.pack('<HHHH', 0, 0x5000, 0x2000, 0x4000))
        return bytes(self.m.mem_read(0x50000, len(manager)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('executable', type=Path)
    parser.add_argument('report', type=Path)
    args = parser.parse_args()
    exe = args.executable.read_bytes()
    with args.archive.open('rb') as f:
        archive_hash = verify_source(f, DEFAULT_SOURCE_MANIFEST)
        r = read_index(f).by_key()['CSTR:505']
        f.seek(r.offset)
        cstr = f.read(r.length)
    native = NativeJournal(exe, cstr)
    vocabulary = source_vocabulary(exe)
    cases = []
    for day, month, phase, prior in [(24, 8, 0, b''), (24, 8, 0, b'earlier entry'),
                                    (1, 1, 5, b''), (31, 12, 6, b'earlier entry')]:
        output = native.entry(day, month, phase, prior)
        if output != linda_entry(vocabulary, cstr, day, month, phase, prior):
            raise ValueError('Recovered Linda entry differs from original helpers')
        cases.append({'day': day, 'month': month, 'phase_word': phase,
                      'prior_empty': not prior, 'output_sha256': hashlib.sha256(output).hexdigest(),
                      'output_length': len(output)})
    matrix = []
    for month in range(1, 13):
        for day in (1, 9, 24, 31):
            for phase in (0, 5, 6, 32767, 32768, 65535):
                for prior in (b'', b'earlier entry'):
                    output = native.entry(day, month, phase, prior)
                    if output != linda_entry(vocabulary, cstr, day, month, phase, prior):
                        raise ValueError(f'Journal native matrix mismatch {day}/{month}/{phase}/{bool(prior)}')
                    matrix.append([day, month, phase, bool(prior), hashlib.sha256(output).hexdigest()])
    location_matrix=[]
    for scene_word in (0,1,1000,3000,4000,32767,32768,65535):
        for day,month,phase in ((23,8,1),(31,12,6),(1,1,65535)):
            for prior in (b'',b'earlier entry'):
                location=(200,0,scene_word)
                output=native.entry(day,month,phase,prior,location)
                if output!=linda_entry(vocabulary,cstr,day,month,phase,prior,location):
                    raise ValueError('Actual Seattle thirdword journal differs from native')
                location_matrix.append([list(location),day,month,phase,bool(prior),hashlib.sha256(output).hexdigest()])
    queue_cases = []
    for fill in (0, 1, 255):
        before = bytes([fill]) * 16
        after = native.queue(before)
        if after != queue_linda_continuation(before):
            raise ValueError('Queued action3 model differs from original routine')
        queue_cases.append({'before_hex': before.hex(), 'after_hex': after.hex()})
    report = {'source_sha256': hashlib.sha256(exe).hexdigest(), 'archive_sha256': archive_hash,
              'resource': 'CSTR:505', 'resource_offset': r.offset, 'resource_length': r.length,
              'resource_sha256': hashlib.sha256(cstr).hexdigest(), 'unicorn_version': '2.1.4',
              'cases': cases, 'synthetic_call_relocations': sorted(native.relocations),
              'differential_matrix_cases': len(matrix), 'mismatches': 0,
              'matrix_rows_sha256': hashlib.sha256(json.dumps(matrix, separators=(',', ':')).encode()).hexdigest(),
              'native_queue_cases': queue_cases,
              'seattle_location_matrix': location_matrix,
              'seattle_location_cases': len(location_matrix),
              'seattle_location_rows_sha256': hashlib.sha256(json.dumps(location_matrix,separators=(',',':')).encode()).hexdigest(),
              'scope': 'Original prefix/date/place/CSTR selector and string helpers; selected Seattle region200/place-index0 with explicit unsigned16 scene word;576 historicalzero-third fixture cases plus48sourcebranch thirdword cases, no allocator, overflow retention, controller activation or UI/date progression; selected non-overflow concatenation checked.'}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
