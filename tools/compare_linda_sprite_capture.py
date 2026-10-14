#!/usr/bin/env python3
"""Compare source-predicted SPRT403 after explicit completion of ASEQ400 sequence5.

No alignment search. Checks every visible nonzero frame pixel; transparent
exterior/underlying scene, clock, other actors and whole scene are excluded.
"""
import argparse, hashlib, json
from pathlib import Path
from yukonbmp import decode, source_palette
from yukonres import read_index, verify_source, DEFAULT_SOURCE_MANIFEST
from yukontransform import source_patterns, transform
from yukonrender import windows_display_indices
from yukonsprite import read_sprite, read_cel_offsets, read_animation, completed_sequence_anchor
from compare_bitmap_capture import read_rgb_capture


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('archive','executable','capture','report'):p.add_argument(name,type=Path)
    p.add_argument('--scene-x',type=int,required=True);p.add_argument('--scene-y',type=int,required=True)
    a=p.parse_args();exe=a.executable.read_bytes();palette=source_palette(exe);patterns=source_patterns(exe);provenance={}
    with a.archive.open('rb') as source:
        archive_hash=verify_source(source,DEFAULT_SOURCE_MANIFEST);index=read_index(source).by_key()
        def read(key):
            r=index[key];source.seek(r.offset);raw=source.read(r.length);tag=key.split(':')[0];data=transform(raw,patterns[tag].opcodes if tag in patterns else None);provenance[key]={'offset':r.offset,'length':r.length,'raw_sha256':hashlib.sha256(raw).hexdigest()};return data
        sprite=read_sprite(read('SPRT:403'));animation=read_animation(read('ASEQ:400'));offsets=read_cel_offsets(read('ACEL:400'));frames=decode(read('CBMP:400'))
    if (sprite.bitmap_id,sprite.animation_id)!=(400,400) or sprite.schedules[0][0]!=5:raise ValueError('selected sprite linkage changed')
    start,successor,duration,count=animation.sequences[5];frame_id=animation.steps[start+count-1][0]
    anchor_x,anchor_y=completed_sequence_anchor(sprite,animation,5);offset_x,offset_y=offsets[frame_id];frame=frames[frame_id]
    ox,oy=a.scene_x+anchor_x-offset_x,a.scene_y+anchor_y-offset_y
    capture=a.capture.read_bytes();width,height,rgb=read_rgb_capture(capture)
    left,top,right,bottom=a.scene_x,a.scene_y,a.scene_x+600,a.scene_y+400
    if not(0<=left<right<=width and 0<=top<bottom<=height):raise ValueError('selected viewport outside capture')
    pixels=windows_display_indices(frame.pixels);compared=mismatches=zero=clipped=0;examples=[]
    for y in range(frame.height):
        for x in range(frame.width):
            i=pixels[y*frame.width+x]
            if not(left<=ox+x<right and top<=oy+y<bottom):clipped+=1;continue
            if not i:zero+=1;continue
            expected=bytes(((v>>2)<<2)|(v>>6)for v in palette[i*3:i*3+3]);at=((oy+y)*width+ox+x)*3;actual=rgb[at:at+3];compared+=1
            if expected!=actual:
                mismatches+=1
                if len(examples)<5:examples.append({'source_xy':[x,y],'index':i,'expected_rgb':list(expected),'actual_rgb':list(actual)})
    report={'archive_sha256':archive_hash,'executable_sha256':hashlib.sha256(exe).hexdigest(),'capture_sha256':hashlib.sha256(capture).hexdigest(),'resources':provenance,'sprite_id':403,'sequence':5,'bitmap_id':400,'frame':frame_id,'frame_size_wh':[frame.width,frame.height],'completed_anchor_xy':[anchor_x,anchor_y],'source_cel_offset_xy':[offset_x,offset_y],'scene_origin_xy':[a.scene_x,a.scene_y],'predicted_capture_origin_xy':[ox,oy],'clip_viewport_ltrb':[left,top,right,bottom],'compared_pixels':compared,'mismatches':mismatches,'excluded_zero_pixels':zero,'clipped_pixels':clipped,'examples':examples,'palette_conversion':'explicit native-checked index normalization and six-bit DAC high-bit replication','scope':'all visible nonzero pixels of predicted frame1 aftersequence5; no automatic alignment; transparent underlay, timer, alternate states/actors and whole scene excluded'}
    a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
    if mismatches:raise SystemExit(1)

if __name__=='__main__':main()
