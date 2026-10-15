import fs from 'node:fs';import crypto from 'node:crypto';import assert from 'node:assert/strict';
import {initializeMapStateBlock,advanceSeaWaypoint,readSeaMap} from '../web/rules/voyage.ts';
const p=JSON.parse(fs.readFileSync(new URL('../docs/voyage-waypoint-recovery-evidence.json',import.meta.url), 'utf8')),hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const set=(b,o,v)=>new DataView(b.buffer,b.byteOffset,b.byteLength).setUint16(o,v,true);
const rows=p.resource.records,encoded=new Uint8Array(272);set(encoded,0,45);rows.forEach((r,i)=>r.forEach((v,j)=>set(encoded,2+i*6+j*2,v)));
assert.deepEqual(readSeaMap(encoded),rows);
for(const [index,partial,speed,gate,dest,inventory,mode,seed,sh,sc,mh,next,opens,audio] of [...p.waypoint_cases,...p.branch_cases]){
  const before=new Uint8Array(0x400).fill(0x55),scene=new Uint8Array(0xa6).fill(0x55),manager=new Uint8Array(128).fill(0x55);
  [[0x334,gate],[0x322,dest],[0x30a,inventory]].forEach(([o,v])=>set(before,o,v));[[0x88,index],[0x8c,partial],[0x96,speed]].forEach(([o,v])=>set(scene,o,v));new DataView(scene.buffer).setUint32(0x98,0x60004000,true);
  const a=advanceSeaWaypoint(before,scene,manager,rows,seed,mode);assert.deepEqual([hash(a.stateBytes),hash(a.sceneBytes),hash(a.managerBytes),a.nextSeed,a.openScenes,a.audioPointers],[sh,sc,mh,next,opens,audio]);
}
for(const [index,partial,gate,sh,sc] of p.entry_cases){
  const before=new Uint8Array(0x400).fill(0x55),scene=new Uint8Array(0xa6).fill(0x55);[[0x336,index],[0x338,partial],[0x334,gate]].forEach(([o,v])=>set(before,o,v));
  const a=initializeMapStateBlock(before,scene);assert.deepEqual([hash(a.stateBytes),hash(a.sceneBytes)],[sh,sc]);
}
assert.throws(()=>readSeaMap(new Uint8Array(272)));set(encoded,6,999);assert.throws(()=>readSeaMap(encoded));
console.log(`Original voyage oracle: ${p.waypoint_cases.length+p.branch_cases.length} waypoints and ${p.entry_cases.length} constructor state blocks match; weather/date/cutscenes excluded.`);
