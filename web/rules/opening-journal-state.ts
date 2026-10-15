// A bounded projection, not an allocated/reset original world or save state.
// Known reset words: initial-state-recovery-evidence.json. Activated Seattle
// tuple: scene-location-recovery-evidence.json. Unknown byte holes are never read.
export const openingJournalKnownWords: readonly (readonly [offset: number, value: number])[] =
  Object.freeze(
    (
      [
        [0x28, 23],
        [0x2a, 8],
        [0x34, 200],
        [0x36, 0],
        [0x38, 4000],
        [0x2fa, 350],
        [0x2fc, 0],
        [0x2fe, 0],
        [0x300, 0],
        [0x302, 0],
        [0x304, 0],
        [0x306, 0],
        [0x308, 0],
        [0x30a, 0],
        [0x310, 1],
        [0x312, 65535],
      ] as [number, number][]
    ).map((row) => Object.freeze(row)),
  )
export function openingJournalProjection(): Uint8Array {
  // Deliberately shorter than the original0x386-byte state/save block.
  const data = new Uint8Array(0x314),
    view = new DataView(data.buffer)
  for (const [offset, value] of openingJournalKnownWords) view.setUint16(offset, value, true)
  return data
}
export function openingJournalCacheWords(): number[] {
  // Exact post-event0→event4 cache, not assumed uninitialized constructor words.
  return [23, 8, 0, 350, 0, 0]
}
