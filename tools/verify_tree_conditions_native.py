#!/usr/bin/env python3
"""Selected Linda override2/1 and merchant whipsaw11/109 conditions."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from unicorn.x86_const import UC_X86_REG_CS,UC_X86_REG_IP,UC_X86_REG_SS,UC_X86_REG_SP
try:
    from .verify_linda_child_native import NativeConditions
except ImportError:
    from verify_linda_child_native import NativeConditions


class Conditions(NativeConditions):
    def __init__(self,executable):
        super().__init__(executable);self.getter_arguments=set()
    def route_far_call(self,m,address,size,user):
        code=bytes(m.mem_read(address,size))
        if code[0]!=0x9a or int.from_bytes(code[1:3],'little') not in (0xa744,0xa774):
            return super().route_far_call(m,address,size,user)
        offset=int.from_bytes(code[1:3],'little');caller=m.reg_read(UC_X86_REG_CS);ip=m.reg_read(UC_X86_REG_IP);sp=m.reg_read(UC_X86_REG_SP)
        args=struct.unpack('<3H',m.mem_read(m.reg_read(UC_X86_REG_SS)*16+sp,6))
        self.getter_arguments.add((ip,offset,*args));self.relocations.add((caller,ip,0x1000,offset))
        sp=(sp-4)&65535;m.mem_write(m.reg_read(UC_X86_REG_SS)*16+sp,struct.pack('<HH',ip+size,caller))
        m.reg_write(UC_X86_REG_SP,sp);m.reg_write(UC_X86_REG_CS,0x1000);m.reg_write(UC_X86_REG_IP,offset)
    def selected(self,condition,context,word_offset,word):
        self.m.mem_write(0x50000,bytes(0x350));self.m.mem_write(0x50000+word_offset,struct.pack('<H',word))
        self.m.mem_write(0x43000,struct.pack('<HH',*condition));before=bytes(self.m.mem_read(0x50000,0x350))
        result=self.call(0x9000,0x5118,struct.pack('<HHHH',0x3000,0x4000,*context))[0]
        if bytes(self.m.mem_read(0x50000,0x350))!=before:raise ValueError('Condition mutated state')
        return result


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('executable',type=Path);parser.add_argument('report',type=Path);args=parser.parse_args()
    executable=args.executable.read_bytes();native=Conditions(executable);rows=[]
    for word in (0,1,2,32767,32768,65535):
        for condition,context,offset,expected in [((2,1),(3400,4),0x220,int(word!=0)),((11,109),(2100,17),0x306,int(word==0))]:
            result=native.selected(condition,context,offset,word)
            if result!=expected:raise ValueError('Selected condition model differs from original')
            rows.append(dict(condition=condition,context_words=context,state_word_offset=offset,input_word=word,result=result))
    report=dict(executable_sha256=hashlib.sha256(executable).hexdigest(),cases=rows,mismatches=0,getter_arguments=sorted(native.getter_arguments),synthetic_call_relocations=sorted(native.relocations),scope='Original selected condition/getter instructions; no behaviorstubs or statewrites. Broader condition catalog unknown.')
    args.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(dict(cases=len(rows),mismatches=0,getter_arguments=sorted(native.getter_arguments))))


if __name__=='__main__':main()
