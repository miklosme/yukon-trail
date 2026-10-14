#!/usr/bin/env python3
"""Selected Linda initial condition then original conversation-array mark.

Executes original condition/getter and NE1:a2e4 unchanged. Constructor order
is checked in source bytes. No OS or behavior stubs for these operations;
whole dialogue constructor/allocation/rendering remain outside this proof.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn.x86_const import UC_X86_REG_CS,UC_X86_REG_IP,UC_X86_REG_DS,UC_X86_REG_ES,UC_X86_REG_SS,UC_X86_REG_SP
try:
    from .verify_tree_conditions_native import Conditions
    from .yukonres import read_index,verify_source,DEFAULT_SOURCE_MANIFEST
    from .yukontransform import source_patterns,transform
    from .yukontree import decode_normalized,open_linda_dialogue
except ImportError:
    from verify_tree_conditions_native import Conditions
    from yukonres import read_index,verify_source,DEFAULT_SOURCE_MANIFEST
    from yukontransform import source_patterns,transform
    from yukontree import decode_normalized,open_linda_dialogue


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('archive','executable','report'):p.add_argument(name,type=Path)
    a=p.parse_args();exe=a.executable.read_bytes();native=Conditions(exe);rows=[];checks=[];resources={}
    for offset,expected in ((0x0883,'e83c23'),(0x092f,'26ff37'),(0x0937,'9ae4a2')):
        if exe[0x460+offset:0x460+offset+len(bytes.fromhex(expected))].hex()!=expected:raise ValueError('Constructor source order changed')
        checks.append(dict(ne=f'0001:{offset:04x}',bytes=expected))
    patterns=source_patterns(exe)
    with a.archive.open('rb') as f:
        archive_hash=verify_source(f,DEFAULT_SOURCE_MANIFEST);index=read_index(f).by_key()
        for key in ('TREE:3400','CONV:3400'):
            r=index[key];f.seek(r.offset);raw=f.read(r.length);resources[key]=dict(offset=r.offset,length=r.length,sha256=hashlib.sha256(raw).hexdigest())
            d=transform(raw,patterns[key.split(':')[0]].opcodes)
            if key.startswith('TREE'):tree=decode_normalized(d)
            elif struct.unpack_from('<H',d)[0]!=4:raise ValueError('Selected CONV context changed')
    for flag in (0,1,2,32767,32768,65535):
        for gate in (0,1,65535):
            condition=native.selected((2,1),(3400,4),0x220,flag)
            state=bytearray(((i*37+11)&255 for i in range(0x350)))
            struct.pack_into('<H',state,0x220,flag);struct.pack_into('<H',state,0x334,gate)
            native.m.mem_write(0x50000,bytes(state));native.m.mem_write(0x352fc,struct.pack('<HH',0,0x7000));native.m.mem_write(0x70054,b'\x00\x00')
            native.call(0x1000,0xa2e4,struct.pack('<HHH',0,0x5000,4))
            actual=bytes(native.m.mem_read(0x50000,len(state)));expected=bytearray(state)
            if not gate:struct.pack_into('<H',expected,0x220,1)
            selected,post=open_linda_dialogue(tree,flag,gate)
            if actual!=expected or struct.unpack_from('<H',actual,0x220)[0]!=post:raise ValueError('Conversation mark mismatch')
            if selected.voice_id!=(3400 if condition else 3401):raise ValueError('Initial selection mismatch')
            dirty=struct.unpack('<H',native.m.mem_read(0x70054,2))[0]
            if dirty!=int(gate==0):raise ValueError('Dirty flag mismatch')
            rows.append(dict(before220=flag,gate334=gate,initial_condition=condition,selected_offset=selected.offset,voice=selected.voice_id,after220=post,dirty54=dirty))
    report=dict(executable_sha256=hashlib.sha256(exe).hexdigest(),archive_sha256=archive_hash,resources=resources,constructor_source_checks=checks,cases=rows,mismatches=0,scope=__doc__)
    a.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(dict(cases=len(rows),mismatches=0)))

if __name__=='__main__':main()
