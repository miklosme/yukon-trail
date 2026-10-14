#!/usr/bin/env python3
"""Census actual PSND headers and bounded decoder acceptance, not audio fidelity."""
import argparse,hashlib,json,struct
from collections import Counter
from pathlib import Path
try:
    from .yukonres import read_index,verify_source,DEFAULT_SOURCE_MANIFEST
    from .yukonsnd import decode,SoundError
except ImportError:
    from yukonres import read_index,verify_source,DEFAULT_SOURCE_MANIFEST
    from yukonsnd import decode,SoundError

def inspect_payload(payload):
    result={}
    if len(payload)>=12:
        result['record_header_hex']=payload[:12].hex()
        result['channels'],result['sample_bits'],result['rate_code'],result['integration_order']=payload[6],payload[7],payload[8],payload[10]
    if len(payload)>=22:
        index_length=struct.unpack_from('<I',payload,14)[0];chunk_offset=12+index_length+6
        result['index_length']=index_length;result['chunk_offset']=chunk_offset
        if chunk_offset+12<=len(payload):
            size,algorithm,flags,bits,expanded=struct.unpack_from('<HBBII',payload,chunk_offset)
            result.update(header_size=size,algorithm=algorithm,flags=flags,packed_bits=bits,expanded_size=expanded)
            # flags0/header12 contains NO count; packed bytes must not be labelled metadata.
            result['checkpoint_count']=struct.unpack_from('<H',payload,chunk_offset+12)[0] if flags==2 and size>=14 and chunk_offset+14<=len(payload) else None
    try:sound=decode(payload)
    except SoundError as error:result.update(status='unsupported_or_invalid',reason=str(error))
    else:result.update(status='decoded',samples=len(sound.samples),pcm_sha256=hashlib.sha256(sound.samples).hexdigest(),encoded_sha256=hashlib.sha256(sound.encoded_values).hexdigest(),padding_bytes=len(sound.block_padding),consumed_bits=sound.consumed_bits,terminal_unused_bits=sound.terminal_unused_bits,terminal_unused_value=sound.terminal_unused_value)
    return result

def audit(archive):
    resources={}
    with archive.open('rb') as f:
        archive_hash=verify_source(f,DEFAULT_SOURCE_MANIFEST)
        for r in read_index(f).resources:
            if r.tag!='PSND':continue
            f.seek(r.offset);raw=f.read(r.length);row=inspect_payload(raw);row.update(offset=r.offset,length=r.length,raw_sha256=hashlib.sha256(raw).hexdigest());resources[r.key]=row
    variants={}
    fields=('channels','sample_bits','rate_code','integration_order','header_size','algorithm','flags','checkpoint_count')
    for key,row in resources.items():
        variant=','.join(str(row.get(field)) for field in fields)
        v=variants.setdefault(variant,dict(parameters={field:row.get(field) for field in fields},ids=[],statuses=Counter()))
        v['ids'].append(key);v['statuses'][row['status']]+=1
    return dict(archive_sha256=archive_hash,resource_count=len(resources),decoder_source_sha256=hashlib.sha256(Path(__file__).with_name('yukonsnd.py').read_bytes()).hexdigest(),statuses=dict(Counter(row['status'] for row in resources.values())),variants=variants,resources=resources,scope='Actualsourceheader census and currentboundeddecoder acceptance/PCMprovenance. Notnativewhole-playback orliveaudiofidelity. Checkpoint countinterpretedonlyflags2; flags0/header12 hasnone.')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('archive',type=Path);p.add_argument('report',type=Path);a=p.parse_args();r=audit(a.archive);a.report.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print(json.dumps(dict(resources=r['resource_count'],statuses=r['statuses'],variants=len(r['variants']))))
