// Expected matrix identity comes from original x86 execution, not JS/Python rules.
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {acceptLinda, changeMoneySlotZero, lindaSceneChildEligible} from '../web/rules/seattle.mjs';
const native = JSON.parse(readFileSync(new URL('../docs/seattle-recovery-evidence.json', import.meta.url)));
const matrix = native.differential_boundary_matrix;
const rows = [];
for (const cashWord of matrix.cash_words) {
  for (const bankWord of matrix.bank_words) {
    for (const delta of matrix.deltas) {
      for (const flag334Word of matrix.flag334) {
        const initial = {cashWord, bankWord, partnerWord: 0, flag334Word, flag344Word: 0};
        const result = delta === 500 ? acceptLinda(initial) : changeMoneySlotZero(
          {...initial, partnerWord: flag334Word ? 0 : 4, flag344Word: 1}, delta);
        const s = result.state;
        rows.push([cashWord, bankWord, delta, flag334Word, s.cashWord, s.bankWord,
          s.partnerWord, s.flag344Word, Number(result.success)]);
        assert.equal(initial.partnerWord, 0, 'Input state mutated');
      }
    }
  }
}
assert.equal(rows.length, matrix.cases);
assert.equal(createHash('sha256').update(JSON.stringify(rows)).digest('hex'), matrix.rows_sha256);
const child = JSON.parse(readFileSync(new URL('../docs/linda-child-recovery-evidence.json', import.meta.url)));
for (const test of child.cases) assert.equal(lindaSceneChildEligible(test.partner_word), test.eligible);
assert.throws(() => acceptLinda({}), TypeError);
assert.throws(() => lindaSceneChildEligible(-1), RangeError);
assert.throws(() => changeMoneySlotZero({cashWord: 0, bankWord: 0, partnerWord: 0,
  flag334Word: 0, flag344Word: 0}, 65536), RangeError);
console.log(`Browser rule module matches ${rows.length} original money cases and ${child.cases.length} original eligibility cases`);
