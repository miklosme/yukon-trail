#!/usr/bin/env python3
"""Original choice-link transitions up to NE1:35f8 UI refresh boundary.

Original tree parser and NE1:2fec execute. Allocator is bounded; child response
action callback records arguments without game mutation. This compares links,
visited words and display text, not action rules, conditions or UI refresh.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_CS,UC_X86_REG_DS,UC_X86_REG_ES,UC_X86_REG_SS,UC_X86_REG_SP
try:
    from .verify_tree_native import NativeTree
    from .yukonres import read_index,verify_source,DEFAULT_SOURCE_MANIFEST
    from .yukontransform import source_patterns,transform
    from .yukontree import decode_normalized,step_choice_links
except ImportError:
    from verify_tree_native import NativeTree
    from yukonres import read_index,verify_source,DEFAULT_SOURCE_MANIFEST
    from yukontransform import source_patterns,transform
    from yukontree import decode_normalized,step_choice_links


def nodes(node,path=()):
    yield path,node
    for index,choice in enumerate(node.choices):
        if choice.response:
            yield from nodes(choice.response,path+(index,))


def compare(executable,payload,root_offset,path,slot,result,all_visited=False):
    source=decode_normalized(payload)
    visited=frozenset(r.record.offset for _,r in nodes(source.root))|frozenset(c.record.offset for _,r in nodes(source.root) for c in r.choices) if all_visited else frozenset()
    expected=step_choice_links(source,path,visited,slot,result)
    n=NativeTree(executable);n.parse_and_compare(payload,root_offset);m=n.m
    pointers={():0x91000}
    for p,node in nodes(source.root):
        if p:
            pointers[p]=n.pointer(pointers[p[:-1]]+0x30+p[-1]*4)
    if all_visited:
        for p,node in nodes(source.root):
            m.mem_write(n.pointer(pointers[p]),b'\x01\0')
            for i in range(len(node.choices)):m.mem_write(n.pointer(pointers[p]+4+i*4),b'\x01\0')
    current=pointers[path]
    m.mem_write(0x40000,struct.pack('<HH',0x4000,0x4000))
    m.mem_write(0x44010,struct.pack('<HH',0xf000,0x9000));m.mem_write(0x9f000,bytes.fromhex('ca0400'))
    m.mem_write(0x4003e,struct.pack('<HH',0x1000,0x9000))
    m.mem_write(0x40042,struct.pack('<HH',current-0x90000,0x9000))
    m.mem_write(0x400b4,struct.pack('<H',len(path)+1));m.mem_write(0x400b6,struct.pack('<10H',*range(10)))
    observed_actions=[]
    def spy(machine,address,size,user):
        if address==0x9f000:
            observed_actions.append(struct.unpack('<4H',machine.mem_read(n.pointer(0x40026),8)))
    m.hook_add(UC_HOOK_CODE,spy)
    for register,value in [(UC_X86_REG_CS,0x1000),(UC_X86_REG_DS,0x3000),(UC_X86_REG_ES,0x4000),(UC_X86_REG_SS,0x7000),(UC_X86_REG_SP,0xf000)]:m.reg_write(register,value)
    m.mem_write(0x7f000,struct.pack('<6H',0xf100,0x1000,0,0x4000,result,slot))
    m.emu_start(0x12fec,0x135f8,count=250000)
    actual_pointer=n.pointer(0x40042)
    wanted_pointer=pointers[expected.next_path] if expected.next_path is not None else 0
    wanted_depth=len(expected.next_path)+1 if expected.next_path is not None else 0
    actual_depth=int.from_bytes(m.mem_read(0x400b4,2),'little')
    if (actual_pointer,actual_depth)!=(wanted_pointer,wanted_depth):
        raise ValueError(f'Original link mismatch path{path}/slot{slot}/result{result}: {(actual_pointer,actual_depth)} vs{(wanted_pointer,wanted_depth)}')
    text_pointer=n.pointer(0x40010)
    text=bytes(m.mem_read(text_pointer,256)).split(b'\0')[0]
    expected_text=expected.response_record.text if expected.response_record else b''
    if text!=expected_text:
        raise ValueError('Original selected display text differs')
    actions=[expected.response_record.action] if expected.response_record else []
    if observed_actions!=actions:
        raise ValueError('Original child-response action arguments differ')
    node_record=n.pointer(current);choice_record=n.pointer(current+4+slot*4)
    if bytes(m.mem_read(node_record,2))!=b'\x01\0' or bytes(m.mem_read(choice_record,2))!=b'\x01\0':
        raise ValueError('Original visited words differ')
    return [list(path),slot,result,all_visited,list(expected.next_path) if expected.next_path is not None else None,hashlib.sha256(text).hexdigest()]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive',type=Path);parser.add_argument('executable',type=Path);parser.add_argument('report',type=Path)
    args=parser.parse_args();executable=args.executable.read_bytes();patterns=source_patterns(executable);reports={}
    with args.archive.open('rb') as f:
        archive_hash=verify_source(f,DEFAULT_SOURCE_MANIFEST);index=read_index(f).by_key()
        for key,root_offset in [('TREE:3400',0x228),('TREE:2100',0x44c)]:
            r=index[key];f.seek(r.offset);raw=f.read(r.length);payload=transform(raw,patterns['TREE'].opcodes);source=decode_normalized(payload);rows=[]
            for path,node in nodes(source.root):
                for slot in range(len(node.choices)):
                    for result in (0,1):
                        for visited in (False,True):rows.append(compare(executable,payload,root_offset,path,slot,result,visited))
            reports[key]=dict(cases=len(rows),matrix_sha256=hashlib.sha256(json.dumps(rows,separators=(',',':')).encode()).hexdigest())
    report=dict(executable_sha256=hashlib.sha256(executable).hexdigest(),archive_sha256=archive_hash,resources=reports,mismatches=0,
                scope='Original graph parser and2fec link/visited/text transitions; syntheticallocator and child-action observation callback; stopsbeforeUIrefresh35f8. Fresh/allvisitedcontexts for every rawchoice; actual actioneffects and GUIconditionfilter excluded.')
    args.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(report))


if __name__=='__main__':main()
