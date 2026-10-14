#!/usr/bin/env python3
"""Import complete selected original-layout cached frame index buffers locally."""
import argparse, hashlib, json
from pathlib import Path
try:
    from .yukonres import verify_source, read_index, DEFAULT_SOURCE_MANIFEST
    from .yukonbmp import EXE_SHA256
    from .yukoncache import decode_cached_frames
except ImportError:
    from yukonres import verify_source, read_index, DEFAULT_SOURCE_MANIFEST
    from yukonbmp import EXE_SHA256
    from yukoncache import decode_cached_frames

SELECTED_IDS=(120,220,320,420,1001,1011,1021,2001,3001,4011,4021,4031,37500,37501)
def source_data(archive, executable, ids=SELECTED_IDS):
    if hashlib.sha256(executable.read_bytes()).hexdigest()!=EXE_SHA256:raise ValueError('Executable identity differs')
    files={};records={};resources={}
    with archive.open('rb') as source:
        archive_hash=verify_source(source,DEFAULT_SOURCE_MANIFEST);index=read_index(source).by_key()
        for id in ids:
            key=f'CBMP:{id}';r=index[key];source.seek(r.offset);data=source.read(r.length)
            resources[key]={'offset':r.offset,'length':r.length,'raw_sha256':hashlib.sha256(data).hexdigest()}
            for i,f in enumerate(decode_cached_frames(data)):
                name=f'CBMP-{id}-frame-{i}-cached-indices.bin';files[name]=f.pixels
                records[f'{id}:{i}']={'format':'original-windows-cache-indices-v1','bitmap_id':id,'frame':i,
                    'width':f.width,'height':f.height,'stride':f.stride,'allocated_height':f.allocated_height,
                    'allocation_bytes':len(f.pixels),'pixels_file':name,'pixels_sha256':hashlib.sha256(f.pixels).hexdigest(),
                    'source_chunk_offset':f.offset,'source_chunk_length':f.length}
    metadata={'schema':'selected-cached-frame-buffers-v1','executable_sha256':EXE_SHA256,'archive_sha256':archive_hash,
              'resources':resources,'frames':records,'scope':'Positive selected cached frame layout including horizontal compressed edge bytes and zero-initialized bottom rows, with original postdecode index normalization. No alpha/palette or rendering mode implied.'}
    return metadata,files

def prepare(archive, executable, output, ids=SELECTED_IDS):
    if output.exists():raise FileExistsError('Fresh cached-frame output directory required')
    metadata,files=source_data(archive,executable,ids)
    output.mkdir(parents=True)
    for name,data in files.items():(output/name).write_bytes(data)
    (output/'cached-frames.json').write_text(json.dumps(metadata,indent=2)+'\n');return metadata

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in('archive','executable','output'):p.add_argument(name,type=Path)
    a=p.parse_args();r=prepare(a.archive,a.executable,a.output);print(json.dumps({'frames':len(r['frames']),'resources':len(r['resources'])}))
