"""Original NE1:a0c2 day increment with explicit recovered state words.

A separate scene timer/leave path calls this routine. Linda's acceptance does
not invoke it directly. No year, initial date, wall clock or leap year invented.
"""
from dataclasses import dataclass, replace

MONTH_LENGTHS = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)


class CalendarError(ValueError):
    pass


@dataclass(frozen=True)
class DateWords:
    day_word: int
    month_word: int
    elapsed_word: int
    phase_word: int
    gate334_word: int

    def __post_init__(self):
        for word in (self.day_word, self.month_word, self.elapsed_word,
                     self.phase_word, self.gate334_word):
            if not isinstance(word, int) or not 0 <= word <= 65535:
                raise CalendarError('Original date context requires unsigned16bit words')
        if not 1 <= self.month_word <= 12 or not 1 <= self.day_word <= MONTH_LENGTHS[self.month_word - 1]:
            raise CalendarError('Only valid original month/day ranges are recovered')


def advance_one_original_day(words):
    """Return original word mutations; UI dirty notification is outside state."""
    if words.gate334_word:
        return words
    day = words.day_word + 1
    month = words.month_word
    phase = words.phase_word
    if day > MONTH_LENGTHS[month - 1]:
        day = 1
        month = month + 1 if month < 12 else 1
        phase = (phase + 1) & 65535
    return replace(words, day_word=day, month_word=month, phase_word=phase,
                   elapsed_word=(words.elapsed_word + 1) & 65535)


def enter_selected_seattle_scene(words, scene_id, visit_word):
    """Bounded NE2:04f0..0559 and0592 effect for SCNE1000/2000/3000/4000.

    Original scene constructor reads SCNE+8 only on a first visit; selected
    Downtown value is1, Wharf value0. Explicit visit/gate inputs are mandatory.
    Allocation, other constructor flags, timers and scene activation excluded.
    """
    if scene_id not in (1000,2000,3000,4000) or not isinstance(visit_word,int) or not 0 <= visit_word <= 65535:
        raise CalendarError('Only explicit selected Seattle scene/visit words supported')
    result=advance_one_original_day(words) if scene_id==1000 and visit_word==0 else words
    return result, visit_word if words.gate334_word else 1
