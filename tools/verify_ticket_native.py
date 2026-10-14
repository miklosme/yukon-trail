#!/usr/bin/env python3
"""Original fare dispatch/state setters/money and CONV selector/conditions.

Only optional GUI cache lookup returnsnull and OpenScene arguments are observed
at the Windows scene-creation boundary; no state/condition/RNG/copy behavior is
stubbed. Full sentinel buffers compared, including insufficient funds. Boarding
uses actual parent-stack lookup and original manager/local queues, not voyage.
"""
import argparse, hashlib, json, struct
from pathlib import Path
from unicorn.x86_const import UC_X86_REG_AX, UC_X86_REG_DX, UC_X86_REG_CS, UC_X86_REG_IP, UC_X86_REG_SS, UC_X86_REG_SP
try:
    from .verify_whipsaw_native import NativePurchase
    from .yukonticket import FARES, purchase_ticket, select_clerk_tree, selected_boarding_choice, queue_boarding, open_clerk_dialogue, select_wharf_dialogue, open_boarding_dialogue
    from .yukontree import decode_normalized
    from .verify_tree_native import NativeTree
    from .yukonres import read_index, verify_source, DEFAULT_SOURCE_MANIFEST
    from .yukontransform import source_patterns, transform
except ImportError:
    from verify_whipsaw_native import NativePurchase
    from yukonticket import FARES, purchase_ticket, select_clerk_tree, selected_boarding_choice, queue_boarding, open_clerk_dialogue, select_wharf_dialogue, open_boarding_dialogue
    from yukontree import decode_normalized
    from verify_tree_native import NativeTree
    from yukonres import read_index, verify_source, DEFAULT_SOURCE_MANIFEST
    from yukontransform import source_patterns, transform


