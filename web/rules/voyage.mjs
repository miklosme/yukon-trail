// Selected original SMAP31000 rule3482/41e0 and36a2 constructor state block.
// Weather/date callback, cutscene creation, audio and graphics are outside.
import {originalRandomStep} from './initial.mjs';
const events=new Set([0,1,2,31101,31102,31103]);
function word(v){if(!Number.isInteger(v)||v<0||v>65535)throw new RangeError('Explicit original word required');return v;}
function view(b,n){if(!(b instanceof Uint8Array)||b.length<n)throw new TypeError('Explicit original buffer required');return new DataView(b.buffer,b.byteOffset,b.byteLength);}
function validateRows(rows){if(!Array.isArray(rows)||rows.length!==45||rows.some(r=>!Array.isArray(r)||r.length!==3||r.some(v=>!Number.isInteger(v)||v<0||v>65535)||!events.has(r[2])))throw new RangeError('Explicit selected SMAP source rows required');return rows;}
export function readSeaMap(normalized){
  const v=view(normalized,2),count=v.getUint16(0,true);
  if(count!==45||normalized.length!==2+count*6)throw new RangeError('Only selected SMAP31000 extent recovered');
  return validateRows(Array.from({length:count},(_,i)=>[0,1,2].map(j=>v.getUint16(2+i*6+j*2,true))));
}
export function initializeMapStateBlock(before,sceneBytes){
  const input=view(before,0x33a);view(sceneBytes,0x90);const state=before.slice(),scene=sceneBytes.slice(),out=view(state,0x33a),sv=view(scene,0x90);
  if(!input.getUint16(0x334,true)){out.setUint16(0x330,31000,true);out.setUint16(0x332,400,true);}
  sv.setUint16(0x88,input.getUint16(0x336,true),true);sv.setUint16(0x8c,input.getUint16(0x338,true),true);
  return {stateBytes:state,sceneBytes:scene};
}
export function advanceSeaWaypoint(before,sceneBytes,managerBytes,records,randomSeed,soundModeWord){
  const input=view(before,0x33a);view(sceneBytes,0xa6);view(managerBytes,12);validateRows(records);word(soundModeWord);
  if(!Number.isInteger(randomSeed)||randomSeed<0||randomSeed>0xffffffff)throw new RangeError('Explicit original RNG seed required');
  const state=before.slice(),scene=sceneBytes.slice(),manager=managerBytes.slice(),sv=view(scene,0xa6),mv=view(manager,12),out=view(state,0x33a);
  const get=o=>sv.getUint16(o,true),put=(o,v)=>sv.setUint16(o,v&65535,true),queue=a=>{mv.setUint16(2,1,true);a.forEach((v,i)=>mv.setUint16(4+i*2,v,true));};
  const index=get(0x88);if(index>=records.length)throw new RangeError('Current source waypoint index out of range');
  const partial=(get(0x8c)+get(0x96))&65535;put(0x8c,partial);const openScenes=[],audioPointers=[];let nextSeed=randomSeed;
  if(partial>=25&&partial<32768){
    put(0x8c,partial-25);const event=records[index][2];
    if(event===1){put(0x7a,1);if(input.getUint16(0x30a,true)===11)queue([2,300,26000,0]);}
    else if(event===2){
      put(0x88,0);put(0x8c,0);put(0x7a,1);put(0x7c,1);let destination=input.getUint16(0x322,true);
      if(![5000,9000].includes(destination)){const r=originalRandomStep(nextSeed);nextSeed=r.nextSeed;destination=r.randomWord%2===0?5000:9000;}
      queue([1,200,destination,0]);
    }else if([31101,31102,31103].includes(event)){
      if(event===31102&&soundModeWord!==2)audioPointers.push(sv.getUint32(0xa2,true));
      put(0x80,1);put(0x7a,1);openScenes.push([event,1700]);
    }else{put(0x80,0);put(0x7a,0);}
    if(event!==2)put(0x88,index+1);
  }
  if(!input.getUint16(0x334,true)){out.setUint16(0x336,get(0x88),true);out.setUint16(0x338,get(0x8c),true);}
  return {stateBytes:state,sceneBytes:scene,managerBytes:manager,nextSeed,openScenes,audioPointers};
}
