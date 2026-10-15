// Source assets are optional local inputs; expected hashes come from original x86.
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {lindaEntry, queueLindaContinuation} from '../web/rules/journal.ts';
if (!process.argv[2]) throw new Error('Pass the prepared ignored selected journal asset JSON');
const assets = JSON.parse(readFileSync(process.argv[2], 'utf8'));
const native = JSON.parse(readFileSync(new URL('../docs/journal-recovery-evidence.json', import.meta.url), 'utf8'));
assert.equal(assets.provenance.executable_sha256, native.source_sha256);
assert.equal(assets.provenance.archive_sha256, native.archive_sha256);
assert.equal(assets.provenance.sha256, native.resource_sha256);
const rows = [];
for (let month = 1; month <= 12; month++) {
  for (const day of [1, 9, 24, 31]) {
    for (const phase of [0, 5, 6, 32767, 32768, 65535]) {
      for (const prior of ['', 'earlier entry']) {
        const entry = lindaEntry(assets, day, month, phase, prior, [200, 0, 0]);
        rows.push([day, month, phase, Boolean(prior),
          createHash('sha256').update(entry, 'latin1').digest('hex')]);
      }
    }
  }
}
assert.equal(rows.length, native.differential_matrix_cases);
assert.equal(createHash('sha256').update(JSON.stringify(rows)).digest('hex'), native.matrix_rows_sha256);
const locationRows = [];
for (const test of native.seattle_location_matrix) {
  const [location, day, month, phase, nonempty, expectedHash] = test;
  const actualHash = createHash('sha256').update(lindaEntry(assets, day, month, phase,
    nonempty ? 'earlier entry' : '', location), 'latin1').digest('hex');
  assert.equal(actualHash, expectedHash);
  locationRows.push([location, day, month, phase, nonempty, actualHash]);
}
assert.equal(locationRows.length, native.seattle_location_cases);
assert.equal(createHash('sha256').update(JSON.stringify(locationRows)).digest('hex'), native.seattle_location_rows_sha256);
assert.throws(() => lindaEntry(assets, 24, 8, 1, '', [200,1,4000]), RangeError);
assert.throws(() => lindaEntry(assets, 24, 8, 1, '', [200,0,65536]), RangeError);
for (const test of native.native_queue_cases) {
  const initial = new Uint8Array(Buffer.from(test.before_hex, 'hex'));
  assert.equal(Buffer.from(queueLindaContinuation(initial)).toString('hex'), test.after_hex);
  assert.equal(Buffer.from(initial).toString('hex'), test.before_hex);
}
assert.throws(() => lindaEntry(assets, 24, 8, 0, 'x'.repeat(0x2800), [200,0,0]), RangeError);
assert.throws(() => lindaEntry(assets, 24, 8, 0, '', [201,0,0]), RangeError);
assert.throws(() => queueLindaContinuation(new Uint8Array(11)), TypeError);
assert.throws(() => lindaEntry(assets, 24, 8, 0, '🙂', [200,0,0]), TypeError);
console.log(`Browser journal matches ${rows.length} original formatter cases and ${locationRows.length} Seattle tuple cases and3 original queue cases`);
