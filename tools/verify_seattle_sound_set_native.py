#!/usr/bin/env python3
"""Recover voices from selected actual Seattle TREE graphs; compare all native PCM.

Source graph voice IDs, not TREE IDs or character-name guesses, choose PSND.
Original integer readers/converter execute; header/terminal proofs are separate.
No live playback, mixer, whole processor, dialogue/UI or condition execution.
"""
import argparse,hashlib,json
from pathlib import Path
try:
    from .yukonres import read_index,verify_source,DEFAULT_SOURCE_MANIFEST
    from .yukontransform import source_patterns,transform
    from .yukontree import decode_normalized
    from .yukonsnd import decode,integrate
    from .verify_sound_native import SoundNativeReader,native_integrate
except ImportError:
    from yukonres import read_index,verify_source,DEFAULT_SOURCE_MANIFEST
    from yukontransform import source_patterns,transform
    from yukontree import decode_normalized
    from yukonsnd import decode,integrate
    from verify_sound_native import SoundNativeReader,native_integrate

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('archive','executable','report'):p.add_argument(name,type=Path)
    p.add_argument('--tree',type=int,action='append',help='Explicit selected TREE ID; repeat to define the oracle corpus')
    a=p.parse_args();exe=a.executable.read_bytes();patterns=source_patterns(exe);trees={};voices=set();sounds={}
    ids=a.tree if a.tree is not None else (1,600,2100,3100,3200,3300,3400)
    if any(not 0<=id<=65535 for id in ids):p.error('TREE IDs must be unsigned16-bit')
    with a.archive.open('rb') as f:
        archive_hash=verify_source(f,DEFAULT_SOURCE_MANIFEST);index=read_index(f).by_key()
        for id in sorted(set(ids)):
            r=index[f'TREE:{id}'];f.seek(r.offset);raw=f.read(r.length);tree=decode_normalized(transform(raw,patterns['TREE'].opcodes));records=list(tree.initial_overrides)
            def walk(node):
                records.append(node.record)
                for choice in node.choices:
                    records.append(choice.record)
                    if choice.response:walk(choice.response)
            walk(tree.root);voiced=[dict(record_offset=r.offset,voice_id=r.voice_id,text_sha256=hashlib.sha256(r.text).hexdigest()) for r in records if r.voice_id]
            voices.update(row['voice_id'] for row in voiced);trees[f'TREE:{id}']=dict(offset=r.offset,length=r.length,raw_sha256=hashlib.sha256(raw).hexdigest(),speaker_word=tree.speaker_word,voiced_records=voiced)
        for id in sorted(voices):
            r=index[f'PSND:{id}'];f.seek(r.offset);raw=f.read(r.length);native=SoundNativeReader(exe);sound=decode(raw,native.compare);actual,state=native_integrate(native,exe,sound.encoded_values,sound.order)
            if (actual,state)!=integrate(sound.encoded_values,sound.order) or actual!=sound.samples:raise ValueError('Selectednativevoice mismatch')
            sounds[r.key]=dict(offset=r.offset,length=r.length,raw_sha256=hashlib.sha256(raw).hexdigest(),order=sound.order,declared_bits=sound.packed_bits,consumed_bits=sound.consumed_bits,terminal_unused_bits=sound.terminal_unused_bits,integer_calls=native.calls,windowed_integer_calls=native.windowed_calls,sample_bytes=len(actual),native_pcm_sha256=hashlib.sha256(actual).hexdigest(),final_state=list(state))
    report=dict(executable_sha256=hashlib.sha256(exe).hexdigest(),archive_sha256=archive_hash,trees=trees,sounds=sounds,voice_count=len(sounds),sample_bytes=sum(x['sample_bytes'] for x in sounds.values()),integer_calls=sum(x['integer_calls'] for x in sounds.values()),mismatches=0,scope=__doc__);a.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(dict(voices=len(sounds),sample_bytes=report['sample_bytes'],integer_calls=report['integer_calls'],mismatches=0)))
if __name__=='__main__':main()
