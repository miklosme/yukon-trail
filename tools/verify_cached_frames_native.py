#!/usr/bin/env python3
"""Original cached-frame allocation, complete decoder and indexed-hit proof."""
import argparse, hashlib, json, struct
from pathlib import Path
from unicorn.x86_const import *
from unicorn import UC_HOOK_CODE
try:
    from .verify_seattle_population_native import NativePopulation, Resources
    from .yukoncache import decode_cached_frames
except ImportError:
    from verify_seattle_population_native import NativePopulation, Resources
    from yukoncache import decode_cached_frames

class NativeFrame(NativePopulation):
    def __init__(self,exe,resources):
        super().__init__(exe,resources)
        self.m.hook_del(self.code_hook)
        # Only platform/provider entrypoints need Python routing. Original
        # decoder/getter instructions otherwise execute without per-op hooks.
        for begin,end in [(0x61eac,0x61ec0),(0x17c88,0x17c88),(0x17818,0x17818),(0xe8100,0xe9000)]:
            self.m.hook_add(UC_HOOK_CODE,self.route,begin=begin,end=end)
    def call(self,seg,off,args):
        # This Win16 code contains compiler-generated MOVSD copies of stack
        # temporaries through DS. Its DGROUP stack convention requires SS=DS.
        m=self.m
        for reg,value in [(UC_X86_REG_CS,self.image.selectors[seg]),(UC_X86_REG_DS,0xd000),(UC_X86_REG_ES,0xf000),(UC_X86_REG_SS,0xd000),(UC_X86_REG_SP,0xf000)]:m.reg_write(reg,value)
        m.mem_write(0xdf000,self.ptr(0xff00,0x1000)+args)
        m.emu_start(self.image.selectors[seg]*16+off,0x1ff00,count=3000000)
        if m.reg_read(UC_X86_REG_CS)!=0x1000 or m.reg_read(UC_X86_REG_IP)!=0xff00:raise ValueError(f'Original frame path stopped at {m.reg_read(UC_X86_REG_CS):x}:{m.reg_read(UC_X86_REG_IP):x}')
    def resource_malloc(self,count):
        off,seg=super().resource_malloc(count)
        self.m.mem_write(seg*16+off,bytes([self.heap_fill])*count)
        return off,seg
    def frame(self,bitmap_id,frame_index):
        data=self.resources.get('CBMP',bitmap_id)
        width,height=struct.unpack_from('<HH',data,2+frame_index*12)
        self.call(2,0x9572,self.ptr(0x2800));self.m.mem_write(0xf2804,struct.pack('<4h',0,0,height,width))
        wrapper=self.malloc(0x14)
        self.call(3,0x0e8e,self.ptr(*wrapper)+self.ptr(0x2800))
        p=wrapper[1]*16+wrapper[0];bo,bs=struct.unpack('<HH',self.m.mem_read(p+0x10,4));buffer=bs*16+bo
        before=bytes(self.m.mem_read(0xa1000,self.handles[1][1]))
        self.m.mem_write(0xd52f4,self.ptr(0x2800))
        view=self.malloc(0x20);self.call(3,0xc316,self.ptr(*view)+struct.pack('<HII',1,bitmap_id,0x43424d50))
        reader=self.malloc(0xc);self.call(2,0x4502,self.ptr(*reader)+self.ptr(*view))
        self.call(2,0x464e,self.ptr(*reader)+struct.pack('<H',frame_index)+self.ptr(bo,bs))
        pixels=bytes(self.m.mem_read(0xa1000,self.handles[1][1]))
        self.call(3,0x0958,self.ptr(0x2900));self.call(2,0x9572,self.ptr(0x2a00))
        self.call(3,0x1132,self.ptr(*wrapper)+self.ptr(0x2900))
        dimensions=list(struct.unpack('<2h',self.m.mem_read(0xf2904,4)))
        self.call(3,0x11a6,self.ptr(*wrapper)+self.ptr(0x2a00))
        returned_buffer=(self.m.reg_read(UC_X86_REG_AX),self.m.reg_read(UC_X86_REG_DX))
        if returned_buffer!=(bo,bs):raise ValueError('Actual frame getter returned different buffer')
        logical_rect=list(struct.unpack('<4h',self.m.mem_read(0xf2a04,8)))
        self.last_wrapper=wrapper
        return {'dimensions_yx':dimensions,'logical_rectangle_tlbr':logical_rect,'wrapper':wrapper,'buffer':(bo,bs),'stride':struct.unpack('<H',self.m.mem_read(buffer+0x1e,2))[0],
                'allocation_length':self.handles[1][1],'initialized_before_decode_hex':before.hex(), 'pixels_hex':pixels.hex(), 'buffer_hex':bytes(self.m.mem_read(buffer,0x3e)).hex()}

    def hit(self,frame_index,x,y):
        # Cache fixture routes actual frame getter methods to the actual constructed
        # wrapper. Full cache multi-frame allocation/lifetime is excluded.
        wrapper=self.last_wrapper;self.m.mem_write(0xf2b00,self.ptr(0x67ea,0x6000))
        self.m.mem_write(0xf2b12,self.ptr(0x2c00))
        self.m.mem_write(0xf2c00+frame_index*4,self.ptr(*wrapper))
        self.m.mem_write(0xf2d5a,self.ptr(0x2b00));self.m.mem_write(0xf2d2a,struct.pack('<H',frame_index))
        self.m.mem_write(0xf2d10,struct.pack('<4h',10,20,10,20))
        self.call(3,0x0958,self.ptr(0x2e00));self.m.mem_write(0xf2e04,struct.pack('<2h',y+10,x+20))
        self.call(2,0xe78a,self.ptr(0x2d00)+self.ptr(0x2e00))
        return bool(self.m.reg_read(UC_X86_REG_AX)&255)

