#!/usr/bin/env python3
"""Compare selected original journal art at source-derived positions; no search.

Includes an unobscured background rectangle and three explicitly selected
inventory frames. Does not infer state visibility, compare text or full scene.
"""
import argparse, hashlib, json, struct
from pathlib import Path
try:
    from .yukonbmp import decode, source_palette, EXE_SHA256, Frame
    from .yukonrender import windows_display_indices
    from .yukonres import read_index, verify_source, DEFAULT_SOURCE_MANIFEST
    from .compare_bitmap_capture import read_rgb_capture
except ImportError:
    from yukonbmp import decode, source_palette, EXE_SHA256, Frame
    from yukonrender import windows_display_indices
    from yukonres import read_index, verify_source, DEFAULT_SOURCE_MANIFEST
    from compare_bitmap_capture import read_rgb_capture


def journal_layout(exe):
    if hashlib.sha256(exe).hexdigest() != EXE_SHA256:
        raise ValueError('Executable source mismatch')
    # Observed constructor NE1:aea4/b032 and consumer bb4c: sixteen 10-byte entries.
    entries = [struct.unpack_from('<5h', exe, 0x4f420 + 0xdf4 + i*10) for i in range(16)]
    # NE13:4e32 segment relocation selects NE9; constructor reads NE9:0000 XYWH.
    ne = struct.unpack_from('<I', exe, 0x3c)[0]
    segment_table = ne + struct.unpack_from('<H', exe, ne+0x22)[0]
    shift = struct.unpack_from('<H', exe, ne+0x32)[0]
    segment9 = struct.unpack_from('<H', exe, segment_table+8*8)[0] << shift
    if segment9 != 0x4f3e0:
        raise ValueError('Selected NE9 mapping changed')
    edit = struct.unpack_from('<4h', exe, segment9)
    selected = {}
    for frame in (10, 6, 11):
        hits = [(n, r) for n, r in enumerate(entries) if r[2] == frame]
        if len(hits) != 1:
            raise ValueError('Selected journal frame mapping is not unique')
        ordinal, (state, comparison, _, y, x) = hits[0]
        selected[frame] = {'ordinal': ordinal, 'state_index': state,
                           'state_compare': comparison, 'anchor_xy': [x, y]}
    return {'edit_xywh': list(edit), 'selected_inventory': selected}


def compare_pixels(frame, palette, capture, origin, rectangles, clip, zero_key):
    """Compare a union of source rectangles; clipping precedes optional zero key."""
    width, height, rgb = capture
    if len(palette) != 768 or len(rgb) != width*height*3 or len(frame.pixels) != frame.width*frame.height:
        raise ValueError('Pixel/palette dimensions mismatch')
    if len(origin) != 2 or len(clip) != 4 or any(not isinstance(n,int) for n in (*origin,*clip)):
        raise ValueError('Integer origin/clip required')
    left, top, right, bottom = clip
    if not 0 <= left < right <= width or not 0 <= top < bottom <= height:
        raise ValueError('Clip outside capture')
    if not rectangles:
        raise ValueError('Explicit source rectangles required')
    points = set()
    for x,y,w,h in rectangles:
        if any(not isinstance(n,int) for n in (x,y,w,h)) or w<=0 or h<=0 or not 0<=x<x+w<=frame.width or not 0<=y<y+h<=frame.height:
            raise ValueError('Source rectangle outside frame')
        points.update((sx,sy) for sy in range(y,y+h) for sx in range(x,x+w))
    compared = mismatches = excluded_zero = excluded_clip = 0
    examples = []
    for sx,sy in sorted(points, key=lambda p:(p[1],p[0])):
        x,y = origin[0]+sx,origin[1]+sy
        if not (left<=x<right and top<=y<bottom):
            excluded_clip += 1
            continue
        index = frame.pixels[sy*frame.width+sx]
        if zero_key and index == 0:
            excluded_zero += 1
            continue
        expected = bytes(((v>>2)<<2)|(v>>6) for v in palette[index*3:index*3+3])
        at = (y*width+x)*3
        actual = rgb[at:at+3]
        compared += 1
        if expected != actual:
            mismatches += 1
            if len(examples)<5:
                examples.append({'source_xy':[sx,sy], 'native_xy':[x,y], 'index':index,
                                 'expected_rgb':list(expected), 'actual_rgb':list(actual)})
    if compared == 0:
        raise ValueError('Selected region has no compared pixels')
    return {'source_rectangles':[list(r) for r in rectangles], 'native_origin_xy':list(origin),
            'clip_ltrb':list(clip), 'zero_key':zero_key, 'candidate_pixels':len(points),
            'compared_pixels':compared, 'mismatches':mismatches, 'excluded_zero_pixels':excluded_zero,
            'excluded_clip_pixels':excluded_clip, 'examples':examples}


