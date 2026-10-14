// Selected original event7 formatting and action3 queue only; no date advance.
// Source and original-oracle comparisons: docs/SEATTLE-RULES.md.
function sourceString(value) {
  if (typeof value !== 'string' || /[^\u0001-\u00ff]/u.test(value)) {
    throw new TypeError('Explicit original one-byte NUL-free text required');
  }
  return value;
}
export function lindaEntry(assets, dayWord, monthWord, phaseWord, previousJournal,
                           location) {
  if (assets?.schema !== 'selected-linda-journal-v1') throw new TypeError('Unsupported source vocabulary');
  if (!Array.isArray(location) || location.length !== 3 ||
      location.some(v => !Number.isInteger(v) || v < 0 || v > 65535) ||
      location[0] !== 200 || location[1] !== 0) throw new RangeError('Only region200/place-index0 with unsigned16 scene word is recovered');
  if (!Number.isInteger(dayWord) || dayWord < 1 || dayWord > 31 ||
      !Number.isInteger(monthWord) || monthWord < 1 || monthWord > 12 ||
      !Number.isInteger(phaseWord) || phaseWord < 0 || phaseWord > 65535) {
    throw new RangeError('Unsupported date words');
  }
  sourceString(previousJournal);
  const v = assets.vocabulary;
  if (!Array.isArray(v?.months) || v.months.length !== 12) throw new TypeError('Twelve source months required');
  const signedPhase = phaseWord >= 32768 ? phaseWord - 65536 : phaseWord;
  const parts = previousJournal ? [v.separator] : [];
  parts.push(v.months[monthWord - 1], String(dayWord), signedPhase <= 5 ? v.early_year : v.later_year,
    v.seattle, assets.linda_text);
  let result = '';
  for (const part of parts) {
    sourceString(part);
    if (result.length + part.length < 255) result += part;
  }
  if (previousJournal.length + result.length >= 0x2800) throw new RangeError('Journal overflow retention unrecovered');
  return result;
}
export function queueLindaContinuation(managerBytes) {
  if (!(managerBytes instanceof Uint8Array) || managerBytes.length < 12) {
    throw new TypeError('Explicit manager bytes covering0..11 required');
  }
  const result = managerBytes.slice();
  result.set([1, 0, 3, 0, 0, 0, 0, 0, 0, 0], 2);
  return result;
}
