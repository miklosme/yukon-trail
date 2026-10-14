"""Bounded normalized TREE record graph from original recursive consumers.

No text recoding, general condition evaluator or dialogue UI is supplied.
Retain original byte offsets and unknown words, links, actions and conditions.
"""
from dataclasses import dataclass
import struct


class TreeError(ValueError):
    pass


@dataclass(frozen=True)
class Record:
    offset: int
    word0: int
    link_word: int
    action: tuple[int, int, int, int]
    condition: tuple[int, int]
    voice_id: int
    text: bytes


@dataclass(frozen=True)
class Choice:
    record: Record
    response: 'Response | None'


@dataclass(frozen=True)
class Response:
    record: Record
    choices: tuple[Choice, ...]


@dataclass(frozen=True)
class Tree:
    speaker_word: int
    count_word: int
    initial_overrides: tuple[Record, ...]
    root: Response
    trailing_empty_offsets: tuple[int, ...]


def decode_normalized(payload):
    if len(payload) < 4 or (len(payload) - 4) % 274:
        raise TreeError('TREE must contain header4 and complete274byte records')
    speaker, count = struct.unpack_from('<HH', payload)
    if count != (len(payload) - 4) // 274 or count == 0:
        raise TreeError('Unsupported TREE count/length')
    records = []
    for index in range(count):
        offset = 4 + index * 274
        words = struct.unpack_from('<9H', payload, offset)
        text = payload[offset + 18:offset + 274]
        if b'\0' not in text:
            raise TreeError(f'Unterminated record text at{offset:x}')
        records.append(Record(offset, words[0], words[1], words[2:6],
                              words[6:8], words[8], text.split(b'\0')[0]))
    cursor = 0

    def take():
        nonlocal cursor
        if cursor >= count:
            raise TreeError('Unexpected end of recursive TREE records')
        record = records[cursor]
        cursor += 1
        return record

    overrides = []
    while cursor < count and records[cursor].text:
        if len(overrides) == 5:
            raise TreeError('More than five initial override records unsupported')
        overrides.append(take())
    take()  # source override-list empty-text terminator

    def response(depth):
        if depth > 64:
            raise TreeError('TREE nesting bound exceeded')
        record = take()
        if not record.text:
            raise TreeError('Response requires nonempty text (space is nonempty)')
        choices = []
        while cursor < count and records[cursor].text:
            if len(choices) >= 10:
                raise TreeError('Original node holds at most ten choice pointers')
            choice = take()
            if cursor >= count:
                raise TreeError('Choice response/terminator missing')
            child = response(depth + 1) if records[cursor].text else None
            if child is None:
                take()  # no-response terminator
            choices.append(Choice(choice, child))
        take()  # choice-list empty-text terminator
        return Response(record, tuple(choices))

    root = response(0)
    trailing = records[cursor:]
    if any(payload[r.offset:r.offset + 274] != bytes(274) for r in trailing):
        raise TreeError('Nonzero trailing records outside supported graph')
    return Tree(speaker, count, tuple(overrides), root, tuple(r.offset for r in trailing))


def select_linda_initial_record(tree, flag220_word):
    """Selected TREE3400 condition(2,1), CONV firstword4→state220.

    Requires explicit original raw flagword. Its broader array meaning remains
    unknown. The original ordered override selector picks this record if the
    word is nonzero; otherwise it uses the root response record.
    """
    if not isinstance(flag220_word,int) or not 0 <= flag220_word <= 65535:
        raise TreeError('Explicit original unsigned state220 word required')
    if tree.speaker_word != 4 or len(tree.initial_overrides) != 1 or tree.initial_overrides[0].condition != (2,1):
        raise TreeError('Only selected Linda initial override condition is recovered')
    return tree.initial_overrides[0] if flag220_word else tree.root.record


@dataclass(frozen=True)
class LinkStep:
    next_path: tuple[int, ...] | None
    visited_offsets: frozenset[int]
    selected_record: Record
    response_record: Record | None


def response_at_path(tree,path):
    node=tree.root
    for index in path:
        if not isinstance(index,int) or not 0 <= index < len(node.choices) or node.choices[index].response is None:
            raise TreeError('Unsupported response path')
        node=node.choices[index].response
    return node


def step_choice_links(tree,current_path,visited_offsets,choice_index,action_success):
    """Selected original NE1:2fec links, after caller dispatches choice action.

    Takes a raw choice slot, not visible menu index. Conditions, action mutation,
    audio and refresh are caller-owned. Native UI handler passes action's0/1
    result. Original response and choice visited words are tracked by offsets.
    """
    if action_success not in (0,1) or not isinstance(current_path,tuple):
        raise TreeError('Explicit path and original action result0/1 required')
    node=response_at_path(tree,current_path)
    if not isinstance(choice_index,int) or not 0 <= choice_index < len(node.choices):
        raise TreeError('Choice slot outside recovered node')
    choice=node.choices[choice_index]
    depth=len(current_path)+1
    link=choice.record.link_word
    if not 1 <= link <= depth+1:
        raise TreeError('Unsupported selected absolute dialogue link depth')
    visited=frozenset(visited_offsets)|{node.record.offset,choice.record.offset}
    response=choice.response.record if action_success and choice.response else None
    target=current_path
    forward_descended=False
    if action_success and link>depth:
        if choice.response is None:
            raise TreeError('Original forward link has no child response')
        # Native32a6 checks child's first option-response pointer, not merely
        # its text or choice count. Forward descent returns before auto-rewind.
        if choice.response.choices and choice.response.choices[0].response is not None:
            target=current_path+(choice_index,)
            forward_descended=True
    else:
        while link<=len(target)+1:
            if not target:
                target=None
                break
            target=target[:-1]
    # Original auto-rewinds non-root nodes without unvisited nonempty choices.
    while target and not forward_descended:
        current=response_at_path(tree,target)
        if any(c.record.word0==0 and c.record.offset not in visited and c.record.text for c in current.choices):
            break
        target=target[:-1]
    return LinkStep(target,visited,choice.record,response)


def open_linda_dialogue(tree, flag220_word, gate334_word):
    """Return selected record and post-open220, using original constructor order.

    Only CONV3400 firstword4 is supported. Initial selection happens before
    NE1:a2e4 marks218+2*4; presentation, allocation and other state excluded.
    """
    if not isinstance(gate334_word,int) or not 0 <= gate334_word <= 65535:
        raise TreeError('Original unsigned16 mutation gate required')
    selected=select_linda_initial_record(tree,flag220_word)
    return selected, flag220_word if gate334_word else 1
