#!/usr/bin/env python3
"""Original event4 journal gate, full formatter and complete inventory selectors.

Only malloc is replaced by bounded initialized local memory; unchanged source
formatters/getters/string operations execute. Stops before entry deallocation.
"""
import argparse, hashlib, json, struct
from pathlib import Path
from unicorn.x86_const import UC_X86_REG_CS,UC_X86_REG_IP,UC_X86_REG_SS,UC_X86_REG_SP,UC_X86_REG_AX,UC_X86_REG_DX
from verify_journal_native import NativeJournal
from yukonbmp import EXE_SHA256

class NativeStatus(NativeJournal):
    def __init__(self,exe):
        super().__init__(exe,b'\0\0');self.next_alloc=0x8000;self.stopped=False;self.allocations=[];self.mode='status';self.request=None
    def route_far_call(self,m,address,size,user):
        cs,ip=m.reg_read(UC_X86_REG_CS),m.reg_read(UC_X86_REG_IP)
        if self.mode=='retention' and (cs,ip)in((0x2000,0x6128),(0x2000,0x612d)):
            if ip==0x6128:self.request=list(struct.unpack('<5H',m.mem_read(m.reg_read(UC_X86_REG_SS)*16+m.reg_read(UC_X86_REG_SP),10)))
            self.stopped=True;m.emu_stop();return
        if (cs,ip)==(0x1000,0xcbac):self.stopped=True;m.emu_stop();return
        code=bytes(m.mem_read(address,size))
        if code[0]!=0x9a:return
        offset=int.from_bytes(code[1:3],'little')
        if offset==0x1ebe:
            count=struct.unpack('<H',m.mem_read(m.reg_read(UC_X86_REG_SS)*16+m.reg_read(UC_X86_REG_SP),2))[0]
            if count not in (8,255):raise ValueError('Unbounded allocation requested')
            off=self.next_alloc;self.next_alloc+=count+16;self.allocations.append(count)
            m.mem_write(0x40000+off,bytes(count));m.reg_write(UC_X86_REG_AX,off);m.reg_write(UC_X86_REG_DX,0x4000);m.reg_write(UC_X86_REG_IP,ip+size);return
        if offset==0xa744:
            self.relocations.add((cs,ip,0x1000,offset));sp=(m.reg_read(UC_X86_REG_SP)-4)&65535
            m.mem_write(m.reg_read(UC_X86_REG_SS)*16+sp,struct.pack('<HH',ip+size,cs));m.reg_write(UC_X86_REG_SP,sp);m.reg_write(UC_X86_REG_CS,0x1000);m.reg_write(UC_X86_REG_IP,offset);return
        super().route_far_call(m,address,size,user)
    def status(self,state,cached,prior,units,event=4):
        self.next_alloc=0x8000;self.stopped=False;self.allocations=[];self.mode='status'
        self.m.mem_write(0x50000,state);self.m.mem_write(0x60000,struct.pack('<6H',*cached)+b'\0\0'+struct.pack('<HH',0x1000,0x6000))
        self.m.mem_write(0x61000,prior+b'\0');self.m.mem_write(0x35314,struct.pack('<HH',0x8000,0x5000));self.m.mem_write(0x58030,struct.pack('<H',units))
        try:self.call(0x1000,0xc474,struct.pack('<4H',0,0x6000,0,event))
        except ValueError as error:
            if not self.stopped:raise
        if bytes(self.m.mem_read(0x50000,len(state)))!=state:raise ValueError('Original changed game state')
        text=bytes(self.m.mem_read(0x61000,0x2800)).split(b'\0')[0]
        snapshot=list(struct.unpack('<6H',self.m.mem_read(0x60000,12)))
        return {'text_hex':text.hex(),'snapshot_words':snapshot,'allocations':self.allocations,'stopped_before_cleanup':self.stopped}

    def inventory(self,state):
        self.mode='inventory';self.m.mem_write(0x50000,state)
        values=[self.call(0x1000,0xbb4c,struct.pack('<3H',0,0x4000,i))[0]for i in range(16)]
        if bytes(self.m.mem_read(0x50000,len(state)))!=state:raise ValueError('Inventory selector mutated state')
        return values
    def retention_request(self,abandon):
        self.mode='retention';self.request=None;self.stopped=False
        self.m.mem_write(0x30df2,struct.pack('<H',abandon));self.m.mem_write(0x35692,struct.pack('<H',123))
        try:self.call(0x2000,0x60fc,struct.pack('<3H',0x1000,0x4000,0))
        except ValueError:
            if not self.stopped:raise
        return self.request


