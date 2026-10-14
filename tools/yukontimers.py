"""Recovered five-slot timer bookkeeping, original NE1:4e94/4f20/4fca/5076.

Clock, allocator and forwarded event are explicit platform/consumer inputs.
No browser wakeup cadence, game callback or wall-clock default is supplied.
"""
import struct


class TimerError(ValueError):
    pass


def _uint(value,bits):
    if not isinstance(value,int) or not 0<=value<(1<<bits):raise TimerError(f'Explicit original unsigned{bits}bit value required')
    return value


def _table(table):
    if not isinstance(table,(bytes,bytearray)) or len(table)<20:raise TimerError('Explicit five-far-pointer timer table required')


def countdown_period(requested_word):
    _uint(requested_word,16)
    count=requested_word if 0<requested_word<32768 else 1
    return count,120//count+30  # selected Wharf4000, not special19000+5


def initialize_timer_table(previous_bytes):
    _table(previous_bytes);after=bytearray(previous_bytes);after[:20]=bytes(20);return bytes(after)


def register_timer(table,allocated_record,allocated_far_pointer,period_word,time_get_time,allocation_succeeds):
    _table(table);_uint(allocated_far_pointer,32);_uint(period_word,16);_uint(time_get_time,32)
    if not isinstance(allocated_record,(bytes,bytearray)) or len(allocated_record)<8 or not isinstance(allocation_succeeds,bool):raise TimerError('Explicit original allocator record/result required')
    if allocation_succeeds and allocated_far_pointer==0:raise TimerError('Successful allocation requires a nonnull far pointer')
    result=bytearray(table);record=bytearray(allocated_record)
    slot=next((i for i in range(5) if struct.unpack_from('<I',table,i*4)[0]==0),65535)
    if slot==65535:return bytes(result),bytes(record),slot
    if allocation_succeeds:
        record[0]=1;struct.pack_into('<H',record,2,period_word)
        period=period_word-65536 if period_word>=32768 else period_word
        struct.pack_into('<I',record,4,((time_get_time>>4)+period)&0xffffffff)
        struct.pack_into('<I',result,slot*4,allocated_far_pointer)
    # Original allocator failure returns the chosen index with null slot.
    return bytes(result),bytes(record),slot


def cancel_timer(table,timer_id):
    _table(table);_uint(timer_id,16)
    if timer_id==5:raise TimerError('Original guard admitsindex5 outside five-slot constructor; adjacent-memory behavior excluded')
    result=bytearray(table);freed=[]
    if timer_id<5:
        pointer=struct.unpack_from('<I',result,timer_id*4)[0]
        if pointer:freed.append(pointer)
        struct.pack_into('<I',result,timer_id*4,0)
    return bytes(result),freed


def poll_timers(table,records,time_get_time,forward_event):
    """One event/eligible slot per poll, then reschedule from fresh clock.

    Callback receives(slot,mutable table,mutable records); mutations are kept.
    Every clock read is explicit. Called game event handlers remain outside.
    """
    _table(table)
    if not callable(time_get_time) or not callable(forward_event):raise TimerError('Explicit clock and forwarded-event services required')
    after=bytearray(table);heap={p:bytearray(r) for p,r in records.items()};fired=[]
    snapshot=_uint(time_get_time(),32)>>4
    for slot in range(5):
        pointer=struct.unpack_from('<I',after,slot*4)[0]
        if not pointer:continue
        if pointer not in heap or len(heap[pointer])<8:raise TimerError('Unmapped timer record')
        record=heap[pointer]
        if struct.unpack_from('<I',record,4)[0]>snapshot or record[0]==0:continue
        fired.append(slot);forward_event(slot,after,heap)
        pointer=struct.unpack_from('<I',after,slot*4)[0]
        if not pointer:continue
        if pointer not in heap or len(heap[pointer])<8:raise TimerError('Callback installed unmapped timer')
        record=heap[pointer];clock=_uint(time_get_time(),32)>>4;period=struct.unpack_from('<h',record,2)[0]
        struct.pack_into('<I',record,4,(clock+period)&0xffffffff)
    return bytes(after),{p:bytes(r) for p,r in heap.items()},fired
