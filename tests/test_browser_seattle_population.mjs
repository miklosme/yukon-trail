import assert from 'node:assert/strict';
import fs from 'node:fs';
import {initialSeattlePopulation, populationHitContexts} from '../web/rules/seattle-population.mjs';
const source = JSON.parse(fs.readFileSync(process.argv[2]));
const oracle = JSON.parse(fs.readFileSync(new URL('../docs/seattle-population-recovery-evidence.json', import.meta.url)));
for (const c of oracle.cases) {
  const input = {sceneId: c.scene_id, partnerWord: 65535, property320Word: 0,
    downtownVisitWord: c.scene_id === 1000 ? c.scene_visit_word : 0,
    regionArrivalWord: c.region_arrival_word, clockMs: c.clock_ms, mmclockMs: c.mmclock_ms};
  const result = initialSeattlePopulation(source, input);
  assert.deepEqual(result.context_head_to_next, c.original_context_head_to_next);
  assert.deepEqual(result.controller_record_words, c.original_controller_records);
  const hits = populationHitContexts(result, () => ({width: 1, height: 1, stride: 1, pixels: new Uint8Array([9])}));
  assert.deepEqual(hits.map(s => s.objectId), result.context_head_to_next.map(s => s.object_id).reverse());
  assert.throws(() => initialSeattlePopulation(source, {...input, partnerWord: 4}), /unpartnered/);
}
console.log(`${oracle.cases.length} original constructor cases matched`);
