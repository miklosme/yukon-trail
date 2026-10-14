#!/usr/bin/env python3
"""Original integer readers and converter for every actual PSND order0/3/4.

Compressed bytes are decoded separately from integration, avoiding an order
parameter alteration in source data. Original order0 leaves bytes/state intact;
orders3/4 use original9b34. Header metadata proof is separate; no playback.
"""
import argparse,hashlib,json,struct
from pathlib import Path
try:
    from .verify_sound_native import SoundNativeReader,native_integrate
    from .yukonsnd import integrate
    from .yukonbmp import Bits,_block
    from .yukonres import read_index,verify_source,DEFAULT_SOURCE_MANIFEST
except ImportError:
    from verify_sound_native import SoundNativeReader,native_integrate
    from yukonsnd import integrate
    from yukonbmp import Bits,_block
    from yukonres import read_index,verify_source,DEFAULT_SOURCE_MANIFEST

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('archive','executable','report'):p.add_argument(name,type=Path)
    a=p.parse_args();exe=a.executable.read_bytes();rows={};palette=bytes(128+i//2 if i%2==0 else 127-i//2 for i in range(256))
    with a.archive.open('rb') as f:
        archive_hash=verify_source(f,DEFAULT_SOURCE_MANIFEST)
        for r in read_index(f).resources:
            if r.tag!='PSND':continue
            f.seek(r.offset);raw=f.read(r.length);order=raw[10]
            if order not in (0,3,4):continue
            native=SoundNativeReader(exe);o=12+struct.unpack_from('<I',raw,14)[0]+6;size,alg,flags,bits,expanded=struct.unpack_from('<HBBII',raw,o)
            if (raw[6],raw[7],raw[8],alg,flags,size)!=(1,8,22,3,0,12):raise ValueError('Unexpected actualrareorder sourcevariant')
            reader=Bits(raw[o+size:],(len(raw)-o-size)*8);output=bytearray()
            while len(output)<(expanded+63)//64*64:
                block,repeat=_block(reader,palette,native.compare,palette_control=False);output.extend(block*(repeat+1))
            if not 0<=reader.limit-reader.position<=7:raise ValueError('Unexpected terminal rareorder remainder')
            encoded=bytes(output[:expanded]);actual,state=native_integrate(native,exe,encoded,order);expected=encoded if order==0 else integrate(encoded,order)[0]
            if actual!=expected:raise ValueError('Originalrareorder conversiondiffers')
            if order==0 and state!=bytes([128]*4):raise ValueError('Originalorder0 changedstate')
            rows[r.key]=dict(offset=r.offset,length=r.length,raw_sha256=hashlib.sha256(raw).hexdigest(),order=order,sample_bytes=len(actual),native_pcm_sha256=hashlib.sha256(actual).hexdigest(),integer_calls=native.calls,final_state=list(state))
    report=dict(executable_sha256=hashlib.sha256(exe).hexdigest(),archive_sha256=archive_hash,resources=rows,mismatches=0,scope=__doc__);a.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(dict(resources=len(rows),mismatches=0)))
if __name__=='__main__':main()
