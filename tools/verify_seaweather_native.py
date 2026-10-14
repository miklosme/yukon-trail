#!/usr/bin/env python3
"""Original NE2:3188 selected sea context0 weather/food/counter/RNG consumers.

Original setters, inventory and RNG execute unchanged; no behavior stubs.
Date/day/reset/journal consumers remain separate. Only far selectors relocated.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn.x86_const import UC_X86_REG_CS,UC_X86_REG_IP,UC_X86_REG_SS,UC_X86_REG_SP
try:
    from .verify_seaday_native import SeaDayNative
    from .yukonseaday import sea_weather_update
    from .yukoninitial import original_random_step
except ImportError:
    from verify_seaday_native import SeaDayNative
    from yukonseaday import sea_weather_update
    from yukoninitial import original_random_step

class SeaWeatherNative(SeaDayNative):
    def route_far_call(self,m,address,size,user):
        code=bytes(m.mem_read(address,size))
        if code[0]!=0x9a:return super().route_far_call(m,address,size,user)
        off=int.from_bytes(code[1:3],'little')
        if off not in (0xa050,0xa074):return super().route_far_call(m,address,size,user)
        caller=m.reg_read(UC_X86_REG_CS);ip=m.reg_read(UC_X86_REG_IP);self.relocations.add((caller,ip,0x1000,off))
        sp=(m.reg_read(UC_X86_REG_SP)-4)&65535;m.mem_write(m.reg_read(UC_X86_REG_SS)*16+sp,struct.pack('<HH',ip+size,caller));m.reg_write(UC_X86_REG_SP,sp);m.reg_write(UC_X86_REG_CS,0x1000);m.reg_write(UC_X86_REG_IP,off)
    def weather(self,state,world,context,seed):
        self.m.mem_write(0x50000,state);self.m.mem_write(0x46000,world);self.m.mem_write(0x47000,context);self.m.mem_write(0x3483e,struct.pack('<I',seed))
        self.call(0x8000,0x3188,struct.pack('<4H',0x6000,0x4000,0x7000,0x4000))
        if bytes(self.m.mem_read(0x47000,len(context)))!=context:raise ValueError('Original sea context mutated')
        return bytes(self.m.mem_read(0x50000,len(state))),bytes(self.m.mem_read(0x46000,len(world))),struct.unpack('<I',self.m.mem_read(0x3483e,4))[0]

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('executable',type=Path);p.add_argument('report',type=Path);a=p.parse_args();exe=a.executable.read_bytes();n=SeaWeatherNative(exe);cases=[]
    keys={('percent',v) for v in range(1,16)}|{('chance',v) for v in (54,55,74,75)}|{('losschance',v)for v in (79,80)};seeds={}
    for seed in range(100000):
        current=seed;values=[]
        for _ in range(4):current,value=original_random_step(current);values.append(value)
        first,second=values[0]%100,values[1]%100
        selected=[('chance',first)]
        if first>=75:
            selected.append(('losschance',second))
            if second>=80:selected.append(('percent',values[2]%15+1))
        for key in selected:
            if key in keys and key not in seeds:seeds[key]=seed
        if set(seeds)==keys:break
    if set(seeds)!=keys:raise ValueError('Weather RNG fixtures incomplete')
    for seed in sorted(set(seeds.values())|{0,1,12345,0x7fffffff,0xffffffff}):
        for ship in (0,1,2,3,32767,32768,65535):
            for food in (0,2400,3276,32767,32768,65535):
                for gate in (0,1):
                    state=bytearray([0x55]*0x400);world=bytes([0x55]*0x38);context=struct.pack('<3H',0,0x5555,0x5555)
                    for o,v in ((0x320,ship),(0x2fe,food),(0x334,gate),(0x32e,65535)):struct.pack_into('<H',state,o,v)
                    actual=n.weather(bytes(state),world,context,seed);wanted=sea_weather_update(bytes(state),world,context,seed)
                    if actual!=wanted:raise ValueError(f'Original weather differs{ship,food,gate,seed}')
                    cases.append([ship,food,gate,seed,hashlib.sha256(actual[0]).hexdigest(),hashlib.sha256(actual[1]).hexdigest(),actual[2]])
    report=dict(executable_sha256=hashlib.sha256(exe).hexdigest(),entry='NE2:3188/Ghidra1008:3188',cases=cases,rng_branch_seeds=[[list(k),v] for k,v in sorted(seeds.items())],mismatches=0,far_selector_relocations=sorted(n.relocations),scope=__doc__)
    a.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(dict(cases=len(cases),mismatches=0)))
if __name__=='__main__':main()
