#!/usr/bin/env python3
"""Run original registration and bounded postread code; no Windows API stubs."""
import argparse
import hashlib
import json
from pathlib import Path
import struct

from unicorn import Uc, UC_ARCH_X86, UC_MODE_16, __version__
from unicorn.x86_const import UC_X86_REG_CS, UC_X86_REG_DS, UC_X86_REG_ES, UC_X86_REG_SS, UC_X86_REG_SP, UC_X86_REG_IP, UC_X86_REG_AX
try:
    from .yukontransform import source_patterns, transform
    from .yukonres import read_index, verify_source, DEFAULT_SOURCE_MANIFEST
except ImportError:
    from yukontransform import source_patterns, transform
    from yukonres import read_index, verify_source, DEFAULT_SOURCE_MANIFEST


class NativeTransform:
    def __init__(self, executable):
        self.patterns = source_patterns(executable)
        if __version__ != '2.1.4':
            raise ValueError('unsupported Unicorn version')
        self.machine = Uc(UC_ARCH_X86, UC_MODE_16)
        self.machine.mem_map(0, 0x80000)
        code = bytearray(executable[0x460:0x460+0x85e6])
        self.relocations = []
        for address in [p.call_offset for p in self.patterns.values()]:
            self.relocations.append(dict(ne=f'0001:{address:04x}', target='0001:83e4', harness_selector=0x1000))
            struct.pack_into('<H', code, address+3, 0x1000)
        for address in (0x84d8, 0x8522, 0x8534, 0x8546):
            self.relocations.append(dict(ne=f'0001:{address:04x}', target=f'0006:{struct.unpack_from("<H",code,address+1)[0]:04x}', harness_selector=0x2000))
            struct.pack_into('<H', code, address+3, 0x2000)
        self.machine.mem_write(0x10000, bytes(code))
        self.machine.mem_write(0x260ae, executable[0x44fc0+0x60ae:0x44fc0+0x60e4])
        self.machine.mem_write(0x40000, bytes(0x70c))
        self.machine.mem_write(0x352f4, struct.pack('<HH', 0, 0x4000))
        self.registers()
        self.machine.reg_write(UC_X86_REG_AX, 0)
        self.machine.emu_start(0x1677f, 0x16a25, count=50000)
        if self.machine.reg_read(UC_X86_REG_IP) != 0x6a25:
            raise ValueError('registration did not finish')
        self.original_registry = bytes(self.machine.mem_read(0x40000, 0x70c))
        if struct.unpack_from('<H', self.original_registry, 0x70a)[0] != 17:
            raise ValueError('native registration count mismatch')
        for i, pattern in enumerate(self.patterns.values()):
            offset = 0x7a+i*0x54
            tag = struct.unpack_from('<I', self.original_registry, offset)[0].to_bytes(4,'big').decode('ascii')
            words = struct.unpack_from('<'+'h'*len(pattern.opcodes), self.original_registry, offset+4)
            if (tag, words) != (pattern.tag, pattern.opcodes):
                raise ValueError('native startup pattern extraction mismatch')

    def registers(self):
        for register, value in [(UC_X86_REG_CS,0x1000),(UC_X86_REG_DS,0x3000),
                                (UC_X86_REG_ES,0x4000),(UC_X86_REG_SS,0x7000),(UC_X86_REG_SP,0xf000)]:
            self.machine.reg_write(register, value)

    def run(self, payload, tag, opcodes=None):
        if len(payload) > 60000:
            raise ValueError('native far-buffer bound exceeded; huge selector behavior unverified')
        context = self.original_registry
        if opcodes is not None:
            data = bytearray(0x70c)
            struct.pack_into('<H', data, 0x70a, 1)
            struct.pack_into('<I', data, 0x7a, int.from_bytes(tag.encode('ascii'),'big'))
            struct.pack_into('<'+'h'*len(opcodes), data, 0x7e, *opcodes)
            context = bytes(data)
        self.machine.mem_write(0x40000, context)
        self.machine.mem_write(0x50000, payload+bytes(16))
        self.registers()
        self.machine.mem_write(0x7f000, struct.pack('<HHHHIHHI',0xf100,0x1000,
                                                  0,0x4000,len(payload),0,0x5000,
                                                  int.from_bytes(tag.encode('ascii'),'big')))
        self.machine.emu_start(0x18462,0x1f100,count=1000000)
        if self.machine.reg_read(UC_X86_REG_CS)!=0x1000 or self.machine.reg_read(UC_X86_REG_IP)!=0xf100:
            raise ValueError('postread did not return within bound')
        if bytes(self.machine.mem_read(0x50000+len(payload),16)) != bytes(16):
            raise ValueError('native postread wrote outside declared payload')
        return bytes(self.machine.mem_read(0x50000,len(payload)))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive',type=Path)
    parser.add_argument('executable',type=Path)
    parser.add_argument('report',type=Path)
    parser.add_argument('--key',action='append',default=[])
    parser.add_argument('--all-bounded',action='store_true',help='compare registered positive buffers <=60000 bytes; report exclusions')
    args=parser.parse_args()
    executable=args.executable.read_bytes()
    native=NativeTransform(executable)
    cases=[(bytes.fromhex('123489abcdef')+b'end',(-2,-3,0)),
           (bytes.fromhex('00020123abcd')+b'end',(-4,-2,-5,0)),
           (bytes.fromhex('0000aabbccdd'),(-4,-2,-5,0)),
           (b'X\x01\x02'+b'z'*256+b'\x03\x04tail',(-1,-2,-6,-2,0)),
           (bytes.fromhex('12345678'),(-1,-8,-1,-2,0)),
           (bytes.fromhex('0123456789ab'),(-7,0))]
    for payload,pattern in cases:
        if native.run(payload,'TEST',pattern)!=transform(payload,pattern):
            raise ValueError('synthetic native/model mismatch')
    if not args.key and not args.all_bounded:
        parser.error('select --key or --all-bounded')
    rows={}
    excluded={}
    with args.archive.open('rb') as source:
        archive_hash=verify_source(source,DEFAULT_SOURCE_MANIFEST)
        index=read_index(source).by_key()
        keys=set(args.key)
        if args.all_bounded:
            for key,resource in index.items():
                if resource.tag not in native.patterns:
                    continue
                if not resource.length or resource.length>60000:
                    excluded[key]=dict(length=resource.length,reason='empty buffer or native far-buffer bound; not validated')
                else:
                    keys.add(key)
        for key in sorted(keys):
            resource=index[key]
            source.seek(resource.offset)
            payload=source.read(resource.length)
            pattern=native.patterns.get(resource.tag)
            normalized=transform(payload,pattern.opcodes if pattern else None)
            actual=native.run(payload,resource.tag)
            if actual!=normalized:
                raise ValueError(f'native transform mismatch for {key}')
            rows[key]=dict(offset=resource.offset,length=resource.length,
                           raw_sha256=hashlib.sha256(payload).hexdigest(),
                           normalized_sha256=hashlib.sha256(normalized).hexdigest())
    report=dict(executable_sha256=hashlib.sha256(executable).hexdigest(),archive_sha256=archive_hash,
                unicorn_version=__version__,registrations=17,synthetic_cases=len(cases),mismatches=0,
                patterns={p.tag:dict(call_ne=f'0001:{p.call_offset:04x}',opcodes=list(p.opcodes)) for p in native.patterns.values()},
                relocations=native.relocations,resources=rows,excluded=excluded,
                scope='Original startup registration and full postread routine with original swap helpers; only far-call selectors relocated. No OS calls/stubs. Buffer <=60000 bytes; huge segmented pointers, malformed-input behavior and resource semantics unverified.')
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps(dict(registrations=17,synthetic_cases=len(cases),resources=len(rows),excluded=len(excluded),mismatches=0)))


if __name__=='__main__':
    main()
