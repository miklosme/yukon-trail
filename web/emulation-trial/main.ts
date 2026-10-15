// Experimental host adapter. No guest execution has been validated yet.
import {
  keyCode,
  mousePoint,
  mouseButton,
  rgbaFrame,
  sha256,
  verifiedFile,
  type StagedFileRecord,
} from './contracts.ts'
// Minimal local typing of the emulators8.5.2 surface this adapter uses
// (src/emulators.ts, src/protocol/protocol.ts). Not vendor-supplied types.
interface CommandEvents {
  onFrameSize(callback: (width: number, height: number) => void): void
  onFrame(callback: (rgb: Uint8Array | null, rgba: Uint8Array | null) => void): void
  onSoundPush(callback: (samples: Float32Array<ArrayBuffer>) => void): void
  onStdout(callback: (message: string) => void): void
  onMessage(callback: (type: string, ...args: unknown[]) => void): void
  onExit(callback: () => void): void
}
interface CommandInterface {
  events(): CommandEvents
  width(): number
  height(): number
  soundFrequency(): number
  sendKeyEvent(key: number, pressed: boolean): void
  sendMouseMotion(x: number, y: number): void
  sendMouseButton(button: number, pressed: boolean): void
  pause(): void
}
interface EmulatorsBackend {
  version: string
  pathPrefix: string
  dosboxXWorker(
    initFs: (Uint8Array | { path: string; contents: Uint8Array })[],
  ): Promise<CommandInterface>
}
interface TrialManifest {
  schema: string
  vendor: { version: string; files: Record<string, StagedFileRecord> }
  guest: StagedFileRecord
  iso: StagedFileRecord
}
interface TrialDiagnostics {
  frames: number
  samplesBeforeGesture: number
  audioUnderruns: number
}
declare global {
  var emulators: EmulatorsBackend | undefined
  var yukonTrial:
    | { diagnostics: TrialDiagnostics; readonly commandInterface: CommandInterface | null }
    | undefined
}
const base = '/emulation-assets/'
const manifestHash = 'bc6d56f8ee78243935559786871a98242608f745759c23dfff1f41209cf23412'
function required<T>(value: T | null, message: string): T {
  if (value === null) throw new Error(message)
  return value
}
const canvas = required(document.querySelector('canvas'), 'Trial canvas missing')
const context = required(canvas.getContext('2d', { alpha: false }), '2D canvas context unavailable')
let ci: CommandInterface | null = null,
  audio: AudioContext | null = null,
  nextSound = 0,
  failed = false
const keys = new Set<number>(),
  buttons = new Set<number>(),
  sources = new Set<AudioBufferSourceNode>()
