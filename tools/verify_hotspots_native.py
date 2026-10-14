#!/usr/bin/env python3
"""Check selected HSPT fallback against original NE2 instructions; no OS calls."""
import argparse, hashlib, json, struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_16, UC_HOOK_CODE, __version__
from unicorn.x86_const import UC_X86_REG_CS, UC_X86_REG_DS, UC_X86_REG_ES, UC_X86_REG_SS, UC_X86_REG_BP, UC_X86_REG_SP, UC_X86_REG_IP
from yukonbmp import EXE_SHA256
from yukonres import read_index, verify_source, DEFAULT_SOURCE_MANIFEST
from yukontransform import source_patterns, transform
from yukonsprite import read_hotspots, hotspot_candidate


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('archive','executable','report'):p.add_argument(name,type=Path)
    p.add_argument('--id',type=int,action='append',required=True);a=p.parse_args()
    exe=a.executable.read_bytes()
    if hashlib.sha256(exe).hexdigest()!=EXE_SHA256 or __version__!='2.1.4':raise ValueError('unsupported source/Unicorn')
    machine=Uc(UC_ARCH_X86,UC_MODE_16);machine.mem_map(0,0x90000);machine.mem_write(0x10000,exe[0xf2c0:0xf2c0+0xe000])
    hit=[False]
    def stop_before_action(m,address,size,user):
        if address==0x10de6:hit[0]=True;m.emu_stop()
    machine.hook_add(UC_HOOK_CODE,stop_before_action)
    patterns=source_patterns(exe);results={};total=0;native_rows=[]
    with a.archive.open('rb') as source:
        source_hash=verify_source(source,DEFAULT_SOURCE_MANIFEST);index=read_index(source).by_key()
        for rid in sorted(set(a.id)):
            r=index[f'HSPT:{rid}'];source.seek(r.offset);raw=source.read(r.length);data=transform(raw,patterns['HSPT'].opcodes);records=read_hotspots(data)
            points={(-32768,-32768),(32767,32767),(0,0),(-1,-1)}
            for rec in records:
                if rec.sentinel:break
                for x in (rec.left-1,rec.left,rec.left+1,(rec.left+rec.right)//2,rec.right-1,rec.right,rec.right+1):
                    for y in (rec.top-1,rec.top,rec.top+1,(rec.top+rec.bottom)//2,rec.bottom-1,rec.bottom,rec.bottom+1):
                        if -32768<=x<=32767 and -32768<=y<=32767:points.add((x,y))
            machine.mem_write(0x60000,data);machine.mem_write(0x50048,struct.pack('<HH',0,0x6000))
            for x,y in sorted(points):
                for reg,value in [(UC_X86_REG_CS,0x1000),(UC_X86_REG_DS,0x4000),(UC_X86_REG_ES,0x5000),(UC_X86_REG_SS,0x7000),(UC_X86_REG_BP,0xf100),(UC_X86_REG_SP,0xf000)]:machine.reg_write(reg,value)
                machine.mem_write(0x7f106,struct.pack('<HHhHh',0,0x5000,y,0,x));hit[0]=False
                machine.emu_start(0x10d4c,0x10df7,count=20000)
                ip=machine.reg_read(UC_X86_REG_IP)
                if ip not in (0xde6,0xdf7):raise ValueError('HSPT branch escaped bounded region')
                actual=struct.unpack('<H',machine.mem_read(0x7f0fe,2))[0] if hit[0] else None
                native_rows.append([rid,x,y,actual])
                expected=hotspot_candidate(records,x,y)
                if actual!=expected:raise ValueError(f'HSPT:{rid} ({x},{y}): native{actual} vs model{expected}')
            total+=len(points);results[r.key]={'offset':r.offset,'length':r.length,'raw_sha256':hashlib.sha256(raw).hexdigest(),'normalized_sha256':hashlib.sha256(data).hexdigest(),'records':len(records),'points':len(points),'record_words':[[v.left,v.right,v.top,v.bottom,v.action_word0,v.action_word1,v.action_dword] for v in records]}
    report={'executable_sha256':EXE_SHA256,'archive_sha256':source_hash,'unicorn_version':__version__,'native_code':'NE0002:0d4c..0de6/0df7; stops before action virtual call','cases':total,'mismatches':0,'resources':results,'native_rows':native_rows,'native_rows_sha256':hashlib.sha256(json.dumps(native_rows,separators=(',',':')).encode()).hexdigest(),'scope':'selected fallback after sprite hit-test returned no object; no action execution, original UI projection or foreground-sprite interception'}
    a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))

if __name__=='__main__':main()
