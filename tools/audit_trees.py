#!/usr/bin/env python3
"""Inventory source TREE graph/voice/action references; no behavior defaults.

Structural acceptance is not original-oracle validation or playable coverage.
Unknown action/condition meanings and unsupported graphs remain explicit.
No dialogue text or raw source payloads are exported.
"""
import argparse,hashlib,json
from collections import Counter
from pathlib import Path
try:
    from .yukonres import read_index,verify_source,DEFAULT_SOURCE_MANIFEST
    from .yukontransform import source_patterns,transform
    from .yukontree import decode_normalized,TreeError
except ImportError:
    from yukonres import read_index,verify_source,DEFAULT_SOURCE_MANIFEST
    from yukontransform import source_patterns,transform
    from yukontree import decode_normalized,TreeError

def inspect_graph(normalized):
    try:tree=decode_normalized(normalized)
    except TreeError as error:return {'status':'unsupported','reason':str(error)}
    records=list(tree.initial_overrides);responses=0;choices=0;max_depth=0
    def walk(node,depth):
        nonlocal responses,choices,max_depth
        responses+=1;max_depth=max(max_depth,depth);records.append(node.record)
        for choice in node.choices:
            choices+=1;records.append(choice.record)
            if choice.response is not None:walk(choice.response,depth+1)
    walk(tree.root,0)
    return {'status':'parsed','speaker_word':tree.speaker_word,'declared_record_count':tree.count_word,
            'initial_override_count':len(tree.initial_overrides),'response_nodes':responses,
            'choice_records':choices,'max_depth':max_depth,'trailing_empty_offsets':list(tree.trailing_empty_offsets),
            'records':[{'offset':r.offset,'word0':r.word0,'link_word':r.link_word,
                        'action_words':list(r.action),'condition_words':list(r.condition),
                        'voice_id':r.voice_id,'text_bytes':len(r.text),
                        'text_sha256':hashlib.sha256(r.text).hexdigest()}for r in records]}

def root_from_source(payload):
    if len(payload)<4 or (len(payload)-4)%274:raise ValueError('Source TREE record boundary unsupported')
    # Original override reader stops at first text-byte zero. No decoded model
    # supplies this start pointer to the original response parser.
    for offset in range(4,len(payload),274):
        if payload[offset+18]==0:
            root=offset+274
            if root>=len(payload):raise ValueError('Source has no response root')
            return root
    raise ValueError('Source has no initial override terminator')

def audit(archive,executable,record_details=False):
    patterns=source_patterns(executable.read_bytes());resources={};voices=set();actions=Counter();conditions=Counter()
    with archive.open('rb')as f:
        archive_hash=verify_source(f,DEFAULT_SOURCE_MANIFEST);index=read_index(f).by_key()
        for key,record in index.items():
            if not key.startswith('TREE:'):continue
            f.seek(record.offset);raw=f.read(record.length)
            try:
                normalized=transform(raw,patterns['TREE'].opcodes);result=inspect_graph(normalized)
            except ValueError as error:
                normalized=None;result={'status':'unsupported','reason':str(error)}
            result.update(offset=record.offset,length=record.length,raw_sha256=hashlib.sha256(raw).hexdigest(),
                          normalized_sha256=hashlib.sha256(normalized).hexdigest()if normalized is not None else None)
            for r in result.get('records',[]):
                if r['voice_id']:voices.add(r['voice_id'])
                actions[r['action_words'][0]]+=1;conditions[r['condition_words'][0]]+=1
            if result['status']=='parsed' and not record_details:
                records=result.pop('records')
                result['record_metadata_sha256']=hashlib.sha256(json.dumps(records,sort_keys=True,separators=(',',':')).encode()).hexdigest()
                result['voice_ids']=sorted({r['voice_id']for r in records if r['voice_id']})
                for label,field in (('action_opcodes','action_words'),('condition_opcodes','condition_words')):
                    ids=sorted({r[field][0]for r in records})
                    result[label]=[{'opcode':id,'record_count':sum(r[field][0]==id for r in records),
                                    'first_record_offset':next(r['offset']for r in records if r[field][0]==id)}for id in ids]
            resources[key]=result
        missing=[id for id in sorted(voices)if f'PSND:{id}'not in index]
    return {'archive_sha256':archive_hash,'executable_sha256':hashlib.sha256(executable.read_bytes()).hexdigest(),
            'scope':__doc__,'resources':resources,'summary':{
                'trees':len(resources),'parsed':sum(r['status']=='parsed'for r in resources.values()),
                'unsupported':{key:r['reason']for key,r in resources.items()if r['status']!='parsed'},
                'distinct_nonzero_voice_ids':len(voices),'missing_psnd_ids':missing,
                'action_opcode_record_counts':dict(sorted(actions.items())),
                'condition_opcode_record_counts':dict(sorted(conditions.items()))}}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('archive','executable','report'):p.add_argument(name,type=Path)
    p.add_argument('--record-details',action='store_true',help='Include per-record metadata for ignored analysis exports')
    a=p.parse_args();report=audit(a.archive,a.executable,a.record_details)
    a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps(report['summary'],sort_keys=True))
