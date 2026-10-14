// Bounded original0740 day branch and Wharf post-animation-cleanup branch.
// Explicit caller prerequisites; no complete timer/animation/voyage service.
import {advanceOneOriginalDay} from './calendar.mjs';
function word(v){if(!Number.isInteger(v)||v<0||v>65535)throw new RangeError('Explicit original word required');return v;}
function view(b,n){if(!(b instanceof Uint8Array)||b.length<n)throw new TypeError('Explicit original buffer required');return new DataView(b.buffer,b.byteOffset,b.byteLength);}
export function advanceCountdownDayBlock(before,countdownWord){
  const input=view(before,0x336);word(countdownWord);if(countdownWord===0||countdownWord>=32768)throw new RangeError('Original positive countdown branch required');
  const get=o=>input.getUint16(o,true),date=advanceOneOriginalDay({dayWord:get(0x28),monthWord:get(0x2a),elapsedWord:get(0x30e),phaseWord:get(0x310),gate334Word:get(0x334)});
  const state=before.slice(),out=view(state,0x336);
  [[0x28,date.dayWord],[0x2a,date.monthWord],[0x30e,date.elapsedWord],[0x310,date.phaseWord]].forEach(([o,v])=>out.setUint16(o,v,true));
  return {stateBytes:state,countdownWord:countdownWord-1};
}
export function finishWharfCountdownBlock(before,sceneBytes,managerBytes,countdownWord){
  const input=view(before,0x33c),sv=view(sceneBytes,0x20);view(managerBytes,12);word(countdownWord);
  if(countdownWord!==0&&countdownWord<32768)throw new RangeError('Exhausted signed countdown required');
  if(sv.getUint16(4,true)!==4000||sv.getUint32(0x18,true)===0||sv.getUint16(0x1c,true)!==65535||sv.getUint16(0x1e,true)!==65535)throw new RangeError('Selected Wharf post-timer-cleanup context required');
  const state=before.slice(),scene=sceneBytes.slice(),manager=managerBytes.slice();
  view(scene,0x20).setUint32(0x18,0,true);
  if(!input.getUint16(0x334,true))view(state,0x33c).setUint16(0x33a,0,true);
  const mv=view(manager,12);mv.setUint16(2,1,true);[1,400,31000,0].forEach((v,i)=>mv.setUint16(4+i*2,v,true));
  return {stateBytes:state,sceneBytes:scene,managerBytes:manager,countdownWord};
}
