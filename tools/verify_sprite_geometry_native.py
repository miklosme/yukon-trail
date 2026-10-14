#!/usr/bin/env python3
"""Check selected sprite anchor/movement using original NE2 word arithmetic.

Executes e62a/e5e4 only; no allocator, animation clock, or OS calls.
"""
import argparse, hashlib, json, struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_16, __version__
from unicorn.x86_const import UC_X86_REG_CS, UC_X86_REG_DS, UC_X86_REG_ES, UC_X86_REG_SS, UC_X86_REG_SP, UC_X86_REG_IP
from yukonbmp import EXE_SHA256, decode
from yukonres import read_index, verify_source, DEFAULT_SOURCE_MANIFEST
from yukontransform import source_patterns, transform
from yukonsprite import read_sprite, read_cel_offsets, read_animation, completed_sequence_anchor


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('archive','executable','report'):p.add_argument(name,type=Path)
    a=p.parse_args();exe=a.executable.read_bytes()
    if hashlib.sha256(exe).hexdigest()!=EXE_SHA256 or __version__!='2.1.4':raise ValueError('unsupported source/Unicorn')
    patterns=source_patterns(exe);provenance={}
    with a.archive.open('rb') as source:
        archive_hash=verify_source(source,DEFAULT_SOURCE_MANIFEST);index=read_index(source).by_key()
        def read(key):
            r=index[key];source.seek(r.offset);raw=source.read(r.length);tag=key.split(':')[0];data=transform(raw,patterns[tag].opcodes if tag in patterns else None);provenance[key]={'offset':r.offset,'length':r.length,'raw_sha256':hashlib.sha256(raw).hexdigest(),'normalized_sha256':hashlib.sha256(data).hexdigest()};return data
        sprite=read_sprite(read('SPRT:403'));offsets=read_cel_offsets(read('ACEL:400'));animation=read_animation(read('ASEQ:400'));frame=decode(read('CBMP:400'))[1]
    x,y=offsets[1];state=bytearray(0xa6)
    struct.pack_into('<4h',state,0x10,0,0,frame.height,frame.width);struct.pack_into('<hh',state,0x1c,y,x)
    machine=Uc(UC_ARCH_X86,UC_MODE_16);machine.mem_map(0,0x90000);machine.mem_write(0x10000,exe[0xf2c0:0xf2c0+0xe8da]);machine.mem_write(0x50000,bytes(state))
    geometry_rows=[]
    def invoke(entry,first,second):
        for reg,value in [(UC_X86_REG_CS,0x1000),(UC_X86_REG_DS,0x4000),(UC_X86_REG_ES,0x5000),(UC_X86_REG_SS,0x7000),(UC_X86_REG_SP,0xf000)]:machine.reg_write(reg,value)
        machine.mem_write(0x7f000,struct.pack('<HHHHhh',0xea00,0x1000,0,0x5000,first,second));machine.emu_start(0x10000+entry,0x1ea00,count=2000)
        if machine.reg_read(UC_X86_REG_IP)!=0xea00:raise ValueError('sprite geometry escaped bounded routine')
        snap=bytes(machine.mem_read(0x50000,len(state)));geometry_rows.append([entry,first,second,list(struct.unpack_from('<4h',snap,0x10)),list(struct.unpack_from('<hh',snap,0x24)),snap[0x54]])
    invoke(0xe62a,sprite.anchor_y,sprite.anchor_x)
    start,successor,duration,count=animation.sequences[5]
    for bitmap,dx,dy,unknown,override,flip in animation.steps[start:start+count]:
        if bitmap!=1 or unknown or flip:raise ValueError('selected proof requires frame1/unflipped movement')
        invoke(0xe5e4,dy,dx)
    actual=bytes(machine.mem_read(0x50000,len(state)));ax,ay=completed_sequence_anchor(sprite,animation,5)
    expected=(ay-y,ax-x,ay-y+frame.height,ax-x+frame.width)
    rectangle=struct.unpack_from('<4h',actual,0x10);anchor_y,anchor_x=struct.unpack_from('<hh',actual,0x24)
    if rectangle!=expected or (anchor_x,anchor_y)!=(ax,ay) or actual[0x54]!=1:raise ValueError('selected original geometry mismatch')
    machine.mem_write(0x30000,exe[0x1dde0:0x1dde0+0xe78e])
    machine.mem_write(0x60010,struct.pack('<HH',0xe5b8,0x1000))
    flag_cases=0;flag_rows=[]
    for suspended in (1,2,65535):
        for enabled in (0,1,2,65535):
            for visible in (0,1,2):
                sample=bytearray(0xa6);struct.pack_into('<HH',sample,0,0,0x6000)
                struct.pack_into('<HH',sample,0x82,enabled,suspended);struct.pack_into('<H',sample,0x28,visible)
                expected_sample=sample.copy()
                if not enabled and visible:struct.pack_into('<H',expected_sample,0x28,0);expected_sample[0x54]=1
                machine.mem_write(0x50000,bytes(sample))
                for reg,value in [(UC_X86_REG_CS,0x3000),(UC_X86_REG_DS,0x4000),(UC_X86_REG_ES,0x5000),(UC_X86_REG_SS,0x7000),(UC_X86_REG_SP,0xf000)]:machine.reg_write(reg,value)
                machine.mem_write(0x7f000,struct.pack('<HHHH',0xf000,0x3000,0,0x5000));machine.emu_start(0x32a52,0x3f000,count=2000)
                if machine.reg_read(UC_X86_REG_IP)!=0xf000 or bytes(machine.mem_read(0x50000,len(sample)))!=expected_sample:raise ValueError('suspended sprite flag mismatch')
                observed=bytes(machine.mem_read(0x50000,len(sample)));flag_rows.append([suspended,enabled,visible,struct.unpack_from('<H',observed,0x28)[0],observed[0x54]])
                flag_cases+=1
    report={'executable_sha256':EXE_SHA256,'archive_sha256':archive_hash,'unicorn_version':__version__,'resources':provenance,'native_code':['NE0002:e62a','NE0002:e5e4','NE0003:2a52 suspended branch and NE0002:e5b8 hide'],'geometry_rows':geometry_rows,'geometry_rows_sha256':hashlib.sha256(json.dumps(geometry_rows,separators=(',',':')).encode()).hexdigest(),'suspended_rows':flag_rows,'suspended_rows_sha256':hashlib.sha256(json.dumps(flag_rows,separators=(',',':')).encode()).hexdigest(),'geometry_calls':count+1,'suspended_flag_cases':flag_cases,'mismatches':0,'initial_anchor_xy':[sprite.anchor_x,sprite.anchor_y],'sequence':5,'sequence_descriptor':list(animation.sequences[5]),'completed_anchor_xy':[ax,ay],'bitmap_frame':1,'cel_offset_xy':[x,y],'frame_size_wh':[frame.width,frame.height],'rectangle_top_left_bottom_right':list(rectangle),'predicted_capture_origin_xy':[20+rectangle[1],59+rectangle[0]],'scope':'source-derived sequence5 movement; original geometry functions executed; suspended flags checked across36 cases; constructor, clock/timer/successor scheduling not executed'}
    a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))

if __name__=='__main__':main()
