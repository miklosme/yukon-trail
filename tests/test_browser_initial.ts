// All expected full-buffer hashes/seed results measured in original native code.
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {originalRandomStep, resetOriginalState} from '../web/rules/initial.ts';
const native = JSON.parse(readFileSync(new URL('../docs/initial-state-recovery-evidence.json', import.meta.url), 'utf8'));
for (const test of native.cases) {
  const before = test.pattern === 'ramp' ? Uint8Array.from({length: 0x400}, (_, i) => (i * 37 + 11) & 255) : new Uint8Array(0x400).fill(test.pattern === '55' ? 0x55 : 0);
  const snapshot = Uint8Array.from(before);
  const step = originalRandomStep(test.seed);
  assert.equal(step.nextSeed, test.next_seed);
  assert.equal(step.randomWord, test.random_word);
  const bytes = resetOriginalState(before, step.randomWord);
  assert.equal(createHash('sha256').update(bytes).digest('hex'), test.state_sha256);
  assert.deepEqual(before, snapshot);
}
assert.throws(() => originalRandomStep(undefined), RangeError);
assert.throws(() => resetOriginalState(new Uint8Array(0x386), undefined), RangeError);
assert.throws(() => resetOriginalState(new Uint8Array(0x385), 1), TypeError);
console.log(`Initial state module matches ${native.native_cases} original full-reset/RNG cases`);