def synthetic_edge_probe(exe,resources):
    # Authored one-block CBMP, control3 literal17, no repeat. Width/height1;
    # native tile writer must copy8 horizontal bytes and leave7 bottom rows.
    bits='11'+format(17,'08b')+'0'
    packed=int(bits.ljust(16,'0'),2).to_bytes(2,'big')
    chunk=struct.pack('<HBBII',12,3,1,11,64)+bytes([0,17])+packed
    payload=struct.pack('<HHHII',1,1,1,14,len(chunk))+chunk
    class SyntheticResource:
        def get(self,tag,id):
            if (tag,id)!=('CBMP',9999):raise ValueError('Unexpected synthetic resource request')
            return payload
    results=[]
    for fill in (0,85):
        n=NativeFrame(exe,SyntheticResource());n.heap_fill=fill;v=n.frame(9999,0)
        pixels=bytes.fromhex(v['pixels_hex'])
        if pixels!=bytes([17])*8+bytes(56):raise ValueError('Original synthetic edge tile differs')
        if decode_cached_frames(payload)[0].pixels!=pixels:raise ValueError('Derived edge layout differs from original')
        results.append({'allocator_fill_byte':fill,'original_buffer_hex':pixels.hex(),'original_buffer_sha256':hashlib.sha256(pixels).hexdigest()})
    return {'fixture_type':'authored CBMP edge probe; not supplied game content','payload_hex':payload.hex(),'payload_sha256':hashlib.sha256(payload).hexdigest(),'width':1,'height':1,'stride':8,'allocated_height':8,'cases':results}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in('archive','executable','report'):p.add_argument(name,type=Path)
    p.add_argument('--id',type=int,action='append');a=p.parse_args();exe=a.executable.read_bytes();r=Resources(a.archive,exe);cases=[]
    ids=a.id or [120,220,320,420,1001,1011,1021,2001,3001,4011,4021,4031,37500,37501]
    for bitmap in ids:
        data=r.get('CBMP',bitmap);frames=decode_cached_frames(data)
        for i,f in enumerate(frames):
            pair=[]
            for fill in (0,85):
                n=NativeFrame(exe,r);n.heap_fill=fill;v=n.frame(bitmap,i)
                pixels=bytes.fromhex(v['pixels_hex']);before=bytes.fromhex(v['initialized_before_decode_hex'])
                if pixels!=f.pixels or v['stride']!=f.stride or v['allocation_length']!=f.stride*f.allocated_height or any(before):raise ValueError(f'Complete native allocation mismatch {bitmap}/{i}/{fill}')
                if v['dimensions_yx']!=[f.height,f.width] or v['logical_rectangle_tlbr']!=[0,0,f.height,f.width]:raise ValueError(f"Actual frame getter dimensions differ: {v['dimensions_yx']}/{v['logical_rectangle_tlbr']}")
                points={(0,0),(f.width-1,0),(0,f.height-1),(f.width-1,f.height-1),(f.width,0),(f.width,f.height//2),(f.width,f.height-1),(0,f.height),(f.width,f.height)}
                for nonzero in (False,True):
                    candidates=[j for j,b in enumerate(pixels[:f.stride*f.height])if bool(b)==nonzero]
                    if candidates:
                        j=candidates[len(candidates)//2];points.add((j%f.stride,j//f.stride))
                hits=[]
                for x,y in sorted(points):
                    original=n.hit(i,x,y);offset=y*f.stride+x
                    if offset<0 or offset>32767:raise ValueError('Selected native hit signed bound exceeded')
                    expected=offset<f.width*f.height and pixels[offset]!=0
                    if original!=expected:raise ValueError(f'Actual frame hit mismatch {bitmap}/{i} at{x}/{y}')
                    hits.append({'x':x,'y':y,'original_hit':original})
                pair.append({'bitmap_id':bitmap,'frame':i,'allocator_fill_byte':fill,'width':f.width,'height':f.height,'stride':f.stride,'allocated_height':f.allocated_height,'allocation_bytes':len(pixels),
                             'original_buffer_sha256':hashlib.sha256(pixels).hexdigest(),'zeroed_before_decode':True,
                             'horizontal_padding_nonzero':sum(bool(pixels[y*f.stride+x])for y in range(f.height)for x in range(f.width,f.stride)),
                             'bottom_padding_nonzero':sum(bool(b)for b in pixels[f.height*f.stride:]),'original_hits':hits})
            if pair[0]['original_buffer_sha256']!=pair[1]['original_buffer_sha256']:raise ValueError('Actual frame depends on allocator fill')
            cases.extend(pair)
    report={'executable_sha256':hashlib.sha256(exe).hexdigest(),'archive_sha256':r.archive_hash,'cases':cases,'resources':r.provenance,
            'synthetic_edge_case':synthetic_edge_probe(exe,r),
            'scope':'Original wrapper0e8e/buffer4e4e+5708/memory8816+92fa, resourceviewc316 and complete464e decoder/normalization, actual1132/11a6 getters and e78a pixel hit. Explicit successful memory/archive platform providers; synthetic cache table routes to actual single-frame wrapper. Full cache lifetime/allocation, manager bbox and rendering excluded.'}
    a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'cases':len(cases),'hits':sum(len(c['original_hits'])for c in cases),'nonzero_horizontal_padding':sum(c['horizontal_padding_nonzero']for c in cases),'mismatches':0}))

if __name__=='__main__':main()
