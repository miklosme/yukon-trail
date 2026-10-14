// Bounded original NE1:9df8/a652/a184 and SCRP4000 record15 behavior.
// Sources, native comparisons and exclusions: docs/SEATTLE-RULES.md.
// No state defaults, calendar progression or scene-loop effects are supplied.
const fields = ['cashWord', 'bankWord', 'partnerWord', 'flag334Word', 'flag344Word'];
function word(value) {
  if (!Number.isInteger(value) || value < 0 || value > 65535) {
    throw new RangeError('Expected an original unsigned 16-bit word');
  }
  return value;
}
function stateWords(state) {
  if (!state || fields.some(field => !Object.hasOwn(state, field))) {
    throw new TypeError('Explicit original state words are required');
  }
  for (const field of fields) word(state[field]);
  return state;
}
const signedWord = value => value >= 32768 ? value - 65536 : value;

export function changeMoneySlotZero(state, delta) {
  stateWords(state);
  if (!Number.isInteger(delta) || delta < -32768 || delta > 32767) {
    throw new RangeError('Only the recovered signed 16-bit slot-zero delta is supported');
  }
  if (state.flag334Word) return {state: {...state}, success: true};
  let cashWord = (state.cashWord + delta) & 65535;
  let bankWord = state.bankWord;
  if (delta < 0 && signedWord(cashWord) < 0) {
    bankWord = (bankWord + cashWord) & 65535;
    if (signedWord(bankWord) < 0) return {state: {...state}, success: false};
    cashWord = 0;
  }
  if (signedWord(cashWord) < 0) cashWord = 0;
  return {state: {...state, cashWord, bankWord}, success: true};
}

export function acceptLinda(state, opcode = 0xf0, partner = 4, amount = 500) {
  stateWords(state);
  if (opcode !== 0xf0 || partner !== 4 || amount !== 500) {
    throw new RangeError('Only the source TREE3400 Linda confirmation is recovered');
  }
  return changeMoneySlotZero({...state, flag344Word: 1,
    partnerWord: state.flag334Word ? state.partnerWord : 4}, amount);
}

export function lindaSceneChildEligible(partnerWord) {
  return word(partnerWord) === 4;
}
