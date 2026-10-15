// Platform values come from emulators8.5.2 src/keys.ts and protocol.ts.
const namedKeys: Readonly<Record<string, number>> = Object.freeze({
  Escape: 256,
  Enter: 257,
  Tab: 258,
  Backspace: 259,
  Insert: 260,
  Delete: 261,
  ArrowRight: 262,
  ArrowLeft: 263,
  ArrowDown: 264,
  ArrowUp: 265,
  PageUp: 266,
  PageDown: 267,
  Home: 268,
  End: 269,
  CapsLock: 280,
  ScrollLock: 281,
  NumLock: 282,
  PrintScreen: 283,
  Pause: 284,
  Space: 32,
  ShiftLeft: 340,
  ControlLeft: 341,
  AltLeft: 342,
  ShiftRight: 344,
  ControlRight: 345,
  AltRight: 346,
  Backquote: 96,
  Minus: 45,
  Equal: 61,
  Backslash: 92,
  BracketLeft: 91,
  BracketRight: 93,
  Semicolon: 59,
  Quote: 39,
  Period: 46,
  Comma: 44,
  Slash: 47,
  IntlBackslash: 348,
  NumpadDecimal: 330,
  NumpadDivide: 331,
  NumpadMultiply: 332,
  NumpadSubtract: 333,
  NumpadAdd: 334,
  NumpadEnter: 335,
})
export function keyCode(code: string): number | null {
  if (/^Key[A-Z]$/.test(code)) return code.charCodeAt(3)
  if (/^Digit[0-9]$/.test(code)) return code.charCodeAt(5)
  if (/^Numpad[0-9]$/.test(code)) return 320 + Number(code.slice(6))
  if (/^F([1-9]|1[0-2])$/.test(code)) return 289 + Number(code.slice(1))
  return Object.hasOwn(namedKeys, code) ? namedKeys[code] : null
}
export interface CanvasRectangle {
  left: number
  top: number
  width: number
  height: number
}
export function mousePoint(x: number, y: number, rect: CanvasRectangle): [number, number] {
  if (
    ![x, y, rect.left, rect.top, rect.width, rect.height].every(Number.isFinite) ||
    rect.width <= 0 ||
    rect.height <= 0
  )
    throw new Error('Invalid canvas geometry')
  return [
    Math.max(0, Math.min(1, (x - rect.left) / rect.width)),
    Math.max(0, Math.min(1, (y - rect.top) / rect.height)),
  ]
}
// DOSBox-X jsdos-x-main.cpp: SDL left/right/middle -> 0/1/2.
// Browser PointerEvent.button instead uses left/middle/right -> 0/1/2.
export function mouseButton(button: number): number | null {
  return Number.isInteger(button) && button >= 0 && button <= 2 ? [0, 2, 1][button] : null
}
export function rgbaFrame(
  width: number,
  height: number,
  rgb: Uint8Array | null,
  rgba: Uint8Array | null,
): Uint8ClampedArray<ArrayBuffer> {
  if (!Number.isSafeInteger(width) || !Number.isSafeInteger(height) || width <= 0 || height <= 0)
    throw new Error('Invalid emulator frame size')
  const pixels = width * height
  if (rgba !== null) {
    if (!(rgba instanceof Uint8Array) || rgba.length !== pixels * 4)
      throw new Error('Unexpected RGBA frame')
    return new Uint8ClampedArray(rgba)
  }
  if (!(rgb instanceof Uint8Array) || rgb.length !== pixels * 3)
    throw new Error('Unexpected RGB frame')
  const result = new Uint8ClampedArray(pixels * 4)
  for (let i = 0; i < pixels; i++) {
    result.set(rgb.subarray(i * 3, i * 3 + 3), i * 4)
    result[i * 4 + 3] = 255
  }
  return result
}
export async function sha256(bytes: Uint8Array<ArrayBuffer>): Promise<string> {
  return Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256', bytes)), (byte) =>
    byte.toString(16).padStart(2, '0'),
  ).join('')
}
/** One staged file of the trial manifest (tools/prepare_emulation_trial.py). */
export interface StagedFileRecord {
  file: string
  bytes: number
  sha256: string
}
export async function verifiedFile(
  base: string,
  record: StagedFileRecord,
): Promise<Uint8Array<ArrayBuffer>> {
  if (
    !record ||
    !/^[a-zA-Z0-9_./-]+$/.test(record.file) ||
    record.file.startsWith('/') ||
    record.file.split('/').includes('..')
  )
    throw new Error('Invalid staged asset path')
  const response = await fetch(base + record.file)
  if (!response.ok) throw new Error(`Cannot load ${record.file}: ${response.status}`)
  const bytes = new Uint8Array(await response.arrayBuffer())
  if (bytes.length !== record.bytes || (await sha256(bytes)) !== record.sha256)
    throw new Error(`Asset identity mismatch: ${record.file}`)
  return bytes
}
