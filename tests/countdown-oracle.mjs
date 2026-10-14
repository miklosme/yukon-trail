import fs from 'node:fs';import crypto from 'node:crypto';import assert from 'node:assert/strict';
import {advanceCountdownDayBlock,finishWharfCountdownBlock} from '../web/rules/countdown.mjs';
const p=JSON.parse(fs.readFileSync(new URL('../docs/countdown-block-recovery-evidence.json',import.meta.url))),hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const set=(b,o,v)=>new DataView(b.buffer,b.byteOffset,b.byteLength).setUint16(o,v,true);
for(const [day,month,elapsed,phase,count,gate,digest,remaining] of p.day_cases){
  const before=new Uint8Array(0x400).fill(0x55);[[0x28,day],[0x2a,month],[0x30e,elapsed],[0x310,phase],[0x334,gate]].forEach(([o,v])=>set(before,o,v));
  const a=advanceCountdownDayBlock(before,count);assert.deepEqual([hash(a.stateBytes),a.countdownWord],[digest,remaining]);
}
for(const [count,gate,sh,sc,mh,remaining] of p.completion_cases){
  const before=new Uint8Array(0x400).fill(0x55),scene=new Uint8Array(128).fill(0x55),manager=new Uint8Array(128).fill(0x55);
  set(before,0x334,gate);set(scene,4,4000);new DataView(scene.buffer).setUint32(0x18,0x60005000,true);set(scene,0x1c,65535);set(scene,0x1e,65535);
  const a=finishWharfCountdownBlock(before,scene,manager,count);assert.deepEqual([hash(a.stateBytes),hash(a.sceneBytes),hash(a.managerBytes),a.countdownWord],[sh,sc,mh,remaining]);
}
assert.throws(()=>advanceCountdownDayBlock(new Uint8Array(0x400),0));
assert.throws(()=>finishWharfCountdownBlock(new Uint8Array(0x400),new Uint8Array(128),new Uint8Array(128),0));
console.log(`Original bounded countdown oracle: ${p.day_cases.length} day/decrement and ${p.completion_cases.length} post-cleanup queue cases match; animation/timer/voyage excluded.`);
