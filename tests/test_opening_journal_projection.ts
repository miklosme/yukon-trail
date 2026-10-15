import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {openingJournalKnownWords,openingJournalProjection,openingJournalCacheWords} from '../web/rules/opening-journal-state.ts';
import {currentJournalStatus,journalInventoryEntries} from '../web/rules/journal-status.ts';
import {resetOriginalState} from '../web/rules/initial.ts';
const initial=JSON.parse(readFileSync(new URL('../docs/initial-state-recovery-evidence.json',import.meta.url), 'utf8'));
const journal=JSON.parse(readFileSync(new URL('../docs/journal-status-recovery-evidence.json',import.meta.url), 'utf8'));
if (process.argv[2]) {
  const manifest=JSON.parse(readFileSync(process.argv[2]+'/manifest.json', 'utf8'));
  const record=manifest.journal_status;
  const bytes=readFileSync(process.argv[2]+'/'+record.file);
  assert.equal(createHash('sha256').update(bytes).digest('hex'),record.sha256);
  assert.deepEqual(JSON.parse(bytes.toString('utf8')),journal.source_assets,'Imported status differs from original oracle vocabulary/table');
  assert.equal(manifest.executable_sha256,journal.executable_sha256);
}
const nativeReset=Buffer.from(initial.sentinel_sample_hex,'hex');
const projection=openingJournalProjection(), view=new DataView(projection.buffer);
// Compare deterministic reset words to actual original sentinel reset output.
for(const [offset,value] of openingJournalKnownWords) {
  assert.equal(view.getUint16(offset,true),value);
  if (![0x34,0x36,0x38].includes(offset)) assert.equal(value,nativeReset.readUInt16LE(offset));
}
assert.equal(view.getUint16(0x34,true),200);assert.equal(view.getUint16(0x36,true),0);
assert.deepEqual(openingJournalCacheWords(),journal.capture094.original_first_event4.snapshot_words);
assert.throws(()=>resetOriginalState(projection,0),TypeError,'Projection must not masquerade as a full world');
const text=Buffer.from(journal.capture094.original_first_event4.text_hex,'hex').toString('latin1');
const reopened=currentJournalStatus(journal.source_assets,projection,openingJournalCacheWords(),text,0);
assert.equal(reopened.text,text);assert.equal(reopened.appended,false);
// Independently measured native024 overlays from journal-capture-comparison.
const entries=journalInventoryEntries(journal.source_assets,projection).map(({frame,anchorXY:[x,y]})=>[frame,x+20,y+59]);
assert.deepEqual(entries,[[10,321,137],[6,470,312],[11,488,397]]);
console.log('Known journal words match original reset, cache/formatter and native024 geometry; full world remains unavailable');
