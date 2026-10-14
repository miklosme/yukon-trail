"""Selected Seattle fares and clerk CONV3500 selection, explicit raw state.

Original NE2:22c6/21ae, NE1:a3bc/a3e0/a184/2c9e and NE3:5118.
No affordability guard is invented: original fare handler ignores the money
routine's failure return. GUI cache, journal, ship waiting and voyage excluded.
"""
import struct
try:
    from .yukoninitial import original_random_step
except ImportError:
    from yukoninitial import original_random_step
try:
    from .yukonseattle import State, change_money_slot_zero
except ImportError:
    from yukonseattle import State, change_money_slot_zero


class TicketError(ValueError):
    pass


FARES = {251: (80, 3, 5000), 252: (60, 2, 5000), 253: (40, 1, 5000),
         254: (80, 3, 9000), 255: (60, 2, 9000), 256: (40, 1, 9000)}


def word(value):
    if not isinstance(value, int) or not 0 <= value <= 65535:
        raise TicketError('Explicit original unsigned 16-bit word required')
    return value


def select_clerk_tree(partner_word, ship_word):
    """Original CONV3500 ordered (3,2); (3,1)+(8,2); (8,1)."""
    partner_word, ship_word = word(partner_word), word(ship_word)
    if partner_word >= 32768:
        return 3500
    return 3570 if ship_word else 3550


def open_clerk_dialogue(tree, flag238_word, gate334_word):
    """CONV3500firstword16 selects using old238, then marks238 ifgatezero."""
    word(flag238_word); word(gate334_word)
    if tree.speaker_word!=16 or len(tree.initial_overrides)!=1 or tree.initial_overrides[0].condition!=(2,1):
        raise TicketError('Only selected clerk initial override recovered')
    return (tree.initial_overrides[0] if flag238_word else tree.root.record,
            flag238_word if gate334_word else 1)


def open_boarding_dialogue(tree, previous_seen_word, word30c, gate334_word):
    """Selected TREE4350/4450 ordered overrides4/2 then2/1.

    CONV4300firstword12→230; CONV4400firstword11→22e. Condition4 also
    reads30c viaa642; broader meaning of that raw word remains unknown.
    """
    word(previous_seen_word);word(word30c);word(gate334_word)
    if len(tree.initial_overrides)!=2 or tuple(r.condition for r in tree.initial_overrides)!=((4,2),(2,1)):
        raise TicketError('Only selected boarding initial overrides recovered')
    record=tree.root.record
    if previous_seen_word:
        record=tree.initial_overrides[0 if word30c==0 else 1]
    return record,previous_seen_word if gate334_word else 1


def purchase_ticket(before, action):
    """Preserve full input bytes except proven fare writes; return (bytes, 1)."""
    if not isinstance(before, (bytes, bytearray)) or len(before) < 0x336:
        raise TicketError('Explicit original state buffer of at least0x336 bytes required')
    if not isinstance(action, (tuple, list)) or len(action) != 4:
        raise TicketError('Four original action words required')
    if action[0] != 250 or action[1] not in FARES or tuple(action[2:]) != (FARES[action[1]][0], 0):
        raise TicketError('Only six source TREE3550 fare actions recovered')
    cash, bank = struct.unpack_from('<HH', before, 0x2fa)
    gate = struct.unpack_from('<H', before, 0x334)[0]
    fare, ship, destination = FARES[action[1]]
    money, _ = change_money_slot_zero(State(cash, bank, 0, gate, 0), -fare)
    after = bytearray(before)
    if not gate:
        struct.pack_into('<HH', after, 0x2fa, money.cash_word, money.bank_word)
        struct.pack_into('<HH', after, 0x320, ship, destination)
        inventory = (struct.unpack_from('<H', before, 0x304)[0] + 1) & 65535
        struct.pack_into('<H', after, 0x304, 0 if inventory >= 32768 else inventory)
    return bytes(after), 1


def selected_boarding_choice(ship_word, condition_value):
    """NE3:5118 condition26: ship3→value0, ship2→1, ship1→2."""
    ship_word, condition_value = word(ship_word), word(condition_value)
    return ship_word in (1, 2, 3) and condition_value == 3 - ship_word


def select_wharf_dialogue(ticket_word, destination_word, ship_word, random_seed):
    """HSPT4000action325 opens4300/4400; CONV selects owned4350/4450.

    Original RNG runs only if signed ticketword304<=0. Explicit seed needed;
    no destination correction or inferred reservation predicate is inserted.
    """
    word(ticket_word);word(destination_word);word(ship_word)
    if not isinstance(random_seed,int) or not 0<=random_seed<=0xffffffff:
        raise TicketError('Explicit original 32-bit random seed required')
    if 0<ticket_word<32768:
        base=4300 if destination_word==5000 else 4400
        seed=random_seed
    else:
        seed,random_word=original_random_step(random_seed)
        base=4300 if random_word&1 else 4400
    return base,base+50 if ship_word else base,seed


def queue_boarding(before, parent_bytes, manager_bytes, action):
    """Action320 copies8bytes to parent+10 and queues manager transition.

    Delays0/7/14 are explicit source TREE4350/4450 actions. No elapsed-day
    transition occurs in this operation. Returned pending request is not a
    completed voyage, and ticket decrement uses original signed clamping.
    """
    if not isinstance(before,(bytes,bytearray)) or len(before)<0x33c:
        raise TicketError('Explicit original state buffer required')
    if len(parent_bytes)<0x18 or len(manager_bytes)<12:
        raise TicketError('Explicit parent scene and manager buffers required')
    if tuple(action) not in ((320,0,0,0),(320,7,0,0),(320,14,0,0)):
        raise TicketError('Only selected source boarding requests recovered')
    state=bytearray(before); parent=bytearray(parent_bytes); manager=bytearray(manager_bytes)
    if not struct.unpack_from('<H',before,0x334)[0]:
        ticket=(struct.unpack_from('<H',before,0x304)[0]-1)&65535
        struct.pack_into('<H',state,0x304,0 if ticket>=32768 else ticket)
        if action[1]==0:struct.pack_into('<H',state,0x33a,0)
    struct.pack_into('<H',parent,0x0e,1)
    struct.pack_into('<4H',parent,0x10,*action)
    struct.pack_into('<H',manager,2,1)
    struct.pack_into('<4H',manager,4,*((1,400,31000,0) if action[1]==0 else (3,0,0,0)))
    return bytes(state),bytes(parent),bytes(manager),1

