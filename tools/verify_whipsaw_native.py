#!/usr/bin/env python3
"""Original selected merchant dispatch/purchase/getters/setters/money routines.

Optional display-cache lookup returnsnull. Insufficient-funds OpenScene is an
argument-observation boundary, not an emulated scene. State arithmetic and
inventory mutation execute original instructions.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_AX,UC_X86_REG_DX,UC_X86_REG_CS,UC_X86_REG_IP,UC_X86_REG_SS,UC_X86_REG_SP
try:
    from .verify_journal_native import NativeJournal
    from .yukonpurchase import WhipsawWords,purchase_selected_whipsaw
except ImportError:
    from verify_journal_native import NativeJournal
    from yukonpurchase import WhipsawWords,purchase_selected_whipsaw


class NativePurchase(NativeJournal):
    def __init__(self,executable):
        super().__init__(executable,b'\0\4one\0two\0three\0four\0');self.refusals=[]
        self.m.mem_write(0x30094,struct.pack('<HH',0x5000,0x6000));self.m.mem_write(0x65000,struct.pack('<HH',0x6000,0x6000));self.m.mem_write(0x6602c,struct.pack('<HH',0xf000,0x9000))
        self.m.mem_write(0x30090,struct.pack('<HH',0x2000,0x6000));self.m.mem_write(0x352fc,struct.pack('<HH',0x3000,0x6000))
    def route_far_call(self,m,address,size,user):
        code=bytes(m.mem_read(address,size));caller=m.reg_read(UC_X86_REG_CS);ip=m.reg_read(UC_X86_REG_IP)
        if code==bytes.fromhex('26ff5f2c') and (caller,ip) in [(0x1000,0xa1bd),(0x8000,0x2575)]:
            m.reg_write(UC_X86_REG_AX,0);m.reg_write(UC_X86_REG_DX,0);m.reg_write(UC_X86_REG_SP,(m.reg_read(UC_X86_REG_SP)+8)&65535);m.reg_write(UC_X86_REG_IP,ip+size);return
        if code[0]!=0x9a:return
        offset=int.from_bytes(code[1:3],'little')
        if offset==0x3f9a:
            args=struct.unpack('<4H',m.mem_read(m.reg_read(UC_X86_REG_SS)*16+m.reg_read(UC_X86_REG_SP),8));self.refusals.append(args)
            m.reg_write(UC_X86_REG_SP,(m.reg_read(UC_X86_REG_SP)+8)&65535);m.reg_write(UC_X86_REG_IP,ip+size);return
        if offset not in (0xa744,0xa632,0x9e40,0xa184):return super().route_far_call(m,address,size,user)
        self.relocations.add((caller,ip,0x1000,offset));sp=(m.reg_read(UC_X86_REG_SP)-4)&65535
        m.mem_write(m.reg_read(UC_X86_REG_SS)*16+sp,struct.pack('<HH',ip+size,caller));m.reg_write(UC_X86_REG_SP,sp);m.reg_write(UC_X86_REG_CS,0x1000);m.reg_write(UC_X86_REG_IP,offset)
    def purchase(self,before):
        state=bytearray([0x55]*0x350)
        for offset,value in [(0x2fa,before.cash_word),(0x2fc,before.bank_word),(0x306,0),(0x312,4),(0x318,before.word318),(0x334,before.gate334_word)]:struct.pack_into('<H',state,offset,value)
        self.m.mem_write(0x50000,bytes(state));self.m.mem_write(0x40026,struct.pack('<HH',0x2000,0x4000));self.m.mem_write(0x42000,struct.pack('<4H',220,109,8,0));self.m.mem_write(0x40030,struct.pack('<HH',0x4000,0x6000));self.m.mem_write(0x64000,struct.pack('<H',17));self.refusals=[]
        result=self.call(0x8000,0x2884,struct.pack('<HH',0,0x4000))[0]
        return bytes(self.m.mem_read(0x50000,len(state))),result,self.refusals,state


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('executable',type=Path);parser.add_argument('report',type=Path);args=parser.parse_args();executable=args.executable.read_bytes();native=NativePurchase(executable);rows=[]
    for cash in (0,7,8,20,850,32767,32768,65535):
        for bank in (0,3,8,20,32767,32768,65535):
            for gate in (0,1):
                before=WhipsawWords(cash,bank,0,4,0x1234,gate);expected=purchase_selected_whipsaw(before);actual,result,refusals,wanted=native.purchase(before)
                for offset,value in [(0x2fa,expected.state.cash_word),(0x2fc,expected.state.bank_word),(0x306,expected.state.whipsaw_word),(0x318,expected.state.word318)]:struct.pack_into('<H',wanted,offset,value)
                expected_refusals=[(0x2000,0x6000,600,300)] if expected.refusal_tree_id else []
                if actual!=wanted or result!=int(expected.action_success) or refusals!=expected_refusals:raise ValueError(f'Original purchase mismatch{before}/{result}/{refusals}')
                rows.append([cash,bank,gate,hashlib.sha256(actual).hexdigest(),result,refusals])
    report=dict(executable_sha256=hashlib.sha256(executable).hexdigest(),cases=len(rows),mismatches=0,matrix_sha256=hashlib.sha256(json.dumps(rows,separators=(',',':')).encode()).hexdigest(),synthetic_call_relocations=sorted(native.relocations),scope='Original220dispatch/24d0purchase/getters/setter/money, selecteditem109cost8unownedword306partner4CONV17. Displaycachelookupnull; refusalOpenSceneargumentscapturedonly; noGUIorjournalcaller.')
    args.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(report))


if __name__=='__main__':main()
