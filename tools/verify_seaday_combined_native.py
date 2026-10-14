#!/usr/bin/env python3
"""Original2a8e with3188/32fa/date/counters and2c8c sea message consumer.

All game-rule/text/status/marker instructions execute unchanged. Actual CSTR2000
is preloaded at explicit constructor/destructor resource-ownership boundaries;
Windows handles/cache lifetime are excluded, not simulated. No game-rule stubs.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn.x86_const import UC_X86_REG_CS,UC_X86_REG_IP,UC_X86_REG_SS,UC_X86_REG_SP
try:
    from .verify_seamessage_native import SeaMessageNative
    from .yukonseaday import advance_sea_day,read_sea_event_strings
    from .yukonres import read_index,verify_source,DEFAULT_SOURCE_MANIFEST
    from .yukontransform import source_patterns,transform
except ImportError:
    from verify_seamessage_native import SeaMessageNative
    from yukonseaday import advance_sea_day,read_sea_event_strings
    from yukonres import read_index,verify_source,DEFAULT_SOURCE_MANIFEST
    from yukontransform import source_patterns,transform

class SeaDayCombinedNative(SeaMessageNative):
    def route_far_call(self,m,address,size,user):
        code=bytes(m.mem_read(address,size))
        if code[0]!=0x9a:return super().route_far_call(m,address,size,user)
        off=int.from_bytes(code[1:3],'little')
        if off not in (0xa098,0xa734,0xa0c2,0xa67e,0x9ec6,0xa050,0xa074):return super().route_far_call(m,address,size,user)
        caller=m.reg_read(UC_X86_REG_CS);ip=m.reg_read(UC_X86_REG_IP);self.relocations.add((caller,ip,0x1000,off));sp=(m.reg_read(UC_X86_REG_SP)-4)&65535;m.mem_write(m.reg_read(UC_X86_REG_SS)*16+sp,struct.pack('<HH',ip+size,caller));m.reg_write(UC_X86_REG_SP,sp);m.reg_write(UC_X86_REG_CS,0x1000);m.reg_write(UC_X86_REG_IP,off)
    def day(self,state,world,context,text,normalized,seed):
        self.m.mem_write(0x3483e,struct.pack('<I',seed))
        result=self.message(state,world,context,text,normalized,entry=0x2a8e)
        return *result[:3],struct.unpack('<I',self.m.mem_read(0x3483e,4))[0],result[3]

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for arg in ('archive','executable','report'):p.add_argument(arg,type=Path)
    a=p.parse_args();exe=a.executable.read_bytes();n=SeaDayCombinedNative(exe);patterns=source_patterns(exe)
    with a.archive.open('rb') as f:
        archive_hash=verify_source(f,DEFAULT_SOURCE_MANIFEST);r=read_index(f).by_key()['CSTR:2000'];f.seek(r.offset);raw=f.read(r.length);normalized=transform(raw,patterns['CSTR'].opcodes)
    strings=read_sea_event_strings(normalized)
    cases=[]
    def case(weather_count,status_count,gate,date,seed,ship=2,context_word=1,counter=3,seen=0):
        state=bytearray([0x55]*0x400);world=bytearray([0x55]*0x38);context=struct.pack('<3H',0,0x5555,context_word);text=b'old text\0'+bytes([0x55]*247)
        for o,v in ((0x31e,weather_count),(0x31a,status_count),(0x334,gate),(0x320,ship),(0x2fe,2400),(0x32e,65535),*zip((0x28,0x2a,0x30e,0x310),date)):struct.pack_into('<H',state,o,v)
        for flag in range(10):struct.pack_into('<H',state,0x19e+2*flag,seen)
        for o,v in ((0x18,counter),(0x28,0),(0x2a,0)):struct.pack_into('<H',world,o,v)
        struct.pack_into('<I',world,0x10,0x40008000)
        actual=n.day(bytes(state),bytes(world),context,text,normalized,seed);wanted=advance_sea_day(bytes(state),bytes(world),context,text,strings,seed)
        if actual[:4]!=wanted[:4] or actual[4]!=(wanted[4] is not None):raise ValueError(f'Original combined sea day differs{weather_count,status_count,gate,date,seed,ship,context_word,counter,seen}')
        return [weather_count,status_count,gate,list(date),seed,ship,context_word,counter,seen,*[hashlib.sha256(b).hexdigest()for b in actual[:3]],actual[3],actual[4],wanted[4]]
    for weather_count in (0,1,2,32767,32768,65535):
        for status_count in (0,1,2,32767,32768,65535):
            for gate in (0,1):
                for date in ((24,8,1,1),(31,8,65535,1),(31,12,0,65535),(28,2,32768,32768)):
                    for seed in (0,10,12345):cases.append(case(weather_count,status_count,gate,date,seed))
    targeted=[]
    for ship in (1,2,3):
        for context_word in (0,1,2):
            for counter in (0,3):
                for weather_count in (0,2):
                    for status_count in (0,1):
                        for seen in (0,1):
                            for seed in (0,10,12345):targeted.append(case(weather_count,status_count,0,(24,8,1,1),seed,ship,context_word,counter,seen))
    report=dict(executable_sha256=hashlib.sha256(exe).hexdigest(),archive_sha256=archive_hash,resource=dict(key=r.key,offset=r.offset,length=r.length,raw_sha256=hashlib.sha256(raw).hexdigest(),normalized_sha256=hashlib.sha256(normalized).hexdigest(),strings_hex=[s.hex()for s in strings]),cases=cases,targeted_cases=targeted,mismatches=0,far_selector_relocations=sorted(n.relocations),scope=__doc__)
    a.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(dict(cases=len(cases),targeted_cases=len(targeted),mismatches=0)))
if __name__=='__main__':main()
