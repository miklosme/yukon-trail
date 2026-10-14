"""Selected actual Seattle TREE predicates, with explicit state/settings context.

Source NE3:5118 and getters. These are the kinds observed in the fourteen
interview/refusal/ticket/boarding graphs, not a general condition dispatcher.
"""
import struct

class ConditionError(ValueError):pass

def evaluate_seattle_condition(condition,state,conversation_index,units_word):
    if not isinstance(condition,(tuple,list))or len(condition)!=2 or any(not isinstance(v,int)or not 0<=v<=65535 for v in condition):raise ConditionError('Two original unsigned condition words required')
    if not isinstance(state,(bytes,bytearray))or len(state)<0x386:raise ConditionError('Explicit full-sized original state input required')
    if not isinstance(conversation_index,int)or not 0<=conversation_index<=60:raise ConditionError('Verified conversation flag index0..60 required')
    if not isinstance(units_word,int)or not 0<=units_word<=65535:raise ConditionError('Explicit original units word required')
    get=lambda off:struct.unpack_from('<H',state,off)[0]
    kind,value=condition
    if kind==0:return True
    if kind==2:return value==(1 if get(0x218+2*conversation_index)!=0 else 2)
    if kind==4:return get(0x218+2*conversation_index)!=0 and value==(1 if get(0x30c)!=0 else 2)
    if kind==7:
        if conversation_index!=17:raise ConditionError('Only observed merchant kind7/index17 recovered')
        positive=lambda v:0<v<32768
        predicate=get(0x318)==17 and any(positive(get(off))for off in(0x300,0x302,0x306))
        return get(0x23a)!=0 and value==(1 if predicate else 2)
    if kind==11:
        if value not in(107,108,109):raise ConditionError('Only observed Seattle inventory conditions107..109 recovered')
        return get({107:0x300,108:0x302,109:0x306}[value])==0
    if kind==172:return value==(1 if units_word!=0 else 2)
    if kind==26:return get(0x320)in(1,2,3)and value==3-get(0x320)
    raise ConditionError(f'Unrecovered condition kind{kind}')