def main():
    from prepare_journal_status import source_data
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('executable',type=Path);p.add_argument('report',type=Path);a=p.parse_args()
    exe=a.executable.read_bytes();assets=source_data(exe);native=NativeStatus(exe)
    base={0x28:24,0x2a:8,0x34:200,0x36:0,0x38:2000,0x2fa:350,0x2fc:0,0x2fe:0,0x310:1,0x312:65535}
    def state(changes):
        data=bytearray(0x386)
        for off,v in (base|changes).items():struct.pack_into('<H',data,off,v)
        return bytes(data)
    cases=[]
    def record(name,changes={},snapshot=(24,8,0,350,0,0),prior=b'edited\xff\r\ntext',units=0):
        data=state(changes);out=native.status(data,snapshot,prior,units)
        cases.append({'name':name,'state_word_changes':[[o,v]for o,v in sorted(changes.items())],
                      'snapshot_words':list(snapshot),'prior_hex':prior.hex(),'units_word':units,'original':out})
        return out
    record('clean_reopen')
    for dirty in(0,1,2,65535):record(f'dirty{dirty}',snapshot=(24,8,0,350,0,dirty))
    for i in range(5):
        snap=[24,8,0,350,0,0];snap[i]=[23,7,1,351,1][i];record(f'cache_word{i}',snapshot=snap)
    for off in(0x28,0x2a,0x2fa,0x2fc,0x2fe,0x310,0x312,0x38):
        values=(1,12)if off==0x2a else (1,31)if off==0x28 else (0,1,4,5,6,32767,32768,65535)
        for v in values:record(f'changed_only_{off:x}_{v}',{off:v})
    for off in range(0x300,0x30c,2):
        for v in(1,7,12,65535):record(f'item_only_{off:x}_{v}',{off:v})
    for food in(0,1,2,99,100,2400,32767,32768,65535):
        for units in(0,1,65535):
            record(f'format_food{food}_units{units}',{0x2fe:food},snapshot=(24,8,0,350,0,1),units=units)
    for cash in(0,1,350,32767,32768,65535):
        for gold in(0,1,32767,32768,65535):record(f'format_cash{cash}_gold{gold}',{0x2fa:cash,0x2fc:gold},snapshot=(24,8,0,350,0,1),prior=b'')
    for phase in(0,5,6,65535):record(f'phase{phase}',{0x310:phase},snapshot=(24,8,0,350,0,1))
    inventory=[]
    for index in range(9):
        for value in(0,1,7,8,9,10,11,12,32767,32768,65535):
            changes={0x2fa+index*2:value};inventory.append({'state_word_changes':[[o,v]for o,v in changes.items()],'original_enabled':native.inventory(state(changes))})
    # Independent recorded094 tail: full original event0 then two event4 calls.
    arrival=native.status(state({0x28:23,0x38:4000}),[0,0,0,0,0,1],b'',0,event=0)
    first=native.status(state({0x28:23,0x38:4000}),arrival['snapshot_words'],bytes.fromhex(arrival['text_hex']),0)
    second=native.status(state({0x38:2000}),first['snapshot_words'],bytes.fromhex(first['text_hex']),0)
    visible=[line.strip()for line in bytes.fromhex(second['text_hex']).decode('latin1').splitlines()if line.strip()]
    expected=['August 23, 1897. Arrived at Seattle.','August 23, 1897. Seattle. We have:','0 pounds of food','$350 in cash','August 24, 1897. Seattle. We have:','0 pounds of food','$350 in cash']
    if visible!=expected:raise ValueError('Native094 observed lines differ from original formatter sequence')
    report={'executable_sha256':EXE_SHA256,'source_assets':assets,'base_state_words':[[o,v]for o,v in sorted(base.items())],
            'status_cases':cases,'inventory_cases':inventory,'retention_requests':[{'abandon_word':v,'original_request':native.retention_request(v)}for v in(0,1,65535)],
            'capture094':{'path':'local/evidence/seattle-reference-2026-10-13/krnl386_094.png','sha256':hashlib.sha256(Path('local/evidence/seattle-reference-2026-10-13/krnl386_094.png').read_bytes()).hexdigest(),'observed_nonempty_tail_lines':expected,'original_event0':arrival,'original_first_event4':first,'original_second_event4':second,'scope':'Manual visible-line comparison excludes name/header and leading/trailing indentation; exact bytes come independently from executed original formatter, not screenshot OCR.'},
            'synthetic_call_relocations':sorted(native.relocations),'scope':'Original c474 event4 gates/dbe2 full formatter/string append; platform malloc replaced with bounded local memory. Stops before entry destructor; overflow/prompt/nativeEdit API execution excluded. Retention records actual import request boundary only.'}
    a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'status_cases':len(cases),'inventory_contexts':len(inventory),'inventory_original_calls':16*len(inventory),'capture094_lines':len(expected)}))

if __name__=='__main__':main()
