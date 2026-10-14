"""Bounded original sea-event update NE2:32fa; no daily/world/UI defaults."""
import struct
try:
    from .yukoninitial import original_random_step
except ImportError:
    from yukoninitial import original_random_step

class SeaDayError(ValueError):
    pass

def signed16(word):
    return word-65536 if word>=32768 else word

def sea_event_update(state_bytes,world_bytes,context_bytes,seed):
    """Return explicit state, world and RNG after unchanged selected 32fa.

    Context is the original far tuple addressed by parameter2, not a scene ID.
    No 2a8e clearing/date/counters or resource/journal consumers are composed.
    """
    if not isinstance(state_bytes,bytes) or len(state_bytes)<0x386 or not isinstance(world_bytes,bytes) or len(world_bytes)<0x2c or not isinstance(context_bytes,bytes) or len(context_bytes)<6:
        raise SeaDayError('Explicit original state/world/context byte buffers required')
    if not isinstance(seed,int) or not 0<=seed<=0xffffffff:
        raise SeaDayError('Explicit original u32 seed required')
    state=bytearray(state_bytes);world=bytearray(world_bytes)
    def get(buf,offset):return struct.unpack_from('<H',buf,offset)[0]
    def put(buf,offset,value):struct.pack_into('<H',buf,offset,value&65535)
    ship=get(state,0x320);ship_index=(ship-1)&65535
    counter=get(world,0x18);context_word=get(context_bytes,4)
    if signed16(counter)>2:
        if context_word==0:
            put(world,2,0);put(world,0x2a,0)
        else:
            seed,chance=original_random_step(seed)
            adjusted=(chance%100-3*ship_index)&65535
            if signed16(adjusted)>=60:
                status=1 if context_word==1 else 2
                put(world,2,status);put(world,0x2a,2*ship_index+status);put(world,4,1)
                seed,chance=original_random_step(seed)
                if ship!=3 and chance%100>=80:
                    seed,percent=original_random_step(seed)
                    percent=percent%15+1
                    # Original IMUL low word followed by CWD: product wraps
                    # before signed IDIV by100, including outlier food words.
                    product=signed16((signed16(get(state,0x2fe))*percent)&65535)
                    loss=(abs(product)//100)*(-1 if product<0 else 1)
                    put(world,8,loss)
                    if get(state,0x334)==0:
                        food=(get(state,0x2fe)-loss)&65535
                        put(state,0x2fe,0 if signed16(food)<0 else food)
                else:
                    put(world,6,0);put(world,8,0)
                put(state,0x32e,get(state,0x32e)+1) # a942 is ungated
            else:
                put(world,2,0);put(world,0x2a,0)
            counter=0
    put(world,0x18,counter+1)
    return bytes(state),bytes(world),seed


def sea_weather_update(state_bytes,world_bytes,context_bytes,seed):
    """Original NE2:3188 selected sea context firstword0, explicit RNG.

    Preserves original food arithmetic; selects weather and duration words.
    Does not itself advance date, compose2a8e or resolve event/journal consumers.
    """
    if not isinstance(state_bytes,bytes) or len(state_bytes)<0x386 or not isinstance(world_bytes,bytes) or len(world_bytes)<0x2c or not isinstance(context_bytes,bytes) or len(context_bytes)<6 or struct.unpack_from('<H',context_bytes)[0]!=0:
        raise SeaDayError('Only explicit original sea context0 weather buffers recovered')
    if not isinstance(seed,int) or not 0<=seed<=0xffffffff:raise SeaDayError('Explicit original u32 seed required')
    state=bytearray(state_bytes);world=bytearray(world_bytes)
    def get(buf,offset):return struct.unpack_from('<H',buf,offset)[0]
    def put(buf,offset,value):struct.pack_into('<H',buf,offset,value&65535)
    put(world,0x28,0)
    seed,chance=original_random_step(seed);chance%=100
    if chance>=75:
        put(state,0x32e,get(state,0x32e)+1)
        seed,chance=original_random_step(seed)
        if get(state,0x320)!=3 and chance%100>=80:
            seed,percent=original_random_step(seed);percent=percent%15+1
            product=signed16((signed16(get(state,0x2fe))*percent)&65535)
            loss=(abs(product)//100)*(-1 if product<0 else 1)
            put(world,8,loss)
            if get(state,0x334)==0:
                food=(get(state,0x2fe)-loss)&65535
                put(state,0x2fe,0 if signed16(food)<0 else food)
        else:put(world,6,0);put(world,8,0)
        put(world,0,2);put(world,0x28,1)
    elif chance>=55:
        put(world,0,1);put(state,0x32e,get(state,0x32e)+1)
    else:put(world,0,0)
    if get(state,0x334)==0:put(state,0x31c,get(world,0))
    seed,duration=original_random_step(seed);duration=duration%4+3
    if get(state,0x334)==0:put(state,0x31e,duration)
    return bytes(state),bytes(world),seed


def advance_sea_day_before_journal(state_bytes,world_bytes,context_bytes,seed):
    """Original NE2:2a8e through2b67 for selected sea context firstword0.

    Stops immediately before2c8c: pending event text/status and clearing are
    excluded. This is an execution boundary, not an invented scene transition.
    """
    if not isinstance(state_bytes,bytes) or len(state_bytes)<0x386 or not isinstance(world_bytes,bytes) or len(world_bytes)<0x38 or not isinstance(context_bytes,bytes) or len(context_bytes)<6 or struct.unpack_from('<H',context_bytes)[0]!=0:
        raise SeaDayError('Only explicit original sea context0 day buffers recovered')
    if not isinstance(seed,int) or not 0<=seed<=0xffffffff:raise SeaDayError('Explicit original u32 seed required')
    try:
        from .yukoncalendar import DateWords,advance_one_original_day
    except ImportError:
        from yukoncalendar import DateWords,advance_one_original_day
    state=bytearray(state_bytes);world=bytearray(world_bytes)
    def get(buf,offset):return struct.unpack_from('<H',buf,offset)[0]
    def put(buf,offset,value):struct.pack_into('<H',buf,offset,value&65535)
    for offset in (2,6,8,10,12):put(world,offset,0)
    if get(state,0x334)==0:
        count=(get(state,0x31e)-1)&65535
        put(state,0x31e,0 if signed16(count)<0 else count)
    if signed16(get(state,0x31e))<=0:
        put(world,0,0);put(world,0x22,0)
        state_result,world_result,seed=sea_weather_update(bytes(state),bytes(world),context_bytes,seed)
        state=bytearray(state_result);world=bytearray(world_result)
    date=advance_one_original_day(DateWords(get(state,0x28),get(state,0x2a),get(state,0x30e),get(state,0x310),get(state,0x334)))
    for offset,value in ((0x28,date.day_word),(0x2a,date.month_word),(0x30e,date.elapsed_word),(0x310,date.phase_word)):put(state,offset,value)
    if get(state,0x31a)==0:
        state_result,world_result,seed=sea_event_update(bytes(state),bytes(world),context_bytes,seed)
        state=bytearray(state_result);world=bytearray(world_result)
    if get(state,0x334)==0:
        count=(get(state,0x31a)-1)&65535
        put(state,0x31a,0 if signed16(count)<0 else count)
    if signed16(get(state,0x31a))<=0:put(world,0x0e,0)
    return bytes(state),bytes(world),seed


def read_sea_event_strings(normalized):
    """Bounded CSTR2000 count9; preserve all original text bytes."""
    if not isinstance(normalized,bytes) or len(normalized)<2 or struct.unpack_from('<H',normalized)[0]!=9:
        raise SeaDayError('Only selected CSTR2000 count9 recovered')
    if not normalized.endswith(b'\0'):raise SeaDayError('Unterminated CSTR2000')
    strings=normalized[2:-1].split(b'\0')
    if len(strings)!=9:raise SeaDayError('CSTR2000 count/extent differs')
    return tuple(strings)


def sea_message_update(state_bytes,world_bytes,context_bytes,text_bytes,strings):
    """Original2c8c sea selection/copy/status/clearing across CSTR provider.

    CSTR constructor/destructor resource ownership and subsequent partner
    notification are excluded. Event-seen flags are read, never set here.
    """
    if not isinstance(state_bytes,bytes) or len(state_bytes)<0x386 or not isinstance(world_bytes,bytes) or len(world_bytes)<0x38 or not isinstance(context_bytes,bytes) or len(context_bytes)<6 or struct.unpack_from('<H',context_bytes)[0]!=0 or not isinstance(text_bytes,bytes) or b'\0' not in text_bytes:
        raise SeaDayError('Explicit selected sea0 state/world/context/text buffers required')
    if not isinstance(strings,(tuple,list)) or len(strings)!=9 or any(not isinstance(s,bytes) or b'\0' in s for s in strings):raise SeaDayError('Explicit original nine CSTR2000 byte strings required')
    state=state_bytes;world=bytearray(world_bytes);text=bytearray(text_bytes)
    def get(buf,offset):return struct.unpack_from('<H',buf,offset)[0]
    def put(buf,offset,value):struct.pack_into('<H',buf,offset,value&65535)
    ship=get(state,0x320);context_word=get(context_bytes,4);weather_marker=get(world,0x28);event_marker=get(world,0x2a)
    # These are the source-produced sea marker/index domains. Unknown/corrupt
    # marker values would read outside the established flag/string extents.
    if ship not in (1,2,3) or context_word not in (0,1,2) or weather_marker not in (0,1) or event_marker not in range(7):raise SeaDayError('Only source-produced sea marker/ship/context domains recovered')
    status=0;selection=None
    if event_marker:
        flag_index=event_marker+3;put(world,0x32,flag_index)
        if get(state,0x19e+2*flag_index)==0:
            selection=context_word*3+ship-1;status=event_marker+33
    if selection is None and weather_marker:
        put(world,0x32,weather_marker)
        if get(state,0x19e+2*weather_marker)==0:
            selection=ship-1;status=weather_marker+30
    if selection is not None:
        replacement=strings[selection]+b'\0'
        if len(replacement)>len(text):raise SeaDayError('Original copied string exceeds explicit text capacity')
        text[:len(replacement)]=replacement
    put(world,0x1c,status)
    for offset in (0x2c,0x28,0x2a,0x2e,0x30):put(world,offset,0)
    return state,bytes(world),bytes(text),selection


def advance_sea_day(state_bytes,world_bytes,context_bytes,text_bytes,strings,seed):
    """Compose selected original sea rules through2c8c with CSTR input.

    Resource-handle ownership, world creation, notification/journal/dialogue
    consumers after this call remain excluded. No voyage defaults provided.
    """
    state,world,seed=advance_sea_day_before_journal(state_bytes,world_bytes,context_bytes,seed)
    state,world,text,selection=sea_message_update(state,world,context_bytes,text_bytes,strings)
    return state,world,text,seed,selection
