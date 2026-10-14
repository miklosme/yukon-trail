#!/usr/bin/env python3
"""Compare bounded TREE graphs to original recursive NE1:1c56/1d88.

Only allocator is replaced by a bounded synthetic heap. Original recursive
consumers, strlen/strcpy/memcpy/memset execute. Loader/UI/condition evaluation
remain separate from this graph-construction comparison.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from unicorn.x86_const import UC_X86_REG_AX, UC_X86_REG_DX, UC_X86_REG_CS, UC_X86_REG_IP, UC_X86_REG_SS, UC_X86_REG_SP
try:
    from .verify_journal_native import NativeJournal
    from .yukonres import read_index, verify_source, DEFAULT_SOURCE_MANIFEST
    from .yukontransform import source_patterns, transform
    from .yukontree import decode_normalized
except ImportError:
    from verify_journal_native import NativeJournal
    from yukonres import read_index, verify_source, DEFAULT_SOURCE_MANIFEST
    from yukontransform import source_patterns, transform
    from yukontree import decode_normalized


class NativeTree(NativeJournal):
    def __init__(self, executable):
        super().__init__(executable, b'\0\4one\0two\0three\0four\0')
        self.m.mem_map(0x90000, 0x10000)
        self.heap = 0x1000
        self.allocations = 0

    def route_far_call(self, m, address, size, user):
        code = bytes(m.mem_read(address, size))
        if code[0] != 0x9a:
            return
        offset = int.from_bytes(code[1:3], 'little')
        if offset == 0x1ebe:
            length = int.from_bytes(m.mem_read(m.reg_read(UC_X86_REG_SS)*16 + m.reg_read(UC_X86_REG_SP), 2), 'little')
            if not 1 <= length <= 256 or self.heap + length >= 0xff00:
                raise ValueError('Original parser allocation exceeds bounded heap')
            m.reg_write(UC_X86_REG_AX, self.heap)
            m.reg_write(UC_X86_REG_DX, 0x9000)
            m.mem_write(0x90000 + self.heap, bytes(length))
            self.heap += (length + 1) & ~1
            self.allocations += 1
            m.reg_write(UC_X86_REG_IP, m.reg_read(UC_X86_REG_IP) + size)
            return
        if offset != 0x291e:
            return super().route_far_call(m, address, size, user)
        caller, ip = m.reg_read(UC_X86_REG_CS), m.reg_read(UC_X86_REG_IP)
        self.relocations.add((caller, ip, 0x2000, offset))
        sp = (m.reg_read(UC_X86_REG_SP) - 4) & 65535
        m.mem_write(m.reg_read(UC_X86_REG_SS)*16+sp,struct.pack('<HH',ip+size,caller))
        m.reg_write(UC_X86_REG_SP,sp)
        m.reg_write(UC_X86_REG_CS,0x2000)
        m.reg_write(UC_X86_REG_IP,offset)

    def pointer(self, address):
        offset, segment = struct.unpack('<HH', self.m.mem_read(address,4))
        return segment*16+offset if offset or segment else 0

    def compare_record(self, pointer, record):
        if not pointer:
            raise ValueError('Original parser missing record pointer')
        words = struct.unpack('<9H', self.m.mem_read(pointer,18))
        expected = (record.word0, record.link_word, *record.action, *record.condition, record.voice_id)
        if words != expected:
            raise ValueError(f'Original record metadata differs at{record.offset:x}')
        text_pointer = self.pointer(pointer+18)
        if bytes(self.m.mem_read(text_pointer,len(record.text)+1)) != record.text+b'\0':
            raise ValueError(f'Original copied text differs at{record.offset:x}')

    def compare_response(self, pointer, response, parent=0):
        self.compare_record(self.pointer(pointer),response.record)
        if parent and self.pointer(pointer+0x2c) != parent:
            raise ValueError('Original response parent link differs')
        total = 1
        for index, choice in enumerate(response.choices):
            self.compare_record(self.pointer(pointer+4+index*4),choice.record)
            child = self.pointer(pointer+0x30+index*4)
            if choice.response:
                total += self.compare_response(child,choice.response,pointer)
            elif child:
                raise ValueError('Original created unexpected child response')
        if len(response.choices)<10 and self.pointer(pointer+4+len(response.choices)*4):
            raise ValueError('Original created unexpected next choice')
        return total

    def parse_and_compare(self,payload,root_offset,instruction_limit=100000):
        model=decode_normalized(payload)
        if model.root.record.offset!=root_offset:
            raise ValueError('Model root differs from independently selected source offset')
        self.m.mem_write(0x60000,payload)
        self.m.mem_write(0x40000,bytes(0xb8))
        self.m.mem_write(0x40038,struct.pack('<HH',root_offset,0x6000))
        node=self.heap;self.heap+=0x58
        self.m.mem_write(0x90000+node,bytes(0x58))
        self.call(0x1000,0x1c56,struct.pack('<HHHH',0,0x4000,node,0x9000),instruction_limit=instruction_limit)
        nodes=self.compare_response(0x90000+node,model.root)
        cursor_offset,cursor_segment=struct.unpack('<HH',self.m.mem_read(0x40038,4))
        expected_end=model.trailing_empty_offsets[0] if model.trailing_empty_offsets else len(payload)
        if (cursor_offset,cursor_segment)!=(expected_end,0x6000):
            raise ValueError('Original parser consumed different record extent')
        return dict(response_nodes=nodes,allocations=self.allocations,consumed_offset=cursor_offset,
                    raw_record_count=model.count_word,initial_overrides=len(model.initial_overrides),
                    trailing_empty_offsets=model.trailing_empty_offsets)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive',type=Path);parser.add_argument('executable',type=Path);parser.add_argument('report',type=Path)
    args=parser.parse_args();executable=args.executable.read_bytes();patterns=source_patterns(executable)
    results={}
    with args.archive.open('rb') as f:
        archive_hash=verify_source(f,DEFAULT_SOURCE_MANIFEST);index=read_index(f).by_key()
        for key,root_offset in [('TREE:3400',0x228),('TREE:2100',0x44c)]:
            r=index[key];f.seek(r.offset);raw=f.read(r.length);normalized=transform(raw,patterns['TREE'].opcodes)
            proof=NativeTree(executable).parse_and_compare(normalized,root_offset)
            results[key]=dict(offset=r.offset,length=r.length,raw_sha256=hashlib.sha256(raw).hexdigest(),**proof)
    report=dict(executable_sha256=hashlib.sha256(executable).hexdigest(),archive_sha256=archive_hash,
                resources=results,mismatches=0,scope='Original recursive graph/copy routines; bounded allocator stub only. Initial override loader, UI choices, conditions and actions excluded.')
    args.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(report))


if __name__=='__main__':
    main()
