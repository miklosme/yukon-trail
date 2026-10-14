import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {currentJournalStatus, journalInventoryEntries} from '../web/rules/journal-status.mjs';
const oracle = JSON.parse(readFileSync(new URL('../docs/journal-status-recovery-evidence.json', import.meta.url)));
const assets = oracle.source_assets;
const table = new Uint8Array(160), tableView = new DataView(table.buffer);
assets.inventory_table.entries.forEach((r, i) => r.forEach((v, j) => tableView.setInt16(i * 10 + j * 2, v, true)));
assert.equal(createHash('sha256').update(table).digest('hex'), assets.inventory_table.sha256);
for (const field of Object.values(assets.fragments)) {
  assert.equal(createHash('sha256').update(Buffer.from(field.text + '\0', 'latin1')).digest('hex'), field.sha256);
}
const state = changes => {
  const data = new Uint8Array(0x386), view = new DataView(data.buffer);
  for (const [offset, value] of [...oracle.base_state_words, ...changes]) view.setUint16(offset, value, true);
  return data;
};
for (const c of oracle.status_cases) {
  const data = state(c.state_word_changes), before = data.slice();
  const result = currentJournalStatus(assets, data, c.snapshot_words, Buffer.from(c.prior_hex, 'hex').toString('latin1'), c.units_word);
  assert.equal(Buffer.from(result.text, 'latin1').toString('hex'), c.original.text_hex, c.name);
  assert.deepEqual(result.snapshotWords, c.original.snapshot_words, c.name);
  assert.equal(result.appended, c.original.allocations.length > 0, c.name);
  assert.deepEqual(data, before);
}
for (const c of oracle.inventory_cases) {
  const selected = journalInventoryEntries(assets, state(c.state_word_changes));
  const flags = assets.inventory_table.entries.map((_, i) => Number(selected.some(r => r.ordinal === i)));
  assert.deepEqual(flags, c.original_enabled);
}
const capture = oracle.capture094;
const first = currentJournalStatus(assets, state([[0x28, 23], [0x38, 4000]]), capture.original_event0.snapshot_words,
  Buffer.from(capture.original_event0.text_hex, 'hex').toString('latin1'), 0);
assert.equal(Buffer.from(first.text, 'latin1').toString('hex'), capture.original_first_event4.text_hex);
const second = currentJournalStatus(assets, state([[0x38, 2000]]), first.snapshotWords, first.text, 0);
assert.equal(Buffer.from(second.text, 'latin1').toString('hex'), capture.original_second_event4.text_hex);
assert.deepEqual(second.text.split(/\r?\n/u).map(s => s.trim()).filter(Boolean), capture.observed_nonempty_tail_lines);
console.log(`Journal status matches ${oracle.status_cases.length} original full-buffer cases; inventory matches ${oracle.inventory_cases.length * 16} original selectors; native094 tail matches.`);
