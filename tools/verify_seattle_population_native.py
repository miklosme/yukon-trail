#!/usr/bin/env python3
"""Bounded original Seattle controller and SPRT constructor execution.

NE fixups are loaded into synthetic selectors. Allocator/resource-file/cache and
clock services are explicit fixture providers; actor/controller game instructions
are not replaced. No Windows UI, guest disk writes or future timer loop.
"""
import argparse, hashlib, json, struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_16, UC_HOOK_CODE, __version__
from unicorn.x86_const import *
try:
    from .yukonne_runtime import load
    from .yukonres import read_index, verify_source, DEFAULT_SOURCE_MANIFEST
    from .yukontransform import source_patterns, transform
except ImportError:
    from yukonne_runtime import load
    from yukonres import read_index, verify_source, DEFAULT_SOURCE_MANIFEST
    from yukontransform import source_patterns, transform

class Resources:
    def __init__(self, archive, executable):
        self.source=archive.open('rb');self.archive_hash=verify_source(self.source,DEFAULT_SOURCE_MANIFEST)
        self.index=read_index(self.source).by_key();self.patterns=source_patterns(executable);self.provenance={}
    def get(self,tag,id):
        key=f'{tag}:{id}';r=self.index[key];self.source.seek(r.offset);raw=self.source.read(r.length)
        data=transform(raw,self.patterns[tag].opcodes)if tag in self.patterns else raw
        self.provenance[key]={'offset':r.offset,'length':r.length,'raw_sha256':hashlib.sha256(raw).hexdigest(),'normalized_sha256':hashlib.sha256(data).hexdigest()}
        return data

