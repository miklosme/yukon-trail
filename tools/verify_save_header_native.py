#!/usr/bin/env python3
"""Execute original header decision branch NE1:95a9..95ca and NE6:2004.

Original constructor92fe..9322 copies source title/version literals to runtime
globals through original1fda; only far selectors relocated. No string comparison
or header decision stub. Full file read, prompt/errors and restore excluded.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn.x86_const import UC_X86_REG_CS,UC_X86_REG_IP,UC_X86_REG_SS,UC_X86_REG_SP,UC_X86_REG_BP,UC_X86_REG_DS,UC_X86_REG_ES
try:
    from .verify_journal_native import NativeJournal
    from .yukonsave import header_status
except ImportError:
    from verify_journal_native import NativeJournal
    from yukonsave import header_status

class HeaderNative(NativeJournal):
    def route_far_call(self,m,address,size,user):
        code=bytes(m.mem_read(address,size))
        if code[0]!=0x9a:return
        cs=m.reg_read(UC_X86_REG_CS);ip=m.reg_read(UC_X86_REG_IP)
        targets={0x9308:0x1fda,0x931a:0x1fda,0x95b9:0x2004,0x9623:0x2004,0x9645:0x2004}
        if cs!=0x1000 or ip not in targets:raise ValueError('Unrecovered header dependency')
        target=targets[ip];self.relocations.add((cs,ip,0x2000,target));sp=(m.reg_read(UC_X86_REG_SP)-4)&65535
        m.mem_write(m.reg_read(UC_X86_REG_SS)*16+sp,struct.pack('<HH',ip+size,cs));m.reg_write(UC_X86_REG_SP,sp);m.reg_write(UC_X86_REG_CS,0x2000);m.reg_write(UC_X86_REG_IP,target)

    def registers(self):
        for r,v in ((UC_X86_REG_CS,0x1000),(UC_X86_REG_DS,0x3000),(UC_X86_REG_ES,0x4000),(UC_X86_REG_SS,0x7000),(UC_X86_REG_SP,0xee00),(UC_X86_REG_BP,0xf000)):self.m.reg_write(r,v)

    def setup(self):
        self.registers();self.m.emu_start(0x192fe,0x19322,count=10000)
        if self.m.reg_read(UC_X86_REG_IP)!=0x9322:raise ValueError('Original header initializer did not finish')
        self.m.mem_write(0x30dbc,struct.pack('<HH',0xdb6,0x3000))
        return bytes(self.m.mem_read(0x3564a,64)),bytes(self.m.mem_read(0x35640,10))

    def status(self,header):
        self.m.mem_write(0x43004,header);self.m.mem_write(0x7f006,struct.pack('<HH',0x3000,0x4000));self.registers()
        self.m.emu_start(0x195a9,0x195ca,count=10000)
        if self.m.reg_read(UC_X86_REG_IP)!=0x95ca:raise ValueError('Header decision failed to join')
        return struct.unpack('<h',self.m.mem_read(0x7effe,2))[0]

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('executable',type=Path);p.add_argument('report',type=Path);a=p.parse_args();exe=a.executable.read_bytes();n=HeaderNative(exe,b'');title,version=n.setup()
    header=b'MECC\0'+title+version;inputs=[('source-current',header)]
    for offset in range(79):
        for value in (0,65,255):
            altered=bytearray(header);altered[offset]=value;inputs.append((f'byte{offset}-value{value}',bytes(altered)))
    for v in (b'0',b'0.0',b'0.10',b'0.2',b'1.0',b'',b'0.1x',b'0.1\0tail'):
        inputs.append(('version-'+v.hex(),header[:69]+v.ljust(10,b'\0')))
    cases=[]
    for name,data in inputs:
        actual=n.status(data)
        if actual!=header_status(data):raise ValueError(f'Header model differs {name}:native{actual}')
        cases.append(dict(name=name,header_hex=data.hex(),native_status=actual))
    report=dict(executable_sha256=hashlib.sha256(exe).hexdigest(),cases=cases,native_cases=len(cases),mismatches=0,reference_title_hex=title.hex(),reference_version_hex=version.hex(),source={'initializer':'0001:92fe..9322','header_branch':'0001:95a9..95ca/9614..9670','compare':'0006:2004..203f','ghidra_mapping':{'1':'1000','6':'1028'},'source_title_file_offset':0x4f420+0xdd2,'source_version_file_offset':0x4f420+0xdce},synthetic_far_relocations=sorted(n.relocations),scope=__doc__)
    a.report.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(cases=len(cases),mismatches=0)))
if __name__=='__main__':main()
