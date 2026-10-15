// Actual Seattle source predicates, not a general or default-true dispatcher.
// Evidence: docs/seattle-condition-recovery-evidence.json and formats/TREE.md.
const inventoryOffsets: Record<number, number> = {107:0x300,108:0x302,109:0x306};
export function evaluateSeattleCondition(condition: readonly number[],state: Uint8Array,conversationIndexWord: number,unitsWord: number): boolean {
  if (!Array.isArray(condition)||condition.length!==2||condition.some(v=>!Number.isInteger(v)||v<0||v>65535))
    throw new TypeError('Two original unsigned condition words required');
  if (!(state instanceof Uint8Array)||state.length<0x386) throw new TypeError('Explicit full-sized original state input required');
  if (!Number.isInteger(conversationIndexWord)||conversationIndexWord<0||conversationIndexWord>60)
    throw new RangeError('Verified conversation flag index0..60 required');
  if (!Number.isInteger(unitsWord)||unitsWord<0||unitsWord>65535) throw new RangeError('Explicit original units word required');
  const view=new DataView(state.buffer,state.byteOffset,state.byteLength),get=(off: number)=>view.getUint16(off,true);
  const [kind,value]=condition;
  switch(kind) {
    case 0:return true;
    case 2:return value===(get(0x218+2*conversationIndexWord)!==0?1:2);
    case 4:return get(0x218+2*conversationIndexWord)!==0&&value===(get(0x30c)!==0?1:2);
    case 7: {
      if (conversationIndexWord!==17) throw new RangeError('Only observed merchant kind7/index17 recovered');
      const predicate=get(0x318)===17&&[0x300,0x302,0x306].some(off=>get(off)>0&&get(off)<32768);
      return get(0x23a)!==0&&value===(predicate?1:2);
    }
    case 11:
      if (![107,108,109].includes(value)) throw new RangeError('Only observed Seattle inventory conditions107..109 recovered');
      return get(inventoryOffsets[value])===0;
    case 172:return value===(unitsWord!==0?1:2);
    case 26:return get(0x320)>=1&&get(0x320)<=3&&value===3-get(0x320);
    default:throw new RangeError(`Unrecovered condition kind${kind}`);
  }
}
