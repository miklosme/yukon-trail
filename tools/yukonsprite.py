"""Bounded normalized SPRT/ACEL/ASEQ and HSPT fields; no general scene engine.

Consumer/source evidence: docs/SEATTLE-SPRITES.md. Inputs are postread buffers,
not raw big-endian resources. Unknown header/action words are preserved.
"""
from dataclasses import dataclass
import struct

class SpriteError(ValueError):
    pass

@dataclass(frozen=True)
class Sprite:
    bitmap_id: int
    animation_id: int
    anchor_x: int
    anchor_y: int
    initial_sequence: int
    click_sequence: int
    schedules: tuple[tuple[int, int, int, int], ...]
    raw_header: bytes

@dataclass(frozen=True)
class Animation:
    # start-step, successor-sequence, default-duration, step-count
    sequences: tuple[tuple[int, int, int, int], ...]
    # bitmap-frame, delta-x, delta-y, unknown-word, duration-override, flip-toggle
    steps: tuple[tuple[int, int, int, int, int, int], ...]

@dataclass(frozen=True)
class Hotspot:
    left: int
    right: int
    top: int
    bottom: int
    action_word0: int
    action_word1: int
    action_dword: int

    @property
    def sentinel(self):
        return (self.left, self.right, self.top, self.bottom) == (0, 0, 0, 0)


def read_sprite(data):
    if len(data) < 38:
        raise SpriteError('truncated SPRT header')
    count = struct.unpack_from('<H', data, 36)[0]
    if len(data) != 38 + count*8:
        raise SpriteError('SPRT schedule count/length mismatch')
    bitmap, animation, x, y = struct.unpack_from('<HHhh', data)
    initial = struct.unpack_from('<h', data, 16)[0]
    click = struct.unpack_from('<h', data, 30)[0]
    schedules = tuple(struct.unpack_from('<4h', data, 38+n*8) for n in range(count))
    return Sprite(bitmap, animation, x, y, initial, click, schedules, data[:38])


def read_cel_offsets(data):
    if len(data) < 2:
        raise SpriteError('truncated ACEL count')
    count = struct.unpack_from('<H', data)[0]
    if len(data) != 2+4*count:
        raise SpriteError('ACEL count/length mismatch')
    return tuple(struct.unpack_from('<hh', data, 2+n*4) for n in range(count))


def read_animation(data):
    if len(data) < 4:
        raise SpriteError('truncated ASEQ counts')
    count = struct.unpack_from('<H', data)[0]
    tail = 2+8*count
    if tail+2 > len(data):
        raise SpriteError('truncated ASEQ sequence table')
    step_count = struct.unpack_from('<H', data, tail)[0]
    if len(data) != tail+2+12*step_count:
        raise SpriteError('ASEQ step count/length mismatch')
    sequences = tuple(struct.unpack_from('<HhHH', data, 2+n*8) for n in range(count))
    steps = tuple(struct.unpack_from('<HhhHHH', data, tail+2+n*12) for n in range(step_count))
    for start, successor, duration, length in sequences:
        if start+length > len(steps) or not -1 <= successor < len(sequences):
            raise SpriteError('ASEQ sequence range unsupported/outside table')
    return Animation(sequences, steps)


def read_hotspots(data):
    if len(data) < 2:
        raise SpriteError('truncated HSPT count')
    count = struct.unpack_from('<H', data)[0]
    if len(data) != 2+16*count:
        raise SpriteError('HSPT count/length mismatch')
    result = tuple(Hotspot(*struct.unpack_from('<hhhhHHI', data, 2+n*16)) for n in range(count))
    if not any(r.sentinel for r in result):
        raise SpriteError('selected HSPT fallback requires a zero-rectangle sentinel')
    return result


def hotspot_candidate(records, x, y):
    """Selected NE2:0d4c fallback after sprite hit testing returned no object.

    Original edges are excluded and an all-zero rectangle ends the search.
    Returning an action record does not execute or infer its action semantics.
    """
    if any(not isinstance(v, int) or not -32768 <= v <= 32767 for v in (x, y)):
        raise SpriteError('HSPT point requires signed 16-bit coordinates')
    for ordinal, r in enumerate(records):
        if r.sentinel:
            return None
        if r.left < x < r.right and r.top < y < r.bottom:
            return ordinal
    raise SpriteError('selected HSPT fallback lacks its terminating sentinel')


def completed_sequence_anchor(sprite, animation, sequence):
    """Sum one explicit unflipped sequence; clock/successor dispatch is excluded."""
    if not 0 <= sequence < len(animation.sequences):
        raise SpriteError('sequence outside table')
    start, successor, duration, count = animation.sequences[sequence]
    x, y = sprite.anchor_x, sprite.anchor_y
    for frame, dx, dy, unknown, override, flip in animation.steps[start:start+count]:
        if unknown or flip:
            raise SpriteError('unrecovered step word/flip in selected movement proof')
        x, y = ((x+dx+32768)&65535)-32768, ((y+dy+32768)&65535)-32768
    return x, y
