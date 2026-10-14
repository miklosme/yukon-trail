"""Bounded recovered Linda acceptance and slot-zero money operations.

Source addresses and validation: docs/SEATTLE-RULES.md. Explicit journal
context can be composed; no calendar advance, UI loop, persistence or general
opcode interpreter is supplied.
"""
from dataclasses import dataclass, replace


class UnsupportedOperation(ValueError):
    pass


@dataclass(frozen=True)
class State:
    cash_word: int
    bank_word: int
    partner_word: int
    flag334_word: int
    flag344_word: int

    def __post_init__(self):
        for value in (self.cash_word, self.bank_word, self.partner_word,
                      self.flag334_word, self.flag344_word):
            if not isinstance(value, int) or not 0 <= value <= 65535:
                raise UnsupportedOperation('State requires original unsigned 16-bit words')


def _signed(word):
    return word - 65536 if word >= 32768 else word


def change_money_slot_zero(state, delta):
    """Return (state, success) for the verified signed-word delta subset.

    Native1:a184 accepts a dword; its broader high-word/other-slot behavior
    is deliberately unsupported here. Display notifications are excluded.
    """
    if not isinstance(delta, int) or not -32768 <= delta <= 32767:
        raise UnsupportedOperation('Only signed 16-bit deltas in slot zero are recovered')
    if state.flag334_word:
        return state, True
    cash = (state.cash_word + delta) & 65535
    bank = state.bank_word
    if delta < 0 and _signed(cash) < 0:
        bank = (bank + cash) & 65535
        if _signed(bank) < 0:
            return state, False
        cash = 0
    # Native1:a266..a26f clamps negative signed slot zero after mutation.
    if _signed(cash) < 0:
        cash = 0
    return replace(state, cash_word=cash, bank_word=bank), True


def accept_linda(state, opcode=0xf0, partner=4, amount=500):
    """Selected TREE3400 confirmation: partner4, flag344=1, cash +=500.

    Explicit parameters allow unsupported evidence to fail loudly. Only this
    selected action is recovered, including native flag334 mutation suppression.
    """
    if (opcode, partner, amount) != (0xf0, 4, 500):
        raise UnsupportedOperation('Only TREE3400 Linda confirmation is recovered')
    next_state = replace(state, flag344_word=1)
    if not state.flag334_word:
        next_state = replace(next_state, partner_word=4)
    return change_money_slot_zero(next_state, 500)


@dataclass(frozen=True)
class LindaEffects:
    state: State
    money_success: bool
    journal_bytes: bytes
    manager_bytes: bytes


def accept_linda_effects(state, vocabulary, cstr505, day_word, month_word, phase_word,
                        previous_journal, manager_bytes, location):
    """Compose recovered money, selected journal and queued manager request.

    Date/location are explicit caller inputs. The original scene-controller
    constructor and the pending-request UI loop remain outside this function.
    """
    try:
        from .yukonjournal import append_linda_entry, queue_linda_continuation
    except ImportError:
        from yukonjournal import append_linda_entry, queue_linda_continuation
    journal = append_linda_entry(vocabulary, cstr505, day_word, month_word,
                                 phase_word, previous_journal, location)
    manager = queue_linda_continuation(manager_bytes)
    next_state, success = accept_linda(state)
    return LindaEffects(next_state, success, journal, manager)


def linda_scene_child_eligible(partner_word):
    """Selected SCRP4000 record15 kind3/SPRT403 condition conjunction.

    Original conditions are (3,1),(5,4),(0,0): nonnegative signed partner,
    partnerword4, unconditional. This only selects the Linda scene child;
    allocation, sprite drawing and other records remain outside this model.
    """
    if not isinstance(partner_word, int) or not 0 <= partner_word <= 65535:
        raise UnsupportedOperation('Partner requires an original unsigned 16-bit word')
    return partner_word == 4
