#!/usr/bin/env python3
"""Compare bounded source NE fixups to independently loaded Ghidra segment bytes."""
import argparse, hashlib, json, struct
from pathlib import Path
try:
    from .yukonne_runtime import load
except ImportError:
    from yukonne_runtime import load

def compare(executable, directory):
    source=executable.read_bytes();loaded=load(source);tested=selectors=0;rows=[]
    for segment,metadata in loaded.segments.items():
        if metadata['file_offset']is None:continue
        original=source[metadata['file_offset']:metadata['file_offset']+metadata['initialized_length']]
        independent=(directory/f'NE{segment}.bin').read_bytes()
        if len(independent)!=len(original):raise ValueError('Ghidra segment length differs')
        ignored=set()
        for fixup in loaded.fixups:
            if fixup['ne_segment']!=segment:continue
            off=fixup['offset'];size=len(bytes.fromhex(fixup['before_hex']));ignored.update(range(off,off+size))
            if fixup['kind']==2:
                expected=0x1000+8*(fixup['target'][0]-1)
                if struct.unpack_from('<H',independent,off)[0]!=expected:raise ValueError(f'Independent selector mismatch NE{segment}:{off:04x}')
                selectors+=1
        for i,(a,b)in enumerate(zip(original,independent)):
            if i not in ignored:
                if a!=b:raise ValueError(f'Non-fixup source byte changed NE{segment}:{i:04x}')
                tested+=1
        rows.append({'ne_segment':segment,'length':len(independent),'ghidra_sha256':hashlib.sha256(independent).hexdigest(),'source_sha256':hashlib.sha256(original).hexdigest()})
    return {'executable_sha256':hashlib.sha256(source).hexdigest(),'ghidra_version':'12.1.4','internal_selector_fields_checked':selectors,'non_fixup_source_bytes_checked':tested,'segments':rows,'mismatches':0,'scope':'Independent Ghidra loaded images vs source internal-selector chain sites and every non-fixup initialized byte. Synthetic import addresses differ intentionally; imported APIs and excluded OS fixups are not executed by this audit.'}
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in('executable','ghidra_exports','report'):p.add_argument(name,type=Path)
    a=p.parse_args();r=compare(a.executable,a.ghidra_exports);a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({k:v for k,v in r.items()if k not in('segments','scope')}))
