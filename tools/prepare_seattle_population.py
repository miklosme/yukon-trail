#!/usr/bin/env python3
"""Prepare source field tables for the bounded initial Seattle population only."""
import argparse, hashlib, json, struct
from pathlib import Path
try:
    from .yukonres import read_index, verify_source, DEFAULT_SOURCE_MANIFEST
    from .yukonbmp import EXE_SHA256
    from .yukontransform import source_patterns, transform
    from .yukonsprite import read_sprite, read_cel_offsets
except ImportError:
    from yukonres import read_index, verify_source, DEFAULT_SOURCE_MANIFEST
    from yukonbmp import EXE_SHA256
    from yukontransform import source_patterns, transform
    from yukonsprite import read_sprite, read_cel_offsets

def source_data(archive, executable):
    exe=executable.read_bytes()
    if hashlib.sha256(exe).hexdigest()!=EXE_SHA256: raise ValueError('Executable source mismatch')
    patterns=source_patterns(exe);provenance={};buffers={}
    with archive.open('rb') as source:
        archive_hash=verify_source(source,DEFAULT_SOURCE_MANIFEST);index=read_index(source).by_key()
        def get(tag,id):
            key=f'{tag}:{id}'
            if key in buffers:return buffers[key]
            r=index[key];source.seek(r.offset);raw=source.read(r.length)
            data=transform(raw,patterns[tag].opcodes) if tag in patterns else raw
            provenance[key]={'offset':r.offset,'length':r.length,'raw_sha256':hashlib.sha256(raw).hexdigest(),'normalized_sha256':hashlib.sha256(data).hexdigest()}
            buffers[key]=data;return data
        scenes={};sprites={};animations={};bitmaps={}
        for id in (1000,2000,3000,4000):
            scne=get('SCNE',id);scrp=get('SCRP',id);count=struct.unpack_from('<H',scrp)[0]
            if len(scne)!=10 or len(scrp)!=2+18*count:raise ValueError('Selected scene length mismatch')
            scenes[id]={'scne_words':list(struct.unpack('<5H',scne)), 'records':[list(struct.unpack_from('<9H',scrp,2+i*18))for i in range(count)]}
        # Includes both Downtown pre-entry visit states; partnered paths deliberately excluded.
        for id in (1013,1003,1014,1004,1023,2003,120,220,320,420,3001,4013,4023,4033):
            s=read_sprite(get('SPRT',id))
            sprites[id]={'bitmap_id':s.bitmap_id,'animation_id':s.animation_id,'anchor_xy':[s.anchor_x,s.anchor_y],
                         'initial_sequence':s.initial_sequence,'raw_header_words':list(struct.unpack('<19H',s.raw_header)),'schedules':s.schedules}
        for id in sorted({s['animation_id']for s in sprites.values()}|{37500,37501}):
            data=get('ASEQ',id);count=struct.unpack_from('<H',data)[0];tail=2+count*8
            if len(data)<tail+2:raise ValueError('ASEQ truncated')
            steps=struct.unpack_from('<H',data,tail)[0]
            if len(data)!=tail+2+steps*12:raise ValueError('ASEQ length mismatch')
            animations[id]={'sequences':[list(struct.unpack_from('<HhHH',data,2+i*8))for i in range(count)],
                            'steps':[list(struct.unpack_from('<HhhHHH',data,tail+2+i*12))for i in range(steps)],
                            'cel_offsets_xy':read_cel_offsets(get('ACEL',id))}
        for id in sorted({s['bitmap_id']for s in sprites.values()}|{37500,37501}):
            data=get('CBMP',id);count=struct.unpack_from('<H',data)[0]
            if len(data)<2+12*count:raise ValueError('CBMP table truncated')
            bitmaps[id]={'frame_sizes_wh':[list(struct.unpack_from('<HH',data,2+i*12))for i in range(count)]}
    result={'schema':'seattle-initial-population-source-v1','executable_sha256':EXE_SHA256,'archive_sha256':archive_hash,
            'scenes':scenes,'sprites':sprites,'animations':animations,'bitmaps':bitmaps,'resources':provenance,
            'scope':'Source fields, not precomputed poses. Partner ffff, state320 zero, selected Downtown visit zero/one, pre-entry Seattle arrival zero/one; initial constant clocks only. ASEQ successors retained without assuming validity (320 successor4 is outside its table).'}
    return result

def prepare(archive, executable, output):
    if output.exists(): raise FileExistsError('Fresh population metadata path required')
    result=source_data(archive,executable)
    output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(result,indent=2)+'\n');return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('archive','executable','output'):p.add_argument(name,type=Path)
    a=p.parse_args();r=prepare(a.archive,a.executable,a.output);print(json.dumps({'resources':len(r['resources']),'sprites':len(r['sprites'])}))