class NativePopulation:
    def __init__(self,exe,resources):
        if __version__!='2.1.4':raise ValueError('Pinned Unicorn required')
        self.image=load(exe);self.resources=resources;self.m=Uc(UC_ARCH_X86,UC_MODE_16);self.m.mem_map(0,0x110000)
        for seg,data in self.image.images.items():self.m.mem_write(self.image.selectors[seg]*16,bytes(data))
        self.code_hook=self.m.hook_add(UC_HOOK_CODE,self.route);self.next_heap=0x3000;self.next_resource=0x1000
        self.cache={};self.handles={};self.trace=[];self.clock=0;self.mmclock=0;self.current_scene=0;self.heap_fill=0
    def ptr(self,off,seg=0xf000):return struct.pack('<HH',off,seg)
    def malloc(self,count):
        if not 0<count<0x8000 or self.next_heap+count>=0xf000:raise ValueError('Bounded heap exhausted')
        off=self.next_heap;self.next_heap=(off+count+3)&~3;self.m.mem_write(0xf0000+off,bytes([self.heap_fill])*count);return off,0xf000
    def resource_malloc(self,count):
        if not 0<count<0x8000 or self.next_resource+count>=0xf000:raise ValueError('Resource heap exhausted')
        off=self.next_resource;self.next_resource=(off+count+3)&~3;self.m.mem_write(0xa0000+off,bytes(count));return off,0xa000
    def args(self,count):
        sp=self.m.reg_read(UC_X86_REG_SP);ss=self.m.reg_read(UC_X86_REG_SS)
        return bytes(self.m.mem_read(ss*16+sp+4,count))
    def returned(self,cleanup,ax=0,dx=0):
        m=self.m;sp=m.reg_read(UC_X86_REG_SP);ss=m.reg_read(UC_X86_REG_SS);ip,cs=struct.unpack('<HH',m.mem_read(ss*16+sp,4))
        m.reg_write(UC_X86_REG_AX,ax);m.reg_write(UC_X86_REG_DX,dx);m.reg_write(UC_X86_REG_SP,(sp+4+cleanup)&65535);m.reg_write(UC_X86_REG_CS,cs);m.reg_write(UC_X86_REG_IP,ip)
    def bitmap_cache(self,id):
        if id in self.cache:return self.cache[id]
        data=self.resources.get('CBMP',id);count=struct.unpack_from('<H',data)[0]
        cache=self.malloc(0x30);array=self.malloc(4*count)
        self.m.mem_write(cache[1]*16+cache[0],self.ptr(0x67ea,0x6000));self.m.mem_write(cache[1]*16+cache[0]+0x12,self.ptr(*array))
        for i in range(count):
            width,height=struct.unpack_from('<HH',data,2+i*12)
            wrapper=self.malloc(0x20);buffer=self.malloc(0x40)
            self.m.mem_write(wrapper[1]*16+wrapper[0],self.ptr(0x739a,0x6000));self.m.mem_write(wrapper[1]*16+wrapper[0]+0x10,self.ptr(*buffer))
            self.m.mem_write(buffer[1]*16+buffer[0]+0x20,struct.pack('<4h',0,0,height,width));self.m.mem_write(buffer[1]*16+buffer[0]+0x1e,struct.pack('<H',(width+3)&~3))
            self.m.mem_write(array[1]*16+array[0]+4*i,self.ptr(*wrapper))
        self.cache[id]=cache;return cache
    def route(self,m,address,size,user):
        cs,ip=m.reg_read(UC_X86_REG_CS),m.reg_read(UC_X86_REG_IP)
        if (cs,ip)==(0x6000,0x1ebe):
            n=struct.unpack('<H',self.args(2))[0];p=self.malloc(n);self.trace.append(['malloc',n]);self.returned(0,*p);return
        if (cs,ip)==(0x6000,0x1eac):self.trace.append(['free',self.args(4).hex()]);self.returned(0);return
        if (cs,ip)==(0x1000,0x7c88):
            _,_,id,tag=struct.unpack('<HHHI',self.args(10));tag=tag.to_bytes(4,'big').decode('ascii');n=len(self.resources.get(tag,id));self.trace.append(['record_length',tag,id,n]);self.returned(10,n&65535,n>>16);return
        if (cs,ip)==(0x1000,0x7818):
            _,_,off,seg,id,tag=struct.unpack('<HHHHHI',self.args(14));tag=tag.to_bytes(4,'big').decode('ascii');data=self.resources.get(tag,id);m.mem_write(seg*16+off,data);self.trace.append(['record_read',tag,id,len(data)]);self.returned(14,len(data));return
        if (cs,ip)==(0x2000,0x9cd6):
            _,_,id=struct.unpack('<HHI',self.args(8));p=self.bitmap_cache(id);self.trace.append(['bitmap_cache',id]);self.returned(8,*p);return
        if (cs,ip)in((0x1000,0xa7bc),(0x1000,0xa7f4),(0x1000,0xa632)):
            self.trace.append(['getter',f'NE1:{ip:04x}',self.args(6 if ip==0xa7bc else 4).hex()])
        if cs==0xe800:
            key=self.image.imports.get((cs,ip));self.trace.append(['import',key])
            if key==('USER',13):self.returned(0,self.clock&65535,self.clock>>16);return
            if key==('MMSYSTEM',607):self.returned(0,self.mmclock&65535,self.mmclock>>16);return
            if key==('KERNEL',15):
                n,flags=struct.unpack('<IH',self.args(6));p=self.resource_malloc(n);h=len(self.handles)+1;self.handles[h]=[p,n,0];self.trace.append(['global_alloc',n,flags,h]);self.returned(6,h);return
            if key==('KERNEL',18):
                h=struct.unpack('<H',self.args(2))[0];self.handles[h][2]+=1;self.returned(2,*self.handles[h][0]);return
            if key==('KERNEL',19):
                h=struct.unpack('<H',self.args(2))[0];self.handles[h][2]-=1;self.returned(2,int(self.handles[h][2]>0));return
            raise ValueError(f'Unsupported platform dependency {key} at source return {self.args(2).hex()}')
    def call(self,seg,off,args):
        m=self.m
        for reg,value in [(UC_X86_REG_CS,self.image.selectors[seg]),(UC_X86_REG_DS,0xd000),(UC_X86_REG_ES,0xf000),(UC_X86_REG_SS,0xd000),(UC_X86_REG_SP,0xf000)]:m.reg_write(reg,value)
        m.mem_write(0xdf000,self.ptr(0xff00,0x1000)+args)
        try:m.emu_start(self.image.selectors[seg]*16+off,0x1ff00,count=1000000)
        except Exception as error:
            raise RuntimeError(f"NE{seg}:{off:04x} stopped at {m.reg_read(UC_X86_REG_CS):04x}:{m.reg_read(UC_X86_REG_IP):04x}; scene={self.current_scene}, clocks={self.clock}/{self.mmclock}, heap_fill={self.heap_fill}, trace={self.trace[-8:]}") from error
        if m.reg_read(UC_X86_REG_CS)!=0x1000 or m.reg_read(UC_X86_REG_IP)!=0xff00:raise ValueError(f'Constructor escaped at {m.reg_read(UC_X86_REG_CS):x}:{m.reg_read(UC_X86_REG_IP):x}')
    def controller(self,scene,state,clock=0,mmclock=0,globals=False):
        self.current_scene=scene;self.clock=clock;self.mmclock=mmclock
        m=self.m;m.mem_write(0xf1000,state);m.mem_write(0xd5308,self.ptr(0x1000));m.mem_write(0xd0094,self.ptr(0x2200));m.mem_write(0xd52f4,self.ptr(0x2800));m.mem_write(0xd56d4,self.ptr(0x2900))
        m.mem_write(0xf2104,struct.pack('<H',scene));m.mem_write(0xf2200,self.ptr(0x706a,0x6000));m.mem_write(0xf2248,self.ptr(0x2300))
        self.call(2,0xddd0,self.ptr(0x2300))
        primary=secondary=None
        if globals:
            primary=self.malloc(0x90);self.call(3,0x5e22,self.ptr(*primary)+struct.pack('<H',0)+self.ptr(0x2200))
            secondary=self.malloc(0x92);self.call(3,0x5f04,self.ptr(*secondary)+self.ptr(0x2200))
            self.call(1,0xa78c,self.ptr(0x1000)+struct.pack('<H',0))
            if m.reg_read(UC_X86_REG_AX)==0:
                self.call(2,0xd556,self.ptr(*primary)+struct.pack('<HH',65535,1))
        self.call(3,0x2268,self.ptr(0x2000)+self.ptr(0x2100)+struct.pack('<H',scene))
        if globals:
            for target in (primary,secondary):
                tail=bytes(m.mem_read(0xf2310,4));self.call(2,0xe06a,self.ptr(0x2300)+tail+self.ptr(*target))
        nodes=[];off,seg=struct.unpack('<HH',m.mem_read(0xf200c,4));visited=set()
        while off or seg:
            p=seg*16+off
            if p in visited:raise ValueError('Controller child cycle')
            visited.add(p);record=list(struct.unpack('<9H',m.mem_read(p+0xc,18)));actor_off,actor_seg=struct.unpack('<HH',m.mem_read(p+0x1e,4));a=actor_seg*16+actor_off
            nodes.append({'controller_record_words':record,'sprite_id':record[1],'actor_snapshot_hex':bytes(m.mem_read(a,0xa6)).hex(),'rectangle_tlbr':list(struct.unpack('<4h',m.mem_read(a+0x10,8))),'anchor_yx':list(struct.unpack('<2h',m.mem_read(a+0x24,4))),'frame':struct.unpack('<H',m.mem_read(a+0x2a,2))[0],'visible_word':struct.unpack('<H',m.mem_read(a+0x28,2))[0],'flip_byte':m.mem_read(a+0x2c,1)[0]})
            off,seg=struct.unpack('<HH',m.mem_read(p+8,4))
        if not globals:return nodes
        actors={n['sprite_id']:n for n in nodes};contexts=[]
        off,seg=struct.unpack('<HH',m.mem_read(0xf230c,4));visited=set()
        reverse_cache={seg*16+off:id for id,(off,seg)in self.cache.items()}
        while off or seg:
            address=seg*16+off
            if address in visited:raise ValueError('Sprite context cycle')
            visited.add(address);data=bytes(m.mem_read(address,0xa6));object_id=struct.unpack_from('<I',data,0x56)[0]
            cbmp_off,cbmp_seg=struct.unpack_from('<HH',data,0x5a)
            contexts.append({'object_id':object_id,'sprite_id':struct.unpack_from('<H',data,0x86)[0]if object_id==200 else None,'bitmap_id':reverse_cache[cbmp_seg*16+cbmp_off],
                             'frame':struct.unpack_from('<H',data,0x2a)[0],'rectangle_tlbr':list(struct.unpack_from('<4h',data,0x10)),
                             'anchor_yx':list(struct.unpack_from('<2h',data,0x24)),'visible_word':struct.unpack_from('<H',data,0x28)[0],'flip_byte':data[0x2c],
                             'sequence_word':struct.unpack_from('<H',data,0x64)[0],'animation_deadline':struct.unpack_from('<I',data,0x76)[0],
                             'schedule_deadline':struct.unpack_from('<I',data,0xa2)[0]if object_id==200 else None})
            off,seg=struct.unpack_from('<HH',data,8)
        if bytes(m.mem_read(0xf1000,len(state)))!=state:raise ValueError('Actor/controller path changed game state')
        return {'controller_nodes':nodes,'context_head_to_next':contexts}

