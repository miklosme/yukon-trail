#!/usr/bin/env python3
"""Original2a8e through2b67, before2c8c, actual weather/event/date/state/RNG.

Selected sea context0. All called game rules execute unchanged. Stops before
journal consumer2c8c, not a full sea-day claim; far selectors only relocated.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn.x86_const import UC_X86_REG_CS,UC_X86_REG_IP,UC_X86_REG_SS,UC_X86_REG_SP
try:
    from .verify_seaweather_native import SeaWeatherNative
    from .yukonseaday import advance_sea_day_before_journal
except ImportError:
    from verify_seaweather_native import SeaWeatherNative
    from yukonseaday import advance_sea_day_before_journal

class SeaDayBlockNative(SeaWeatherNative):
    def route_far_call(self,m,address,size,user):
        caller=m.reg_read(UC_X86_REG_CS);ip=m.reg_read(UC_X86_REG_IP)
        if (caller,ip)==(0x8000,0x2b68):self.stopped=True;m.emu_stop();return
        code=bytes(m.mem_read(address,size))
        if code[0]!=0x9a:return super().route_far_call(m,address,size,user)
        off=int.from_bytes(code[1:3],'little')
        if off not in (0xa098,0xa734,0xa0c2,0xa67e,0x9ec6):return super().route_far_call(m,address,size,user)
        self.relocations.add((caller,ip,0x1000,off));sp=(m.reg_read(UC_X86_REG_SP)-4)&65535;m.mem_write(m.reg_read(UC_X86_REG_SS)*16+sp,struct.pack('<HH',ip+size,caller));m.reg_write(UC_X86_REG_SP,sp);m.reg_write(UC_X86_REG_CS,0x1000);m.reg_write(UC_X86_REG_IP,off)
    def day(self,state,world,context,seed):
        self.stopped=False;self.m.mem_write(0x50000,state);self.m.mem_write(0x46000,world);self.m.mem_write(0x47000,context);self.m.mem_write(0x3483e,struct.pack('<I',seed))
        try:self.call(0x8000,0x2a8e,struct.pack('<4H',0x6000,0x4000,0x7000,0x4000))
        except ValueError:
            if not self.stopped:raise
        if not self.stopped:raise ValueError('Original day block escaped journal boundary')
        if bytes(self.m.mem_read(0x47000,len(context)))!=context:raise ValueError('Original sea context mutated')
        return bytes(self.m.mem_read(0x50000,len(state))),bytes(self.m.mem_read(0x46000,len(world))),struct.unpack('<I',self.m.mem_read(0x3483e,4))[0]

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('executable',type=Path);p.add_argument('report',type=Path);a=p.parse_args();exe=a.executable.read_bytes();n=SeaDayBlockNative(exe);cases=[]
    def case(weather_count,status_count,gate,date,seed,counter=3,context_word=1,ship=2,food=2400):
        state=bytearray([0x55]*0x400);world=bytearray([0x55]*0x38);context=struct.pack('<3H',0,0x5555,context_word)
        for o,v in ((0x31e,weather_count),(0x31a,status_count),(0x334,gate),(0x320,ship),(0x2fe,food),(0x32e,65535),*zip((0x28,0x2a,0x30e,0x310),date)):struct.pack_into('<H',state,o,v)
        struct.pack_into('<H',world,0x18,counter)
        actual=n.day(bytes(state),bytes(world),context,seed);wanted=advance_sea_day_before_journal(bytes(state),bytes(world),context,seed)
        if actual!=wanted:raise ValueError(f'Original day block differs{weather_count,status_count,gate,date,seed,counter,context_word,ship,food}')
        return [weather_count,status_count,gate,list(date),seed,counter,context_word,ship,food,hashlib.sha256(actual[0]).hexdigest(),hashlib.sha256(actual[1]).hexdigest(),actual[2]]
    for weather_count in (0,1,2,32767,32768,65535):
        for status_count in (0,1,2,32767,32768,65535):
            for gate in (0,1):
                for date in ((24,8,1,1),(31,8,65535,1),(31,12,0,65535),(28,2,32768,32768)):
                    for seed in (0,1,10,12345,0xffffffff):cases.append(case(weather_count,status_count,gate,date,seed))
    targeted=[]
    for seed in (10,76,103,256,438,597):
        for counter in (0,3,65535):
            for context_word in (0,1,2):
                for ship in (1,2,3):
                    for food in (2400,32767):
                        for gate in (0,1):targeted.append(case(0,0,gate,(24,8,1,1),seed,counter,context_word,ship,food))
    report=dict(executable_sha256=hashlib.sha256(exe).hexdigest(),entry='NE2:2a8e through2b67/Ghidra1008',cases=cases,targeted_cases=targeted,mismatches=0,far_selector_relocations=sorted(n.relocations),scope=__doc__)
    a.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(dict(cases=len(cases),targeted_cases=len(targeted),mismatches=0)))
if __name__=='__main__':main()
