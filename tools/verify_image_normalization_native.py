#!/usr/bin/env python3
"""Execute original NE2 postdecode byte normalization against all256 indices.

Optional local Unicorn2.1.4; bounded snippet invokes no OS functions.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from unicorn import Uc, UC_ARCH_X86, UC_MODE_16, __version__
from unicorn.x86_const import UC_X86_REG_CS, UC_X86_REG_ES, UC_X86_REG_SS, UC_X86_REG_BP, UC_X86_REG_SP, UC_X86_REG_IP
from yukonbmp import EXE_SHA256
from yukonrender import windows_display_indices


def verify(executable):
    if hashlib.sha256(executable).hexdigest()!=EXE_SHA256 or __version__!='2.1.4':raise ValueError('unsupported source or Unicorn version')
    machine=Uc(UC_ARCH_X86,UC_MODE_16);machine.mem_map(0,0x80000)
    machine.mem_write(0x10000,executable[0xf2c0:0xf2c0+0x485e])
    actual=bytearray()
    for value in range(256):
        for reg,data in [(UC_X86_REG_CS,0x1000),(UC_X86_REG_ES,0x4000),(UC_X86_REG_SS,0x6000),(UC_X86_REG_SP,0xf000),(UC_X86_REG_BP,0xf100)]:machine.reg_write(reg,data)
        machine.mem_write(0x6f0b4,struct.pack('<HH',0,0x4000));machine.mem_write(0x40000,bytes([value]))
        machine.emu_start(0x147c4,0x147dd,count=30)
        if machine.reg_read(UC_X86_REG_IP)!=0x47dd:raise ValueError('normalizer escaped bounded snippet')
        actual.extend(machine.mem_read(0x40000,1))
    derived=windows_display_indices(bytes(range(256)))
    if actual!=derived:raise ValueError('normalization mismatch')
    return {'executable_sha256':EXE_SHA256,'unicorn_version':__version__,'native_code':'NE0002:47c4..47dc; stop at47dd; file base0xf2c0','cases':256,'mismatches':0,'derived_table_sha256':hashlib.sha256(derived).hexdigest(),'scope':'individual normalization bytes; row iteration/padding and live scene pixel effects unverified'}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('executable',type=Path);p.add_argument('report',type=Path);a=p.parse_args();result=verify(a.executable.read_bytes());a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))

if __name__=='__main__':main()
