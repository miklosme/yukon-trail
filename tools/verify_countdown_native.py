#!/usr/bin/env python3
"""Original bounded0740 day/post-cleanup blocks; no behavior stubs.

Animation draw/advance and timer cancellation/destruction/free are outside the
executed blocks. Explicit synthetic caller frames preserve original operands.
This is not a full callback, timer scheduling or voyage execution proof.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn.x86_const import UC_X86_REG_CS,UC_X86_REG_DS,UC_X86_REG_ES,UC_X86_REG_SS,UC_X86_REG_SP,UC_X86_REG_BP,UC_X86_REG_IP
try:
    from .verify_ticket_native import TicketNative
    from .yukoncountdown import advance_countdown_day_block,finish_wharf_countdown_block
except ImportError:
    from verify_ticket_native import TicketNative
    from yukoncountdown import advance_countdown_day_block,finish_wharf_countdown_block


class CountdownNative(TicketNative):
    def route_far_call(self,m,address,size,user):
        code=bytes(m.mem_read(address,size))
        if code[0]!=0x9a or int.from_bytes(code[1:3],'little')!=0xa0c2:return super().route_far_call(m,address,size,user)
        caller=m.reg_read(UC_X86_REG_CS);ip=m.reg_read(UC_X86_REG_IP);sp=(m.reg_read(UC_X86_REG_SP)-4)&65535
        self.relocations.add((caller,ip,0x1000,0xa0c2));m.mem_write(m.reg_read(UC_X86_REG_SS)*16+sp,struct.pack('<HH',ip+size,caller));m.reg_write(UC_X86_REG_SP,sp);m.reg_write(UC_X86_REG_CS,0x1000);m.reg_write(UC_X86_REG_IP,0xa0c2)
    def block(self,offset,before,scene,manager,countdown):
        self.m.mem_write(0x50000,before);self.m.mem_write(0x40000,scene);self.m.mem_write(0x62000,manager);self.m.mem_write(0x31188,struct.pack('<H',countdown))
        for r,v in ((UC_X86_REG_CS,0x8000),(UC_X86_REG_DS,0x3000),(UC_X86_REG_ES,0x4000),(UC_X86_REG_SS,0x7000),(UC_X86_REG_BP,0xf000),(UC_X86_REG_SP,0xefe8)):self.m.reg_write(r,v)
        self.m.mem_write(0x7f000,struct.pack('<5H',0,0xf100,0x1000,0,0x4000));self.m.emu_start(0x80000+offset,0x1f100,count=10000)
        if self.m.reg_read(UC_X86_REG_IP)!=0xf100 or self.m.reg_read(UC_X86_REG_CS)!=0x1000:raise ValueError('Countdown block escaped')
        return bytes(self.m.mem_read(0x50000,len(before))),bytes(self.m.mem_read(0x40000,len(scene))),bytes(self.m.mem_read(0x62000,len(manager))),struct.unpack('<H',self.m.mem_read(0x31188,2))[0]


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('executable',type=Path);p.add_argument('report',type=Path);a=p.parse_args();exe=a.executable.read_bytes();n=CountdownNative(exe);days=[];completion=[]
    scene=bytearray([0x55]*128);struct.pack_into('<H',scene,4,4000);struct.pack_into('<I',scene,0x18,0x60005000);struct.pack_into('<HH',scene,0x1c,65535,65535);manager=bytes([0x55]*128)
    for day,month,elapsed,phase in ((24,8,1,1),(31,8,65535,5),(28,2,32767,32767),(31,12,65535,65535)):
        for count in (1,7,14,32767):
            for gate in (0,1,65535):
                before=bytearray([0x55]*0x400)
                for o,v in ((0x28,day),(0x2a,month),(0x30e,elapsed),(0x310,phase),(0x334,gate)):struct.pack_into('<H',before,o,v)
                expected,remaining=advance_countdown_day_block(bytes(before),count);actual=n.block(0x079f,bytes(before),bytes(scene),manager,count)
                if actual!=(expected,bytes(scene),manager,remaining):raise ValueError('Original day/decrement block differs')
                days.append([day,month,elapsed,phase,count,gate,hashlib.sha256(actual[0]).hexdigest(),actual[3]])
    for count in (0,32768,65535):
        for gate in (0,1,65535):
            before=bytearray([0x55]*0x400);struct.pack_into('<H',before,0x334,gate)
            actual=n.block(0x0817,bytes(before),bytes(scene),manager,count);expected=finish_wharf_countdown_block(bytes(before),bytes(scene),manager,count)
            if actual!=expected:raise ValueError('Original post-cleanup queue block differs')
            completion.append([count,gate,*[hashlib.sha256(b).hexdigest() for b in actual[:3]],actual[3]])
    report=dict(executable_sha256=hashlib.sha256(exe).hexdigest(),day_cases=days,completion_cases=completion,mismatches=0,synthetic_far_relocations=sorted(n.relocations),scope=__doc__)
    a.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(dict(day_cases=len(days),completion_cases=len(completion),mismatches=0)))
if __name__=='__main__':main()
