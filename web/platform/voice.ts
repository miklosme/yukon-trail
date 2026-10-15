// Only the canonical WAV files produced by tools/prepare_browser_assets.py.
// Original PSND decoding is outside this platform adapter. No timing, volume,
// autoplay, interruption, queue or mixer policy is supplied here.
export interface PreparedVoice {
  channels: number
  sampleBits: number
  sampleRate: number
  pcm: Uint8Array<ArrayBuffer>
}
export function readPreparedVoice(bytes: Uint8Array): PreparedVoice {
  if (!(bytes instanceof Uint8Array) || bytes.length < 44)
    throw new TypeError('Prepared WAV bytes required')
  const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength)
  const tag = (at: number) => String.fromCharCode(...bytes.subarray(at, at + 4))
  if (
    tag(0) !== 'RIFF' ||
    tag(8) !== 'WAVE' ||
    tag(12) !== 'fmt ' ||
    tag(36) !== 'data' ||
    view.getUint32(4, true) !== bytes.length - 8 ||
    view.getUint32(16, true) !== 16 ||
    view.getUint16(20, true) !== 1 ||
    view.getUint16(22, true) !== 1 ||
    view.getUint32(24, true) !== 22050 ||
    view.getUint32(28, true) !== 22050 ||
    view.getUint16(32, true) !== 1 ||
    view.getUint16(34, true) !== 8 ||
    view.getUint32(40, true) !== bytes.length - 44 ||
    bytes.length === 44
  )
    throw new RangeError('Unsupported prepared mono8-bit22050Hz WAV')
  return { channels: 1, sampleBits: 8, sampleRate: 22050, pcm: bytes.slice(44) }
}
export function unsigned8ToFloat32(pcm: Uint8Array): Float32Array<ArrayBuffer> {
  if (!(pcm instanceof Uint8Array) || !pcm.length)
    throw new TypeError('Nonempty unsigned8-bit PCM required')
  return Float32Array.from(pcm, (value) => (value - 128) / 128)
}
export function makeVoiceBuffer(context: BaseAudioContext, voice: PreparedVoice): AudioBuffer {
  if (
    !context ||
    typeof context.createBuffer !== 'function' ||
    voice?.channels !== 1 ||
    voice.sampleBits !== 8 ||
    voice.sampleRate !== 22050
  )
    throw new TypeError('Explicit AudioContext and supported source voice required')
  const samples = unsigned8ToFloat32(voice.pcm)
  const buffer = context.createBuffer(1, samples.length, 22050)
  buffer.copyToChannel(samples, 0)
  return buffer
}
