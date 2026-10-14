#!/usr/bin/env python3
"""Original32fa and actual RNG/ship/food/32e consumers, no behavior stubs.

This is the sea-event subroutine only; date/world-day2a8e and journal2c8c
consumers are excluded. Far selectors are relocated; source code unchanged.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn.x86_const import UC_X86_REG_CS,UC_X86_REG_IP,UC_X86_REG_SS,UC_X86_REG_SP
try:
    from .verify_ticket_native import TicketNative
    from .yukonseaday import sea_event_update
except ImportError:
    from verify_ticket_native import TicketNative
    from yukonseaday import sea_event_update

class SeaDayNative(TicketNative):
    def route_far_call(self,m,address,size,user):
        code=bytes(m.mem_read(address,size))
        if code[0]!=0x9a:return super().route_far_call(m,address,size,user)
        off=int.from_bytes(code[1:3],'little')
        if off!=0xa942:return super().route_far_call(m,address,size,user)
        caller=m.reg_read(UC_X86_REG_CS);ip=m.reg_read(UC_X86_REG_IP);self.relocations.add((caller,ip,0x1000,off))
        sp=(m.reg_read(UC_X86_REG_SP)-4)&65535;m.mem_write(m.reg_read(UC_X86_REG_SS)*16+sp,struct.pack('<HH',ip+size,caller));m.reg_write(UC_X86_REG_SP,sp);m.reg_write(UC_X86_REG_CS,0x1000);m.reg_write(UC_X86_REG_IP,off)
    def update(self,state,world,context,seed):
        self.m.mem_write(0x50000,state);self.m.mem_write(0x46000,world);self.m.mem_write(0x47000,context);self.m.mem_write(0x3483e,struct.pack('<I',seed))
        self.call(0x8000,0x32fa,struct.pack('<4H',0x6000,0x4000,0x7000,0x4000))
        if bytes(self.m.mem_read(0x47000,len(context)))!=context:raise ValueError('Original sea context mutated')
        return bytes(self.m.mem_read(0x50000,len(state))),bytes(self.m.mem_read(0x46000,len(world))),struct.unpack('<I',self.m.mem_read(0x3483e,4))[0]

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('executable',type=Path);p.add_argument('report',type=Path);a=p.parse_args();exe=a.executable.read_bytes();n=SeaDayNative(exe);cases=[]
    def case(counter,ship,context_word,food,gate,seed):
        state=bytearray([0x55]*0x400);world=bytearray([0x55]*0x38);context=bytearray([0x55]*6)
        for o,v in ((0x320,ship),(0x2fe,food),(0x334,gate),(0x32e,65535)):struct.pack_into('<H',state,o,v)
        struct.pack_into('<H',world,0x18,counter);struct.pack_into('<H',context,4,context_word)
        actual=n.update(bytes(state),bytes(world),bytes(context),seed);wanted=sea_event_update(bytes(state),bytes(world),bytes(context),seed)
        if actual!=wanted:raise ValueError(f'Original sea event differs{counter,ship,context_word,food,gate,seed} diffs={[[[i,x,y] for i,(x,y) in enumerate(zip(a,b)) if x!=y] for a,b in zip(actual[:2],wanted[:2])]}')
        return [counter,ship,context_word,food,gate,seed,hashlib.sha256(actual[0]).hexdigest(),hashlib.sha256(actual[1]).hexdigest(),actual[2]]
    for counter in (0,2,3,32767,32768,65535):
        for ship in (0,1,2,3,32767,32768,65535):
            for context_word in (0,1,2,32768,65535):
                for food in (0,2400,32767,32768,65535):
                    for gate in (0,1):
                        for seed in (0,1,12345,0x7fffffff,0xffffffff):cases.append(case(counter,ship,context_word,food,gate,seed))
    # Select reproducible RNG branch inputs, not outputs from the model under
    # comparison: every loss percentage, plus exact first/second thresholds.
    try:
        from .yukoninitial import original_random_step
    except ImportError:
        from yukoninitial import original_random_step
    seeds={};wanted_keys={('percent',v) for v in range(1,16)}|{('threshold',f,s) for f in (59,60,62,63,65,66) for s in (79,80)}
    for seed in range(100000):
        current=seed;values=[]
        for _ in range(3):current,value=original_random_step(current);values.append(value)
        first,second=values[0]%100,values[1]%100
        keys=[('threshold',first,second)]
        if first>=66 and second>=80:keys.append(('percent',values[2]%15+1))
        for key in keys:
            if key in wanted_keys and key not in seeds:seeds[key]=seed
        if set(seeds)==wanted_keys:break
    if set(seeds)!=wanted_keys:raise ValueError('RNG threshold fixture search incomplete')
    targeted=[]
    for seed in sorted(set(seeds.values())):
        for ship in (1,2,3):
            for context_word in (1,2):
                for food in (0,2400,3276,32767,32768,65535):
                    for gate in (0,1):targeted.append(case(3,ship,context_word,food,gate,seed))
    report=dict(executable_sha256=hashlib.sha256(exe).hexdigest(),entry='NE2:32fa/Ghidra1008:32fa',cases=cases,targeted_cases=targeted,rng_branch_seeds=[[list(k),v] for k,v in sorted(seeds.items())],mismatches=0,far_selector_relocations=sorted(n.relocations),scope=__doc__)
    a.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(dict(cases=len(cases),targeted_cases=len(targeted),mismatches=0)))
if __name__=='__main__':main()
