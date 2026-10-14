#!/usr/bin/env python3
"""Check selected SCRP4000 Linda child conditions in original native code.

Runs original NE3:5118 and NE1:a632, relocating far calls to synthetic code
selectors. No condition behavior is stubbed. Other SCRP records unsupported.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from unicorn.x86_const import UC_X86_REG_CS, UC_X86_REG_IP, UC_X86_REG_SS, UC_X86_REG_SP
try:
    from .verify_journal_native import NativeJournal
    from .yukonres import read_index, verify_source, DEFAULT_SOURCE_MANIFEST
    from .yukontransform import source_patterns, transform
    from .yukonseattle import linda_scene_child_eligible
except ImportError:
    from verify_journal_native import NativeJournal
    from yukonres import read_index, verify_source, DEFAULT_SOURCE_MANIFEST
    from yukontransform import source_patterns, transform
    from yukonseattle import linda_scene_child_eligible


class NativeConditions(NativeJournal):
    def __init__(self, executable):
        # This inherited harness executes no journal calls or CSTR reads here.
        super().__init__(executable, b'\0\4one\0two\0three\0four\0')
        self.m.mem_map(0x90000, 0x10000)
        self.m.mem_write(0x90000, executable[0x1dde0:0x1dde0 + 59278])

    def route_far_call(self, m, address, size, user):
        code = bytes(m.mem_read(address, size))
        if code[0] != 0x9a or code[1:3] != bytes.fromhex('32a6'):
            return super().route_far_call(m, address, size, user)
        caller, ip = m.reg_read(UC_X86_REG_CS), m.reg_read(UC_X86_REG_IP)
        if caller != 0x9000:
            raise ValueError('Unexpected partner getter call segment')
        self.relocations.add((caller, ip, 0x1000, 0xa632))
        sp = (m.reg_read(UC_X86_REG_SP) - 4) & 65535
        m.mem_write(m.reg_read(UC_X86_REG_SS) * 16 + sp,
                    struct.pack('<HH', ip + size, caller))
        m.reg_write(UC_X86_REG_SP, sp)
        m.reg_write(UC_X86_REG_CS, 0x1000)
        m.reg_write(UC_X86_REG_IP, 0xa632)

    def condition(self, kind, value, partner):
        self.m.mem_write(0x50312, struct.pack('<H', partner))
        self.m.mem_write(0x43000, struct.pack('<HH', kind, value))
        before = bytes(self.m.mem_read(0x50000, 0x350))
        result = self.call(0x9000, 0x5118, struct.pack('<HHHH', 0x3000, 0x4000, 4000, 0))[0]
        if bytes(self.m.mem_read(0x50000, 0x350)) != before:
            raise ValueError('Selected condition unexpectedly mutated state')
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('executable', type=Path)
    parser.add_argument('report', type=Path)
    args = parser.parse_args()
    executable = args.executable.read_bytes()
    patterns = source_patterns(executable)
    with args.archive.open('rb') as f:
        archive_hash = verify_source(f, DEFAULT_SOURCE_MANIFEST)
        resource = read_index(f).by_key()['SCRP:4000']
        f.seek(resource.offset)
        raw = f.read(resource.length)
    normalized = transform(raw, patterns['SCRP'].opcodes)
    if len(normalized) != 290 or struct.unpack_from('<H', normalized)[0] != 16:
        raise ValueError('Unsupported selected SCRP count/length')
    words = struct.unpack_from('<9H', normalized, 2 + 15 * 18)
    if words != (3, 403, 0, 3, 1, 5, 4, 0, 0):
        raise ValueError('Selected Linda child record differs from source evidence')
    conditions = list(zip(words[3::2], words[4::2]))
    native = NativeConditions(executable)
    cases = []
    partners = list(range(10)) + [32766, 32767, 32768, 32769, 65534, 65535]
    for partner in partners:
        outputs = [native.condition(kind, value, partner) for kind, value in conditions]
        if any(output not in (0, 1) for output in outputs):
            raise ValueError('Original condition returned unsupported result')
        eligible = all(outputs)
        if eligible != linda_scene_child_eligible(partner):
            raise ValueError(f'Linda child model mismatch at partnerword{partner}')
        cases.append(dict(partner_word=partner, condition_outputs=outputs, eligible=eligible))
    report = dict(executable_sha256=hashlib.sha256(executable).hexdigest(),
                  archive_sha256=archive_hash, resource='SCRP:4000',
                  resource_offset=resource.offset, resource_length=resource.length,
                  resource_sha256=hashlib.sha256(raw).hexdigest(), selected_record_index=15,
                  selected_record_words=words, cases=cases, mismatches=0,
                  native_condition_calls=len(cases)*3,
                  synthetic_call_relocations=sorted(native.relocations),
                  scope='Selected kind3/SPRT403 eligibility only; no allocation, rendering, controller list construction or calendar progression.')
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
    print(json.dumps(dict(cases=len(cases), native_condition_calls=len(cases)*3, mismatches=0)))


if __name__ == '__main__':
    main()
