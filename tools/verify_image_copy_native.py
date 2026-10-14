#!/usr/bin/env python3
"""Check original NE1 excluded-byte copy kernels against independent small buffers.

Optional local Unicorn2.1.4 only; no Windows calls or original assets exported.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_16, __version__
from unicorn.x86_const import UC_X86_REG_CS, UC_X86_REG_DS, UC_X86_REG_ES, UC_X86_REG_SS, UC_X86_REG_SP, UC_X86_REG_IP
from yukonbmp import EXE_SHA256


def verify(executable):
    if hashlib.sha256(executable).hexdigest() != EXE_SHA256 or __version__ != '2.1.4':
        raise ValueError('unsupported executable or Unicorn version')
    machine = Uc(UC_ARCH_X86, UC_MODE_16)
    machine.mem_map(0, 0x80000)
    machine.mem_write(0x10000, executable[0x460:0x460+0x5e2])
    cases = 0
    rows = []
    for entry, reverse, unconditional in [(0x344, False, False), (0x4fc, True, False), (0x42a, False, True)]:
        for width in range(1, 10):
            for height in (1, 2, 3):
                for key in (0, 37, 255):
                    stride = width + 3
                    src = bytes([key if i % 3 == 0 else (i*17+5)%256 for i in range(stride*height)])
                    initial = bytes([203]*(stride*height))
                    expected = bytearray(initial)
                    for y in range(height):
                        for x in range(width):
                            value = src[y*stride+(width-1-x if reverse else x)]
                            if unconditional or value != key: expected[y*stride+x] = value
                    machine.mem_write(0x40000, src)
                    machine.mem_write(0x50000, initial)
                    for reg, value in [(UC_X86_REG_CS,0x1000),(UC_X86_REG_DS,0x4000),(UC_X86_REG_ES,0x5000),(UC_X86_REG_SS,0x6000),(UC_X86_REG_SP,0xf000)]: machine.reg_write(reg,value)
                    # far return, dst far pointer, src far pointer, width/height,
                    # dst stride/source stride, excluded-byte word
                    machine.mem_write(0x6f000,struct.pack('<HHHHHHIIIIH',0x600,0x1000,0,0x5000,width-1 if reverse else 0,0x4000,width,height,stride,stride,key))
                    machine.emu_start(0x10000+entry,0x10600,count=10000)
                    if machine.reg_read(UC_X86_REG_IP)!=0x600 or bytes(machine.mem_read(0x50000,len(expected)))!=expected: raise ValueError(f'kernel mismatch: {entry:x}/{width}/{height}/{key}')
                    actual = bytes(machine.mem_read(0x50000, len(expected)))
                    rows.append([entry, reverse, unconditional, width, height, key,
                                 hashlib.sha256(actual).hexdigest()])
                    cases += 1
    return {'executable_sha256':EXE_SHA256,'unicorn_version':__version__,'kernels':['NE0001:0344','NE0001:04fc','NE0001:042a'],'cases':cases,'output_matrix_rows_sha256':hashlib.sha256(json.dumps(rows,separators=(',', ':')).encode()).hexdigest(),'mismatches':0,'scope':'synthetic buffers; excluded-byte/forward/reverse and unconditional copy; source zero is copied by042a; scene dispatch verified statically, not executed'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('executable',type=Path);p.add_argument('report',type=Path);a=p.parse_args()
    result=verify(a.executable.read_bytes());a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

if __name__=='__main__':main()
