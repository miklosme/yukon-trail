#!/usr/bin/env python3
"""Import selected normalized scene buffers and provenance into a fresh local directory.

No images, display transforms, action guesses or automatic timing are generated.
"""
import argparse, hashlib, json
from pathlib import Path
try:
    from .yukonres import read_index, verify_source, DEFAULT_SOURCE_MANIFEST
    from .yukonbmp import EXE_SHA256, decode
    from .yukontransform import source_patterns, transform
    from .yukonsprite import read_sprite, read_cel_offsets, read_animation, read_hotspots
except ImportError:
    from yukonres import read_index, verify_source, DEFAULT_SOURCE_MANIFEST
    from yukonbmp import EXE_SHA256, decode
    from yukontransform import source_patterns, transform
    from yukonsprite import read_sprite, read_cel_offsets, read_animation, read_hotspots


def prepare(archive, executable, output, hotspot_ids=(1000, 4000)):
    if output.exists(): raise FileExistsError('Fresh scene asset directory required')
    exe=executable.read_bytes()
    if hashlib.sha256(exe).hexdigest()!=EXE_SHA256: raise ValueError('Executable source mismatch')
    if any(not isinstance(i,int) or not 0<=i<=65535 for i in hotspot_ids): raise ValueError('Invalid HSPT ID')
    patterns=source_patterns(exe);resources={};files={};buffers={}
    with archive.open('rb') as source:
        archive_hash=verify_source(source,DEFAULT_SOURCE_MANIFEST);index=read_index(source).by_key()
        for key in ['SPRT:403','ACEL:400','ASEQ:400',*[f'HSPT:{i}' for i in sorted(set(hotspot_ids))]]:
            r=index[key];source.seek(r.offset);raw=source.read(r.length)
            data=transform(raw,patterns[key.split(':')[0]].opcodes)
            filename=key.replace(':','-')+'-normalized.bin';files[filename]=data;buffers[key]=data
            resources[key]={'offset':r.offset,'length':r.length,'raw_sha256':hashlib.sha256(raw).hexdigest(),
                            'normalized_sha256':hashlib.sha256(data).hexdigest(),'normalized_file':filename}
        r=index['CBMP:400'];source.seek(r.offset);raw=source.read(r.length);frames=decode(raw)
        resources[r.key]={'offset':r.offset,'length':r.length,'raw_sha256':hashlib.sha256(raw).hexdigest(),
                         'frame_sizes_wh':[[f.width,f.height] for f in frames]}
    sprite=read_sprite(buffers['SPRT:403']);animation=read_animation(buffers['ASEQ:400'])
    for key,data in buffers.items():
        if key.startswith('HSPT:'): read_hotspots(data)
    metadata={'schema':'selected-scene-resources-v1','executable_sha256':EXE_SHA256,'archive_sha256':archive_hash,
              'resources':resources,'selected_sprite':{'resource':'SPRT:403','bitmap_id':sprite.bitmap_id,
              'animation_id':sprite.animation_id,'anchor_xy':[sprite.anchor_x,sprite.anchor_y],
              'cel_offsets_xy':read_cel_offsets(buffers['ACEL:400']),'sequence':5,
              'sequence_descriptor':animation.sequences[5]},
              'scope':'Normalized selected resources; no timeline, dispatch or inferred actions. Raw archive unchanged.'}
    files['scene-resources.json']=(json.dumps(metadata,indent=2)+'\n').encode()
    output.mkdir(parents=True)
    for name,data in files.items(): (output/name).write_bytes(data)
    return metadata

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('archive','executable','output'):p.add_argument(name,type=Path)
    p.add_argument('--hotspot',type=int,action='append');a=p.parse_args()
    print(json.dumps(prepare(a.archive,a.executable,a.output,a.hotspot if a.hotspot is not None else (1000,4000))))
