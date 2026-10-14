#!/usr/bin/env python3
"""Execute original selected scene constructor visit/date branch and visit marker.

Bounded block NE2:04f0..055b executes actual getter and date calls, then original
NE1:a368 marks visit. No behavior stubs. Resource allocation, background/UI,
other constructor state setters and global animation countdown excluded.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn.x86_const import UC_X86_REG_CS,UC_X86_REG_DS,UC_X86_REG_ES,UC_X86_REG_SS,UC_X86_REG_SP,UC_X86_REG_BP,UC_X86_REG_IP
try:
    from .verify_journal_native import NativeJournal
    from .yukoncalendar import DateWords,enter_selected_seattle_scene
    from .yukonres import read_index,verify_source,DEFAULT_SOURCE_MANIFEST
    from .yukontransform import source_patterns,transform
    from .yukonsprite import read_hotspots
except ImportError:
    from verify_journal_native import NativeJournal
    from yukoncalendar import DateWords,enter_selected_seattle_scene
    from yukonres import read_index,verify_source,DEFAULT_SOURCE_MANIFEST
    from yukontransform import source_patterns,transform
    from yukonsprite import read_hotspots

class SceneNative(NativeJournal):
    def route_far_call(self,m,address,size,user):
        code=bytes(m.mem_read(address,size))
        if code[0]!=0x9a or int.from_bytes(code[1:3],'little') not in (0xa7bc,0xa0c2):return super().route_far_call(m,address,size,user)
        offset=int.from_bytes(code[1:3],'little');caller=m.reg_read(UC_X86_REG_CS);ip=m.reg_read(UC_X86_REG_IP)
        self.relocations.add((caller,ip,0x1000,offset));sp=(m.reg_read(UC_X86_REG_SP)-4)&65535
        m.mem_write(m.reg_read(UC_X86_REG_SS)*16+sp,struct.pack('<HH',ip+size,caller));m.reg_write(UC_X86_REG_SP,sp);m.reg_write(UC_X86_REG_CS,0x1000);m.reg_write(UC_X86_REG_IP,offset)
    def branch(self,scene_id,data):
        self.m.mem_write(0x42000,struct.pack('<HH',0,0)+struct.pack('<H',scene_id)+bytes(0x50))
        self.m.mem_write(0x42044,struct.pack('<HH',0x3000,0x4000));self.m.mem_write(0x43000,data)
        for r,v in ((UC_X86_REG_CS,0x8000),(UC_X86_REG_DS,0x3000),(UC_X86_REG_ES,0x4000),(UC_X86_REG_SS,0x7000),(UC_X86_REG_SP,0xef80),(UC_X86_REG_BP,0xf000)):self.m.reg_write(r,v)
        self.m.mem_write(0x7f006,struct.pack('<HH',0x2000,0x4000))
        self.m.emu_start(0x804f0,0x8055b,count=10000)
        if self.m.reg_read(UC_X86_REG_IP)!=0x55b:raise ValueError('Constructor branch escaped bound')
        self.call(0x1000,0xa368,struct.pack('<HHH',0,0x5000,scene_id//1000))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('archive','executable','report'):p.add_argument(name,type=Path)
    a=p.parse_args();exe=a.executable.read_bytes();native=SceneNative(exe,b'\0\4one\0two\0three\0four\0');patterns=source_patterns(exe);resources={};buffers={};rows=[]
    native.m.mem_write(0x352fc,struct.pack('<HH',0x3000,0x6000))
    with a.archive.open('rb') as f:
        archive_hash=verify_source(f,DEFAULT_SOURCE_MANIFEST);index=read_index(f).by_key()
        for key in ('SCNE:1000','SCNE:2000','SCNE:3000','SCNE:4000','HSPT:4000'):
            r=index[key];f.seek(r.offset);raw=f.read(r.length);buffers[key]=transform(raw,patterns[key.split(':')[0]].opcodes)
            resources[key]=dict(offset=r.offset,length=r.length,sha256=hashlib.sha256(raw).hexdigest(),normalized_hex=buffers[key].hex())
    hotspots=read_hotspots(buffers['HSPT:4000'])
    if any((h.action_word0,h.action_word1,h.action_dword)!=(1,200,1000) for h in hotspots[1:3]):raise ValueError('Selected downtown action changed')
    if struct.unpack_from('<H',buffers['SCNE:1000'],8)[0]!=1 or struct.unpack_from('<H',buffers['SCNE:4000'],8)[0]!=0:raise ValueError('Selected scene entry count changed')
    if any(struct.unpack_from('<H',buffers[f'SCNE:{id}'],8)[0]!=0 for id in (2000,3000)):raise ValueError('Selected merchant scene day count changed')
    for scene in (1000,2000,3000,4000):
        for visit in (0,1,2,32767,32768,65535):
            for day,month,elapsed,phase in ((23,8,0,0),(31,12,65535,65535),(28,2,32767,5),(31,8,0,0)):
                for gate in (0,1):
                    date=DateWords(day,month,elapsed,phase,gate);wanted_date,wanted_visit=enter_selected_seattle_scene(date,scene,visit)
                    state=bytearray([0x55]*0x350)
                    for offset,value in ((0x28,day),(0x2a,month),(0x30e,elapsed),(0x310,phase),(0x334,gate),(0x2aa+2*(scene//1000),visit)):struct.pack_into('<H',state,offset,value)
                    wanted=bytearray(state)
                    for offset,value in ((0x28,wanted_date.day_word),(0x2a,wanted_date.month_word),(0x30e,wanted_date.elapsed_word),(0x310,wanted_date.phase_word),(0x2aa+2*(scene//1000),wanted_visit)):struct.pack_into('<H',wanted,offset,value)
                    native.m.mem_write(0x50000,bytes(state));native.m.mem_write(0x63054,bytes(2));native.branch(scene,buffers[f'SCNE:{scene}'])
                    actual=bytes(native.m.mem_read(0x50000,len(state)));dirty=int.from_bytes(native.m.mem_read(0x63054,2),'little')
                    if actual!=wanted or dirty!=int(scene==1000 and visit==0 and gate==0):raise ValueError('Scene visit/date model differs')
                    rows.append(dict(scene=scene,before_visit=visit,before_date=[day,month,elapsed,phase,gate],after_visit=wanted_visit,after_date=[wanted_date.day_word,wanted_date.month_word,wanted_date.elapsed_word,wanted_date.phase_word],state_sha256=hashlib.sha256(actual).hexdigest(),dirty54=dirty))
    report=dict(executable_sha256=hashlib.sha256(exe).hexdigest(),archive_sha256=archive_hash,resources=resources,cases=rows,native_cases=len(rows),mismatches=0,synthetic_far_relocations=sorted(native.relocations),scope=__doc__)
    a.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(dict(cases=len(rows),mismatches=0)))
if __name__=='__main__':main()
