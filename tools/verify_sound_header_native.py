#!/usr/bin/env python3
"""Run original variable packed-sound header and checkpoint copy consumers.

Original NE3:baae/bfd8 and NE4 memory stream accessors execute. Bounded
allocation/buffer construction/lock are explicit platform stubs. No record or
checkpoint parsing, cursor calculation, palette or block-count behavior stub.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_AX,UC_X86_REG_DX,UC_X86_REG_CS,UC_X86_REG_DS,UC_X86_REG_ES,UC_X86_REG_SS,UC_X86_REG_SP,UC_X86_REG_IP
try:
    from .verify_bitmap_native import NativeReader
    from .yukonres import verify_source,read_index,DEFAULT_SOURCE_MANIFEST
except ImportError:
    from verify_bitmap_native import NativeReader
    from yukonres import verify_source,read_index,DEFAULT_SOURCE_MANIFEST


class Header:
    def __init__(self,executable):
        self.m=NativeReader(executable).machine
        self.m.mem_write(0x10000,executable[0x1dde0:0x1dde0+59278])
        self.m.mem_write(0x20000,executable[0x2cac0:0x2cac0+60252])
        self.m.hook_add(UC_HOOK_CODE,self.platform)
        self.allocations=[];self.constructions=[];self.locks=0
    def platform(self,m,address,size,user):
        code=bytes(m.mem_read(address,size));ip=m.reg_read(UC_X86_REG_IP);sp=m.reg_read(UC_X86_REG_SP);ss=m.reg_read(UC_X86_REG_SS)*16
        if code==bytes.fromhex('26ff5f04') and address==0x1c0a5:
            self.locks+=1;m.reg_write(UC_X86_REG_AX,0x3000);m.reg_write(UC_X86_REG_DX,0x5000);m.reg_write(UC_X86_REG_SP,sp+4);m.reg_write(UC_X86_REG_IP,ip+size);return
        if code[0]!=0x9a:return
        offset=int.from_bytes(code[1:3],'little')
        if offset==0x1ebe:
            length=int.from_bytes(m.mem_read(ss+sp,2),'little')
            if length!=24:raise ValueError('Unexpected header allocation')
            self.allocations.append(length);m.reg_write(UC_X86_REG_AX,0x2000);m.reg_write(UC_X86_REG_DX,0x5000);m.reg_write(UC_X86_REG_IP,ip+size);return
        if offset==0x8912:
            obj,segment,flags,length=struct.unpack('<HHHI',m.mem_read(ss+sp,10))
            if flags!=16 or not 8<=length<=208 or length%8:raise ValueError('Unsupported checkpoint allocation request')
            self.constructions.append([obj,segment,flags,length]);m.mem_write(segment*16+obj,struct.pack('<HH',0x4000,0x4000)+bytes(20));m.reg_write(UC_X86_REG_AX,obj);m.reg_write(UC_X86_REG_DX,segment);m.reg_write(UC_X86_REG_SP,sp+10);m.reg_write(UC_X86_REG_IP,ip+size);return
        raise ValueError(f'Unrecovered native header dependency{address:x}:{code.hex()}')
    def run(self,chunk):
        m=self.m;size,algorithm,flags,bits,expanded=struct.unpack_from('<HBBII',chunk)
        count=struct.unpack_from('<H',chunk,12)[0] if flags==2 and len(chunk)>=14 else 0
        if algorithm!=3 or not ((flags==0 and size==12) or (flags==2 and 1<=count<=26 and size==14+8*count)):
            raise ValueError('Unsupported bounded header/count variant')
        self.allocations=[];self.constructions=[];self.locks=0
        m.mem_write(0x40000,bytes(0x590));m.mem_write(0x4000e,struct.pack('<HH',0,0x5000))
        stream=bytearray(0x1a);struct.pack_into('<HH',stream,0,0x1000,0x5000);struct.pack_into('<HHII',stream,0xe,0,0x6000,len(chunk),0);m.mem_write(0x50000,bytes(stream))
        for slot,target in [(0x18,0xf4c),(0x1c,0xfd8),(0x20,0xfa8),(0x24,0xfc6)]:m.mem_write(0x51000+slot,struct.pack('<HH',target,0x2000))
        # Header reader never reads packed bytes; avoid source data overlapping
        # the synthetic stack for >64KiB clips, while retaining true length.
        m.mem_write(0x60000,chunk[:size]+bytes(16));m.mem_write(0x53000,bytes(208))
        for r,v in [(UC_X86_REG_CS,0x1000),(UC_X86_REG_DS,0x3000),(UC_X86_REG_ES,0x4000),(UC_X86_REG_SS,0x7000),(UC_X86_REG_SP,0xf000)]:m.reg_write(r,v)
        m.mem_write(0x7f000,struct.pack('<HHHH',0xf100,0x1000,0,0x4000));m.emu_start(0x1baae,0x1f100,count=100000)
        if m.reg_read(UC_X86_REG_CS)!=0x1000 or m.reg_read(UC_X86_REG_IP)!=0xf100 or m.reg_read(UC_X86_REG_AX)!=0:raise ValueError('Original header reader did not succeed')
        cursor=int.from_bytes(m.mem_read(0x50016,4),'little');end=int.from_bytes(m.mem_read(0x40574,4),'little');copied=bytes(m.mem_read(0x53000,count*8));actual_count=int.from_bytes(m.mem_read(0x40584,2),'little')
        if (cursor,end,actual_count)!=(size,size,count) or copied!=chunk[14:size]:raise ValueError('Original header/count/checkpoint copy differs')
        if int.from_bytes(m.mem_read(0x40014,4),'little')!=expanded or int.from_bytes(m.mem_read(0x40580,4),'little')!=bits or int.from_bytes(m.mem_read(0x40018,4),'little')!=(expanded+63)//64:raise ValueError('Original expansion/block fields differ')
        palette=bytes(128+i//2 if i%2==0 else 127-i//2 for i in range(256))
        if bytes(m.mem_read(0x40024,256))!=palette or bytes(m.mem_read(0x40124,1))!=b'\0':raise ValueError('Original palette fields differ')
        return dict(header_size=size,checkpoint_count=count if flags==2 else None,native_cursor=cursor,packed_bits=bits,expanded_size=expanded,copied_checkpoint_sha256=hashlib.sha256(copied).hexdigest(),allocation_requests=self.allocations,buffer_requests=self.constructions,buffer_locks=self.locks)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('archive',type=Path);p.add_argument('executable',type=Path);p.add_argument('report',type=Path);args=p.parse_args();executable=args.executable.read_bytes();resources={};native=Header(executable)
    with args.archive.open('rb') as f:
        archive_hash=verify_source(f,DEFAULT_SOURCE_MANIFEST);index=read_index(f).by_key()
        for key,r in index.items():
            if not key.startswith('PSND:'):continue
            resource_id=int(key.split(':')[1]);f.seek(r.offset);payload=f.read(r.length);chunk_offset=12+struct.unpack_from('<I',payload,14)[0]+6
            resources[f'PSND:{resource_id}']=dict(offset=r.offset,length=r.length,raw_sha256=hashlib.sha256(payload).hexdigest(),chunk_offset=chunk_offset,**native.run(payload[chunk_offset:]))
    synthetic=[]
    for count in range(1,27):
        size=14+count*8
        opaque=bytes((i*37+11)&255 for i in range(count*8))
        chunk=struct.pack('<HBBIIH',size,3,2,1,65,count)+opaque+b'\0'
        synthetic.append(native.run(chunk))
    synthetic.append(native.run(struct.pack('<HBBII',12,3,0,1,65)+b'\0'))
    report=dict(executable_sha256=hashlib.sha256(executable).hexdigest(),archive_sha256=archive_hash,resources=resources,actual_header_cases=len(resources),synthetic_cases=synthetic,mismatches=0,scope='Originalbaae/bfd8/memorystreamcursor/getters/count/copy/palette/blockcounts. Boundedallocator, memorybufferconstructor/lock stubs; no seeking, meaning ofcheckpointpairvalues or wholeplayback established.')
    args.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(dict(actual_header_cases=len(resources),synthetic_cases=len(synthetic),mismatches=0)))


if __name__=='__main__':main()
