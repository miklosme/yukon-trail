import fs from 'node:fs';import crypto from 'node:crypto';import assert from 'node:assert/strict';
import {countdownPeriod,initializeTimerTable,registerTimer,cancelTimer,pollTimers} from '../web/rules/timers.mjs';
const p=JSON.parse(fs.readFileSync(new URL('../docs/timer-recovery-evidence.json',import.meta.url))),hash=b=>crypto.createHash('sha256').update(b).digest('hex');
function table(mask){const b=new Uint8Array(32).fill(0x55),v=new DataView(b.buffer);for(let i=0;i<5;i++)v.setUint32(i*4,mask&(1<<i)?0x60005000+i*16:0,true);return b;}
for(const [r,c,d] of p.period_cases)assert.deepEqual(countdownPeriod(r),{countdownWord:c,periodWord:d});
for(const [value,digest] of p.initialization_cases)assert.equal(hash(initializeTimerTable(new Uint8Array(32).fill(value))),digest);
for(const [mask,period,clock,alloc,th,rh,id] of p.registration_cases){const a=registerTimer(table(mask),new Uint8Array(8).fill(0x5a),0x40005000,period,clock,alloc);assert.deepEqual([hash(a.tableBytes),hash(a.recordBytes),a.timerId],[th,rh,id]);}
for(const [mask,id,th,freed] of p.cancellation_cases){const a=cancelTimer(table(mask),id);assert.deepEqual([hash(a.tableBytes),a.freedPointers],[th,freed]);}
for(const [clock,active,delta,effect,th,rh,fired,reads] of p.poll_cases){
  const t=table(31),records=new Map();for(let i=0;i<5;i++){const b=new Uint8Array(8).fill(0x5a),v=new DataView(b.buffer);b[0]=active;v.setUint16(2,35+i,true);v.setUint32(4,((clock>>>4)+delta)>>>0,true);records.set(0x60005000+i*16,b);}
  let n=0;const clocks=[clock,...[1,2,3,4,5].map(i=>(clock+i*16)>>>0)];
  const a=pollTimers(t,records,()=>clocks[n++],(slot,b,h)=>{const v=new DataView(b.buffer,b.byteOffset,b.byteLength),ptr=v.getUint32(slot*4,true);if(effect==='remove')v.setUint32(slot*4,0,true);else if(effect==='disable')h.get(ptr)[0]=0;});
  assert.deepEqual([hash(a.tableBytes),[...a.records.values()].map(hash),a.firedIds,n],[th,rh,fired,reads]);
}
assert.throws(()=>cancelTimer(table(31),5));
console.log(`Original timer oracle: ${p.registration_cases.length} registrations, ${p.cancellation_cases.length} cancellations, ${p.poll_cases.length} polls and ${p.period_cases.length} countdown periods match.`);
