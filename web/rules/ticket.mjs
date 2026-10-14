// Original Seattle TREE3550 fare actions and4350/4450 boarding requests.
// docs/TICKETS.md and independent full-buffer native oracle. No date/wait UI.
import {changeMoneySlotZero} from './seattle.mjs';
import {originalRandomStep} from './initial.mjs';
const fares = new Map([[251,[80,3,5000]],[252,[60,2,5000]],[253,[40,1,5000]],
  [254,[80,3,9000]],[255,[60,2,9000]],[256,[40,1,9000]]]);
function word(v) { if (!Number.isInteger(v) || v<0 || v>65535) throw new RangeError('Explicit original word required'); return v; }
function bytes(v,n) { if (!(v instanceof Uint8Array) || v.length<n) throw new TypeError('Explicit original byte buffer required'); return v; }
function view(v) { return new DataView(v.buffer,v.byteOffset,v.byteLength); }
export function selectClerkTree(partnerWord,shipWord) {
  word(partnerWord);word(shipWord);return partnerWord>=32768?3500:shipWord?3570:3550;
}
export function openClerkDialogue(graph,flag238Word,gate334Word) {
  word(flag238Word);word(gate334Word);
  if (graph?.speaker_word!==16 || graph.initial_overrides?.length!==1 ||
      graph.initial_overrides[0].condition?.[0]!==2 || graph.initial_overrides[0].condition?.[1]!==1) {
    throw new RangeError('Only selected clerk initial override recovered');
  }
  return {selectedRecord:flag238Word?graph.initial_overrides[0]:graph.root.record,
    flag238Word:gate334Word?flag238Word:1};
}
export function openBoardingDialogue(graph,previousSeenWord,word30c,gate334Word) {
  word(previousSeenWord);word(word30c);word(gate334Word);
  if (graph?.initial_overrides?.length!==2 || graph.initial_overrides[0].condition?.join(',')!=='4,2' ||
      graph.initial_overrides[1].condition?.join(',')!=='2,1') throw new RangeError('Only selected boarding initial overrides recovered');
  return {selectedRecord:previousSeenWord?graph.initial_overrides[word30c===0?0:1]:graph.root.record,
    seenWord:gate334Word?previousSeenWord:1};
}
export function selectedBoardingChoice(shipWord,conditionValue) {
  word(shipWord);word(conditionValue);return shipWord>=1 && shipWord<=3 && conditionValue===3-shipWord;
}
export function selectWharfDialogue(ticketWord,destinationWord,shipWord,randomSeed) {
  word(ticketWord);word(destinationWord);word(shipWord);
  if (!Number.isInteger(randomSeed) || randomSeed<0 || randomSeed>0xffffffff) throw new RangeError('Explicit original random seed required');
  let base,nextSeed=randomSeed;
  if (ticketWord>0 && ticketWord<32768) base=destinationWord===5000?4300:4400;
  else { const r=originalRandomStep(randomSeed);nextSeed=r.nextSeed;base=r.randomWord&1?4300:4400; }
  return {baseSceneId:base,treeId:shipWord?base+50:base,nextSeed};
}
export function purchaseTicket(before,action) {
  bytes(before,0x336);
  if (!Array.isArray(action) || action.length!==4 || action[0]!==250 || !fares.has(action[1]) ||
      action[2]!==fares.get(action[1])[0] || action[3]!==0) throw new RangeError('Only six source fare actions recovered');
  const input=view(before),gate=input.getUint16(0x334,true),[fare,ship,destination]=fares.get(action[1]);
  const after=before.slice(),out=view(after);
  // Adapter placeholders are not returned game defaults; arithmetic reads
  // onlycash/bank/gate. Fare handler ignores insufficient-money return.
  const money=changeMoneySlotZero({cashWord:input.getUint16(0x2fa,true),bankWord:input.getUint16(0x2fc,true),
    partnerWord:0,flag334Word:gate,flag344Word:0},-fare).state;
  if (!gate) {
    out.setUint16(0x2fa,money.cashWord,true);out.setUint16(0x2fc,money.bankWord,true);
    out.setUint16(0x320,ship,true);out.setUint16(0x322,destination,true);
    const ticket=(input.getUint16(0x304,true)+1)&65535;out.setUint16(0x304,ticket>=32768?0:ticket,true);
  }
  return {stateBytes:after,actionResult:1};
}
export function queueBoarding(before,parentBytes,managerBytes,action) {
  bytes(before,0x33c);bytes(parentBytes,0x18);bytes(managerBytes,12);
  if (!Array.isArray(action) || action.length!==4 || action[0]!==320 || ![0,7,14].includes(action[1]) ||
      action[2]!==0 || action[3]!==0) throw new RangeError('Only source boarding requests recovered');
  const state=before.slice(),parent=parentBytes.slice(),manager=managerBytes.slice();
  const input=view(before),out=view(state),pv=view(parent),mv=view(manager);
  if (!input.getUint16(0x334,true)) {
    const ticket=(input.getUint16(0x304,true)-1)&65535;out.setUint16(0x304,ticket>=32768?0:ticket,true);
    if (action[1]===0) out.setUint16(0x33a,0,true);
  }
  pv.setUint16(0xe,1,true);action.forEach((v,i)=>pv.setUint16(0x10+i*2,v,true));
  mv.setUint16(2,1,true);(action[1]===0?[1,400,31000,0]:[3,0,0,0]).forEach((v,i)=>mv.setUint16(4+i*2,v,true));
  return {stateBytes:state,parentBytes:parent,managerBytes:manager,actionResult:1};
}
