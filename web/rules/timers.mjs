// Original five-slot timer4e94/4f20/4fca/5076; explicit platform services.
// Clock values are original TIMEGETTIME u32; callbacks are caller-owned.
function uint(v,bits){if(!Number.isInteger(v)||v<0||v>2**bits-1)throw new RangeError(`Explicit unsigned${bits} value required`);return v;}
function view(b,n){if(!(b instanceof Uint8Array)||b.length<n)throw new TypeError('Explicit original buffer required');return new DataView(b.buffer,b.byteOffset,b.byteLength);}
export function countdownPeriod(requestedWord){uint(requestedWord,16);const count=requestedWord>0&&requestedWord<32768?requestedWord:1;return {countdownWord:count,periodWord:Math.floor(120/count)+30};}
export function initializeTimerTable(previousBytes){view(previousBytes,20);const a=previousBytes.slice();a.fill(0,0,20);return a;}
export function registerTimer(table,allocatedRecord,allocatedFarPointer,periodWord,timeGetTime,allocationSucceeds){
  const input=view(table,20);view(allocatedRecord,8);uint(allocatedFarPointer,32);uint(periodWord,16);uint(timeGetTime,32);
  if(typeof allocationSucceeds!=='boolean'||(allocationSucceeds&&allocatedFarPointer===0))throw new RangeError('Explicit allocator result required');
  const t=table.slice(),record=allocatedRecord.slice(),tv=view(t,20),rv=view(record,8);let timerId=65535;
  for(let i=0;i<5;i++)if(input.getUint32(i*4,true)===0){timerId=i;break;}
  if(timerId!==65535&&allocationSucceeds){record[0]=1;rv.setUint16(2,periodWord,true);const period=periodWord>=32768?periodWord-65536:periodWord;rv.setUint32(4,((timeGetTime>>>4)+period)>>>0,true);tv.setUint32(timerId*4,allocatedFarPointer,true);}
  return {tableBytes:t,recordBytes:record,timerId};
}
export function cancelTimer(table,timerId){
  view(table,20);uint(timerId,16);if(timerId===5)throw new RangeError('Original index5 guard exceeds constructor extent; excluded');
  const t=table.slice(),v=view(t,20),freedPointers=[];
  if(timerId<5){const p=v.getUint32(timerId*4,true);if(p)freedPointers.push(p);v.setUint32(timerId*4,0,true);}
  return {tableBytes:t,freedPointers};
}
export function pollTimers(table,records,timeGetTime,forwardEvent){
  view(table,20);if(!(records instanceof Map)||typeof timeGetTime!=='function'||typeof forwardEvent!=='function')throw new TypeError('Explicit timer records/clock/event services required');
  const t=table.slice(),tv=view(t,20),heap=new Map([...records].map(([p,r])=>[p,r.slice()])),firedIds=[];
  const snapshot=uint(timeGetTime(),32)>>>4;
  for(let slot=0;slot<5;slot++){
    let pointer=tv.getUint32(slot*4,true);if(!pointer)continue;
    if(!heap.has(pointer))throw new RangeError('Unmapped timer record');let record=heap.get(pointer),rv=view(record,8);
    if(rv.getUint32(4,true)>snapshot||record[0]===0)continue;
    firedIds.push(slot);forwardEvent(slot,t,heap);pointer=tv.getUint32(slot*4,true);if(!pointer)continue;
    if(!heap.has(pointer))throw new RangeError('Callback installed unmapped timer');record=heap.get(pointer);rv=view(record,8);
    const now=uint(timeGetTime(),32)>>>4;rv.setUint32(4,(now+rv.getInt16(2,true))>>>0,true);
  }
  return {tableBytes:t,records:heap,firedIds};
}
