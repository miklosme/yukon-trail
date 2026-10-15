// Visible fresh-game initialization independently observed in original004/056/087.
// Hidden game words are intentionally absent; this is not a full state initializer.
import type { LindaJournalAssets } from './journal.ts'
export const observedOpening = Object.freeze({ day: 23, month: 8, year: 1897, cash: 350, food: 0 })
export function openingJournal(assets: LindaJournalAssets, ownerName: string): string {
  if (assets?.schema !== 'selected-linda-journal-v1' || assets.header_strings?.length !== 3) {
    throw new TypeError('Source journal header/vocabulary required')
  }
  if (typeof ownerName !== 'string' || !ownerName || /[^\x20-\x7e]/.test(ownerName)) {
    throw new RangeError('Blank/non-ASCII name behavior remains unrecovered')
  }
  const v = assets.vocabulary,
    f = assets.initial_fragments
  const date = v.months[observedOpening.month - 1] + String(observedOpening.day) + v.early_year
  return (
    assets.header_strings[0] +
    '\r\n' +
    assets.header_strings[1] +
    ownerName +
    '\r\n' +
    assets.header_strings[2] +
    v.separator +
    date +
    f.arrival_prefix.text +
    v.seattle +
    v.separator +
    date +
    v.seattle +
    f.have_prefix.text +
    String(observedOpening.food) +
    f.food_to_cash.text +
    String(observedOpening.cash) +
    f.cash_suffix.text
  )
}
