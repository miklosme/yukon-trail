#!/usr/bin/env python3
"""Original selected Seattle constructor location switch and journal place heading.

Runs NE2:00e6..0214 throughactual NE1:9ffa setter, then NE1:cff8 place heading
for ungated actual tuples. Only far selectors relocated; no behavior stubs.
Full constructor allocation/rendering and other scene families excluded.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn.x86_const import UC_X86_REG_CS,UC_X86_REG_DS,UC_X86_REG_ES,UC_X86_REG_SS,UC_X86_REG_SP,UC_X86_REG_BP,UC_X86_REG_IP
try:
    from .verify_journal_native import NativeJournal
except ImportError:
    from verify_journal_native import NativeJournal
class LocationNative(NativeJournal):
    def route_far_call(self,m,address,size,user):
        code=bytes(m.mem_read(address,size))
        if code[0]!=0x9a or code[1:3]!=bytes.fromhex('fa9f'):return super().route_far_call(m,address,size,user)
        caller=m.reg_read(UC_X86_REG_CS);ip=m.reg_read(UC_X86_REG_IP);self.relocations.add((caller,ip,0x1000,0x9ffa));sp=(m.reg_read(UC_X86_REG_SP)-4)&65535
        m.mem_write(m.reg_read(UC_X86_REG_SS)*16+sp,struct.pack('<HH',ip+size,caller));m.reg_write(UC_X86_REG_SP,sp);m.reg_write(UC_X86_REG_CS,0x1000);m.reg_write(UC_X86_REG_IP,0x9ffa)
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('executable',type=Path);p.add_argument('report',type=Path);a=p.parse_args();exe=a.executable.read_bytes();n=LocationNative(exe,b'');m=n.m;rows=[]
    m.mem_write(0x352fc,struct.pack('<HH',0x3000,0x6000))
    for scene in (1000,2000,3000,4000):
        for gate in (0,1):
            state=bytearray([0x55]*0x400);struct.pack_into('<H',state,0x334,gate);m.mem_write(0x50000,bytes(state));m.mem_write(0x63054,bytes(2));m.mem_write(0x42004,struct.pack('<H',scene));m.mem_write(0x7f006,struct.pack('<HH',0x2000,0x4000))
            for r,v in ((UC_X86_REG_CS,0x8000),(UC_X86_REG_DS,0x3000),(UC_X86_REG_ES,0x4000),(UC_X86_REG_SS,0x7000),(UC_X86_REG_SP,0xef80),(UC_X86_REG_BP,0xf000)):m.reg_write(r,v)
            m.emu_start(0x800e6,0x80214,count=10000)
            actual=bytes(m.mem_read(0x50000,len(state)));wanted=bytearray(state)
            if not gate:struct.pack_into('<3H',wanted,0x34,200,0,scene)
            dirty=int.from_bytes(m.mem_read(0x63054,2),'little')
            if m.reg_read(UC_X86_REG_IP)!=0x214 or actual!=wanted or dirty!=int(gate==0):raise ValueError('Original selected location constructor differs')
            heading=None
            if not gate:
                m.mem_write(0x41000,bytes(255));n.call(0x1000,0xcff8,struct.pack('<HHH',0,0x4000,0));heading=bytes(m.mem_read(0x41000,255)).split(b'\0')[0]
                # Literal original Data13 Seattle string, not a new formatter.
                source=exe[0x4f420+0xfa2:].split(b'\0')[0]
                if heading!=source or bytes(m.mem_read(0x50000,len(state)))!=actual:raise ValueError('Actual tuple journal place differs from original Seattle literal')
            rows.append(dict(scene=scene,gate334=gate,location_words=struct.unpack_from('<3H',actual,0x34),dirty54=dirty,state_sha256=hashlib.sha256(actual).hexdigest(),journal_place_hex=heading.hex() if heading is not None else None))
    report=dict(executable_sha256=hashlib.sha256(exe).hexdigest(),cases=rows,mismatches=0,synthetic_far_relocations=sorted(n.relocations),scope=__doc__);a.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(dict(cases=rows,mismatches=0)))
if __name__=='__main__':main()
