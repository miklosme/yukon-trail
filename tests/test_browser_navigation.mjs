import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {readHotspots} from '../web/rules/scene-resources.mjs';
import {dispatchSeattleClientButton, queuedSeattleScene, spritePixelHit} from '../web/rules/seattle-navigation.mjs';
const oracle = JSON.parse(readFileSync(new URL('../docs/navigation-recovery-evidence.json', import.meta.url)));
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
const records = {};
for (const [id, resource] of Object.entries(oracle.resources)) {
  const bytes = new Uint8Array(2 + resource.record_words.length * 16), v = new DataView(bytes.buffer);
  v.setUint16(0, resource.record_words.length, true);
  resource.record_words.forEach((r, i) => {
    r.slice(0, 6).forEach((n, k) => v.setUint16(2 + i * 16 + k * 2, n & 65535, true));
    v.setUint32(14 + i * 16, r[6], true);
  });
  assert.equal(hash(bytes), resource.normalized_sha256);
  records[Number(id.split(':')[1])] = readHotspots(bytes);
}
const f = oracle.synthetic_sprite_fixture;
const sprite = {rectangleTLBR: f.rectangle_tlbr, width: f.frame_size_wh[0], height: f.frame_size_wh[1],
  stride: f.stride, pixels: new Uint8Array(f.pixels), objectId: f.object_id};
const rows = oracle.native_rows.map(([rid, x, y, message, activationWord, countdownWord, managerBusyWord, hasSprite]) =>
  [rid, x, y, message, activationWord, countdownWord, managerBusyWord, hasSprite,
    dispatchSeattleClientButton(records[rid], {x, y, message, activationWord, countdownWord,
      managerBusyWord, sprites: hasSprite ? [sprite] : []})]);
assert.deepEqual(rows, oracle.native_rows);
const ticketRows = oracle.derived_ticket_rows.map(([rid, x, y, message, activationWord, countdownWord, managerBusyWord, hasSprite]) =>
  [rid, x, y, message, activationWord, countdownWord, managerBusyWord, hasSprite,
    dispatchSeattleClientButton(records[rid], {x, y, message, activationWord, countdownWord, managerBusyWord,
      sprites: hasSprite ? [sprite] : [], handler: 'ticket-office'})]);
assert.deepEqual(ticketRows, oracle.derived_ticket_rows);
assert.equal(hash(JSON.stringify(ticketRows)), oracle.derived_ticket_rows_sha256);
assert.equal(hash(JSON.stringify(rows)), oracle.native_rows_sha256);
assert.throws(() => dispatchSeattleClientButton(records[4000], {x: 580, y: 350, message: 0x201,
  activationWord: 0, countdownWord: 0, managerBusyWord: 0}), TypeError);
assert.throws(() => queuedSeattleScene([2, 300, 3500]), RangeError);
assert.throws(() => spritePixelHit({...sprite, stride: 0}, 160, 168), RangeError);
assert.throws(() => dispatchSeattleClientButton(records[4000], {x: 580, y: 350, message: 0x201,
  activationWord: 0, countdownWord: 0, managerBusyWord: 0, sprites: [], sceneDeferredActionWord: 1}), RangeError);
console.log(`Navigation module matches ${rows.length} original instruction cases, plus ${ticketRows.length} actual ticket-office handler cases; both include cached-frame sprite hit/interception`);
