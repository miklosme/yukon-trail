"""Bounded event7 Linda journal formatting for the selected Seattle location.

No calendar advance, scene-loop processing, journal overflow repair, or general
event dispatcher is supplied. Text and date words are explicit source inputs.
"""
from dataclasses import dataclass
import hashlib
import struct

EXE_SHA256 = '9ca8f0a12f4798e762fbf27634f99afcb5c0c1a3836604bf0a4049a73227dd06'


class JournalError(ValueError):
    pass


@dataclass(frozen=True)
class Vocabulary:
    months: tuple[bytes, ...]
    early_year: bytes
    later_year: bytes
    seattle: bytes
    separator: bytes


def source_vocabulary(executable):
    if hashlib.sha256(executable).hexdigest() != EXE_SHA256:
        raise JournalError('Unsupported executable identity')

    def string(offset):
        raw = executable[0x4f420 + offset:0x4f420 + offset + 64]
        if b'\0' not in raw:
            raise JournalError('Unterminated source journal string')
        return raw.split(b'\0')[0]

    offsets = (0xf2e, 0xf37, 0xf41, 0xf48, 0xf4f, 0xf54,
               0xf5a, 0xf60, 0xf68, 0xf73, 0xf7c, 0xf86)
    return Vocabulary(tuple(string(o) for o in offsets), string(0xf90),
                      string(0xf99), string(0xfa2), string(0x1093) + string(0x1096))


def linda_text_from_raw_cstr505(payload):
    """Selected raw CSTR505 count4 + four NUL-terminated strings; returns4th."""
    if payload[:2] != b'\x00\x04':
        raise JournalError('Unsupported raw partner CSTR count')
    strings = payload[2:].split(b'\0')
    if len(strings) != 5 or strings[-1] != b'':
        raise JournalError('Partner CSTR must contain exactly four terminated strings')
    return strings[3]


def linda_entry(vocabulary, cstr505, day_word, month_word, phase_word, previous_journal,
                location=(200, 0, 0)):
    # NE1:d1eb selectsregion200; d1f2 usessecondword asplace-table index.
    # Selectedindex0 isSeattle; thirdword isnotread on thisbranch.
    if (not isinstance(location,tuple) or len(location)!=3 or
            any(not isinstance(v,int) or not 0<=v<=65535 for v in location) or
            location[:2]!=(200,0)):
        raise JournalError('Only region200/place-index0 with unsigned16 scene word is recovered')
    if not 1 <= day_word <= 31 or not 1 <= month_word <= 12 or not 0 <= phase_word <= 65535:
        raise JournalError('Unsupported date/phase words')
    if not isinstance(previous_journal, bytes) or b'\0' in previous_journal:
        raise JournalError('Journal requires explicit NUL-free bytes')
    if len(vocabulary.months) != 12:
        raise JournalError('Twelve source month strings are required')
    signed_phase = phase_word - 65536 if phase_word >= 32768 else phase_word
    parts = [vocabulary.separator] if previous_journal else []
    parts.extend([vocabulary.months[month_word - 1], str(day_word).encode('ascii'),
                  vocabulary.early_year if signed_phase <= 5 else vocabulary.later_year,
                  vocabulary.seattle, linda_text_from_raw_cstr505(cstr505)])
    result = b''
    # Original component appends check total <255, excluding terminatingNUL.
    for part in parts:
        if b'\0' in part:
            raise JournalError('Unterminated component passed to recovered formatter')
        if len(result) + len(part) < 255:
            result += part
    if len(previous_journal) + len(result) >= 0x2800:
        raise JournalError('Original journal overflow/retention path is unrecovered')
    return result


def append_linda_entry(vocabulary, cstr505, day_word, month_word, phase_word, previous_journal,
                       location=(200, 0, 0)):
    return previous_journal + linda_entry(vocabulary, cstr505, day_word, month_word,
                                         phase_word, previous_journal, location)


def queue_linda_continuation(manager_bytes):
    """NE1:4dba selected action3: pending word+2=1, eight action bytes+4.

    This records a native manager request. Its later UI-loop effect is outside
    this bounded operation; it does not itself advance the date or draw a scene.
    """
    if not isinstance(manager_bytes, bytes) or len(manager_bytes) < 12:
        raise JournalError('Explicit manager bytes covering offsets0..11 required')
    result = bytearray(manager_bytes)
    struct.pack_into('<H', result, 2, 1)
    struct.pack_into('<4H', result, 4, 3, 0, 0, 0)
    return bytes(result)
