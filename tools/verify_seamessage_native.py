#!/usr/bin/env python3
"""Original2c8c sea blocks, event flags2040 CSTR selector and1f22 string copy.

CSTR2000 is explicitly preloaded from original postread data between original
resource constructor/destructor call boundaries. Windows handle/resourceclass
ownership is excluded, never claimed executed. All game selection/text/status/
clearing instructions execute unchanged; no game-rule behavior stubs.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn.x86_const import UC_X86_REG_CS,UC_X86_REG_IP,UC_X86_REG_SS,UC_X86_REG_SP,UC_X86_REG_BP
try:
    from .verify_seaday_native import SeaDayNative
    from .yukonseaday import sea_message_update,read_sea_event_strings
    from .yukonres import read_index,verify_source,DEFAULT_SOURCE_MANIFEST
    from .yukontransform import source_patterns,transform
except ImportError:
    from verify_seaday_native import SeaDayNative
    from yukonseaday import sea_message_update,read_sea_event_strings
    from yukonres import read_index,verify_source,DEFAULT_SOURCE_MANIFEST
    from yukontransform import source_patterns,transform

class SeaMessageNative(SeaDayNative):
    def route_far_call(self,m,address,size,user):
        caller=m.reg_read(UC_X86_REG_CS);ip=m.reg_read(UC_X86_REG_IP)
        if caller==0x8000 and ip in (0x2ccf,0x2d4d,0x2d92):self.boundary=ip;m.emu_stop();return
        code=bytes(m.mem_read(address,size))
        if code[0]!=0x9a:return super().route_far_call(m,address,size,user)
        off=int.from_bytes(code[1:3],'little')
        if off not in (0x9cce,0x2040):return super().route_far_call(m,address,size,user)
        target=0x1000 if off==0x9cce else 0x8000
        self.relocations.add((caller,ip,target,off));sp=(m.reg_read(UC_X86_REG_SP)-4)&65535;m.mem_write(m.reg_read(UC_X86_REG_SS)*16+sp,struct.pack('<HH',ip+size,caller));m.reg_write(UC_X86_REG_SP,sp);m.reg_write(UC_X86_REG_CS,target);m.reg_write(UC_X86_REG_IP,off)
    def message(self,state,world,context,text,normalized,entry=0x2c8c):
        self.boundary=None;self.m.mem_write(0x50000,state);self.m.mem_write(0x46000,world);self.m.mem_write(0x47000,context);self.m.mem_write(0x48000,text);self.m.mem_write(0x64000,normalized)
        try:self.call(0x8000,entry,struct.pack('<4H',0x6000,0x4000,0x7000,0x4000))
        except ValueError:
            if self.boundary is None:raise
        constructed=self.boundary is not None
        if constructed:
            if self.boundary not in (0x2ccf,0x2d4d):raise ValueError('Unexpected CSTR first boundary')
            # Explicit source-backed locked instance layout: handle+0 excluded,
            # datafar+4 contains normalized original CSTR2000. No constructor.
            self.m.mem_write(self.m.reg_read(UC_X86_REG_SS)*16+self.m.reg_read(UC_X86_REG_BP)-0x18,struct.pack('<4H',0,0,0x4000,0x6000))
            ip=self.boundary;self.boundary=None;self.m.reg_write(UC_X86_REG_SP,(self.m.reg_read(UC_X86_REG_SP)+6)&65535);self.m.reg_write(UC_X86_REG_IP,ip+5)
            self.m.emu_start(0x80000+ip+5,0x1f100,count=100000)
            if self.boundary!=0x2d92:raise ValueError('Original sea message did not reach destructor boundary')
            self.boundary=None;self.m.reg_write(UC_X86_REG_SP,(self.m.reg_read(UC_X86_REG_SP)+4)&65535);self.m.reg_write(UC_X86_REG_IP,0x2d97)
            self.m.emu_start(0x82d97,0x1f100,count=100000)
        if (self.m.reg_read(UC_X86_REG_CS),self.m.reg_read(UC_X86_REG_IP))!=(0x1000,0xf100):raise ValueError('Original sea message blocks did not return')
        return bytes(self.m.mem_read(0x50000,len(state))),bytes(self.m.mem_read(0x46000,len(world))),bytes(self.m.mem_read(0x48000,len(text))),constructed

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for arg in ('archive','executable','report'):p.add_argument(arg,type=Path)
    a=p.parse_args();exe=a.executable.read_bytes();n=SeaMessageNative(exe);cases=[];patterns=source_patterns(exe)
    with a.archive.open('rb') as f:
        archive_hash=verify_source(f,DEFAULT_SOURCE_MANIFEST);r=read_index(f).by_key()['CSTR:2000'];f.seek(r.offset);raw=f.read(r.length);normalized=transform(raw,patterns['CSTR'].opcodes)
    strings=read_sea_event_strings(normalized)
    for ship in (1,2,3):
        for context_word in (0,1,2):
            for weather_marker in (0,1):
                for event_marker in range(7):
                    for weather_seen in (0,1,65535):
                        for event_seen in (0,1,65535):
                            state=bytearray([0x55]*0x400);world=bytearray([0x55]*0x38);context=struct.pack('<3H',0,0x5555,context_word);text=b'old text\0'+bytes([0x55]*247)
                            struct.pack_into('<H',state,0x320,ship);struct.pack_into('<H',state,0x1a0,weather_seen)
                            if event_marker:struct.pack_into('<H',state,0x19e+2*(event_marker+3),event_seen)
                            for o,v in ((0x28,weather_marker),(0x2a,event_marker)):struct.pack_into('<H',world,o,v)
                            struct.pack_into('<I',world,0x10,0x40008000)
                            actual=n.message(bytes(state),bytes(world),context,text,normalized);wanted=sea_message_update(bytes(state),bytes(world),context,text,strings)
                            if actual[:3]!=wanted[:3] or actual[3]!=(wanted[3] is not None):raise ValueError(f'Original sea message differs{ship,context_word,weather_marker,event_marker,weather_seen,event_seen}')
                            cases.append([ship,context_word,weather_marker,event_marker,weather_seen,event_seen,*[hashlib.sha256(b).hexdigest()for b in actual[:3]],actual[3],wanted[3]])
    report=dict(executable_sha256=hashlib.sha256(exe).hexdigest(),archive_sha256=archive_hash,resource=dict(key=r.key,offset=r.offset,length=r.length,raw_sha256=hashlib.sha256(raw).hexdigest(),normalized_sha256=hashlib.sha256(normalized).hexdigest(),strings_hex=[s.hex()for s in strings]),cases=cases,mismatches=0,far_selector_relocations=sorted(n.relocations),scope=__doc__)
    a.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(dict(cases=len(cases),mismatches=0)))
if __name__=='__main__':main()
