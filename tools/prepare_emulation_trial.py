#!/usr/bin/env python3
"""Stage a frozen, source-verified browser-emulation trial without executing it.

Native reference guest and ISO are read-only inputs. No browser access, emulator
launch, architecture switch, public distribution or license decision is implied.
"""
import argparse,hashlib,json,shutil,tarfile,tempfile,zipfile
from pathlib import Path,PurePosixPath

ROOT=Path(__file__).resolve().parents[1]
BASELINE_SHA='86a7b6ffcbd0e09353b4a6a29efefa54a084c2ce479a17add7724e288019e6dd'
ISO_SHA='89f8eb97bd7d3afdbabbd05dce10854673eff5c5617825940994aba7a0360ed8'
EXE_SHA='9ca8f0a12f4798e762fbf27634f99afcb5c0c1a3836604bf0a4049a73227dd06'
FONT_SHA='6a2c8f3356a9affef9711a14070b5de1cac95c320799360d10c78d8df40f4f18'

CONFIG='''[sdl]
autolock=false
showmenu=false
mouse emulation=integration
[dosbox]
title=The Yukon Trail
machine=svga_s3
memsize=16
[cpu]
core=normal
cputype=pentium
cycles=fixed 20000
integration device=true
[sblaster]
sbtype=sb16
sbbase=220
irq=7
dma=1
hdma=5
[midi]
mididevice=none
[autoexec]
@ECHO OFF
MOUNT C /home/web_user/c
IMGMOUNT D /home/web_user/YUKONCD.ISO -t iso
C:
SET BLASTER=A220 I7 D1 H5 P330 T6
SET SOUND=C:\\SB16
SET MIDI=SYNTH:1 MAP:E
C:\\SB16\\DIAGNOSE /S
C:\\SB16\\MIXERSET /P /Q
SET PATH=%PATH%;C:\\WINDOWS
SET TEMP=C:\\WINDOWS\\TEMP
CD \\WINDOWS
WIN C:\\MECC\\YUKON\\YUKON.EXE
'''

def digest(path):
    h=hashlib.sha256()
    with path.open('rb')as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def safe_member(member):
    path=PurePosixPath(member.name)
    if path.is_absolute() or '..' in path.parts or '\\' in member.name or ':' in member.name:
        raise ValueError('Unsafe baseline member path')
    if not member.isdir() and not member.isfile():raise ValueError('Unsupported baseline member type')
    return path.as_posix().removeprefix('./')

def frozen_guest(baseline,output,expected_sha=BASELINE_SHA):
    if digest(baseline)!=expected_sha:raise ValueError('Frozen guest baseline identity mismatch')
    rows=[];omitted=[];seen=set();critical={}
    with tarfile.open(baseline,'r:gz')as source,zipfile.ZipFile(output,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6)as target:
        for member in source:
            name=safe_member(member)
            if name=='.':continue
            if name.casefold() in seen:raise ValueError('Duplicate DOS baseline member')
            seen.add(name.casefold())
            data=source.extractfile(member).read() if member.isfile() else b''
            row={'source_member':member.name,'path':'c/'+name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'kind':'file'if member.isfile()else'directory'}
            if any(part.startswith('._')for part in PurePosixPath(name).parts):
                if not member.isfile() or data[:4]!=bytes.fromhex('00051607'):
                    raise ValueError('Unrecognized AppleDouble metadata member')
                omitted.append(row);continue
            # Canonical ZIP timestamps/order avoid depending on host metadata.
            info=zipfile.ZipInfo('c/'+name+('/'if member.isdir()else''),(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=((0o40755 if member.isdir() else 0o100644)<<16)|(0x10 if member.isdir() else 0)
            target.writestr(info,data);rows.append(row)
            if name.upper()in('MECC/YUKON/YUKON.EXE','WINDOWS/SYSTEM/YUF_____.TTF'):critical[name.upper()]=row['sha256']
        info=zipfile.ZipInfo('.jsdos/dosbox.conf',(1980,1,1,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;target.writestr(info,CONFIG.encode('ascii'))
    return rows,omitted,critical

def prepare(baseline,iso,vendor,output,evidence):
    if output.exists():raise FileExistsError('Fresh trial directory required')
    if digest(baseline)!=BASELINE_SHA or digest(iso)!=ISO_SHA:raise ValueError('Source baseline/ISO identity mismatch')
    files=evidence['deployment_files']
    for name in ('emulators.js','wdosbox-x.js','wdosbox-x.wasm'):
        if digest(vendor/name)!=files[name]['sha256'] or (vendor/name).stat().st_size!=files[name]['bytes']:
            raise ValueError('Pinned emulator artifact mismatch: '+name)
    output.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='yukon-trial-',dir=output.parent)as temporary:
        stage=Path(temporary);guest=stage/'guest.zip';rows,omitted,critical=frozen_guest(baseline,guest)
        if critical.get('MECC/YUKON/YUKON.EXE')!=EXE_SHA or critical.get('WINDOWS/SYSTEM/YUF_____.TTF')!=FONT_SHA:
            raise ValueError('Installed executable/font differ from source')
        shutil.copyfile(iso,stage/'YUKONCD.ISO')
        if digest(stage/'YUKONCD.ISO')!=ISO_SHA:raise ValueError('Staged ISO copy changed')
        (stage/'vendor').mkdir()
        staged={}
        for name in ('emulators.js','wdosbox-x.js','wdosbox-x.wasm'):
            shutil.copyfile(vendor/name,stage/'vendor'/name);staged[name]={'file':'vendor/'+name,'sha256':digest(stage/'vendor'/name),'bytes':(stage/'vendor'/name).stat().st_size}
        config_bytes=CONFIG.encode('ascii')
        manifest={'schema':'yukon-emulation-trial-v1','scope':__doc__,'vendor':{'version':'8.5.2','declared_license':evidence['package']['declared_vendor_license'],'files':staged},'baseline':{'path':str(baseline),'sha256':BASELINE_SHA,'bytes':baseline.stat().st_size},'iso':{'file':'YUKONCD.ISO','source':str(iso),'sha256':ISO_SHA,'bytes':iso.stat().st_size},'guest':{'file':'guest.zip','sha256':digest(guest),'bytes':guest.stat().st_size,'files':rows,'omitted_appledouble_metadata':omitted},'config':{'sha256':hashlib.sha256(config_bytes).hexdigest(),'text':CONFIG,'adaptations':['Virtual mount paths replace host paths','DOSBox menu hidden; low-level backend supplies no vendor toolbar','WIN command requests direct original executable launch; unverified']},'unverified':['Guest launch and WIN command','Mouse integration/frame/sound compatibility','Performance and peak memory','Game save close/extraction/restoration and filesystem deletion','Supported browsers and offline requests']}
        (stage/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        stage.rename(output)
    return manifest

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('baseline','iso','vendor','output'):p.add_argument(name,type=Path)
    p.add_argument('--vendor-evidence',type=Path,default=ROOT/'docs/browser-emulation-source-evidence.json');a=p.parse_args()
    result=prepare(a.baseline,a.iso,a.vendor,a.output,json.loads(a.vendor_evidence.read_text()))
    print(json.dumps({'output':str(a.output),'guest_members':len(result['guest']['files']),'omitted_metadata':len(result['guest']['omitted_appledouble_metadata']),'guest_zip_bytes':result['guest']['bytes'],'iso_bytes':result['iso']['bytes']}))
