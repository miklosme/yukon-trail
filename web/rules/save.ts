// Original NE1:974a/97ec five-block container; source/native provenance in
// docs/save-container-recovery-evidence.json. No scene rebuild or defaults.
export const SAVE_SIZE = 11221
const lengths = [5, 64, 10, 902, 10240]
const names = ['signature', 'title', 'version', 'state', 'journal'] as const
export type OriginalSaveBlockName = (typeof names)[number]
export type OriginalSaveBlocks = Record<OriginalSaveBlockName, Uint8Array>
export function originalHeaderStatus(header: Uint8Array): number {
  if (!(header instanceof Uint8Array) || header.length !== 79)
    throw new TypeError('Exact79byte original header required')
  function compare(actual: Uint8Array, text: string, count: number): number {
    for (let i = 0; i < count; i++) {
      const expected = i < text.length ? text.charCodeAt(i) : 0
      if (actual[i] !== expected) return actual[i] > expected ? 1 : -1
      if (actual[i] === 0) return 0
    }
    return 0
  }
  if (compare(header.subarray(0, 5), 'MECC\0', 4)) return -1
  if (compare(header.subarray(5, 69), 'The Yukon Trail\0', 64)) return -2
  const version = compare(header.subarray(69, 79), '0.1\0', 10)
  return version < 0 ? 1 : version > 0 ? -3 : 0
}
function supportedHeader(bytes: Uint8Array): void {
  if (originalHeaderStatus(bytes.subarray(0, 79)) !== 0)
    throw new RangeError('Unsupported original save header status')
}
export function readOriginalSave(bytes: Uint8Array): OriginalSaveBlocks {
  if (!(bytes instanceof Uint8Array) || bytes.length !== SAVE_SIZE)
    throw new TypeError('Exact11221byte original save required')
  supportedHeader(bytes)
  const result: Partial<OriginalSaveBlocks> = {}
  let offset = 0
  for (let i = 0; i < names.length; i++) {
    result[names[i]] = bytes.slice(offset, offset + lengths[i])
    offset += lengths[i]
  }
  return result as OriginalSaveBlocks
}
export function writeOriginalSave(save: OriginalSaveBlocks): Uint8Array {
  const result = new Uint8Array(SAVE_SIZE)
  let offset = 0
  for (let i = 0; i < names.length; i++) {
    const value = save?.[names[i]]
    if (!(value instanceof Uint8Array) || value.length !== lengths[i])
      throw new TypeError(`Original ${names[i]} block required`)
    result.set(value, offset)
    offset += lengths[i]
  }
  supportedHeader(result)
  return result
}
