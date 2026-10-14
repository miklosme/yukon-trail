#!/usr/bin/env python3
"""Prepare the current bounded opening with the original-oracle Seattle voice set.

No game behavior, scene population or source media distribution is inferred.
All sounds must match the original converter evidence before any output is made.
"""
import argparse,json
from pathlib import Path
from prepare_browser_assets import prepare
from prepare_seattle_population import source_data as population_source_data
ROOT=Path(__file__).resolve().parents[1]
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('archive','executable','font','output'):p.add_argument(name,type=Path)
    p.add_argument('--voice-evidence',type=Path,default=ROOT/'docs/seattle-sound-set-recovery-evidence.json')
    p.add_argument('--journal-status',action='store_true',help='Include the recovered full status and inventory vocabulary')
    p.add_argument('--seattle-population',action='store_true',help='Include bounded initial actor fields and all source-required bitmaps')
    a=p.parse_args();evidence=json.loads(a.voice_evidence.read_text())
    trees=[int(key.split(':')[1])for key in evidence['trees']]
    sounds=[int(key.split(':')[1])for key in evidence['sounds']]
    bitmap_ids=[1,2,400,403,4001,1000,2000,3000,4000,37000,37001]
    if a.seattle_population:bitmap_ids+=list(population_source_data(a.archive,a.executable)['bitmaps'])
    result=prepare(a.archive,a.executable,a.font,a.output,bitmap_ids,(0,0,0),trees,sounds,True,sound_evidence=evidence,journal_status=a.journal_status,seattle_population=a.seattle_population)
    print(json.dumps(dict(output=str(a.output),bitmaps=len(result['resources']),trees=len(result['trees']),voices=len(result['sounds']),sample_bytes=sum(row['samples']for row in result['sounds'].values()))))
