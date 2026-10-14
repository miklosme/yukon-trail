import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import assert from 'node:assert/strict';
import { advanceSeaDay } from '../web/rules/seaday.mjs';
const report = JSON.parse(readFileSync(new URL('../docs/seaday-combined-recovery-evidence.json', import.meta.url)));
assert.equal(report.executable_sha256, '9ca8f0a12f4798e762fbf27634f99afcb5c0c1a3836604bf0a4049a73227dd06');
assert.equal(report.archive_sha256, '438d729386cdb2effb120ed7652d14af00fb8a0e78f4426c12b17c934c3db8b6');
const strings = report.resource.strings_hex.map(h => new Uint8Array(Buffer.from(h, 'hex')));
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
for (const [weatherCount, statusCount, gate, date, seed, ship, contextWord, counter, seen, stateHash, worldHash, textHash, nextSeed, constructed, selection] of [...report.cases, ...report.targeted_cases]) {
  const state = new Uint8Array(0x400).fill(0x55), world = new Uint8Array(0x38).fill(0x55), context = new Uint8Array([0, 0, 0x55, 0x55, contextWord & 255, contextWord >>> 8]), text = new Uint8Array(256).fill(0x55);
  text.set(Buffer.from('old text\0'));
  const word = (b, o, v) => { b[o] = v & 255; b[o + 1] = v >>> 8; };
  for (const [o, v] of [[0x31e, weatherCount], [0x31a, statusCount], [0x334, gate], [0x320, ship], [0x2fe, 2400], [0x32e, 65535], ...[0x28, 0x2a, 0x30e, 0x310].map((o, i) => [o, date[i]])]) word(state, o, v);
  for (let flag = 0; flag < 10; flag++) word(state, 0x19e + 2 * flag, seen);
  word(world, 0x18, counter); word(world, 0x28, 0); word(world, 0x2a, 0); new DataView(world.buffer).setUint32(0x10, 0x40008000, true);
  const actual = advanceSeaDay(state, world, context, text, strings, seed);
  assert.equal(hash(actual.stateBytes), stateHash); assert.equal(hash(actual.worldBytes), worldHash); assert.equal(hash(actual.textBytes), textHash); assert.equal(actual.seed, nextSeed); assert.equal(actual.selection, selection); assert.equal(actual.selection !== null, constructed);
}
console.log(`Original composed sea-day oracle: ${report.cases.length + report.targeted_cases.length} full-state/world/text/RNG cases match; resource ownership and later notification excluded.`);
