// Bounded normalized resource readers and original-code-checked primitives.
// Source/case provenance: docs/browser-scene-resource-evidence.json.
// No clock, successor dispatch, screen projection, sprite interception or actions.
export const SOURCE_EXE_SHA256 = '9ca8f0a12f4798e762fbf27634f99afcb5c0c1a3836604bf0a4049a73227dd06'
export interface SpriteResource {
  bitmapId: number
  animationId: number
  anchorX: number
  anchorY: number
  initialSequence: number
  clickSequence: number
  rawHeader: Uint8Array
  schedules: number[][]
}
export type CelOffsetXY = [number, number]
/** ASEQ sequence row: [first step, successor sequence, word2, step count]. */
export type AnimationSequence = [number, number, number, number]
/** ASEQ step row: [frame, dx, dy, unknown word, deadline override, flip]. */
export type AnimationStep = [number, number, number, number, number, number]
export interface AnimationResource {
  sequences: AnimationSequence[]
  steps: AnimationStep[]
}
export interface HotspotRecord {
  left: number
  right: number
  top: number
  bottom: number
  actionWord0: number
  actionWord1: number
  actionDword: number
}
/** Original signed-word rectangle order: [top, left, bottom, right]. */
export type RectangleTLBR = [number, number, number, number]
const signed16 = (n: number): number => ((n + 32768) & 65535) - 32768
function integer(n: number, min: number, max: number, label: string): number {
  if (!Number.isInteger(n) || n < min || n > max)
    throw new RangeError(`${label} outside supported integer range`)
  return n
}
function view(bytes: Uint8Array): DataView {
  if (!(bytes instanceof Uint8Array)) throw new TypeError('Normalized Uint8Array required')
  return new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength)
}
function exact(v: DataView, length: number, name: string): void {
  if (v.byteLength !== length) throw new RangeError(`${name} count/length mismatch`)
}
function minimum(v: DataView, length: number, name: string): void {
  if (v.byteLength < length) throw new RangeError(`Truncated ${name}`)
}
export function readSprite(bytes: Uint8Array): SpriteResource {
  const v = view(bytes)
  minimum(v, 38, 'SPRT')
  const count = v.getUint16(36, true)
  exact(v, 38 + count * 8, 'SPRT')
  return {
    bitmapId: v.getUint16(0, true),
    animationId: v.getUint16(2, true),
    anchorX: v.getInt16(4, true),
    anchorY: v.getInt16(6, true),
    initialSequence: v.getInt16(16, true),
    clickSequence: v.getInt16(30, true),
    rawHeader: bytes.slice(0, 38),
    schedules: Array.from({ length: count }, (_, n) =>
      Array.from({ length: 4 }, (_, k) => v.getInt16(38 + n * 8 + k * 2, true)),
    ),
  }
}
export function readCelOffsets(bytes: Uint8Array): CelOffsetXY[] {
  const v = view(bytes)
  minimum(v, 2, 'ACEL')
  const count = v.getUint16(0, true)
  exact(v, 2 + count * 4, 'ACEL')
  return Array.from({ length: count }, (_, n) => [
    v.getInt16(2 + n * 4, true),
    v.getInt16(4 + n * 4, true),
  ])
}
export function readAnimation(bytes: Uint8Array): AnimationResource {
  const v = view(bytes)
  minimum(v, 4, 'ASEQ')
  const count = v.getUint16(0, true),
    tail = 2 + count * 8
  minimum(v, tail + 2, 'ASEQ sequence table')
  const stepCount = v.getUint16(tail, true)
  exact(v, tail + 2 + stepCount * 12, 'ASEQ')
  const sequences = Array.from({ length: count }, (_, n): AnimationSequence => {
    const p = 2 + n * 8
    return [
      v.getUint16(p, true),
      v.getInt16(p + 2, true),
      v.getUint16(p + 4, true),
      v.getUint16(p + 6, true),
    ]
  })
  const steps = Array.from({ length: stepCount }, (_, n): AnimationStep => {
    const p = tail + 2 + n * 12
    return [
      v.getUint16(p, true),
      v.getInt16(p + 2, true),
      v.getInt16(p + 4, true),
      v.getUint16(p + 6, true),
      v.getUint16(p + 8, true),
      v.getUint16(p + 10, true),
    ]
  })
  for (const [start, successor, , length] of sequences) {
    if (start + length > steps.length || successor < -1 || successor >= sequences.length)
      throw new RangeError('ASEQ sequence outside supported table')
  }
  return { sequences, steps }
}
const sentinel = (r: HotspotRecord): boolean =>
  r.left === 0 && r.right === 0 && r.top === 0 && r.bottom === 0
