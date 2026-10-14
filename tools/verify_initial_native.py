#!/usr/bin/env python3
"""Execute original NE1:9900 reset, NE6:2a28 RNG/multiply and291e memset.

Only far selectors relocated; no allocation, random, memset or state behavior
stubs. Explicit prior buffers/seeds test untouched byte preservation. Fresh
scene activation, initial name/journal UI and OS startup seed remain excluded.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn.x86_const import UC_X86_REG_CS,UC_X86_REG_IP,UC_X86_REG_SS,UC_X86_REG_SP
try:
    from .verify_journal_native import NativeJournal
    from .yukoninitial import original_random_step,reset_original_state
except ImportError:
    from verify_journal_native import NativeJournal
    from yukoninitial import original_random_step,reset_original_state

class InitialNative(NativeJournal):
    def route_far_call(self,m,address,size,user):
        code=bytes(m.mem_read(address,size))
        if code[0]!=0x9a or int.from_bytes(code[1:3],'little') not in (0x2a28,0x2c48,0x291e):return super().route_far_call(m,address,size,user)
        offset=int.from_bytes(code[1:3],'little');caller=m.reg_read(UC_X86_REG_CS);ip=m.reg_read(UC_X86_REG_IP);self.relocations.add((caller,ip,0x2000,offset))
        sp=(m.reg_read(UC_X86_REG_SP)-4)&65535;m.mem_write(m.reg_read(UC_X86_REG_SS)*16+sp,struct.pack('<HH',ip+size,caller));m.reg_write(UC_X86_REG_SP,sp);m.reg_write(UC_X86_REG_CS,0x2000);m.reg_write(UC_X86_REG_IP,offset)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('executable',type=Path);p.add_argument('report',type=Path);a=p.parse_args();exe=a.executable.read_bytes();native=InitialNative(exe,b'\0\4one\0two\0three\0four\0');rows=[]
    for seed in (0,1,2,3,32767,32768,65535,65536,0x7fffffff,0x80000000,0xfffffffe,0xffffffff):
        next_seed,random_word=original_random_step(seed)
        for pattern in ('zero','55','ramp'):
            before=bytes(0x400) if pattern=='zero' else bytes([0x55]*0x400) if pattern=='55' else bytes((i*37+11)&255 for i in range(0x400))
            native.m.mem_write(0x50000,before);native.m.mem_write(0x3483e,struct.pack('<I',seed))
            native.call(0x1000,0x9900,struct.pack('<HH',0,0x5000))
            actual=bytes(native.m.mem_read(0x50000,len(before)));actual_seed=struct.unpack('<I',native.m.mem_read(0x3483e,4))[0]
            expected=reset_original_state(before,random_word)
            if actual!=expected or actual_seed!=next_seed:raise ValueError(f'Original full reset/RNG differs seed{seed} pattern{pattern}')
            rows.append(dict(seed=seed,pattern=pattern,next_seed=actual_seed,random_word=random_word,state_sha256=hashlib.sha256(actual).hexdigest()))
    # Persist independently measured full source reset for a sentinel prior buffer.
    sample=reset_original_state(bytes([0x55]*0x400),original_random_step(1)[1])
    known={f'{offset:03x}':struct.unpack_from('<H',sample,offset)[0] for offset in (0x28,0x2a,0x30e,0x310,0x312,0x220,0x2ac,0x2b2,0x2fa,0x2fc,0x2fe,0x300,0x302,0x304,0x306,0x308,0x30a,0x318,0x334,0x344)}
    report=dict(executable_sha256=hashlib.sha256(exe).hexdigest(),cases=rows,native_cases=len(rows),mismatches=0,selected_reset_words=known,sentinel_sample_hex=sample.hex(),synthetic_far_relocations=sorted(native.relocations),scope=__doc__)
    a.report.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n');print(json.dumps(dict(cases=len(rows),mismatches=0,selected_reset_words=known)))
if __name__=='__main__':main()
