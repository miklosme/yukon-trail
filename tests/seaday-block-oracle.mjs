import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import assert from 'node:assert/strict';
import { advanceSeaDayBeforeJournal } from '../web/rules/seaday.mjs';
const report = JSON.parse(readFileSync(new URL('../docs/seaday-block-recovery-evidence.json', import.meta.url)));
assert.equal(report.executable_sha256, '9ca8f0a12f4798e762fbf27634f99afcb5c0c1a3836604bf0a4049a73227dd06');
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
for (const [weatherCount, statusCount, gate, date, seed, counter, contextWord, ship, food, stateHash, worldHash, nextSeed] of [...report.cases, ...report.targeted_cases]) {
  const state = new Uint8Array(0x400).fill(0x55), world = new Uint8Array(0x38).fill(0x55), context = new Uint8Array([0, 0, 0x55, 0x55, contextWord & 255, contextWord >>> 8]);
  const word = (b, o, v) => { b[o] = v & 255; b[o + 1] = v >>> 8; };
  for (const [o, v] of [[0x31e, weatherCount], [0x31a, statusCount], [0x334, gate], [0x320, ship], [0x2fe, food], [0x32e, 65535], ...[0x28, 0x2a, 0x30e, 0x310].map((o, i) => [o, date[i]])]) word(state, o, v);
  word(world, 0x18, counter);
  const actual = advanceSeaDayBeforeJournal(state, world, context, seed);
  assert.equal(hash(actual.stateBytes), stateHash); assert.equal(hash(actual.worldBytes), worldHash); assert.equal(actual.seed, nextSeed);
}
console.log(`Original sea-day pre-journal oracle: ${report.cases.length + report.targeted_cases.length} full-state/world/RNG cases match; 2c8c consumer excluded.`);
