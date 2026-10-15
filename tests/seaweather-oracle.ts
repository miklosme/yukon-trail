import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import assert from 'node:assert/strict';
import { seaWeatherUpdate } from '../web/rules/seaday.ts';
const report = JSON.parse(readFileSync(new URL('../docs/seaweather-recovery-evidence.json', import.meta.url), 'utf8'));
assert.equal(report.executable_sha256, '9ca8f0a12f4798e762fbf27634f99afcb5c0c1a3836604bf0a4049a73227dd06');
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
for (const [ship, food, gate, seed, stateHash, worldHash, nextSeed] of report.cases) {
  const state = new Uint8Array(0x400).fill(0x55), world = new Uint8Array(0x38).fill(0x55), context = new Uint8Array([0, 0, 0x55, 0x55, 0x55, 0x55]);
  const word = (b, o, v) => { b[o] = v & 255; b[o + 1] = v >>> 8; };
  for (const [o, v] of [[0x320, ship], [0x2fe, food], [0x334, gate], [0x32e, 65535]]) word(state, o, v);
  const actual = seaWeatherUpdate(state, world, context, seed);
  assert.equal(hash(actual.stateBytes), stateHash); assert.equal(hash(actual.worldBytes), worldHash); assert.equal(actual.seed, nextSeed);
}
console.log(`Original sea-weather oracle: ${report.cases.length} full-state/world/RNG cases match; daily/journal excluded.`);
