// Original NE1:a0c2 and selected NE2:04f0 first-visit caller branch.
// Source/native evidence: docs/SEATTLE-RULES.md. No initial date/visit defaults.
export const MONTH_LENGTHS: readonly number[] = Object.freeze([
  31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31,
])
export interface OriginalDateWords {
  dayWord: number
  monthWord: number
  elapsedWord: number
  phaseWord: number
  gate334Word: number
}
const fields = ['dayWord', 'monthWord', 'elapsedWord', 'phaseWord', 'gate334Word'] as const
function word(value: unknown): number {
  if (typeof value !== 'number' || !Number.isInteger(value) || value < 0 || value > 65535)
    throw new RangeError('Original unsigned 16-bit word required')
  return value
}
function dateWords(state: OriginalDateWords): void {
  if (!state || fields.some((f) => !Object.hasOwn(state, f)))
    throw new TypeError('Explicit original date context required')
  for (const field of fields) word(state[field])
  if (
    state.monthWord < 1 ||
    state.monthWord > 12 ||
    state.dayWord < 1 ||
    state.dayWord > MONTH_LENGTHS[state.monthWord - 1]
  ) {
    throw new RangeError('Only valid original fixed-calendar dates are recovered')
  }
}
export function advanceOneOriginalDay(state: OriginalDateWords): OriginalDateWords {
  dateWords(state)
  if (state.gate334Word) return { ...state }
  let dayWord = state.dayWord + 1
  let monthWord = state.monthWord
  let phaseWord = state.phaseWord
  if (dayWord > MONTH_LENGTHS[monthWord - 1]) {
    dayWord = 1
    monthWord = monthWord < 12 ? monthWord + 1 : 1
    phaseWord = (phaseWord + 1) & 65535
  }
  return { ...state, dayWord, monthWord, phaseWord, elapsedWord: (state.elapsedWord + 1) & 65535 }
}
export function enterSelectedSeattleScene(
  state: OriginalDateWords,
  sceneId: number,
  visitWord: number,
): { state: OriginalDateWords; visitWord: number } {
  dateWords(state)
  word(visitWord)
  if (![1000, 2000, 3000, 4000].includes(sceneId))
    throw new RangeError('Only four selected Seattle scene entries recovered')
  return {
    state: sceneId === 1000 && visitWord === 0 ? advanceOneOriginalDay(state) : { ...state },
    visitWord: state.gate334Word ? visitWord : 1,
  }
}
