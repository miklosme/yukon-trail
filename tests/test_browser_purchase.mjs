// Expected matrix hash is unchanged original dispatch/purchase full sentinel state.
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {purchaseSelectedWhipsaw, whipsawOptionVisible} from '../web/rules/purchase.mjs';
const native = JSON.parse(readFileSync(new URL('../docs/whipsaw-recovery-evidence.json', import.meta.url)));
const hash = data => createHash('sha256').update(data).digest('hex');
const rows = [];
for (const cashWord of [0, 7, 8, 20, 850, 32767, 32768, 65535]) {
  for (const bankWord of [0, 3, 8, 20, 32767, 32768, 65535]) {
    for (const gate334Word of [0, 1]) {
      const before = {cashWord, bankWord, whipsawWord: 0, partnerWord: 4, word318: 0x1234, gate334Word};
      const result = purchaseSelectedWhipsaw(before);
      const buffer = Buffer.alloc(0x350, 0x55);
      for (const [offset, field] of [[0x2fa, 'cashWord'], [0x2fc, 'bankWord'], [0x306, 'whipsawWord'], [0x312, 'partnerWord'], [0x318, 'word318'], [0x334, 'gate334Word']]) {
        buffer.writeUInt16LE(result.state[field], offset);
      }
      const refusals = result.refusalTreeId === null ? [] : [[0x2000, 0x6000, result.refusalTreeId, 300]];
      rows.push([cashWord, bankWord, gate334Word, hash(buffer), Number(result.actionSuccess), refusals]);
      assert.equal(before.whipsawWord, 0, 'Input purchase state mutated');
    }
  }
}
assert.equal(rows.length, native.cases);
assert.equal(hash(JSON.stringify(rows)), native.matrix_sha256);
const source = JSON.parse(readFileSync(new URL('../public/game-assets/seattle-opening-v2-20261013/TREE-2100.json', import.meta.url)));
function* records(node) {
  yield node.record;
  for (const choice of node.choices) { yield choice.record; if (choice.response) yield* records(choice.response); }
}
const action = [...records(source.graph.root)].find(r => r.offset === 0x4d14).action;
assert.deepEqual(action, [220, 109, 8, 0]);
const selected = {cashWord: 850, bankWord: 0, whipsawWord: 0, partnerWord: 4, word318: 0x1234, gate334Word: 0};
const result = purchaseSelectedWhipsaw(selected, action, 17);
assert.equal(result.state.cashWord, 842);
assert.equal(whipsawOptionVisible(result.state.whipsawWord), false);
assert.equal(whipsawOptionVisible(0), true);
assert.throws(() => purchaseSelectedWhipsaw({}), TypeError);
assert.throws(() => purchaseSelectedWhipsaw({...selected, whipsawWord: 1}), RangeError);
assert.throws(() => purchaseSelectedWhipsaw(selected, [220, 109, 9, 0]), RangeError);
assert.throws(() => whipsawOptionVisible(undefined), RangeError);
console.log(`Purchase module matches ${rows.length} original whipsaw dispatch/state cases`);
