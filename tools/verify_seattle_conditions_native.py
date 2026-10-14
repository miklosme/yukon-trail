#!/usr/bin/env python3
"""Compare every observed Seattle dialogue predicate kind to unchanged NE3 code.

Full-sized synthetic state and settings words are explicit, not world defaults.
Checked NE selector routing only; no condition/getter/state behavior is stubbed.
No live dialogue, choice visibility, action dispatch or general condition proof.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn.x86_const import UC_X86_REG_CS,UC_X86_REG_IP,UC_X86_REG_SS,UC_X86_REG_SP
try:
    from .verify_tree_conditions_native import Conditions
    from .yukonconditions import evaluate_seattle_condition
    from .yukonne_runtime import load
    from .yukonres import read_index,verify_source,DEFAULT_SOURCE_MANIFEST
    from .yukontransform import source_patterns,transform
    from .yukontree import decode_normalized
except ImportError:
    from verify_tree_conditions_native import Conditions
    from yukonconditions import evaluate_seattle_condition
    from yukonne_runtime import load
    from yukonres import read_index,verify_source,DEFAULT_SOURCE_MANIFEST
    from yukontransform import source_patterns,transform
    from yukontree import decode_normalized

class SeattleConditions(Conditions):
    def __init__(self,exe):
        super().__init__(exe);self.loaded=load(exe);self.instructions={}
    def route_far_call(self,m,address,size,user):
        cs=m.reg_read(UC_X86_REG_CS);ip=m.reg_read(UC_X86_REG_IP);code=bytes(m.mem_read(address,size))
        if cs in(0x1000,0x9000):self.instructions[(1 if cs==0x1000 else 3,ip)]=code.hex()
        if code[0]!=0x9a or int.from_bytes(code[1:3],'little')not in(0xa642,0xa040):return super().route_far_call(m,address,size,user)
        off=int.from_bytes(code[1:3],'little')
        if cs!=0x9000 or bytes(self.loaded.images[3][ip:ip+5])!=b'\x9a'+struct.pack('<HH',off,0x1000):raise ValueError('New getter FAR call target differs from source NE fixup')
        self.relocations.add((cs,ip,0x1000,off));sp=(m.reg_read(UC_X86_REG_SP)-4)&65535
        m.mem_write(m.reg_read(UC_X86_REG_SS)*16+sp,struct.pack('<HH',ip+size,cs));m.reg_write(UC_X86_REG_SP,sp);m.reg_write(UC_X86_REG_CS,0x1000);m.reg_write(UC_X86_REG_IP,off)
    def evaluate(self,condition,state,context,units):
        self.m.mem_write(0x50000,state);self.m.mem_write(0x43000,struct.pack('<2H',*condition))
        self.m.mem_write(0x35314,struct.pack('<2H',0x8000,0x5000));settings=bytearray([0x77]*0x40);struct.pack_into('<H',settings,0x30,units);self.m.mem_write(0x58000,bytes(settings))
        result=self.call(0x9000,0x5118,struct.pack('<4H',0x3000,0x4000,*context))[0]
        if bytes(self.m.mem_read(0x50000,len(state)))!=state or bytes(self.m.mem_read(0x58000,0x40))!=settings:raise ValueError('Condition mutated explicit state/settings')
        return result

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in('archive','executable','report'):p.add_argument(name,type=Path)
    a=p.parse_args();exe=a.executable.read_bytes();n=SeattleConditions(exe);rows=[];sources={};patterns=source_patterns(exe)
    with a.archive.open('rb')as f:
        archive_hash=verify_source(f,DEFAULT_SOURCE_MANIFEST);index=read_index(f).by_key()
        for id in(1,600,2100,3100,3200,3300,3400,3500,3550,3570,4300,4350,4400,4450):
            r=index[f'TREE:{id}'];f.seek(r.offset);raw=f.read(r.length);tree=decode_normalized(transform(raw,patterns['TREE'].opcodes));records=list(tree.initial_overrides)
            def walk(node):
                records.append(node.record)
                for c in node.choices:
                    records.append(c.record)
                    if c.response:walk(c.response)
            walk(tree.root)
            sources[r.key]={'offset':r.offset,'length':r.length,'raw_sha256':hashlib.sha256(raw).hexdigest(),
                            'speaker_word':tree.speaker_word,'nonzero_conditions':[{'record_offset':r.offset,'words':list(r.condition)}for r in records if r.condition[0]]}
    values=(0,1,2,7,17,32767,32768,65535)
    def check(pattern,kind,value,index,flag,other_offset=0x318,other=0,units=0,scene=2100,item_words=None):
        state=bytearray(0x386)
        if pattern==1:state[:]=bytes([0x55])*len(state)
        if pattern==2:state[:]=bytes(i&255 for i in range(len(state)))
        for off,v in((0x218+2*index,flag),(other_offset,other)):struct.pack_into('<H',state,off,v)
        if item_words is not None:
            for off,v in zip((0x300,0x302,0x306),item_words):struct.pack_into('<H',state,off,v)
        state=bytes(state);actual=n.evaluate((kind,value),state,(scene,index),units)
        if actual!=int(evaluate_seattle_condition((kind,value),state,index,units)):raise ValueError(f'Native predicate mismatch{kind,value,index,flag,other_offset,other,units,actual}')
        rows.append([pattern,kind,value,index,flag,other_offset,other,units,scene,item_words,actual])
    for pattern in range(3):
        check(pattern,0,0,17,0)
        for index in(1,2,3,4,11,12,16,17,60):
            for flag in values:
                for value in(0,1,2,65535):check(pattern,2,value,index,flag)
        for index in(11,12,17):
            for flag in values:
                for other in values:
                    for value in(0,1,2,65535):check(pattern,4,value,index,flag,0x30c,other)
        for flag in values:
            for other in(0,1,16,17,18,60,32767,65535):
                for value in(0,1,2,65535):check(pattern,7,value,17,flag,0x318,other)
            for items in((0,0,0),(1,0,0),(0,1,0),(0,0,1),(32768,0,0),(0,65535,0),(0,0,32767),(65535,65535,65535)):
                for value in(0,1,2,65535):check(pattern,7,value,17,flag,0x318,17,item_words=items)
        for value in(107,108,109):
            for other in values:check(pattern,11,value,17,0,{107:0x300,108:0x302,109:0x306}[value],other)
        for units in values:
            for value in(0,1,2,65535):check(pattern,172,value,17,0,units=units)
        for ship in(0,1,2,3,4,32767,32768,65535):
            for value in(0,1,2,3,65535):check(pattern,26,value,12,0,0x320,ship,scene=4300)
    report={'executable_sha256':hashlib.sha256(exe).hexdigest(),'archive_sha256':archive_hash,'sources':sources,
            'row_columns':['state_pattern','kind','value','conversation_index','flag_word','other_state_offset','other_word','units_word','scene_word','item_words_300_302_306','original_result'],
            'state_patterns':['zero','55','byte_ramp'],'native_cases':rows,'mismatches':0,
            'executed_instruction_bytes':[{'ne_segment':seg,'offset':off,'raw_hex':raw}for(seg,off),raw in sorted(n.instructions.items())],
            'synthetic_far_relocations':sorted(n.relocations),'getter_arguments':sorted(n.getter_arguments),'scope':__doc__}
    a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'native_cases':len(rows),'source_graphs':len(sources),'mismatches':0}))
if __name__=='__main__':main()