export function readHotspots(bytes: Uint8Array): HotspotRecord[] {
  const v = view(bytes)
  minimum(v, 2, 'HSPT')
  const count = v.getUint16(0, true)
  exact(v, 2 + count * 16, 'HSPT')
  const records = Array.from({ length: count }, (_, n): HotspotRecord => {
    const p = 2 + n * 16
    return {
      left: v.getInt16(p, true),
      right: v.getInt16(p + 2, true),
      top: v.getInt16(p + 4, true),
      bottom: v.getInt16(p + 6, true),
      actionWord0: v.getUint16(p + 8, true),
      actionWord1: v.getUint16(p + 10, true),
      actionDword: v.getUint32(p + 12, true),
    }
  })
  if (!records.some(sentinel))
    throw new RangeError('HSPT fallback requires zero rectangle sentinel')
  return records
}
export function hotspotCandidate(
  records: readonly HotspotRecord[],
  x: number,
  y: number,
): number | null {
  integer(x, -32768, 32767, 'HSPT x')
  integer(y, -32768, 32767, 'HSPT y')
  for (let i = 0; i < records.length; i++) {
    const r = records[i]
    if (sentinel(r)) return null
    if (r.left < x && x < r.right && r.top < y && y < r.bottom) return i
  }
  throw new RangeError('HSPT fallback lacks terminating sentinel')
}
export function completeUnflippedSequence(
  sprite: { anchorX: number; anchorY: number },
  animation: AnimationResource,
  sequence: number,
): [number, number] {
  integer(sequence, 0, animation.sequences.length - 1, 'Sequence')
  const [start, , , count] = animation.sequences[sequence]
  let x = integer(sprite.anchorX, -32768, 32767, 'Anchor x')
  let y = integer(sprite.anchorY, -32768, 32767, 'Anchor y')
  for (const [, dx, dy, unknown, , flip] of animation.steps.slice(start, start + count)) {
    if (unknown || flip) throw new RangeError('Unrecovered step word/flip in selected movement')
    x = signed16(x + dx)
    y = signed16(y + dy)
  }
  return [x, y]
}
export function frameRectangle(
  anchorXY: readonly number[],
  offsetXY: readonly number[],
  sizeWH: readonly number[],
): RectangleTLBR {
  for (const n of [...anchorXY, ...offsetXY]) integer(n, -32768, 32767, 'Anchor/offset')
  for (const n of sizeWH) integer(n, 0, 65535, 'Frame dimension')
  if (anchorXY.length !== 2 || offsetXY.length !== 2 || sizeWH.length !== 2)
    throw new RangeError('Pairs required')
  const left = signed16(anchorXY[0] - offsetXY[0]),
    top = signed16(anchorXY[1] - offsetXY[1])
  return [top, left, signed16(top + sizeWH[1]), signed16(left + sizeWH[0])]
}
// Only the source-proven suspended branch; zero requires unrecovered scheduling.
export function suspendedSpriteState(
  suspendedWord: number,
  enabledWord: number,
  visibleWord: number,
  dirtyByte = 0,
): { visibleWord: number; dirtyByte: number } {
  integer(suspendedWord, 1, 65535, 'Suspension')
  integer(enabledWord, 0, 65535, 'Enabled')
  integer(visibleWord, 0, 65535, 'Visible')
  integer(dirtyByte, 0, 255, 'Dirty')
  return enabledWord === 0 && visibleWord !== 0
    ? { visibleWord: 0, dirtyByte: 1 }
    : { visibleWord, dirtyByte }
}
