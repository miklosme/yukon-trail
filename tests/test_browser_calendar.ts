// Independent original full-state/matrix identities, no GUI or wall clock.
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {MONTH_LENGTHS, advanceOneOriginalDay, enterSelectedSeattleScene} from '../web/rules/calendar.ts';
const json = path => JSON.parse(readFileSync(new URL(path, import.meta.url), 'utf8'));
const hash = data => createHash('sha256').update(data).digest('hex');
const native = json('../docs/calendar-recovery-evidence.json');
const rows = [];
function dateState(dayWord, monthWord, elapsedWord, phaseWord, gate334Word) {
  return {dayWord, monthWord, elapsedWord, phaseWord, gate334Word};
}
function writeDate(buffer, state) {
  for (const [offset, field] of [[0x28, 'dayWord'], [0x2a, 'monthWord'], [0x30e, 'elapsedWord'], [0x310, 'phaseWord'], [0x334, 'gate334Word']]) buffer.writeUInt16LE(state[field], offset);
}
for (const [m, days] of MONTH_LENGTHS.entries()) {
  for (let day = 1; day <= days; day++) {
    for (const [elapsed, phase] of [[0, 0], [32767, 5], [65535, 65535]]) {
      for (const gate of [0, 1]) {
        const before = dateState(day, m + 1, elapsed, phase, gate);
        const state = advanceOneOriginalDay(before);
        const buffer = Buffer.alloc(0x350, 0x55); writeDate(buffer, state);
        rows.push([day, m + 1, elapsed, phase, gate, hash(buffer), gate ? 0 : 1]);
        assert.equal(before.dayWord, day, 'Input date mutated');
      }
    }
  }
}
assert.equal(rows.length, native.native_cases);
assert.equal(hash(JSON.stringify(rows)), native.matrix_sha256);
const entry = json('../docs/scene-entry-recovery-evidence.json');
for (const test of entry.cases) {
  const before = dateState(...(test.before_date as [number, number, number, number, number]));
  const result = enterSelectedSeattleScene(before, test.scene, test.before_visit);
  assert.deepEqual([result.state.dayWord, result.state.monthWord, result.state.elapsedWord, result.state.phaseWord], test.after_date);
  assert.equal(result.visitWord, test.after_visit);
  const buffer = Buffer.alloc(0x350, 0x55); writeDate(buffer, result.state);
  buffer.writeUInt16LE(result.visitWord, 0x2aa + 2 * (test.scene / 1000));
  assert.equal(hash(buffer), test.state_sha256);
}
assert.throws(() => advanceOneOriginalDay({} as never), TypeError);
assert.throws(() => advanceOneOriginalDay(dateState(29, 2, 0, 0, 0)), RangeError);
assert.throws(() => enterSelectedSeattleScene(dateState(23, 8, 0, 0, 0), 5000, 0), RangeError);
console.log(`Calendar module matches ${rows.length} original day cases and ${entry.native_cases} original scene-entry cases`);
