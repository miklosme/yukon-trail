"""Bounded SMAP31000 waypoint consumer and map entry state blocks.

Original NE4:3482/41e0 and constructor36a2..36e0. Weather, daily callback,
cutscene creation, journal/audio/rendering are explicit outside boundaries.
"""
import struct
try:
    from .yukoninitial import original_random_step
except ImportError:
    from yukoninitial import original_random_step


class VoyageError(ValueError):
    pass


def read_sea_map(normalized):
    if len(normalized)<2:raise VoyageError('Truncated SMAP')
    count=struct.unpack_from('<H',normalized)[0]
    if count!=45 or len(normalized)!=2+count*6:raise VoyageError('Only selected SMAP31000 count/extent recovered')
    records=tuple(struct.unpack_from('<3H',normalized,2+i*6) for i in range(count))
    if any(r[2] not in (0,1,2,31101,31102,31103) for r in records):raise VoyageError('Unsupported waypoint event')
    return records


def _buffer(b,n):
    if not isinstance(b,(bytes,bytearray)) or len(b)<n:raise VoyageError('Explicit original byte buffer required')


def initialize_map_state_block(before,scene_bytes):
    """Original36a2..36e0: metadata330/332, scene88/8c from saved336/338."""
    _buffer(before,0x33a);_buffer(scene_bytes,0x90)
    state=bytearray(before);scene=bytearray(scene_bytes)
    if not struct.unpack_from('<H',before,0x334)[0]:struct.pack_into('<HH',state,0x330,31000,400)
    struct.pack_into('<H',scene,0x88,struct.unpack_from('<H',before,0x336)[0]);struct.pack_into('<H',scene,0x8c,struct.unpack_from('<H',before,0x338)[0])
    return bytes(state),bytes(scene)


def advance_sea_waypoint(before,scene_bytes,manager_bytes,records,random_seed,sound_mode_word):
    """Original3482 whole rule routine; OpenScene/audio are emitted boundaries.

    Caller supplies speed96, currentindex88, remainder8c and actual source rows.
    No day, speed default, weather event or cutscene effect is manufactured.
    """
    _buffer(before,0x33a);_buffer(scene_bytes,0xa6);_buffer(manager_bytes,12)
    if len(records)!=45 or any(len(r)!=3 or any(not isinstance(v,int) or not 0<=v<=65535 for v in r) or r[2] not in (0,1,2,31101,31102,31103) for r in records):raise VoyageError('Explicit selected source SMAP rows required')
    if not isinstance(random_seed,int) or not 0<=random_seed<=0xffffffff or not isinstance(sound_mode_word,int) or not 0<=sound_mode_word<=65535:raise VoyageError('Explicit original RNG/sound words required')
    state=bytearray(before);scene=bytearray(scene_bytes);manager=bytearray(manager_bytes)
    get=lambda o:struct.unpack_from('<H',scene,o)[0]
    put=lambda o,v:struct.pack_into('<H',scene,o,v&65535)
    index=get(0x88)
    if not 0<=index<len(records):raise VoyageError('Current source waypoint index out of range')
    partial=(get(0x8c)+get(0x96))&65535;put(0x8c,partial);opens=[];audio=[];seed=random_seed
    if 25<=partial<32768:
        put(0x8c,partial-25);event=records[index][2]
        if event==1:
            put(0x7a,1)
            if struct.unpack_from('<H',before,0x30a)[0]==11:
                struct.pack_into('<H',manager,2,1);struct.pack_into('<4H',manager,4,2,300,26000,0)
        elif event==2:
            put(0x88,0);put(0x8c,0);put(0x7a,1);put(0x7c,1)
            destination=struct.unpack_from('<H',before,0x322)[0]
            if destination not in (5000,9000):
                seed,r=original_random_step(seed);destination=5000 if r%2==0 else 9000
            struct.pack_into('<H',manager,2,1);struct.pack_into('<4H',manager,4,1,200,destination,0)
        elif event in (31101,31102,31103):
            if event==31102 and sound_mode_word!=2:audio.append(struct.unpack_from('<I',scene,0xa2)[0])
            put(0x80,1);put(0x7a,1);opens.append((event,1700))
        else:put(0x80,0);put(0x7a,0)
        if event!=2:put(0x88,index+1)
    if not struct.unpack_from('<H',before,0x334)[0]:
        struct.pack_into('<H',state,0x336,get(0x88));struct.pack_into('<H',state,0x338,get(0x8c))
    return bytes(state),bytes(scene),bytes(manager),seed,opens,audio
