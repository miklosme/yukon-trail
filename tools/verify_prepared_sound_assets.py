#!/usr/bin/env python3
"""Verify selected prepared WAV files against independent original-code PCM proof."""
import argparse,hashlib,json,wave
from pathlib import Path

def verify(directory,proof):
    manifest=json.loads((directory/'manifest.json').read_text())
    for key in ('executable_sha256','archive_sha256'):
        if manifest[key]!=proof[key]:raise ValueError('Preparedsound sourceidentitydiffers')
    rows={}
    for key,native in proof['sounds'].items():
        entry=manifest['sounds'][key];name=entry['file']
        if Path(name).name!=name:raise ValueError('WAVpath must beflatlocalfilename')
        path=directory/name;file_hash=hashlib.sha256(path.read_bytes()).hexdigest()
        if file_hash!=entry['sha256'] or entry['raw_sha256']!=native['raw_sha256']:raise ValueError('PreparedWAV/source hashdiffers')
        with wave.open(str(path),'rb') as sound:
            params=(sound.getnchannels(),sound.getsampwidth(),sound.getframerate(),sound.getnframes())
            pcm=sound.readframes(sound.getnframes())
        if params!=(1,1,22050,native['sample_bytes']) or hashlib.sha256(pcm).hexdigest()!=native['native_pcm_sha256']:raise ValueError('PreparedWAV differsfromoriginalPCM oracle')
        rows[key]=dict(file=name,wav_sha256=file_hash,pcm_sha256=native['native_pcm_sha256'],samples=native['sample_bytes'])
    return dict(executable_sha256=proof['executable_sha256'],archive_sha256=proof['archive_sha256'],sound_count=len(rows),sounds=rows,mismatches=0,scope='Locallyprepared actualWAV params/PCMagainstoriginalnativevoiceoracle; no browseraudio/mixer/seek/loop/playbacktest.')
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('directory','native_proof','report'):p.add_argument(name,type=Path)
    a=p.parse_args();proof=json.loads(a.native_proof.read_text());r=verify(a.directory,proof);a.report.write_text(json.dumps(r,indent=2,sort_keys=True)+'\n');print(json.dumps(dict(sounds=r['sound_count'],mismatches=0)))
