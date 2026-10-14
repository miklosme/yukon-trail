#!/usr/bin/env python3
"""Original sea waypoint rule3482/arrival41e0/setters/RNG, full state buffers.

OpenScene arguments and audio-play invocation are observed boundaries; their
consumers do not execute. No progression/queue/RNG/getter behavior stubs.
Constructor state block36a2..36e0 excludes resource allocation/render/journal.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn.x86_const import UC_X86_REG_CS,UC_X86_REG_DS,UC_X86_REG_ES,UC_X86_REG_SS,UC_X86_REG_SP,UC_X86_REG_BP,UC_X86_REG_IP
try:
    from .verify_ticket_native import TicketNative
    from .yukonvoyage import read_sea_map,advance_sea_waypoint,initialize_map_state_block
    from .yukonres import read_index,verify_source,DEFAULT_SOURCE_MANIFEST
    from .yukontransform import source_patterns,transform
except ImportError:
    from verify_ticket_native import TicketNative
    from yukonvoyage import read_sea_map,advance_sea_waypoint,initialize_map_state_block
    from yukonres import read_index,verify_source,DEFAULT_SOURCE_MANIFEST
    from yukontransform import source_patterns,transform


class VoyageNative(TicketNative):
    def __init__(self,exe):
        super().__init__(exe);self.m.mem_map(0xa0000,0x10000);self.m.mem_write(0xa0000,exe[0x2cac0:0x2cac0+60252]);self.audio=[]
    def route_far_call(self,m,address,size,user):
        code=bytes(m.mem_read(address,size));caller=m.reg_read(UC_X86_REG_CS);ip=m.reg_read(UC_X86_REG_IP)
        if code[0]!=0x9a:return super().route_far_call(m,address,size,user)
        off=int.from_bytes(code[1:3],'little')
        if (caller,ip)==(0xa000,0x3542):
            sp=m.reg_read(UC_X86_REG_SP);self.audio.append(struct.unpack('<I',m.mem_read(m.reg_read(UC_X86_REG_SS)*16+sp,4))[0]);m.reg_write(UC_X86_REG_IP,ip+size);return
        targets={0x41e0:0xa000,0xa4e8:0x1000,0xa50c:0x1000,0x9f14:0x1000,0xa4ce:0x1000,0xa8d0:0x1000,0xa8e0:0x1000}
        if off not in targets:return super().route_far_call(m,address,size,user)
        cs=targets[off];self.relocations.add((caller,ip,cs,off));sp=(m.reg_read(UC_X86_REG_SP)-4)&65535;m.mem_write(m.reg_read(UC_X86_REG_SS)*16+sp,struct.pack('<HH',ip+size,caller));m.reg_write(UC_X86_REG_SP,sp);m.reg_write(UC_X86_REG_CS,cs);m.reg_write(UC_X86_REG_IP,off)
    def step(self,before,scene,manager,seed,mode):
        self.m.mem_write(0x50000,before);self.m.mem_write(0x40000,scene);self.m.mem_write(0x62000,manager);self.m.mem_write(0x3483e,struct.pack('<I',seed));self.m.mem_write(0x300b0,struct.pack('<H',mode));self.refusals=[];self.audio=[]
        self.call(0xa000,0x3482,struct.pack('<HH',0,0x4000))
        return bytes(self.m.mem_read(0x50000,len(before))),bytes(self.m.mem_read(0x40000,len(scene))),bytes(self.m.mem_read(0x62000,len(manager))),struct.unpack('<I',self.m.mem_read(0x3483e,4))[0],[(a[2],a[3]) for a in self.refusals],self.audio
    def entry(self,before,scene):
        self.m.mem_write(0x50000,before);self.m.mem_write(0x40000,scene)
        for r,v in ((UC_X86_REG_CS,0xa000),(UC_X86_REG_DS,0x3000),(UC_X86_REG_ES,0x4000),(UC_X86_REG_SS,0x7000),(UC_X86_REG_BP,0xf000),(UC_X86_REG_SP,0xefcc)):self.m.reg_write(r,v)
        self.m.mem_write(0x7f006,struct.pack('<3H',0,0x4000,31000));self.m.emu_start(0xa36a2,0xa36e0,count=10000)
        if self.m.reg_read(UC_X86_REG_IP)!=0x36e0:raise ValueError('Map constructor block escaped')
        return bytes(self.m.mem_read(0x50000,len(before))),bytes(self.m.mem_read(0x40000,len(scene)))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for arg in ('archive','executable','report'):p.add_argument(arg,type=Path)
    a=p.parse_args();exe=a.executable.read_bytes();n=VoyageNative(exe);patterns=source_patterns(exe);rows=[];entry=[];branches=[]
    with a.archive.open('rb') as f:
        archive_hash=verify_source(f,DEFAULT_SOURCE_MANIFEST);r=read_index(f).by_key()['SMAP:31000'];f.seek(r.offset);raw=f.read(r.length);normalized=transform(raw,patterns['SMAP'].opcodes)
    records=read_sea_map(normalized);n.m.mem_write(0x64000,normalized[2:]);manager=bytes([0x55]*128)
    def case(index,partial,speed,gate,destination=5000,inventory=0,mode=2,seed=1):
        before=bytearray([0x55]*0x400);scene=bytearray([0x55]*0xa6)
        for o,v in ((0x334,gate),(0x322,destination),(0x30a,inventory)):struct.pack_into('<H',before,o,v)
        for o,v in ((0x88,index),(0x8c,partial),(0x96,speed)):struct.pack_into('<H',scene,o,v)
        struct.pack_into('<I',scene,0x98,0x60004000)
        actual=n.step(bytes(before),bytes(scene),manager,seed,mode);wanted=advance_sea_waypoint(bytes(before),bytes(scene),manager,records,seed,mode)
        if actual!=wanted:raise ValueError(f'Original sea map differs{index,partial,speed,gate,destination,inventory,mode,seed}')
        return [index,partial,speed,gate,destination,inventory,mode,seed,*[hashlib.sha256(x).hexdigest() for x in actual[:3]],actual[3],actual[4],actual[5]]
    speeds=sorted(set(struct.unpack_from('<9H',exe,0x4f420+0x14cc))|{0,32767,32768,65535})
    for index in range(45):
        for partial in (0,24,25,32767,32768,65535):
            for speed in speeds:
                for gate in (0,1):rows.append(case(index,partial,speed,gate))
    for index,record in enumerate(records):
        if record[2] not in (1,2,31102):continue
        for destination in (0,5000,9000):
            for inventory in (0,11):
                for mode in (0,2):
                    for seed in (0,1,0xffffffff):branches.append(case(index,24,18,0,destination,inventory,mode,seed))
    for saved_index in (0,44,32768,65535):
        for partial in (0,24,32768,65535):
            for gate in (0,1):
                before=bytearray([0x55]*0x400);scene=bytes([0x55]*0xa6)
                for o,v in ((0x336,saved_index),(0x338,partial),(0x334,gate)):struct.pack_into('<H',before,o,v)
                actual=n.entry(bytes(before),scene)
                if actual!=initialize_map_state_block(bytes(before),scene):raise ValueError('Original map constructor metadata differs')
                entry.append([saved_index,partial,gate,*[hashlib.sha256(x).hexdigest() for x in actual]])
    report=dict(executable_sha256=hashlib.sha256(exe).hexdigest(),archive_sha256=archive_hash,resource=dict(key=r.key,offset=r.offset,length=r.length,raw_sha256=hashlib.sha256(raw).hexdigest(),normalized_sha256=hashlib.sha256(normalized).hexdigest(),records=records),source_speed_words=struct.unpack_from('<9H',exe,0x4f420+0x14cc),waypoint_cases=rows,branch_cases=branches,entry_cases=entry,mismatches=0,synthetic_far_relocations=sorted(n.relocations),scope=__doc__)
    a.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(dict(waypoint_cases=len(rows),branch_cases=len(branches),entry_cases=len(entry),mismatches=0)))
if __name__=='__main__':main()