class TicketNative(NativePurchase):
    def __init__(self, executable):
        super().__init__(executable)
        self.m.mem_map(0x90000, 0x10000)
        self.m.mem_write(0x90000, executable[0x1dde0:0x1dde0+59278])

    def route_far_call(self, m, address, size, user):
        code = bytes(m.mem_read(address, size)); caller=m.reg_read(UC_X86_REG_CS); ip=m.reg_read(UC_X86_REG_IP)
        if code == bytes.fromhex('26ff5f2c') and (caller,ip)==(0x8000,0x2221):
            m.reg_write(UC_X86_REG_AX,0); m.reg_write(UC_X86_REG_DX,0)
            m.reg_write(UC_X86_REG_SP,(m.reg_read(UC_X86_REG_SP)+8)&65535); m.reg_write(UC_X86_REG_IP,ip+size); return
        if code[0] != 0x9a: return super().route_far_call(m,address,size,user)
        offset=int.from_bytes(code[1:3],'little')
        targets={0xa3bc:0x1000,0xa3e0:0x1000,0x5118:0x9000,0xa7f4:0x1000,
                 0x1250:0x1000,0x3e6a:0x1000,0x100e:0x8000,0xa530:0x1000,0x4dba:0x1000,
                 0xa774:0x1000,0xa2e4:0x1000,0xa642:0x1000,0x2a28:0x2000,0x2c48:0x2000}
        if offset not in targets: return super().route_far_call(m,address,size,user)
        cs=targets[offset]; self.relocations.add((caller,ip,cs,offset)); sp=(m.reg_read(UC_X86_REG_SP)-4)&65535
        m.mem_write(m.reg_read(UC_X86_REG_SS)*16+sp,struct.pack('<HH',ip+size,caller))
        m.reg_write(UC_X86_REG_SP,sp); m.reg_write(UC_X86_REG_CS,cs); m.reg_write(UC_X86_REG_IP,offset)

    def fare(self, before, action):
        self.m.mem_write(0x50000,before)
        self.m.mem_write(0x40026,struct.pack('<HH',0x2000,0x4000)); self.m.mem_write(0x42000,struct.pack('<4H',*action))
        result=self.call(0x8000,0x22c6,struct.pack('<HH',0,0x4000))[0]
        return bytes(self.m.mem_read(0x50000,len(before))),result

    def selection(self,before,conv,sceneid=3500):
        self.m.mem_write(0x50000,before); self.m.mem_write(0x43000,conv)
        self.m.mem_write(0x40030,struct.pack('<HH',0x3000,0x4000)); self.m.mem_write(0x4000e,struct.pack('<H',sceneid))
        value=self.call(0x1000,0x2c9e,struct.pack('<HH',0,0x4000))[0]
        if bytes(self.m.mem_read(0x50000,len(before)))!=before: raise ValueError('Selector mutated original state')
        return value

    def board(self,before,parent,manager,action):
        self.m.mem_write(0x50000,before);self.m.mem_write(0x45000,parent);self.m.mem_write(0x62000,manager)
        self.m.mem_write(0x40026,struct.pack('<HH',0x2000,0x4000));self.m.mem_write(0x42000,struct.pack('<4H',*action))
        result=self.call(0x8000,0x22c6,struct.pack('<HH',0,0x4000))[0]
        return bytes(self.m.mem_read(0x50000,len(before))),bytes(self.m.mem_read(0x45000,len(parent))),bytes(self.m.mem_read(0x62000,len(manager))),result


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('archive',type=Path);p.add_argument('executable',type=Path);p.add_argument('report',type=Path);a=p.parse_args()
    exe=a.executable.read_bytes();n=TicketNative(exe);rows=[];selections=[];conditions=[];boarding=[];opening=[];boardopening=[];wharf=[];resources={};trees={};boardtrees={};wharfconv={};graph_proofs={}
    for offset,wanted in ((0x0883,'e83c23'),(0x092f,'26ff37'),(0x0937,'9ae4a2')):
        if exe[0x460+offset:0x460+offset+len(bytes.fromhex(wanted))].hex()!=wanted:raise ValueError('Original initial-selector/seenmark constructor order differs')
    patterns=source_patterns(exe)
    with a.archive.open('rb') as f:
        archive_hash=verify_source(f,DEFAULT_SOURCE_MANIFEST)
        index=read_index(f).by_key()
        for key in ['SCNE:3000','HSPT:3000','HSPT:4000','CONV:3500','TREE:3500','TREE:3550','TREE:3570','CONV:4300','CONV:4400','TREE:4300','TREE:4350','TREE:4400','TREE:4450']:
            r=index[key];f.seek(r.offset);raw=f.read(r.length);resources[key]=dict(offset=r.offset,length=r.length,sha256=hashlib.sha256(raw).hexdigest())
            if key=='CONV:3500':conv=transform(raw,patterns['CONV'].opcodes)
            if key in ('CONV:4300','CONV:4400'):wharfconv[int(key.split(':')[1])]=transform(raw,patterns['CONV'].opcodes)
            if key in ('TREE:3500','TREE:3550','TREE:3570'):trees[int(key.split(':')[1])]=decode_normalized(transform(raw,patterns['TREE'].opcodes))
            if key in ('TREE:4350','TREE:4450'):boardtrees[int(key.split(':')[1])]=decode_normalized(transform(raw,patterns['TREE'].opcodes))
            if key.startswith('TREE:'):
                root_offset=0x33a if key in ('TREE:4350','TREE:4450') else 0x228
                graph_proofs[key]=NativeTree(exe).parse_and_compare(transform(raw,patterns['TREE'].opcodes),root_offset)
    if struct.unpack('<36H',conv)!=(16,3002,3002,3002,0,0,0,4,3500,3,2,0,0,0,0,3550,3,1,8,2,0,0,3570,8,1,0,0,0,0,0,0,0,0,0,0,0):raise ValueError('Selected source CONV3500 table differs')
    for shipid,(fare,_,_) in FARES.items():
        action=(250,shipid,fare,0)
        for cash in (0,39,40,59,60,79,80,422,32767,32768,65535):
            for bank in (0,20,80,32767,32768,65535):
                for ticket in (0,1,32767,32768,65535):
                    for gate in (0,1):
                        before=bytearray([0x55]*0x400)
                        for off,v in [(0x2fa,cash),(0x2fc,bank),(0x304,ticket),(0x334,gate)]:struct.pack_into('<H',before,off,v)
                        before=bytes(before);actual,result=n.fare(before,action);expected,wanted=purchase_ticket(before,action)
                        if (actual,result)!=(expected,wanted):raise ValueError(f'Original fare mismatch{shipid,cash,bank,ticket,gate}')
                        rows.append([shipid,cash,bank,ticket,gate,hashlib.sha256(actual).hexdigest(),result])
    for partner in (0,1,4,32767,32768,65535):
        for ship in (0,1,2,3,32767,32768,65535):
            before=bytearray([0x55]*0x400);struct.pack_into('<H',before,0x312,partner);struct.pack_into('<H',before,0x320,ship)
            actual=n.selection(bytes(before),conv)
            if actual!=select_clerk_tree(partner,ship):raise ValueError(f'Original clerk selector differs{partner,ship,actual}')
            selections.append([partner,ship,actual])
    for treeid,tree in trees.items():
        for flag in (0,1,2,32767,32768,65535):
            for gate in (0,1,65535):
                before=bytearray([0x55]*0x400);struct.pack_into('<H',before,0x238,flag);struct.pack_into('<H',before,0x334,gate)
                n.m.mem_write(0x50000,bytes(before));n.m.mem_write(0x43000,struct.pack('<HH',2,1))
                initial=n.call(0x9000,0x5118,struct.pack('<HHHH',0x3000,0x4000,3500,16))[0]
                n.call(0x1000,0xa2e4,struct.pack('<HHH',0,0x5000,16))
                actual=bytes(n.m.mem_read(0x50000,len(before)));wanted=bytearray(before)
                selected,afterflag=open_clerk_dialogue(tree,flag,gate);struct.pack_into('<H',wanted,0x238,afterflag)
                if actual!=wanted or selected.voice_id!=(treeid if initial else treeid+1):raise ValueError('Original clerk opening differs')
                opening.append([treeid,flag,gate,selected.offset,selected.voice_id,afterflag,hashlib.sha256(actual).hexdigest()])
    for treeid,tree in boardtrees.items():
        base=treeid-50;index=12 if base==4300 else 11;seenoffset=0x218+2*index
        for seen in (0,1,32768,65535):
            for word30c in (0,1,32768,65535):
                for gate in (0,1):
                    before=bytearray([0x55]*0x400)
                    for off,v in [(seenoffset,seen),(0x30c,word30c),(0x334,gate)]:struct.pack_into('<H',before,off,v)
                    n.m.mem_write(0x50000,bytes(before));outputs=[]
                    for condition in ((4,2),(2,1)):
                        n.m.mem_write(0x43000,struct.pack('<HH',*condition));outputs.append(n.call(0x9000,0x5118,struct.pack('<4H',0x3000,0x4000,base,index))[0])
                    offset=4 if outputs[0] else 0x116 if outputs[1] else 0x33a
                    n.call(0x1000,0xa2e4,struct.pack('<3H',0,0x5000,index));actual=bytes(n.m.mem_read(0x50000,len(before)))
                    selected,post=open_boarding_dialogue(tree,seen,word30c,gate);wanted=bytearray(before);struct.pack_into('<H',wanted,seenoffset,post)
                    if selected.offset!=offset or actual!=wanted:raise ValueError('Original boarding opening differs')
                    boardopening.append([treeid,seen,word30c,gate,selected.offset,selected.voice_id,post,hashlib.sha256(actual).hexdigest()])
    for ship in (0,1,2,3,4,32767,32768,65535):
        n.m.mem_write(0x50320,struct.pack('<H',ship))
        for value in (0,1,2,3,65535):
            n.m.mem_write(0x43000,struct.pack('<HH',26,value));actual=n.call(0x9000,0x5118,struct.pack('<HHHH',0x3000,0x4000,4300,12))[0]
            if actual!=int(selected_boarding_choice(ship,value)):raise ValueError(f'Original boarding condition differs{ship,value,actual}')
            conditions.append([ship,value,actual])
    for delay in (0,7,14):
        for ticket in (0,1,2,32767,32768,65535):
            for gate in (0,1):
                before=bytearray([0x55]*0x400);struct.pack_into('<H',before,0x304,ticket);struct.pack_into('<H',before,0x334,gate)
                parent=bytes([0x55]*128);manager=bytearray([0x55]*128)
                # Original SceneManager_GetParent sees the child first and
                # returns the next actual far stack entry. No lookup stub.
                struct.pack_into('<4H',manager,0x16,0,0x4000,0x5000,0x4000)
                action=(320,delay,0,0);actual=n.board(bytes(before),parent,bytes(manager),action)
                if actual!=queue_boarding(bytes(before),parent,bytes(manager),action):raise ValueError(f'Original boarding queue mismatch{delay,ticket,gate}')
                boarding.append([delay,ticket,gate,*[hashlib.sha256(x).hexdigest() for x in actual[:3]],actual[3]])
    for ticket in (0,1,2,32767,32768,65535):
        for destination in (0,5000,9000):
            for ship in (0,1,2,3,32767,32768,65535):
                for seed in (0,1,32768,0x7fffffff,0xffffffff):
                    before=bytearray([0x55]*0x400)
                    for off,v in [(0x304,ticket),(0x322,destination),(0x320,ship)]:struct.pack_into('<H',before,off,v)
                    n.m.mem_write(0x50000,bytes(before));n.m.mem_write(0x3483e,struct.pack('<I',seed));n.m.mem_write(0x42000,struct.pack('<4H',325,0,0,0));n.refusals=[]
                    n.call(0x8000,0x0890,struct.pack('<4H',0,0x4000,0x2000,0x4000))
                    base,selected,afterseed=select_wharf_dialogue(ticket,destination,ship,seed)
                    actualseed=struct.unpack('<I',n.m.mem_read(0x3483e,4))[0]
                    if n.refusals!=[(0x2000,0x6000,base,300)] or actualseed!=afterseed or bytes(n.m.mem_read(0x50000,len(before)))!=before:raise ValueError('Original Wharf action/RNG differs')
                    actualtree=n.selection(bytes(before),wharfconv[base],base)
                    if actualtree!=selected:raise ValueError('Original Wharf CONV differs')
                    wharf.append([ticket,destination,ship,seed,base,actualtree,actualseed])
    report=dict(executable_sha256=hashlib.sha256(exe).hexdigest(),archive_sha256=archive_hash,resources=resources,original_recursive_graph_proofs=graph_proofs,fare_cases=rows,fare_matrix_sha256=hashlib.sha256(json.dumps(rows,separators=(',',':')).encode()).hexdigest(),clerk_selection_cases=selections,clerk_opening_cases=opening,boarding_opening_cases=boardopening,wharf_opening_cases=wharf,boarding_condition_cases=conditions,boarding_cases=boarding,boarding_matrix_sha256=hashlib.sha256(json.dumps(boarding,separators=(',',':')).encode()).hexdigest(),mismatches=0,synthetic_far_relocations=sorted(n.relocations),scope=__doc__)
    a.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(dict(fare_cases=len(rows),clerk_selection_cases=len(selections),clerk_opening_cases=len(opening),boarding_opening_cases=len(boardopening),wharf_opening_cases=len(wharf),boarding_condition_cases=len(conditions),boarding_cases=len(boarding),mismatches=0,fare_matrix_sha256=report['fare_matrix_sha256'],boarding_matrix_sha256=report['boarding_matrix_sha256'])))

if __name__=='__main__':main()
