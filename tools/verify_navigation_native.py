#!/usr/bin/env python3
"""Record original client button dispatch/HSPT/queue outputs, without Windows APIs.

Empty initialized sprite list is explicit. Other action selection stops at its
original call boundary. Source bytes unchanged; only far-call selectors routed.
"""
import argparse, hashlib, json, struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_16, UC_HOOK_CODE, __version__
from unicorn.x86_const import UC_X86_REG_CS, UC_X86_REG_DS, UC_X86_REG_ES, UC_X86_REG_SS, UC_X86_REG_SP, UC_X86_REG_BP, UC_X86_REG_IP
from yukonbmp import EXE_SHA256
from yukonres import read_index, verify_source, DEFAULT_SOURCE_MANIFEST
from yukontransform import source_patterns, transform
from yukonsprite import read_hotspots


class NativeNavigation:
    def __init__(self, exe):
        if hashlib.sha256(exe).hexdigest()!=EXE_SHA256 or __version__!='2.1.4':raise ValueError('Unsupported source/Unicorn')
        self.m=Uc(UC_ARCH_X86,UC_MODE_16);self.m.mem_map(0,0xa0000)
        for address,offset,length in [(0x10000,0x460,60176),(0x20000,0xf2c0,59610),(0x30000,0x1dde0,59278),(0x80000,0x44fc0,39822)]:self.m.mem_write(address,exe[offset:offset+length])
        self.relocations=set();self.m.hook_add(UC_HOOK_CODE,self.route)
        self.targets={0x3c28:0x1000,0x098c:0x3000,0x0a66:0x3000,0x9542:0x2000,
                      0x955c:0x2000,0x4dba:0x1000,0x28c0:0x8000,0x9572:0x2000,0x0958:0x3000,
                      0x6790:0x8000,0x97fc:0x2000,0x9722:0x2000,0x09c2:0x3000,0x0a84:0x3000,0x981a:0x2000,0x0c72:0x2000}

    def route(self,m,address,size,user):
        cs,ip=m.reg_read(UC_X86_REG_CS),m.reg_read(UC_X86_REG_IP)
        if (cs,ip) in ((0x2000,0x0c76),(0x1000,0xbfe4)):
            bp=m.reg_read(UC_X86_REG_BP);self.transmitted=list(struct.unpack('<hhH',m.mem_read(0x40000+bp+0xe,2)+m.mem_read(0x40000+bp+0xa,2)+m.mem_read(0x40000+bp+0x10,2)))
        if (cs,ip) in ((0x2000,0x0cf9),(0x1000,0xc02c)):
            bp=m.reg_read(UC_X86_REG_BP);off,seg=struct.unpack('<HH',m.mem_read(0x40000+bp-8,4));self.sprite_id=struct.unpack('<I',m.mem_read(seg*16+off+0x56,4))[0]
        if (cs,ip) in ((0x2000,0x0d43),(0x1000,0xc077)):self.stopped='unexecuted_sprite_action';m.emu_stop();return
        if (cs,ip) in ((0x2000,0x0de6),(0x1000,0xc11a)):
            bp=m.reg_read(UC_X86_REG_BP);sp=m.reg_read(UC_X86_REG_SP)
            self.ordinal=struct.unpack('<H',m.mem_read(0x40000+bp-2,2))[0]
            off,seg=struct.unpack('<HH',m.mem_read(0x40000+sp+4,4));self.action=list(struct.unpack('<HHI',m.mem_read(seg*16+off,8)))
            if self.action[0] not in (1,2,3):self.stopped='unexecuted_action';m.emu_stop();return
        code=bytes(m.mem_read(address,size))
        if code[0]!=0x9a:return
        off=int.from_bytes(code[1:3],'little')
        if off not in self.targets:raise ValueError(f'Unrecovered far call {cs:04x}:{ip:04x} {code.hex()}')
        target=self.targets[off];self.relocations.add((cs,ip,target,off))
        sp=(m.reg_read(UC_X86_REG_SP)-4)&65535;m.mem_write(0x40000+sp,struct.pack('<HH',ip+size,cs))
        m.reg_write(UC_X86_REG_SP,sp);m.reg_write(UC_X86_REG_CS,target);m.reg_write(UC_X86_REG_IP,off)

    def button(self,data,x,y,message=0x201,activation=0,countdown=0,manager_busy=0,sprite=False,ticket=False):
        m=self.m;m.mem_write(0x40000,bytes(0xe000));m.mem_write(0x50000,bytes(0x5000))
        m.mem_write(0x40090,struct.pack('<HH',0,0x5000));m.mem_write(0x40094,struct.pack('<HH',0x3000,0x5000))
        m.mem_write(0x45330,struct.pack('<H',activation));m.mem_write(0x41188,struct.pack('<H',countdown))
        m.mem_write(0x50000,struct.pack('<H',manager_busy));m.mem_write(0x50016,struct.pack('<HH',0x1000,0x5000))
        m.mem_write(0x51000,struct.pack('<HH',0,0x7000));m.mem_write(0x51048,struct.pack('<HH',0,0x9000))
        m.mem_write(0x53000,struct.pack('<HH',0x100,0x7000));m.mem_write(0x53048,struct.pack('<HH',0x4000,0x5000))
        # Synthetic vtables route real original methods; list+10 tail is null.
        m.mem_write(0x70004,struct.pack('<HH',0xbfe0 if ticket else 0x0c72,0x1000 if ticket else 0x2000));m.mem_write(0x70010,struct.pack('<HH',0x0890,0x2000))
        m.mem_write(0x70130,struct.pack('<HH',0x3bea,0x2000));m.mem_write(0x90000,data)
        if sprite:
            # Synthetic initialized loaded frame8x8, stride8, opaque/zero stencil.
            # Real cached-frame/point/rect/hit routines execute; no callback stubs.
            m.mem_write(0x54010,struct.pack('<HH',0x5000,0x5000))
            m.mem_write(0x55000,struct.pack('<HH',0x400,0x7000));m.mem_write(0x70428,struct.pack('<HH',0xe78a,0x2000))
            m.mem_write(0x55010,struct.pack('<4h',164,155,172,163));m.mem_write(0x55056,struct.pack('<I',200))
            m.mem_write(0x5505a,struct.pack('<HH',0x6000,0x5000))
            m.mem_write(0x56000,struct.pack('<HH',0x200,0x7000));m.mem_write(0x56012,struct.pack('<HH',0x6800,0x5000))
            m.mem_write(0x70238,struct.pack('<HH',0x4d52,0x2000));m.mem_write(0x7023c,struct.pack('<HH',0x4d7a,0x2000))
            m.mem_write(0x56800,struct.pack('<HH',0x7000,0x5000))
            m.mem_write(0x57000,struct.pack('<HH',0x300,0x7000));m.mem_write(0x57010,struct.pack('<HH',0x8000,0x5000))
            m.mem_write(0x70320,struct.pack('<HH',0x1132,0x3000));m.mem_write(0x7032c,struct.pack('<HH',0x11a6,0x3000))
            m.mem_write(0x5801a,struct.pack('<HH',0x1000,0x9000));m.mem_write(0x5801e,struct.pack('<H',8))
            m.mem_write(0x58020,struct.pack('<4h',0,0,8,8))
            m.mem_write(0x91000,bytes([0,1,0,1,2,0,3,0]*8))
        self.transmitted=None;self.ordinal=None;self.action=None;self.stopped=None;self.sprite_id=None
        for reg,value in [(UC_X86_REG_CS,0x1000),(UC_X86_REG_DS,0x4000),(UC_X86_REG_ES,0x5000),(UC_X86_REG_SS,0x4000),(UC_X86_REG_SP,0xf000)]:m.reg_write(reg,value)
        m.mem_write(0x4f000,struct.pack('<HHhhHHH',0xf000,0x1000,x,y,0,message,123))
        m.emu_start(0x161b8,0x1f000,count=20000)
        if self.stopped is None and m.reg_read(UC_X86_REG_IP)!=0xf000:raise ValueError('Original dispatch escaped')
        pending=struct.unpack('<H',m.mem_read(0x50002,2))[0]
        queue=list(struct.unpack('<HHI',m.mem_read(0x50004,8))) if pending else None
        return {'transmitted':self.transmitted,'activation_after':struct.unpack('<H',m.mem_read(0x45330,2))[0],
                'hotspot_ordinal':self.ordinal,'selected_action':self.action,'pending_word':pending,
                'queued_action':queue,'boundary_stop':self.stopped,'sprite_object_id':self.sprite_id}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('archive','executable','report'):p.add_argument(n,type=Path)
    a=p.parse_args();exe=a.executable.read_bytes();native=NativeNavigation(exe);patterns=source_patterns(exe)
    resources={};rows=[]
    with a.archive.open('rb') as f:
        archive_hash=verify_source(f,DEFAULT_SOURCE_MANIFEST);idx=read_index(f).by_key()
        for rid in (1000,2000,3000,4000):
            r=idx[f'HSPT:{rid}'];f.seek(r.offset);raw=f.read(r.length);data=transform(raw,patterns['HSPT'].opcodes);records=read_hotspots(data)
            points={(-32768,-32768),(32767,32767),(0,0),(-1,-1)}
            for v in records:
                if v.sentinel:break
                for x in (v.left-1,v.left,v.left+1,(v.left+v.right)//2,v.right-1,v.right,v.right+1):
                    for y in (v.top-1,v.top,v.top+1,(v.top+v.bottom)//2,v.bottom-1,v.bottom,v.bottom+1):
                        if -32768<=x<=32767 and -32768<=y<=32767:points.add((x,y))
            resources[r.key]={'offset':r.offset,'length':r.length,'raw_sha256':hashlib.sha256(raw).hexdigest(),
                              'normalized_sha256':hashlib.sha256(data).hexdigest(),'record_words':[[v.left,v.right,v.top,v.bottom,v.action_word0,v.action_word1,v.action_dword]for v in records]}
            for x,y in sorted(points):rows.append([rid,x,y,0x201,0,0,0,False,native.button(data,x,y)])
            center=next(v for v in records if not v.sentinel);x=(center.left+center.right)//2;y=(center.top+center.bottom)//2
            for message in (0x201,0x204,0x207,0x202,0x205,0x208):
                for activation,countdown,busy in [(0,0,0),(1,0,0),(65535,0,0),(0,1,0),(0,0,1)]:
                    rows.append([rid,x,y,message,activation,countdown,busy,False,native.button(data,x,y,message,activation,countdown,busy)])
            if rid==1000:
                for px in range(154,165):
                    for py in range(163,174):
                        rows.append([rid,px,py,0x201,0,0,0,True,native.button(data,px,py,sprite=True)])
    ticket_data=struct.pack('<H',len(resources['HSPT:3000']['record_words']))+b''.join(struct.pack('<hhhhHHI',*r)for r in resources['HSPT:3000']['record_words'])
    ticket_rows=[row[:8]+[native.button(ticket_data,*row[1:7],sprite=row[7],ticket=True)]for row in rows if row[0]==3000]
    for x in range(154,165):
        for y in range(163,174):
            ticket_rows.append([3000,x,y,0x201,0,0,0,True,native.button(ticket_data,x,y,sprite=True,ticket=True)])
    report={'executable_sha256':EXE_SHA256,'archive_sha256':archive_hash,'unicorn_version':__version__,
            'native_code':['NE1:61b8 button dispatcher','NE1:3c28 event forwarding','NE2:0c72/3bea empty and initialized cached-frame interception','NE3:098c/0a66 point helpers','NE2:e78a cached pixel hit and NE2:4d52/4d7a to NE3:1132/11a6 getters','NE2:0890 opcodes1..3','NE1:4dba and NE6:28c0 exact queue copy'],
            'derived_ticket_rows':ticket_rows,'derived_ticket_rows_sha256':hashlib.sha256(json.dumps(ticket_rows,separators=(',',':')).encode()).hexdigest(),'derived_ticket_scope':'Actual NE1:bfe0 table624a slot4. Button464 duplicates hit/HSPT dispatch without common DS1188 countdown gate; up46e delegates NE2:0c72. Modal46b/date/schedule and actual sprite population unsupported.','resources':resources,'cases':len(rows),'native_rows':rows,'native_rows_sha256':hashlib.sha256(json.dumps(rows,separators=(',',':')).encode()).hexdigest(),
            'synthetic_sprite_fixture':{'rectangle_tlbr':[164,155,172,163],'frame_size_wh':[8,8],'stride':8,'pixels':[0,1,0,1,2,0,3,0]*8,'object_id':200,'scope':'Initialized cached8x8 frame fixture; not recovered actual active Seattle sprite state'},'synthetic_call_relocations':sorted(native.relocations),
            'scope':'Original client button→HSPT/queue with empty list and121 initialized cached-frame sprite interception cases. Non1..3 and sprite200 dialogue stop at actual dispatch boundaries; no OS APIs, active-scene sprite population, queue-consumption/scene construction or capture→client OS transform executed.'}
    a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'cases':len(rows),'derived_ticket_cases':len(ticket_rows),'rows_sha256':report['native_rows_sha256']}))

if __name__=='__main__':main()
