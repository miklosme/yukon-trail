#!/usr/bin/env python3
"""Compare explicitly selected source rectangles to an unscaled native capture.

Rectangles are source x,y,width,height. Selection must be documented separately;
matching a static region does not validate overlaid animation or compositing.
"""
import argparse
import hashlib
import json
from dataclasses import replace
from pathlib import Path

try:
    from .compare_bitmap_capture import read_rgb_capture
    from .yukonbmp import decode, source_palette
    from .yukonrender import windows_display_indices
    from .yukonres import read_index, verify_source, DEFAULT_SOURCE_MANIFEST
except ImportError:
    from compare_bitmap_capture import read_rgb_capture
    from yukonbmp import decode, source_palette
    from yukonrender import windows_display_indices
    from yukonres import read_index, verify_source, DEFAULT_SOURCE_MANIFEST


def compare(frame, palette, capture, origin, rectangles):
    width, height, pixels = capture
    ox, oy = origin
    positions = set()
    for x, y, w, h in rectangles:
        if not (w > 0 and h > 0 and 0 <= x <= frame.width-w and 0 <= y <= frame.height-h
                and 0 <= ox+x <= width-w and 0 <= oy+y <= height-h):
            raise ValueError('rectangle outside source or capture')
        positions.update((row, col) for row in range(y, y+h) for col in range(x, x+w))
    if not positions:
        raise ValueError('no comparison pixels')
    differences = []
    mismatch_count = 0
    for row, col in sorted(positions):
        index = frame.pixels[row*frame.width+col]
        expected = bytes(((v >> 2) << 2) | (v >> 6) for v in palette[index*3:index*3+3])
        offset = ((oy+row)*width+ox+col)*3
        actual = pixels[offset:offset+3]
        if actual != expected:
            mismatch_count += 1
            if len(differences) < 5:
                differences.append(dict(x=col, y=row, index=index, expected=list(expected), actual=list(actual)))
    return dict(compared_pixels=len(positions), mismatches=mismatch_count, examples=differences,
                origin=list(origin), source_rectangles=[list(r) for r in rectangles],
                palette_conversion='six-bit DAC, high-bit replication')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('archive', 'executable', 'capture', 'report'):
        parser.add_argument(name, type=Path)
    parser.add_argument('--id', required=True, type=int)
    parser.add_argument('--x', required=True, type=int)
    parser.add_argument('--y', required=True, type=int)
    parser.add_argument('--rect', required=True, action='append', help='source x,y,width,height')
    parser.add_argument('--windows-display-indices', action='store_true',
                        help='apply explicitly derived NE2 postdecode index normalization')
    parser.add_argument('--system-palette-zero-rgb',
                        help='explicit reference-system palette entry0 RGB, e.g.0,0,0; no alpha')
    args = parser.parse_args()
    rectangles = [tuple(map(int, r.split(','))) for r in args.rect]
    if any(len(r) != 4 for r in rectangles):
        parser.error('each rectangle requires four integers')
    palette = source_palette(args.executable.read_bytes())
    system_zero = None
    if args.system_palette_zero_rgb is not None:
        try:
            system_zero = tuple(map(int, args.system_palette_zero_rgb.split(',')))
        except ValueError:
            parser.error('system palette RGB requires three integers0..255')
        if len(system_zero) != 3 or any(not 0 <= v <= 255 for v in system_zero):
            parser.error('system palette RGB requires three integers0..255')
        palette = bytes(system_zero) + palette[3:]
    capture_bytes = args.capture.read_bytes()
    with args.archive.open('rb') as source:
        archive_hash = verify_source(source, DEFAULT_SOURCE_MANIFEST)
        resource = read_index(source).by_key()[f'CBMP:{args.id}']
        source.seek(resource.offset)
        payload = source.read(resource.length)
    frame = decode(payload)[0]
    if args.windows_display_indices:
        frame = replace(frame, pixels=windows_display_indices(frame.pixels))
    result = compare(frame, palette, read_rgb_capture(capture_bytes),
                     (args.x, args.y), rectangles)
    result.update(render_index_transform='NE0002:47c4..47dc' if args.windows_display_indices else None,
                  supplied_system_palette_zero_rgb=list(system_zero) if system_zero is not None else None,
                  system_palette_scope='Explicitly supplied runtime value; no claim about all reserved entries or independent API return capture' if system_zero is not None else None,
                  resource=resource.key, archive_offset=resource.offset, archive_length=resource.length,
                  payload_sha256=hashlib.sha256(payload).hexdigest(), archive_sha256=archive_hash,
                  capture_sha256=hashlib.sha256(capture_bytes).hexdigest())
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    print(json.dumps(result, sort_keys=True))
    if result['mismatches']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
