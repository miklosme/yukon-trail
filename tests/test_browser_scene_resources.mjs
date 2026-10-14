// Expected outputs are recorded original instruction results, not Python rules.
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {readSprite, readCelOffsets, readAnimation, readHotspots, hotspotCandidate,
  completeUnflippedSequence, frameRectangle, suspendedSpriteState} from '../web/rules/scene-resources.mjs';
const oracle = JSON.parse(readFileSync(new URL('../docs/browser-scene-resource-evidence.json', import.meta.url)));
const hash = x => createHash('sha256').update(x).digest('hex');
const rowHash = x => hash(JSON.stringify(x));
function words(values) {
  const bytes = new Uint8Array(values.length * 2), v = new DataView(bytes.buffer);
  values.forEach((n, i) => v.setUint16(i * 2, n & 65535, true));
  return bytes;
}
function checked(bytes, resource) {
  assert.equal(hash(bytes), resource.normalized_sha256, 'Fixture differs from original normalized bytes');
  return bytes;
}
const records = {};
for (const [key, resource] of Object.entries(oracle.hotspots.resources)) {
  const bytes = new Uint8Array(2 + resource.record_words.length * 16), v = new DataView(bytes.buffer);
  v.setUint16(0, resource.record_words.length, true);
  resource.record_words.forEach((r, i) => {
    r.slice(0, 6).forEach((n, k) => v.setUint16(2 + i * 16 + k * 2, n & 65535, true));
    v.setUint32(14 + i * 16, r[6], true);
  });
  records[Number(key.split(':')[1])] = readHotspots(checked(bytes, resource));
}
const hotspotRows = oracle.hotspots.native_rows.map(([id, x, y]) => [id, x, y, hotspotCandidate(records[id], x, y)]);
assert.deepEqual(hotspotRows, oracle.hotspots.native_rows);
assert.equal(rowHash(hotspotRows), oracle.hotspots.native_rows_sha256);
const input = oracle.source_inputs, provenance = oracle.sprite.resources;
const spriteBytes = checked(words([...input.sprite_header_words, ...input.sprite_schedules.flat()]), provenance['SPRT:403']);
const celBytes = checked(words([input.cel_offsets_xy.length, ...input.cel_offsets_xy.flat()]), provenance['ACEL:400']);
const animationBytes = checked(words([input.animation_sequences.length, ...input.animation_sequences.flat(),
  input.animation_steps.length, ...input.animation_steps.flat()]), provenance['ASEQ:400']);
// Views with nonzero offsets must parse without exposing adjacent buffer bytes.
const padded = new Uint8Array(spriteBytes.length + 6); padded.set(spriteBytes, 3);
const sprite = readSprite(padded.subarray(3, padded.length - 3));
const offsets = readCelOffsets(celBytes), animation = readAnimation(animationBytes);
const anchor = completeUnflippedSequence(sprite, animation, oracle.sprite.sequence);
const nativeLast = oracle.sprite.geometry_rows.at(-1);
assert.deepEqual(anchor, [nativeLast[4][1], nativeLast[4][0]]);
assert.deepEqual(frameRectangle(anchor, offsets[oracle.sprite.bitmap_frame], oracle.sprite.frame_size_wh), nativeLast[3]);
let current = [sprite.anchorX, sprite.anchorY];
for (const [entry, first, second, rectangle, anchorYX] of oracle.sprite.geometry_rows) {
  if (entry === 0xe62a) current = [second, first];
  else if (entry === 0xe5e4) current = current.map((n, i) => ((n + (i ? first : second) + 32768) & 65535) - 32768);
  else throw new Error('Unsupported original geometry oracle entry');
  assert.deepEqual([current[1], current[0]], anchorYX);
  assert.deepEqual(frameRectangle(current, offsets[oracle.sprite.bitmap_frame], oracle.sprite.frame_size_wh), rectangle);
}
const flags = oracle.sprite.suspended_rows.map(([s, e, v]) => {
  const result = suspendedSpriteState(s, e, v);
  return [s, e, v, result.visibleWord, result.dirtyByte];
});
assert.deepEqual(flags, oracle.sprite.suspended_rows);
assert.equal(rowHash(flags), oracle.sprite.suspended_rows_sha256);
assert.equal(rowHash(oracle.sprite.geometry_rows), oracle.sprite.geometry_rows_sha256);
for (const [reader, bytes] of [[readSprite, spriteBytes], [readCelOffsets, celBytes], [readAnimation, animationBytes]]) {
  assert.throws(() => reader(bytes.subarray(0, bytes.length - 1)), RangeError);
  assert.throws(() => reader([]), TypeError);
}
assert.throws(() => readHotspots(words([1, 1, 2, 3, 4, 0, 0, 0, 0])), RangeError);
assert.throws(() => hotspotCandidate(records[4000], 32768, 0), RangeError);
assert.throws(() => completeUnflippedSequence(sprite, animation, -1), RangeError);
const unsupported = structuredClone(animation); unsupported.steps[12][5] = 1;
assert.throws(() => completeUnflippedSequence(sprite, unsupported, 5), RangeError);
assert.throws(() => suspendedSpriteState(0, 1, 1), RangeError);
console.log(`Scene module: ${hotspotRows.length} original hotspot cases, ${oracle.sprite.geometry_rows.length} geometry calls, ${flags.length} suspension cases; source resource hashes match`);
