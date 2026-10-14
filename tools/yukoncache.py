"""Derived original cached CBMP layout; lossless visible decoder stays separate.

Positive selected frames only. Source wrapper rounds both dimensions to8,
zero-clears full allocation, writes all8 columns but only logical-height rows,
then normalizes height*stride indexed bytes (NE2:464e).
"""
from dataclasses import dataclass
import struct
try:
    from .yukonbmp import BitmapError, unpack
    from .yukonrender import windows_display_indices
except ImportError:
    from yukonbmp import BitmapError, unpack
    from yukonrender import windows_display_indices

@dataclass(frozen=True)
class CachedFrame:
    width: int
    height: int
    stride: int
    allocated_height: int
    pixels: bytes
    offset: int
    length: int

def decode_cached_frames(data):
    if len(data)<2:raise BitmapError('Truncated cached frame table')
    count=struct.unpack_from('<H',data)[0]
    if not count or len(data)<2+12*count:raise BitmapError('Invalid cached frame count')
    frames=[]
    for i in range(count):
        w,h,off,length=struct.unpack_from('<HHII',data,2+i*12)
        if not 0<w<32768 or not 0<h<32768:raise BitmapError('Only positive cached frame dimensions supported')
        if off<2+12*count or off>len(data) or length>len(data)-off:raise BitmapError('Cached frame outside resource')
        stride=(w+7)&~7;ah=(h+7)&~7;cols=stride//8;rows=ah//8
        blocks=unpack(data[off:off+length],cols*rows*64)
        out=bytearray(stride*ah)
        for tile in range(cols*rows):
            x,y=tile//rows*8,tile%rows*8
            for dy in range(min(8,h-y)):
                start=(y+dy)*stride+x;src=tile*64+dy*8
                out[start:start+8]=blocks[src:src+8]
        out[:h*stride]=windows_display_indices(bytes(out[:h*stride]))
        frames.append(CachedFrame(w,h,stride,ah,bytes(out),off,length))
    return tuple(frames)
