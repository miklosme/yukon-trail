// Original NE1:9900 raw reset and NE6:2a28 controlled RNG, source/native proof
// docs/initial-state-recovery-evidence.json. Prior bytes and RNG seed/output
// are explicit. No allocation, seed, scene activation or journal defaults.
export interface OriginalRandomStep {
  nextSeed: number
  randomWord: number
}
export function originalRandomStep(seed: number): OriginalRandomStep {
  if (!Number.isInteger(seed) || seed < 0 || seed > 0xffffffff)
    throw new RangeError('Explicit unsigned32 random seed required')
  const nextSeed = (Math.imul(seed, 214013) + 2531011) >>> 0
  return { nextSeed, randomWord: (nextSeed >>> 16) & 0x7fff }
}
export function resetOriginalState(previousBytes: Uint8Array, randomWord: number): Uint8Array {
  if (!(previousBytes instanceof Uint8Array) || previousBytes.length < 0x386)
    throw new TypeError('Explicit original state buffer of at least0x386 bytes required')
  if (!Number.isInteger(randomWord) || randomWord < 0 || randomWord > 32767)
    throw new RangeError('Explicit original random output0..32767 required')
  const bytes = Uint8Array.from(previousBytes)
  const view = new DataView(bytes.buffer)
  const word = (offset: number, value = 0) => view.setUint16(offset, value, true)
  const dword = (offset: number, value = 0) => view.setUint32(offset, value, true)
  bytes[0] = bytes[0x14] = 0
  word(0x312, 65535)
  word(0x2a, 8)
  word(0x28, 23)
  dword(0x2c)
  dword(0x30)
  word(0x31a)
  dword(0x30e, 0x10001)
  for (const offset of [0x36, 0x38, 0x31c, 0x31e, 0x30c, 0x318, 0x322]) word(offset)
  for (const [start, count] of [
    [0x2fa, 9],
    [0x1dc, 30],
    [0x218, 61],
    [0x292, 8],
    [0x2aa, 40],
    [0x42, 50],
    [0xa6, 4],
    [0xae, 120],
    [0x19e, 31],
  ]) {
    for (let i = 0; i < count; i++) word(start + 2 * i)
  }
  word(0x2fa, 350)
  word(0x2fc)
  word(0x314, 7 + (randomWord % 3))
  word(0x316, 10 + (randomWord % 3))
  dword(0x3a)
  for (const offset of [
    0x320, 0x324, 0x326, 0x328, 0x32a, 0x32c, 0x330, 0x332, 0x334, 0x336, 0x338, 0x33a, 0x33c,
    0x33e, 0x340, 0x32e, 0x342, 0x384, 0x346,
  ])
    word(offset)
  bytes.fill(0, 0x348, 0x370)
  dword(0x370)
  for (const offset of [0x376, 0x378, 0x37a, 0x374, 0x382, 0x37c, 0x37e, 0x40, 0x380, 0x344])
    word(offset)
  return bytes
}
