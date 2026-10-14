#!/usr/bin/env python3
"""Compare every nonempty source TREE response graph to original recursive code.

Initial root is independently located from normalized empty-text sentinel bytes.
Only bounded allocation and checked segmented call routing are substituted.
Original copy/recursion/string routines execute. Initial override construction,
conditions/actions, live dialogue, UI and sound playback remain excluded.
"""
import argparse,hashlib,json
from pathlib import Path
try:
    from .verify_tree_native import NativeTree
    from .yukonres import read_index,verify_source,DEFAULT_SOURCE_MANIFEST
    from .yukontransform import source_patterns,transform
    from .audit_trees import root_from_source
except ImportError:
    from verify_tree_native import NativeTree
    from yukonres import read_index,verify_source,DEFAULT_SOURCE_MANIFEST
    from yukontransform import source_patterns,transform
    from audit_trees import root_from_source

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('archive','executable','report'):p.add_argument(name,type=Path)
    a=p.parse_args();exe=a.executable.read_bytes();patterns=source_patterns(exe);results={};excluded={};relocations=set()
    with a.archive.open('rb')as f:
        archive_hash=verify_source(f,DEFAULT_SOURCE_MANIFEST);index=read_index(f).by_key()
        for key,r in index.items():
            if not key.startswith('TREE:'):continue
            f.seek(r.offset);raw=f.read(r.length)
            if key=='TREE:39' and not raw:
                excluded[key]={'offset':r.offset,'length':r.length,'raw_sha256':hashlib.sha256(raw).hexdigest(),'reason':'Empty source payload has no response graph; original out-of-bounds handling excluded'}
                continue
            if len(raw)>60000:raise ValueError(f'{key} exceeds initialized input segment bound')
            normalized=transform(raw,patterns['TREE'].opcodes);root=root_from_source(normalized)
            native=NativeTree(exe)
            try:proof=native.parse_and_compare(normalized,root,instruction_limit=1000000)
            except Exception as error:raise ValueError(f'{key} at0x{r.offset:x}: {error}')from error
            relocations.update(native.relocations)
            results[key]={'offset':r.offset,'length':r.length,'raw_sha256':hashlib.sha256(raw).hexdigest(),
                          'normalized_sha256':hashlib.sha256(normalized).hexdigest(),'independent_root_offset':root,**proof}
    report={'executable_sha256':hashlib.sha256(exe).hexdigest(),'archive_sha256':archive_hash,'scope':__doc__,
            'instruction_limit_per_graph':1000000,'resources':results,'excluded':excluded,'mismatches':0,
            'synthetic_far_relocations':sorted(relocations)}
    a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'trees':len(results),'response_nodes':sum(v['response_nodes']for v in results.values()),
                      'allocations':sum(v['allocations']for v in results.values()),'excluded':excluded,'mismatches':0}))
if __name__=='__main__':main()
