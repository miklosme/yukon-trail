#!/usr/bin/env python3
"""Read verified executable status fragments and all16 inventory table entries."""
import argparse,hashlib,json,struct
from dataclasses import asdict
from pathlib import Path
try:
    from .yukonjournal import source_vocabulary,EXE_SHA256
except ImportError:
    from yukonjournal import source_vocabulary,EXE_SHA256

def source_data(executable):
    if hashlib.sha256(executable).hexdigest()!=EXE_SHA256:raise ValueError('Source mismatch')
    vocab=asdict(source_vocabulary(executable))
    vocab={k:[s.decode('latin1')for s in v]if isinstance(v,tuple)else v.decode('latin1')for k,v in vocab.items()}
    def field(offset):
        if executable[0x4f420+offset-1]!=0:raise ValueError('Not a source string boundary')
        value=executable[0x4f420+offset:].split(b'\0')[0]
        return {'text':value.decode('latin1'),'ne_address':f'NE13:{offset:04x}','file_offset':0x4f420+offset,'length':len(value)+1,'sha256':hashlib.sha256(value+b'\0').hexdigest()}
    fragments={name:field(off)for name,off in [('have',0x1106),('kilograms',0x1117),('pounds',0x1133),('cash',0x114c),('gold_prefix',0x1155),('gold',0x115f)]}
    table=executable[0x50214:0x50214+160]
    return {'schema':'recovered-journal-status-v1','vocabulary':vocab,'fragments':fragments,
            'inventory_table':{'entries':[list(struct.unpack_from('<5h',table,i*10))for i in range(16)],'ne_address':'NE13:0df4','file_offset':0x50214,'length':160,'sha256':hashlib.sha256(table).hexdigest()},
            'provenance':{'executable_sha256':EXE_SHA256,'encoding':'Source byte to Latin1 codepoint mapping; typography not inferred'}}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('executable',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    if a.output.exists():raise FileExistsError('Refusing to replace prepared assets')
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(source_data(a.executable.read_bytes()),indent=2)+'\n')
