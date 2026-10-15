// Selected TREE2100 action220/item109/cost8, CONV17, partner4, unowned whipsaw.
// Original NE2:2884/24d0 and NE1 setters; evidence: docs/SEATTLE-RULES.md.
// Other items/actions, scene creation, journal and GUI excluded.
import { changeMoneySlotZero } from './seattle.ts'
export interface WhipsawPurchaseState {
  cashWord: number
  bankWord: number
  whipsawWord: number
  partnerWord: number
  word318: number
  gate334Word: number
}
export interface WhipsawPurchaseResult {
  state: WhipsawPurchaseState
  actionSuccess: boolean
  refusalTreeId: number | null
}
const fields = [
  'cashWord',
  'bankWord',
  'whipsawWord',
  'partnerWord',
  'word318',
  'gate334Word',
] as const
function word(value: unknown): number {
  if (typeof value !== 'number' || !Number.isInteger(value) || value < 0 || value > 65535)
    throw new RangeError('Explicit original unsigned 16-bit word required')
  return value
}
export function whipsawOptionVisible(whipsawWord: number): boolean {
  return word(whipsawWord) === 0
}
export function purchaseSelectedWhipsaw(
  state: WhipsawPurchaseState,
  action: readonly number[] = [220, 109, 8, 0],
  convFirstWord = 17,
): WhipsawPurchaseResult {
  if (!state || fields.some((f) => !Object.hasOwn(state, f)))
    throw new TypeError('Explicit original purchase state required')
  for (const field of fields) word(state[field])
  if (
    !Array.isArray(action) ||
    action.length !== 4 ||
    action.some((v, i) => v !== [220, 109, 8, 0][i]) ||
    convFirstWord !== 17 ||
    state.partnerWord !== 4 ||
    state.whipsawWord !== 0
  ) {
    throw new RangeError('Only selected unowned Seattle whipsaw with Linda context recovered')
  }
  const total = (state.cashWord + state.bankWord) & 65535
  if ((total >= 32768 ? total - 65536 : total) < 8) {
    return { state: { ...state }, actionSuccess: false, refusalTreeId: 600 }
  }
  // Only cash/bank/gate are used by this arithmetic adapter; flag344 is not
  // a game-state default and is never returned or exposed by this operation.
  const money = changeMoneySlotZero(
    {
      cashWord: state.cashWord,
      bankWord: state.bankWord,
      partnerWord: 4,
      flag334Word: state.gate334Word,
      flag344Word: 0,
    },
    -8,
  ).state
  return {
    state: {
      ...state,
      cashWord: money.cashWord,
      bankWord: money.bankWord,
      whipsawWord: state.gate334Word ? state.whipsawWord : 1,
      word318: state.gate334Word ? state.word318 : 17,
    },
    actionSuccess: true,
    refusalTreeId: null,
  }
}