def versioned_report(report, raw_bytes, source_metadata=None):
    cases=[]
    for c in report['cases']:
        row={k:v for k,v in c.items() if k!='original'}
        row['original_context_head_to_next']=c['original']['context_head_to_next']
        row['original_controller_records']=[n['controller_record_words'] for n in c['original']['controller_nodes']]
        cases.append(row)
    for i in range(0,len(cases),2):
        if cases[i]['original_context_head_to_next']!=cases[i+1]['original_context_head_to_next'] or cases[i]['original_controller_records']!=cases[i+1]['original_controller_records']:
            raise ValueError('Initial reported pose/order depends on allocator fill')
    result=report|{'cases':cases,'native_raw_report_sha256':hashlib.sha256(raw_bytes).hexdigest(),'allocator_pose_invariance_pairs':len(cases)//2}
    if source_metadata is not None:
        data=source_metadata.read_bytes();metadata=json.loads(data)
        if metadata['executable_sha256']!=report['executable_sha256'] or metadata['archive_sha256']!=report['archive_sha256']:
            raise ValueError('Source preparation identity differs')
        result['source_preparation_resources']=metadata['resources']
        result['source_preparation_metadata_sha256']=hashlib.sha256(data).hexdigest()
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in('archive','executable','report'):p.add_argument(name,type=Path)
    p.add_argument('--versioned-report',type=Path);p.add_argument('--source-metadata',type=Path)
    a=p.parse_args();exe=a.executable.read_bytes();r=Resources(a.archive,exe);cases=[]
    base={0x28:23,0x2a:8,0x34:200,0x2fa:350,0x30e:1,0x310:1,0x312:65535}
    for scene in(1000,2000,3000,4000):
        for arrival in(0,1):
            for visit in(0,1):
                for clock,mmclock in((0,0),(1000,1000),(65535,65535)):
                    for fill in(0,85):
                        state=bytearray(0x386)
                        changes=base|{0x38:scene,0x292:arrival,0x2aa+2*(scene//1000):visit}
                        for off,value in changes.items():struct.pack_into('<H',state,off,value)
                        n=NativePopulation(exe,r);n.heap_fill=fill
                        result=n.controller(scene,bytes(state),clock,mmclock,globals=True)
                        cases.append({'scene_id':scene,'region_arrival_word':arrival,'scene_visit_word':visit,'clock_ms':clock,'mmclock_ms':mmclock,'heap_fill_byte':fill,'state_word_inputs':[[o,v]for o,v in sorted(changes.items())],
                                      'original':result,'original_getter_requests':[v for v in n.trace if v[0]=='getter']})
    report={'executable_sha256':hashlib.sha256(exe).hexdigest(),'archive_sha256':r.archive_hash,'cases':cases,'resources':r.provenance,
            'ne_loader_internal_audit':'docs/ne-runtime-loader-evidence.json','scope':'Original global37500/37501 constructors, actual controller2268/2394, generic/clerk SPRT constructors, initial sequence/update and source context reordering. Uses explicit successful allocator/resource providers and constant per-case GetTickCount/TimeGetTime clocks. Full scene background install, arrivaljournal/firstvisitdate/mark effects, future timers, actual bitmap-cache construction/rendering and OS APIs excluded.'}
    a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(report,indent=2)+'\n')
    if a.versioned_report:
        a.versioned_report.parent.mkdir(parents=True,exist_ok=True)
        a.versioned_report.write_text(json.dumps(versioned_report(report,a.report.read_bytes(),a.source_metadata),indent=2)+'\n')
    print(json.dumps({'cases':len(cases),'resources':len(r.provenance)}))

if __name__=='__main__':main()
