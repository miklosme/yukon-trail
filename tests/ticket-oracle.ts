import fs from 'node:fs';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import {purchaseTicket,selectClerkTree,selectedBoardingChoice,queueBoarding,openClerkDialogue,selectWharfDialogue,openBoardingDialogue} from '../web/rules/ticket.ts';
const proof=JSON.parse(fs.readFileSync(new URL('../docs/ticket-recovery-evidence.json',import.meta.url), 'utf8'));
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const set=(b,o,v)=>new DataView(b.buffer,b.byteOffset,b.byteLength).setUint16(o,v,true);
for (const [id,cash,bank,ticket,gate,digest,result] of proof.fare_cases) {
  const before=new Uint8Array(0x400).fill(0x55);
  [[0x2fa,cash],[0x2fc,bank],[0x304,ticket],[0x334,gate]].forEach(([o,v])=>set(before,o,v));
  const fare=id===251||id===254?80:id===252||id===255?60:40;
  const actual=purchaseTicket(before,[250,id,fare,0]);assert.equal(hash(actual.stateBytes),digest);assert.equal(actual.actionResult,result);
}
for(const [p,s,r] of proof.clerk_selection_cases) assert.equal(selectClerkTree(p,s),r);
for(const [s,v,r] of proof.boarding_condition_cases) assert.equal(Number(selectedBoardingChoice(s,v)),r);
for(const [t,d,s,seed,base,tree,next] of proof.wharf_opening_cases) {
  const a=selectWharfDialogue(t,d,s,seed);assert.deepEqual([a.baseSceneId,a.treeId,a.nextSeed],[base,tree,next]);
}
for(const [id,flag,gate,offset,voice,post,digest] of proof.clerk_opening_cases) {
  const graph={speaker_word:16,initial_overrides:[{offset:4,voice_id:id,condition:[2,1]}],root:{record:{offset:552,voice_id:id+1}}};
  const a=openClerkDialogue(graph,flag,gate);assert.deepEqual([a.selectedRecord.offset,a.selectedRecord.voice_id,a.flag238Word],[offset,voice,post]);
  const b=new Uint8Array(0x400).fill(0x55);set(b,0x238,post);set(b,0x334,gate);assert.equal(hash(b),digest);
}
for(const [id,seen,w30c,gate,offset,voice,post,digest] of proof.boarding_opening_cases) {
  const graph={initial_overrides:[{offset:4,voice_id:id,condition:[4,2]},{offset:278,voice_id:id+1,condition:[2,1]}],root:{record:{offset:826,voice_id:id+2}}};
  const a=openBoardingDialogue(graph,seen,w30c,gate);assert.deepEqual([a.selectedRecord.offset,a.selectedRecord.voice_id,a.seenWord],[offset,voice,post]);
  const b=new Uint8Array(0x400).fill(0x55);set(b,id===4350?0x230:0x22e,post);set(b,0x30c,w30c);set(b,0x334,gate);assert.equal(hash(b),digest);
}
for(const [delay,ticket,gate,sh,ph,mh,result] of proof.boarding_cases) {
  const before=new Uint8Array(0x400).fill(0x55),parent=new Uint8Array(128).fill(0x55),manager=new Uint8Array(128).fill(0x55);
  set(before,0x304,ticket);set(before,0x334,gate);
  [0,0x4000,0x5000,0x4000].forEach((v,i)=>set(manager,0x16+i*2,v));
  const a=queueBoarding(before,parent,manager,[320,delay,0,0]);
  assert.deepEqual([hash(a.stateBytes),hash(a.parentBytes),hash(a.managerBytes),a.actionResult],[sh,ph,mh,result]);
}
assert.throws(()=>purchaseTicket(new Uint8Array(0x400),[250,254,81,0]));
assert.throws(()=>queueBoarding(new Uint8Array(0x400),new Uint8Array(128),new Uint8Array(128),[320,1,0,0]));
console.log(`Original native oracle matches ${proof.fare_cases.length} fares, ${proof.clerk_selection_cases.length} clerk selectors, ${proof.clerk_opening_cases.length} clerk opening and ${proof.boarding_opening_cases.length} boarding opening conditions/marks, ${proof.wharf_opening_cases.length} Wharf dispatch/RNG selections, ${proof.boarding_condition_cases.length} conditions and ${proof.boarding_cases.length} boarding requests.`);
