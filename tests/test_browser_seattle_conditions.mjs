import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {evaluateSeattleCondition} from '../web/rules/seattle-conditions.mjs';
const proof=JSON.parse(readFileSync(new URL('../docs/seattle-condition-recovery-evidence.json',import.meta.url)));
for(const [pattern,kind,value,index,flag,offset,other,units,scene,items,expected] of proof.native_cases) {
  const state=new Uint8Array(0x386);
  if(pattern===1)state.fill(0x55);
  if(pattern===2)state.forEach((_,i)=>{state[i]=i&255;});
  const view=new DataView(state.buffer);
  view.setUint16(0x218+2*index,flag,true);view.setUint16(offset,other,true);
  if(items)items.forEach((v,i)=>view.setUint16([0x300,0x302,0x306][i],v,true));
  const before=state.slice();
  assert.equal(Number(evaluateSeattleCondition([kind,value],state,index,units)),expected,
    `${pattern}/${kind}/${value}/${index}/${flag}/${offset}/${other}/${units}/${scene}/${items}`);
  assert.deepEqual(state,before);
}
const state=new Uint8Array(0x386);
assert.throws(()=>evaluateSeattleCondition([99,0],state,17,0),RangeError);
assert.throws(()=>evaluateSeattleCondition([11,106],state,17,0),RangeError);
assert.throws(()=>evaluateSeattleCondition([7,1],state,9,0),RangeError);
assert.throws(()=>evaluateSeattleCondition([2,1],new Uint8Array(0x314),17,0),TypeError);
assert.throws(()=>evaluateSeattleCondition([2,1],state,61,0),RangeError);
assert.throws(()=>evaluateSeattleCondition([2,1],state,17,undefined),RangeError);
const tested=new Set(proof.native_cases.map(row=>`${row[1]},${row[2]}`));
for(const resource of Object.values(proof.sources))for(const record of resource.nonzero_conditions)
  assert.ok(tested.has(record.words.join(',')),`Source condition lacks native comparison: ${record.words}`);
console.log(`Seattle predicates match ${proof.native_cases.length} original cases across all condition pairs in ${Object.keys(proof.sources).length} source graphs; UI filtering remains untested`);
