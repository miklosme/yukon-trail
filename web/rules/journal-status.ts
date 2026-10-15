// Original event4/full-buffer oracle and source table: JOURNAL-STATUS.md.
import type {JournalVocabulary, SourceTextFragment} from './journal.ts';
/** tools/prepare_journal_status.py output (schema recovered-journal-status-v1). */
export interface JournalStatusAssets {
  schema: string;
  vocabulary: JournalVocabulary;
  fragments: {
    have: SourceTextFragment;
    kilograms: SourceTextFragment;
    pounds: SourceTextFragment;
    cash: SourceTextFragment;
    gold_prefix: SourceTextFragment;
    gold: SourceTextFragment;
  };
  /** Complete original NE13:0df4 rows: [state index, compare, frame, y, x]. */
  inventory_table: {entries: number[][]; sha256?: string};
  provenance?: {executable_sha256?: string};
}
export interface JournalStatusResult { text: string; snapshotWords: number[]; appended: boolean }
export interface JournalInventoryEntry { ordinal: number; frame: number; anchorXY: [number, number] }
const word = (n: unknown): number => {
  if (typeof n !== 'number' || !Number.isInteger(n) || n < 0 || n > 65535) throw new RangeError('Original unsigned word required');
  return n;
};
const signed = (n: number): number => n >= 32768 ? n - 65536 : n;
const text = (s: unknown): string => {
  if (typeof s !== 'string' || /[^\u0001-ÿ]/u.test(s)) throw new TypeError('Original NUL-free one-byte text required');
  return s;
};
function stateReader(state: Uint8Array): (offset: number) => number {
  if (!(state instanceof Uint8Array) || state.length < 0x314) throw new TypeError('Explicit original state bytes required');
  const v = new DataView(state.buffer, state.byteOffset, state.byteLength);
  return offset => v.getUint16(offset, true);
}
export function currentJournalStatus(assets: JournalStatusAssets, state: Uint8Array, snapshotWords: readonly number[], previousJournal: string, unitsWord: number): JournalStatusResult {
  if (assets?.schema !== 'recovered-journal-status-v1') throw new TypeError('Verified source status vocabulary required');
  if (!Array.isArray(snapshotWords) || snapshotWords.length !== 6) throw new TypeError('Cached day/month/food/cash/gold/dirty words required');
  snapshotWords.forEach(word); word(unitsWord); text(previousJournal);
  const get = stateReader(state), day = get(0x28), month = get(0x2a);
  if (day < 1 || day > 31 || month < 1 || month > 12 || get(0x34) !== 200 || get(0x36) !== 0)
    throw new RangeError('Selected Seattle date/place scope required');
  const food = get(0x2fe), cash = get(0x2fa), gold = get(0x2fc);
  const append = snapshotWords[0] !== day || snapshotWords[2] !== food || snapshotWords[3] !== cash ||
    snapshotWords[4] !== gold || snapshotWords[5] === 1;
  const updated = [day, month, food, cash, gold, append ? 0 : snapshotWords[5]];
  if (!append) return {text: previousJournal, snapshotWords: updated, appended: false};
  const v = assets.vocabulary, f = assets.fragments;
  if (!Array.isArray(v?.months) || v.months.length !== 12) throw new TypeError('Source month vocabulary required');
  const parts = previousJournal ? [v.separator] : [];
  parts.push(v.months[month - 1], String(day), signed(get(0x310)) <= 5 ? v.early_year : v.later_year,
    v.seattle, f.have.text, String(unitsWord ? Math.trunc(signed(food) * 45 / 100) : signed(food)),
    unitsWord ? f.kilograms.text : f.pounds.text, String(signed(cash)), f.cash.text);
  if (signed(gold) > 0) parts.push(f.gold_prefix.text, String(signed(gold)), f.gold.text);
  let entry = '';
  for (const part of parts) { text(part); if (entry.length + part.length < 255) entry += part; }
  if (previousJournal.length + entry.length >= 0x2800) throw new RangeError('Original overflow prompt/retention path unsupported');
  return {text: previousJournal + entry, snapshotWords: updated, appended: true};
}
export function journalInventoryEntries(assets: JournalStatusAssets, state: Uint8Array): JournalInventoryEntry[] {
  if (assets?.schema !== 'recovered-journal-status-v1' || assets.inventory_table?.entries?.length !== 16)
    throw new TypeError('Complete verified source inventory table required');
  const get = stateReader(state);
  return assets.inventory_table.entries.flatMap(([index, compare, frame, y, x], ordinal): JournalInventoryEntry[] => {
    if (![index, compare, frame, y, x].every(Number.isInteger) || index < -1 || index > 8)
      throw new RangeError('Selected inventory table field outside source scope');
    const enabled = index === -1 || ([7, 8].includes(index) ? signed(get(0x2fa + index * 2)) === compare : get(0x2fa + index * 2) !== 0);
    return enabled && frame >= 0 ? [{ordinal, frame, anchorXY: [x, y]}] : [];
  });
}
