import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import assert from 'node:assert/strict';
import { seaMessageUpdate, readSeaEventStrings } from '../web/rules/seaday.mjs';
const report = JSON.parse(readFileSync(new URL('../docs/seamessage-recovery-evidence.json', import.meta.url)));
assert.equal(report.executable_sha256, '9ca8f0a12f4798e762fbf27634f99afcb5c0c1a3836604bf0a4049a73227dd06');
assert.equal(report.archive_sha256, '438d729386cdb2effb120ed7652d14af00fb8a0e78f4426c12b17c934c3db8b6');
const strings = report.resource.strings_hex.map(h => new Uint8Array(Buffer.from(h, 'hex')));
const normalized = new Uint8Array(Buffer.concat([Buffer.from([9, 0]), ...strings.flatMap(s => [Buffer.from(s), Buffer.from([0])])]));
assert.equal(createHash('sha256').update(normalized).digest('hex'), report.resource.normalized_sha256);
assert.deepEqual(readSeaEventStrings(normalized), strings);
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
for (const [ship, contextWord, weatherMarker, eventMarker, weatherSeen, eventSeen, stateHash, worldHash, textHash, constructed, selection] of report.cases) {
  const state = new Uint8Array(0x400).fill(0x55), world = new Uint8Array(0x38).fill(0x55), context = new Uint8Array([0, 0, 0x55, 0x55, contextWord & 255, contextWord >>> 8]), text = new Uint8Array(256).fill(0x55);
  text.set(Buffer.from('old text\0'));
  const word = (b, o, v) => { b[o] = v & 255; b[o + 1] = v >>> 8; };
  word(state, 0x320, ship); word(state, 0x1a0, weatherSeen);
  if (eventMarker) word(state, 0x19e + 2 * (eventMarker + 3), eventSeen);
  word(world, 0x28, weatherMarker); word(world, 0x2a, eventMarker); new DataView(world.buffer).setUint32(0x10, 0x40008000, true);
  const actual = seaMessageUpdate(state, world, context, text, strings);
  assert.equal(hash(actual.stateBytes), stateHash); assert.equal(hash(actual.worldBytes), worldHash); assert.equal(hash(actual.textBytes), textHash); assert.equal(actual.selection, selection); assert.equal(actual.selection !== null, constructed);
}
console.log(`Original sea-message blocks oracle: ${report.cases.length} state/world/text cases match; resource ownership excluded.`);
