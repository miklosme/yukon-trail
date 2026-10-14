#!/usr/bin/env python3
"""Original timer constructor/register/cancel/poll and countdown period blocks.

Only malloc/free and TIMEGETTIME platform services are controlled. Poll's
forwarded game-event call is an argument/mutation boundary, not an emulated
scene callback. Timer logic and memory writes execute original instructions.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn.x86_const import UC_X86_REG_AX,UC_X86_REG_DX,UC_X86_REG_CS,UC_X86_REG_DS,UC_X86_REG_ES,UC_X86_REG_SS,UC_X86_REG_SP,UC_X86_REG_BP,UC_X86_REG_IP
try:
    from .verify_countdown_native import CountdownNative
    from .yukontimers import countdown_period,initialize_timer_table,register_timer,cancel_timer,poll_timers
except ImportError:
    from verify_countdown_native import CountdownNative
    from yukontimers import countdown_period,initialize_timer_table,register_timer,cancel_timer,poll_timers


class TimerNative(CountdownNative):
    def __init__(self,exe):
        super().__init__(exe);self.clocks=[];self.clock_reads=0;self.allocate=True;self.frees=[];self.events=[];self.effect='keep'
    def route_far_call(self,m,address,size,user):
        code=bytes(m.mem_read(address,size));caller=m.reg_read(UC_X86_REG_CS);ip=m.reg_read(UC_X86_REG_IP)
        if code[0]!=0x9a:return super().route_far_call(m,address,size,user)
        sp=m.reg_read(UC_X86_REG_SP);stack=m.reg_read(UC_X86_REG_SS)*16+sp
        if caller==0x1000 and ip in (0x4f81,0x507c,0x50f9):
            if self.clock_reads>=len(self.clocks):raise ValueError('Unexpected native clock request')
            clock=self.clocks[self.clock_reads];self.clock_reads+=1;m.reg_write(UC_X86_REG_AX,clock&65535);m.reg_write(UC_X86_REG_DX,clock>>16);m.reg_write(UC_X86_REG_IP,ip+size);return
        if caller==0x1000 and ip==0x4f61:
            if struct.unpack('<H',m.mem_read(stack,2))[0]!=8:raise ValueError('Unexpected timer allocation extent')
            m.reg_write(UC_X86_REG_AX,0x5000 if self.allocate else 0);m.reg_write(UC_X86_REG_DX,0x4000 if self.allocate else 0);m.reg_write(UC_X86_REG_IP,ip+size);return
        if caller==0x1000 and ip==0x4ffd:
            self.frees.append(struct.unpack('<I',m.mem_read(stack,4))[0]);m.reg_write(UC_X86_REG_IP,ip+size);return
        if caller==0x1000 and ip==0x50da:
            args=list(struct.unpack('<6H',m.mem_read(stack,12)));self.events.append(args);slot=args[4]
            if self.effect=='remove':m.mem_write(0x64000+slot*4,bytes(4))
            elif self.effect=='disable':
                pointer=struct.unpack('<I',m.mem_read(0x64000+slot*4,4))[0];off,seg=pointer&65535,pointer>>16;m.mem_write(seg*16+off,b'\0')
            m.reg_write(UC_X86_REG_SP,(sp+12)&65535);m.reg_write(UC_X86_REG_IP,ip+size);return
        return super().route_far_call(m,address,size,user)
    def reset_clock(self,clocks):self.clocks=list(clocks);self.clock_reads=0;self.frees=[];self.events=[]
    def period(self,requested):
        for r,v in ((UC_X86_REG_CS,0x8000),(UC_X86_REG_DS,0x3000),(UC_X86_REG_ES,0x4000),(UC_X86_REG_SS,0x7000),(UC_X86_REG_BP,0xf000),(UC_X86_REG_SP,0xefe4)):self.m.reg_write(r,v)
        self.m.mem_write(0x7f006,struct.pack('<3H',0,0x4000,requested));self.m.mem_write(0x40004,struct.pack('<H',4000))
        self.m.emu_start(0x8103a,0x81045,count=1000);count=struct.unpack('<H',self.m.mem_read(0x7f00a,2))[0]
        self.m.emu_start(0x810c4,0x810e6,count=1000);return count,self.m.reg_read(UC_X86_REG_AX)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('executable',type=Path);p.add_argument('report',type=Path);a=p.parse_args();exe=a.executable.read_bytes();n=TimerNative(exe);registration=[];cancellation=[];polls=[];periods=[];initial=[]
    for requested in (0,1,2,7,14,120,121,32767,32768,65535):
        actual=n.period(requested)
        if actual!=countdown_period(requested):raise ValueError('Original countdown period differs')
        periods.append([requested,*actual])
    for value in (0,0x55,0xff):
        before=bytes([value]*32);n.m.mem_write(0x64000,before);n.call(0x1000,0x4e94,struct.pack('<2H',0x4000,0x6000));actual=bytes(n.m.mem_read(0x64000,32))
        if actual!=initialize_timer_table(before):raise ValueError('Original five-slot initialization differs')
        initial.append([value,hashlib.sha256(actual).hexdigest()])
    for mask in range(32):
        table=bytearray([0x55]*32)
        for slot in range(5):struct.pack_into('<I',table,slot*4,0x60005000+slot*16 if mask&(1<<slot) else 0)
        for period in (0,2,35,38,47,150,32767,32768,65535):
            for clock in (0,15,16,65535,0x7fffffff,0xffffffff):
                for allocate in (False,True):
                    heap=bytes([0x5a]*8);n.m.mem_write(0x64000,bytes(table));n.m.mem_write(0x45000,heap);n.reset_clock([clock]);n.allocate=allocate
                    result=n.call(0x1000,0x4f20,struct.pack('<3H',0x4000,0x6000,period))[0];actual=(bytes(n.m.mem_read(0x64000,32)),bytes(n.m.mem_read(0x45000,8)),result)
                    if actual!=register_timer(bytes(table),heap,0x40005000,period,clock,allocate):raise ValueError('Original timer registration differs')
                    registration.append([mask,period,clock,allocate,hashlib.sha256(actual[0]).hexdigest(),hashlib.sha256(actual[1]).hexdigest(),result,n.clock_reads])
        for timer_id in (0,1,2,3,4,6,32767,32768,65535):
            n.m.mem_write(0x64000,bytes(table));n.reset_clock([]);n.call(0x1000,0x4fca,struct.pack('<3H',0x4000,0x6000,timer_id));actual=bytes(n.m.mem_read(0x64000,32))
            wanted,freed=cancel_timer(bytes(table),timer_id)
            if actual!=wanted or n.frees!=freed:raise ValueError('Original timer cancellation differs')
            cancellation.append([mask,timer_id,hashlib.sha256(actual).hexdigest(),n.frees])
    for clock in (0,15,16,160,0xffffffff):
        for active in (0,1,2,255):
            for delta in (-1,0,1):
                for effect in ('keep','remove','disable'):
                    table=bytearray([0x55]*32);records={}
                    for slot in range(5):
                        pointer=0x60005000+slot*16;struct.pack_into('<I',table,slot*4,pointer);record=bytearray([0x5a]*8);record[0]=active;struct.pack_into('<H',record,2,35+slot);struct.pack_into('<I',record,4,((clock>>4)+delta)&0xffffffff);records[pointer]=bytes(record);n.m.mem_write(0x65000+slot*16,bytes(record))
                    clocks=[clock]+[(clock+i*16)&0xffffffff for i in range(1,6)];n.m.mem_write(0x64000,bytes(table));n.reset_clock(clocks);n.effect=effect
                    n.call(0x1000,0x5076,struct.pack('<2H',0x4000,0x6000));actual_table=bytes(n.m.mem_read(0x64000,32));actual_heap={p:bytes(n.m.mem_read(0x65000+i*16,8)) for i,p in enumerate(records)}
                    reads=iter(clocks)
                    def callback(slot,t,h):
                        pointer=struct.unpack_from('<I',t,slot*4)[0]
                        if effect=='remove':struct.pack_into('<I',t,slot*4,0)
                        elif effect=='disable':h[pointer][0]=0
                    expected_table,expected_heap,fired=poll_timers(bytes(table),records,lambda:next(reads),callback)
                    if actual_table!=expected_table or actual_heap!=expected_heap or n.events!=[[0x2000,0x6000,0,0,s,0x466] for s in fired]:raise ValueError('Original timer polling differs')
                    polls.append([clock,active,delta,effect,hashlib.sha256(actual_table).hexdigest(),[hashlib.sha256(actual_heap[p]).hexdigest() for p in records],fired,n.clock_reads])
    report=dict(executable_sha256=hashlib.sha256(exe).hexdigest(),period_cases=periods,initialization_cases=initial,registration_cases=registration,cancellation_cases=cancellation,poll_cases=polls,mismatches=0,scope=__doc__)
    a.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(dict(period_cases=len(periods),registration_cases=len(registration),cancellation_cases=len(cancellation),poll_cases=len(polls),mismatches=0)))
if __name__=='__main__':main()
