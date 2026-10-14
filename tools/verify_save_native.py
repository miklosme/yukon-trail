#!/usr/bin/env python3
"""Execute original NE1:974a/97ec and original8d88/8e24/8d70 wrappers.

Only file-open dialog and KERNEL file I/O calls are substituted with an in-memory
file; original five-block transfer order/pointers/counts and wrapper count checks
execute. No full load validation, constructor, scene rebuild, OS disk failure or
browser persistence claim. Synthetic selectors relocate unchanged source calls.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn.x86_const import UC_X86_REG_CS,UC_X86_REG_IP,UC_X86_REG_SS,UC_X86_REG_SP,UC_X86_REG_AX
try:
    from .verify_journal_native import NativeJournal
    from .yukonsave import read_save
except ImportError:
    from verify_journal_native import NativeJournal
    from yukonsave import read_save

class SaveNative(NativeJournal):
    def route_far_call(self,m,address,size,user):
        code=bytes(m.mem_read(address,size))
        if code[0]!=0x9a:return
        cs=m.reg_read(UC_X86_REG_CS);ip=m.reg_read(UC_X86_REG_IP);sp=m.reg_read(UC_X86_REG_SP);ss=m.reg_read(UC_X86_REG_SS)*16
        if cs==0x1000 and ip in (0x9754,0x97f7):
            m.reg_write(UC_X86_REG_AX,7);m.reg_write(UC_X86_REG_IP,ip+size);return
        if cs==0x1000 and ip in (0x8d9a,0x8e36):
            count,off,seg,handle=struct.unpack('<4H',m.mem_read(ss+sp,8))
            if handle!=7:raise ValueError('Unexpected synthetic handle')
            if ip==0x8d9a:
                chunk=self.file[self.position:self.position+count]
                if len(chunk)!=count:raise ValueError('Unexpected native short read')
                m.mem_write(seg*16+off,chunk)
            else:
                chunk=bytes(m.mem_read(seg*16+off,count));self.file+=chunk
            self.transfers.append(dict(count=count,offset=off,selector=seg,sha256=hashlib.sha256(chunk).hexdigest()))
            self.position+=count;m.reg_write(UC_X86_REG_AX,count);m.reg_write(UC_X86_REG_SP,sp+8);m.reg_write(UC_X86_REG_IP,ip+size);return
        if cs==0x1000 and ip==0x8d79:
            m.reg_write(UC_X86_REG_AX,0);m.reg_write(UC_X86_REG_SP,sp+2);m.reg_write(UC_X86_REG_IP,ip+size);return
        targets={0x9771:0x8d88,0x9788:0x8d88,0x979f:0x8d88,0x97b5:0x8d88,0x97cf:0x8d88,0x97df:0x8d70,0x9814:0x8e24,0x982b:0x8e24,0x9842:0x8e24,0x9858:0x8e24,0x9872:0x8e24,0x9882:0x8d70}
        if cs!=0x1000 or ip not in targets:raise ValueError(f'Unexpected save dependency {cs:04x}:{ip:04x}')
        target=targets[ip];self.relocations.add((cs,ip,0x1000,target));sp=(sp-4)&65535
        m.mem_write(ss+sp,struct.pack('<HH',ip+size,cs));m.reg_write(UC_X86_REG_SP,sp);m.reg_write(UC_X86_REG_CS,0x1000);m.reg_write(UC_X86_REG_IP,target)

    def transfer(self,data):
        self.file=data;self.position=0;self.transfers=[]
        self.m.mem_write(0x43000,bytes([0x55])*0x80);self.m.mem_write(0x50000,bytes([0x55])*902);self.m.mem_write(0x61000,bytes([0x55])*10240)
        ax,_=self.call(0x1000,0x974a,struct.pack('<HH',0x3000,0x4000))
        blocks=[bytes(self.m.mem_read(a,n))for a,n in ((0x43004,5),(0x43009,64),(0x43049,10),(0x50000,902),(0x61000,10240))]
        if ax!=1 or b''.join(blocks)!=data:raise ValueError('Original read transfer differs')
        reads=self.transfers;self.file=b'';self.position=0;self.transfers=[]
        ax,_=self.call(0x1000,0x97ec,struct.pack('<HH',0x3000,0x4000))
        if ax!=1 or self.file!=data:raise ValueError('Original write transfer differs')
        return reads,self.transfers

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('executable',type=Path);p.add_argument('report',type=Path);p.add_argument('saves',type=Path,nargs='+');a=p.parse_args();exe=a.executable.read_bytes();n=SaveNative(exe,b'');cases=[]
    for path in a.saves:
        data=path.read_bytes();s=read_save(data);reads,writes=n.transfer(data)
        if s.bytes()!=data:raise ValueError('Container roundtrip changed bytes')
        cases.append(dict(path=str(path),size=len(data),sha256=hashlib.sha256(data).hexdigest(),read_transfers=reads,write_transfers=writes,state_sha256=hashlib.sha256(s.state).hexdigest(),journal_buffer_sha256=hashlib.sha256(s.journal).hexdigest(),journal_text_sha256=hashlib.sha256(s.journal_text()).hexdigest(),words={f'{off:03x}':s.word(off)for off in (0x28,0x2a,0x34,0x36,0x38,0x2fa,0x2fc,0x2fe,0x306,0x30e,0x310,0x312,0x330,0x332)}))
    ranges=[(0x974a,0x97ec),(0x97ec,0x988f),(0x8d88,0x8e24),(0x8e24,0x8ec0),(0x8d70,0x8d88)]
    source_ranges=[dict(ne_segment=1,offset=start,end_exclusive=end,ghidra=f'1000:{start:04x}',file_offset=0x460+start,sha256=hashlib.sha256(exe[0x460+start:0x460+end]).hexdigest())for start,end in ranges]
    report=dict(executable_sha256=hashlib.sha256(exe).hexdigest(),source_instruction_ranges=source_ranges,cases=cases,mismatches=0,synthetic_far_relocations=sorted(n.relocations),scope=__doc__)
    a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(cases=len(cases),mismatches=0)))
if __name__=='__main__':main()
