"""Bounded original countdown rule blocks, excluding animation/timer services.

Positive branch NE2:079f..07ae, post-cleanup Wharf branch0817..088c. Explicit
caller prerequisites matter: these are not whole0740 callbacks or wall clocks.
"""
import struct
try:
    from .yukoncalendar import DateWords,advance_one_original_day
except ImportError:
    from yukoncalendar import DateWords,advance_one_original_day


class CountdownError(ValueError):
    pass


def _word(value):
    if not isinstance(value,int) or not 0<=value<=65535:
        raise CountdownError('Explicit original unsigned word required')
    return value


def _buffer(value,length):
    if not isinstance(value,(bytes,bytearray)) or len(value)<length:
        raise CountdownError('Explicit original byte buffer required')


def advance_countdown_day_block(before,countdown_word):
    """After animation updates, execute original day branch and decrement.

    Requires original positive signed countdown; no timer/animation fabricated.
    Gate334 suppresses date mutation, but does not suppress countdown decrease.
    """
    _buffer(before,0x336);_word(countdown_word)
    if not 0<countdown_word<32768:raise CountdownError('Original positive countdown branch required')
    get=lambda off:struct.unpack_from('<H',before,off)[0]
    after=bytearray(before)
    date=advance_one_original_day(DateWords(get(0x28),get(0x2a),get(0x30e),get(0x310),get(0x334)))
    for off,v in ((0x28,date.day_word),(0x2a,date.month_word),(0x30e,date.elapsed_word),(0x310,date.phase_word)):struct.pack_into('<H',after,off,v)
    return bytes(after),countdown_word-1


def finish_wharf_countdown_block(before,scene_bytes,manager_bytes,countdown_word):
    """Original0817 branch after timer cancel/animation destructor/free.

    Input scene still holds the old animation pointer, while its timer words
    must already beffff as original07c0/07d7. This block clears the pointer,
    writes33a gated334 and queues1/400/31000/0; it advances no date.
    """
    _buffer(before,0x33c);_buffer(scene_bytes,0x20);_buffer(manager_bytes,12);_word(countdown_word)
    if countdown_word!=0 and countdown_word<32768:raise CountdownError('Exhausted signed countdown required')
    if struct.unpack_from('<H',scene_bytes,4)[0]!=4000 or struct.unpack_from('<I',scene_bytes,0x18)[0]==0:
        raise CountdownError('Selected Wharf with original animation pointer required')
    if struct.unpack_from('<HH',scene_bytes,0x1c)!=(65535,65535):raise CountdownError('Original timer cleanup prerequisite required')
    state=bytearray(before);scene=bytearray(scene_bytes);manager=bytearray(manager_bytes)
    struct.pack_into('<I',scene,0x18,0)
    if not struct.unpack_from('<H',before,0x334)[0]:struct.pack_into('<H',state,0x33a,0)
    struct.pack_into('<H',manager,2,1);struct.pack_into('<4H',manager,4,1,400,31000,0)
    return bytes(state),bytes(scene),bytes(manager),countdown_word
