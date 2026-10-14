#!/usr/bin/env python3
"""Original NE3:be0e final-block loop,63fe wholeblock and NE1 bit helpers.

Tests selected declared-bit discrepancies with a bounded relocated input suffix.
Original blocks, memory stream cursors, requested/remaining block counts run;
only far selectors relocated. Header platform allocation uses documented stubs.
No full playback, whole processor, huge-buffer allocator or mixer proof.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn.x86_const import UC_X86_REG_CS,UC_X86_REG_DS,UC_X86_REG_ES,UC_X86_REG_SS,UC_X86_REG_SP,UC_X86_REG_IP,UC_X86_REG_AX,UC_X86_REG_DX
try:
    from .verify_sound_header_native import Header
    from .yukonbmp import Bits,_block
    from .yukonres import read_index,verify_source,DEFAULT_SOURCE_MANIFEST
except ImportError:
    from verify_sound_header_native import Header
    from yukonbmp import Bits,_block
    from yukonres import read_index,verify_source,DEFAULT_SOURCE_MANIFEST

class Terminal(Header):
    def __init__(self,exe):
        super().__init__(exe);self.m.mem_map(0x80000,0x10000);self.m.mem_write(0x80000,exe[0x460:0x460+60176]);self.relocations=set()
    def platform(self,m,address,size,user):
        code=bytes(m.mem_read(address,size))
        if code[0]!=0x9a or int.from_bytes(code[1:3],'little') not in (0,0x62,0x129,0x63fe):return super().platform(m,address,size,user)
        offset=int.from_bytes(code[1:3],'little');target=0x1000 if offset==0x63fe else 0x8000;caller=m.reg_read(UC_X86_REG_CS);ip=m.reg_read(UC_X86_REG_IP);self.relocations.add((caller,ip,target,offset));sp=(m.reg_read(UC_X86_REG_SP)-4)&65535
        m.mem_write(m.reg_read(UC_X86_REG_SS)*16+sp,struct.pack('<HH',ip+size,caller));m.reg_write(UC_X86_REG_SP,sp);m.reg_write(UC_X86_REG_CS,target);m.reg_write(UC_X86_REG_IP,offset)
    def last_block(self,chunk):
        self.run(chunk);size,_,_,declared,expanded=struct.unpack_from('<HBBII',chunk);data=chunk[size:];palette=bytes(self.m.mem_read(0x40024,256));reader=Bits(data,len(data)*8);total=0
        while total<((expanded+63)//64)*64:
            start=reader.position;kind=Bits(data,len(data)*8,start).get(2);block,repeat=_block(reader,palette,None,palette_control=False);total+=64*(repeat+1)
        if repeat or kind==2:raise ValueError('Terminal probe onlynonreferenced/nonrepeated lastblocks')
        end=reader.position;origin=max(0,start//8-256);window=data[origin:]
        if len(window)>60000:raise ValueError('Terminal suffix bound exceeded')
        m=self.m;m.mem_write(0x60000,window+bytes(16));m.mem_write(0x50012,struct.pack('<II',len(window),0));m.mem_write(0x40018,struct.pack('<I',1));m.mem_write(0x4001e,struct.pack('<I',start-origin*8));m.mem_write(0x40126,bytes(4));m.mem_write(0x54000,bytes(64));m.mem_write(0x54080,struct.pack('<I',1))
        for r,v in ((UC_X86_REG_CS,0x1000),(UC_X86_REG_DS,0x3000),(UC_X86_REG_ES,0x4000),(UC_X86_REG_SS,0x7000),(UC_X86_REG_SP,0xf000)):m.reg_write(r,v)
        m.mem_write(0x7f000,struct.pack('<8H',0xf100,0x1000,0,0x4000,0x4000,0x5000,0x4080,0x5000));m.emu_start(0x1be0e,0x1f100,count=100000)
        if m.reg_read(UC_X86_REG_CS)!=0x1000 or m.reg_read(UC_X86_REG_IP)!=0xf100:raise ValueError('Native terminal block didnotreturn')
        cursor=int.from_bytes(m.mem_read(0x50016,4),'little');bit=int.from_bytes(m.mem_read(0x4001e,4),'little');native_end=(origin+cursor)*8+bit;remaining=int.from_bytes(m.mem_read(0x40018,4),'little');emitted=int.from_bytes(m.mem_read(0x54080,4),'little')
        if bytes(m.mem_read(0x54000,64))!=block or native_end!=end or remaining!=0 or emitted!=1:raise ValueError('Original finalblock/cursor/count differs')
        return dict(declared_bits=declared,consumed_bits=end,physical_bits=len(data)*8,terminal_unused_bits=len(data)*8-end,last_block_start=start,last_block_kind=kind,last_block_sha256=hashlib.sha256(block).hexdigest(),native_end_bits=native_end,remaining_blocks=remaining,emitted_blocks=emitted,source_window_origin=origin)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('archive','executable','report'):p.add_argument(name,type=Path)
    a=p.parse_args();exe=a.executable.read_bytes();native=Terminal(exe);rows={}
    with a.archive.open('rb') as f:
        archive_hash=verify_source(f,DEFAULT_SOURCE_MANIFEST);index=read_index(f).by_key()
        for id in (3402,1302,2105,395,4123,4452,630,638,8114):
            r=index[f'PSND:{id}'];f.seek(r.offset);raw=f.read(r.length);offset=12+struct.unpack_from('<I',raw,14)[0]+6
            rows[f'PSND:{id}']=dict(offset=r.offset,length=r.length,raw_sha256=hashlib.sha256(raw).hexdigest(),**native.last_block(raw[offset:]))
    report=dict(executable_sha256=hashlib.sha256(exe).hexdigest(),archive_sha256=archive_hash,resources=rows,mismatches=0,synthetic_far_relocations=sorted(native.relocations),scope=__doc__);a.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(dict(cases=len(rows),mismatches=0)))
if __name__=='__main__':main()
