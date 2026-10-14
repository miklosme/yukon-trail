#!/usr/bin/env python3
"""Conservative source sprite census for initial partnerwordffff navigation regions.

Does not choose active conditions except the independently recovered3/1 gate.
Zero movement axes over every ASEQ step are invariant without clock assumptions.
"""
import argparse, hashlib, json, struct
from pathlib import Path
from yukonbmp import EXE_SHA256, decode
from yukonres import read_index, verify_source, DEFAULT_SOURCE_MANIFEST
from yukontransform import source_patterns, transform
from yukonsprite import read_sprite, read_cel_offsets, read_hotspots, hotspot_candidate


def inspect(archive, executable):
    exe=executable.read_bytes()
    if hashlib.sha256(exe).hexdigest()!=EXE_SHA256:raise ValueError('Source mismatch')
    patterns=source_patterns(exe);resources={};scenes={}
    evidence_path=Path(__file__).resolve().parents[1]/'docs/linda-child-recovery-evidence.json'
    eligibility=json.loads(evidence_path.read_text())
    reset_path=evidence_path.with_name('initial-state-recovery-evidence.json')
    reset=json.loads(reset_path.read_text())
    if reset['executable_sha256']!=EXE_SHA256 or reset['selected_reset_words']['312']!=65535:
        raise ValueError('Original fresh reset partner proof missing')
    native_ffff=next(c for c in eligibility['cases']if c['partner_word']==65535)
    if eligibility['executable_sha256']!=EXE_SHA256 or native_ffff['condition_outputs'][0]!=0:
        raise ValueError('Original condition(3,1) proof for ffff missing')
    with archive.open('rb')as source:
        archive_hash=verify_source(source,DEFAULT_SOURCE_MANIFEST);index=read_index(source).by_key()
        def read(key):
            r=index[key];source.seek(r.offset);raw=source.read(r.length);tag=key.split(':')[0]
            data=transform(raw,patterns[tag].opcodes)if tag in patterns else raw
            resources[key]={'offset':r.offset,'length':r.length,'raw_sha256':hashlib.sha256(raw).hexdigest(),
                            'normalized_sha256':hashlib.sha256(data).hexdigest()}
            return data
        def geometry(bitmap, animation, anchor, initial_zero_offset=False):
            frames=decode(read(f'CBMP:{bitmap}'));offsets=read_cel_offsets(read(f'ACEL:{animation}'))
            if len(frames)!=len(offsets):raise ValueError('Selected frame/offset count differs')
            data=read(f'ASEQ:{animation}');count=struct.unpack_from('<H',data)[0];tail=2+8*count
            steps_count=struct.unpack_from('<H',data,tail)[0]
            if len(data)!=tail+2+steps_count*12:raise ValueError('ASEQ physical count mismatch')
            steps=[struct.unpack_from('<HhhHHH',data,tail+2+i*12)for i in range(steps_count)]
            rectangles=[[anchor[1]-oy,anchor[0]-ox,anchor[1]-oy+f.height,anchor[0]-ox+f.width]
                        for f,(ox,oy)in zip(frames,offsets)]
            if initial_zero_offset:
                rectangles.append([anchor[1],anchor[0],anchor[1]+frames[0].height,anchor[0]+frames[0].width])
            return {'bitmap_id':bitmap,'animation_id':animation,'anchor_xy':list(anchor),
                    'frame_rectangles_tlbr':rectangles,'zero_horizontal_motion':all(s[1]==0 for s in steps),
                    'zero_vertical_motion':all(s[2]==0 for s in steps),
                    'flip_toggle_present':any(s[5]!=0 for s in steps),
                    'scope':'All frames and all physically stored step movement vectors; no successor/range/schedule interpretation'}
        for sid in (1000,2000,3000,4000):
            fields=struct.unpack('<5H',read(f'SCNE:{sid}'));data=read(f'SCRP:{fields[3]}');count=struct.unpack_from('<H',data)[0]
            if len(data)!=2+18*count:raise ValueError('SCRP record count mismatch')
            entries=[]
            for ordinal in range(count):
                words=struct.unpack_from('<9H',data,2+18*ordinal)
                if words[0]!=3:raise ValueError('Non-SPRT selected controller child requires separate bounds recovery')
                sprite=read_sprite(read(f'SPRT:{words[1]}'))
                entry={'ordinal':ordinal,'sprite_id':words[1],'condition_pairs':[list(words[i:i+2])for i in (3,5,7)],
                       'excluded_for_partner_ffff':[3,1]in[list(words[i:i+2])for i in (3,5,7)],
                       'geometry':geometry(sprite.bitmap_id,sprite.animation_id,(sprite.anchor_x,sprite.anchor_y))}
                entries.append(entry)
            scenes[str(sid)]={'scne_words':list(fields),'hotspot_id':fields[2],'controller_id':fields[3],'entries':entries,'hotspots':[list(struct.unpack_from('<hhhhHHI',read(f'HSPT:{fields[2]}'),2+i*16)) for i in range(struct.unpack_from('<H',read(f'HSPT:{fields[2]}'))[0])]}
        globals_=[{'object_id':rid,'constructor':ctor,'geometry':geometry(rid,rid,anchor,True)}
                  for rid,ctor,anchor in [(37500,'NE3:5e22',(110,100)),(37501,'NE3:5f04',(80,122))]]
    clear=[{'source_scene':4000,'destination_scene':1000,'open_rectangle_lrtb':[489,600,313,371],'example_client_xy':[580,350]},
           {'source_scene':1000,'destination_scene':4000,'open_rectangle_lrtb':[149,188,150,178],'example_client_xy':[153,160]},
           {'source_scene':1000,'destination_scene':2000,'open_rectangle_lrtb':[500,595,150,191],'example_client_xy':[550,175]},
           {'source_scene':1000,'destination_scene':3000,'open_rectangle_lrtb':[59,84,187,191],'example_client_xy':[70,189]},
           {'source_scene':2000,'destination_scene':1000,'open_rectangle_lrtb':[415,520,110,180],'example_client_xy':[500,150]},
           {'source_scene':3000,'destination_scene':1000,'open_rectangle_lrtb':[149,170,187,223],'example_client_xy':[160,200]}]
    # Prove each region lies outside every potentially admitted sprite on at least
    # one zero-motion axis. Bounding inclusive edges means regions stay open.
    for region in clear:
        left,right,top,bottom=region['open_rectangle_lrtb']
        rows=scenes[str(region['source_scene'])]['hotspots']
        records=read_hotspots(struct.pack('<H',len(rows))+b''.join(struct.pack('<hhhhHHI',*r)for r in rows))
        checked=0
        for y in range(top+1,bottom):
            for x in range(left+1,right):
                ordinal=hotspot_candidate(records,x,y)
                if ordinal is None or rows[ordinal][4:] != [1,200,region['destination_scene']]:
                    raise ValueError('Region does not select source navigation action')
                checked+=1
        region['integer_points_with_selected_source_action']=checked
        potential=[e['geometry']for e in scenes[str(region['source_scene'])]['entries']if not e['excluded_for_partner_ffff']]
        potential.extend(g['geometry']for g in globals_)
        for g in potential:
            boxes=g['frame_rectangles_tlbr']
            separated_x=g['zero_horizontal_motion']and(right<=min(b[1]for b in boxes)or left>=max(b[3]for b in boxes))
            separated_y=g['zero_vertical_motion']and(bottom<=min(b[0]for b in boxes)or top>=max(b[2]for b in boxes))
            if not(separated_x or separated_y):raise ValueError(f'Unknown/intersecting sprite in clear region {region}, {g}')
    return {'executable_sha256':EXE_SHA256,'archive_sha256':archive_hash,'resources':resources,'scenes':scenes,
            'global_scene_sprites':globals_,'clear_navigation_regions':clear,
            'fresh_reset_native_evidence':{'path':'docs/initial-state-recovery-evidence.json','sha256':hashlib.sha256(reset_path.read_bytes()).hexdigest(),'state_word_offset':0x312,'original_value':65535},
            'partner_condition_native_evidence':{'path':'docs/linda-child-recovery-evidence.json','sha256':hashlib.sha256(evidence_path.read_bytes()).hexdigest(),'partner_word':65535,'condition':[3,1],'original_result':native_ffff['condition_outputs'][0],'original_function':'NE3:5118 calling NE1:a632'},
            'state_scope':'Partnerwordffff, all controller conditions otherwise conservatively included; actual source sprite contexts, no dialogue/journal/modal overlays or shifted anchors. Source-handler-specific activation/busy/countdown/deferred-action handling remains outside this geometric census.',
            'global_animation_wrappers':[{'ne_address':a,'ghidra_address':g,'file_offset':0x44fc0+o,'raw_sha256':hashlib.sha256(exe[0x44fc0+o:0x44fc0+o+25]).hexdigest(),'length':25,'observed':'Checks object+8a; calls NE2:d61e; no separate anchor mutation'}for a,g,o in [('NE6:7b0a','1028:7b0a',0x7b0a),('NE6:7b24','1028:7b24',0x7b24)]],
            'source':'NE2:0002 loads SCNE+4 HSPT,+6SCRP; NE3:2394 creates kind3SPRT; NE3:274a sets anchor/ACEL0; NE2:d61e applies ASEQ step dx/dy. Global constructors5e22/5f04 anchor and zero-offset initial frame included.',
            'scope':'Axis-disjoint conservative regions only; does not infer actual sprite visibility/frame/timing or prove whole scene/sprite order.'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('archive','executable','report'):p.add_argument(n,type=Path)
    a=p.parse_args();r=inspect(a.archive,a.executable);a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'scenes':len(r['scenes']),'clear_regions':len(r['clear_navigation_regions'])}))
