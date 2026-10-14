"""Original NE1:9900 raw-state reset and NE6:2a28 controlled random step.

Reset preserves bytes not written by the original; it does not allocate a
zeroed state or provide a wall-clock/random seed default. Scene entry is separate.
"""
import struct

class InitialStateError(ValueError):
    pass


def original_random_step(seed):
    if not isinstance(seed,int) or not 0 <= seed <= 0xffffffff:
        raise InitialStateError('Explicit original unsigned32 random seed required')
    next_seed=(seed*214013+2531011)&0xffffffff
    return next_seed,(next_seed>>16)&0x7fff


def reset_original_state(previous_bytes, random_word):
    if not isinstance(previous_bytes,bytes) or len(previous_bytes)<0x386:
        raise InitialStateError('Explicit original state buffer of at least386hex bytes required')
    if not isinstance(random_word,int) or not 0 <= random_word <= 32767:
        raise InitialStateError('Explicit original random output0..32767 required')
    result=bytearray(previous_bytes)
    result[0]=result[0x14]=0
    def word(offset,value=0):struct.pack_into('<H',result,offset,value)
    def dword(offset,value=0):struct.pack_into('<I',result,offset,value)
    word(0x312,65535);word(0x2a,8);word(0x28,23)
    dword(0x2c);dword(0x30);word(0x31a);dword(0x30e,0x10001)
    for offset in (0x36,0x38,0x31c,0x31e,0x30c,0x318,0x322):word(offset)
    for start,count in ((0x2fa,9),(0x1dc,30),(0x218,61),(0x292,8),(0x2aa,40),(0x42,50),(0xa6,4),(0xae,120),(0x19e,31)):
        for i in range(count):word(start+2*i)
    word(0x2fa,350);word(0x2fc)
    pair=random_word%3
    word(0x314,7+pair);word(0x316,10+pair)
    dword(0x3a)
    for offset in (0x320,0x324,0x326,0x328,0x32a,0x32c,0x330,0x332,0x334,0x336,0x338,0x33a,0x33c,0x33e,0x340,0x32e,0x342,0x384,0x346):word(offset)
    result[0x348:0x370]=bytes(0x28)
    dword(0x370)
    for offset in (0x376,0x378,0x37a,0x374,0x382,0x37c,0x37e,0x40,0x380,0x344):word(offset)
    return bytes(result)