const diagnostics: TrialDiagnostics = { frames: 0, samplesBeforeGesture: 0, audioUnderruns: 0 }
// Console-only handoff; no extra in-game controls or automatic persistence.
globalThis.yukonTrial = {
  diagnostics,
  get commandInterface() {
    return ci
  },
}
function fit() {
  const scale = Math.min(innerWidth / canvas.width, innerHeight / canvas.height)
  canvas.style.width = `${canvas.width * scale}px`
  canvas.style.height = `${canvas.height * scale}px`
}
function release() {
  if (ci) {
    for (const key of keys) ci.sendKeyEvent(key, false)
    for (const button of buttons) ci.sendMouseButton(button, false)
  }
  keys.clear()
  buttons.clear()
}
function fail(error: unknown) {
  failed = true
  release()
  ci?.pause()
  for (const source of sources) source.stop()
  sources.clear()
  console.error('Yukon emulation trial stopped:', error)
}
function activateAudio() {
  if (!audio) audio = new AudioContext()
  audio.resume().catch(fail)
}
function sound(samples: Float32Array<ArrayBuffer>) {
  if (failed) return
  if (!(samples instanceof Float32Array)) return fail(new Error('Unexpected audio buffer'))
  if (!audio || audio.state !== 'running') {
    diagnostics.samplesBeforeGesture += samples.length
    return
  }
  const rate = ci?.soundFrequency()
  if (typeof rate !== 'number' || !Number.isSafeInteger(rate) || rate <= 0)
    return fail(new Error('Invalid sound frequency'))
  if (samples.some((value) => !Number.isFinite(value)))
    return fail(new Error('Invalid audio samples'))
  if (!samples.length) return
  const now = audio.currentTime
  if (nextSound < now) {
    if (nextSound !== 0) diagnostics.audioUnderruns++
    nextSound = now
  }
  // A failed trial stops explicitly instead of silently dropping a growing queue.
  if (nextSound - now + samples.length / rate > 2)
    return fail(new Error('Audio backlog exceeds the trial limit of two seconds'))
  const buffer = audio.createBuffer(1, samples.length, rate)
  buffer.copyToChannel(samples, 0)
  const source = audio.createBufferSource()
  source.buffer = buffer
  source.connect(audio.destination)
  sources.add(source)
  source.onended = () => {
    sources.delete(source)
    source.disconnect()
  }
  source.start(nextSound)
  nextSound += buffer.duration
}
canvas.addEventListener('keydown', (event) => {
  if (!ci || failed || event.metaKey) return
  const key = keyCode(event.code)
  if (key === null) return
  event.preventDefault()
  activateAudio()
  if (!keys.has(key)) {
    keys.add(key)
    ci.sendKeyEvent(key, true)
  }
})
canvas.addEventListener('keyup', (event) => {
  const key = keyCode(event.code)
  if (ci && key !== null && keys.delete(key)) {
    event.preventDefault()
    ci.sendKeyEvent(key, false)
  }
})
function motion(event: PointerEvent) {
  if (ci && !failed)
    ci.sendMouseMotion(...mousePoint(event.clientX, event.clientY, canvas.getBoundingClientRect()))
}
canvas.addEventListener('pointermove', motion)
canvas.addEventListener('pointerdown', (event) => {
  if (!ci || failed || event.button < 0 || event.button > 2) return
  const button = mouseButton(event.button)
  if (button === null) return
  event.preventDefault()
  canvas.focus()
  activateAudio()
  motion(event)
  canvas.setPointerCapture(event.pointerId)
  buttons.add(button)
  ci.sendMouseButton(button, true)
})
canvas.addEventListener('pointerup', (event) => {
  motion(event)
  const button = mouseButton(event.button)
  if (ci && button !== null && buttons.delete(button)) ci.sendMouseButton(button, false)
})
canvas.addEventListener('contextmenu', (event) => event.preventDefault())
canvas.addEventListener('pointercancel', release)
canvas.addEventListener('lostpointercapture', release)
canvas.addEventListener('blur', release)
window.addEventListener('blur', release)
window.addEventListener('resize', fit)
fit()
async function start() {
  const response = await fetch(base + 'manifest.json')
  if (!response.ok) throw new Error(`Cannot load trial manifest: ${response.status}`)
  const bytes = new Uint8Array(await response.arrayBuffer())
  if ((await sha256(bytes)) !== manifestHash) throw new Error('Trial manifest identity mismatch')
  const manifest: TrialManifest = JSON.parse(new TextDecoder().decode(bytes))
  if (manifest.schema !== 'yukon-emulation-trial-v1' || manifest.vendor.version !== '8.5.2')
    throw new Error('Unsupported trial package')
  const scriptBytes = await verifiedFile(base, manifest.vendor.files['emulators.js'])
  // Preflight both backend files. Vendor loading then uses these same local paths.
  for (const name of ['wdosbox-x.js', 'wdosbox-x.wasm'])
    await verifiedFile(base, manifest.vendor.files[name])
  const guest = await verifiedFile(base, manifest.guest)
  const iso = await verifiedFile(base, manifest.iso)
  const scriptURL = URL.createObjectURL(new Blob([scriptBytes], { type: 'text/javascript' }))
  try {
    await new Promise<void>((resolve, reject) => {
      const script = document.createElement('script')
      script.src = scriptURL
      script.onload = () => resolve()
      script.onerror = () => reject(new Error('Vendor script load failed'))
      document.head.append(script)
    })
  } finally {
    URL.revokeObjectURL(scriptURL)
  }
  const backend = globalThis.emulators
  if (!backend || backend.version !== '8.5.2') throw new Error('Unexpected emulator API')
  backend.pathPrefix = base + 'vendor/'
  ci = await backend.dosboxXWorker([guest, { path: 'YUKONCD.ISO', contents: iso }])
  const events = ci.events()
  function resize(width: number, height: number) {
    // Validate dimensions before allocating a frame or altering the display.
    if (
      !Number.isSafeInteger(width) ||
      !Number.isSafeInteger(height) ||
      width <= 0 ||
      height <= 0 ||
      width > 4096 ||
      height > 4096
    )
      return fail(new Error('Unsupported trial frame dimensions'))
    canvas.width = width
    canvas.height = height
    fit()
  }
  events.onFrameSize(resize)
  events.onFrame((rgb, rgba) => {
    if (failed) return
    try {
      context.putImageData(
        new ImageData(
          rgbaFrame(canvas.width, canvas.height, rgb, rgba),
          canvas.width,
          canvas.height,
        ),
        0,
        0,
      )
      diagnostics.frames++
    } catch (error) {
      fail(error)
    }
  })
  events.onSoundPush(sound)
  events.onStdout((message) => console.info('DOSBox-X:', message))
  events.onMessage((type, ...args) => console.info('DOSBox-X', type, ...args))
  events.onExit(() => {
    release()
    for (const source of sources) source.stop()
    sources.clear()
  })
  if (ci.width() > 0 && ci.height() > 0) resize(ci.width(), ci.height())
  canvas.focus()
}
start().catch(fail)