def compare(archive, executable, capture_path, scene_origin, system_zero):
    exe = executable.read_bytes(); layout = journal_layout(exe)
    palette = source_palette(exe)
    if len(system_zero)!=3 or any(not isinstance(n,int) or not 0<=n<=255 for n in system_zero):
        raise ValueError('Explicit palette index0 RGB required')
    palette = bytes(system_zero)+palette[3:]
    capture_bytes = capture_path.read_bytes(); capture = read_rgb_capture(capture_bytes)
    sx,sy = scene_origin
    viewport = [sx,sy,sx+600,sy+400]
    resources = {}; frames = {}
    with archive.open('rb') as source:
        archive_hash = verify_source(source,DEFAULT_SOURCE_MANIFEST); index = read_index(source).by_key()
        for key in ('CBMP:37000','CBMP:37001'):
            r=index[key];source.seek(r.offset);raw=source.read(r.length)
            frames[key] = decode(raw)
            resources[key]={'offset':r.offset,'length':r.length,'raw_sha256':hashlib.sha256(raw).hexdigest()}
    def display(frame):
        return Frame(frame.width,frame.height,frame.offset,frame.length,
                     windows_display_indices(frame.pixels))
    cloth = compare_pixels(display(frames['CBMP:37000'][0]),palette,capture,(sx,sy),
                           [(400,0,190,200)],viewport,False)
    cloth['resource']='CBMP:37000';cloth['frame']=0
    cloth['source_indices_sha256']=hashlib.sha256(frames['CBMP:37000'][0].pixels).hexdigest()
    cloth['display_indices_sha256']=hashlib.sha256(windows_display_indices(frames['CBMP:37000'][0].pixels)).hexdigest()
    cloth['scope']='Fixed unobscured cloth rectangle; background index0 is copied, not excluded'
    edit_x,edit_y,edit_w,edit_h = layout['edit_xywh']
    pane = [sx+edit_x+edit_w,sy,sx+600,sy+400]
    items=[]
    for frame_id in (10,6,11):
        entry=layout['selected_inventory'][frame_id];frame=frames['CBMP:37001'][frame_id]
        ox,oy=sx+entry['anchor_xy'][0],sy+entry['anchor_xy'][1]
        clip=pane.copy()
        if frame_id==6:
            # Conservative exclusion at the overlapping frame11's source-derived top.
            # Does not assert that every lower pixel is actually covered by opaque art.
            clip[3]=sy+layout['selected_inventory'][11]['anchor_xy'][1]
        result=compare_pixels(display(frame),palette,capture,(ox,oy),[(0,0,frame.width,frame.height)],clip,True)
        result.update(resource='CBMP:37001',frame=frame_id,frame_size_wh=[frame.width,frame.height],
                      source_entry=entry,source_indices_sha256=hashlib.sha256(frame.pixels).hexdigest(),
                      display_indices_sha256=hashlib.sha256(windows_display_indices(frame.pixels)).hexdigest(),scope='Explicit selected frame; zero key and edit/viewport excluded'+
                      ('; entire region at/below frame11 top conservatively excluded' if frame_id==6 else ''))
        items.append(result)
    return {'archive_sha256':archive_hash,'executable_sha256':EXE_SHA256,
            'capture_sha256':hashlib.sha256(capture_bytes).hexdigest(),'capture_size_wh':list(capture[:2]),
            'scene_origin_xy':list(scene_origin),'layout':layout,'resources':resources,'cloth':cloth,'inventory':items,
            'compared_pixels':cloth['compared_pixels']+sum(r['compared_pixels'] for r in items),
            'mismatches':cloth['mismatches']+sum(r['mismatches'] for r in items),
            'render_index_transform':'NE2:47c4..47dc','palette_conversion':'six-bit DAC high-bit replication',
            'supplied_system_palette_zero_rgb':list(system_zero),
            'system_palette_scope':'Explicit supplied reference value; not an API return capture',
            'layout_source':'NE1:aea4/b032..b060/bb4c; NE13:0df4, NE13:4e32 selector relocation -> NE9:0000',
            'scope':'No alignment search; selected cloth and visible nonzero inventory only. Text, native controls, underlay, lower guide overlap, visibility conditions and full-scene composite excluded.'}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('archive','executable','capture','report'):p.add_argument(name,type=Path)
    p.add_argument('--scene-x',type=int,required=True);p.add_argument('--scene-y',type=int,required=True)
    p.add_argument('--system-palette-zero-rgb',required=True)
    a=p.parse_args();zero=tuple(int(v) for v in a.system_palette_zero_rgb.split(','))
    report=compare(a.archive,a.executable,a.capture,(a.scene_x,a.scene_y),zero)
    a.report.parent.mkdir(parents=True,exist_ok=True);a.report.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'compared_pixels':report['compared_pixels'],'mismatches':report['mismatches'],
                      'inventory':[(r['frame'],r['compared_pixels'],r['mismatches']) for r in report['inventory']]}))
    if report['mismatches']: raise SystemExit(1)

if __name__=='__main__':main()
