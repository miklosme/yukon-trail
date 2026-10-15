import { readPreparedVoice, type PreparedVoice } from './voice.ts'
import {
  cachedFrameProvider,
  type CachedFrameMetadata,
  type CachedFrameProvider,
} from '../rules/cached-frames.ts'
import { readHotspots, type HotspotRecord } from '../rules/scene-resources.ts'
import type { LindaJournalAssets } from '../rules/journal.ts'
import type { JournalStatusAssets } from '../rules/journal-status.ts'
import type { SeattlePopulationSource } from '../rules/seattle-population.ts'
import type { TreeGraph } from '../rules/tree.ts'
const expectedArchive = '438d729386cdb2effb120ed7652d14af00fb8a0e78f4426c12b17c934c3db8b6'
const expectedExe = '9ca8f0a12f4798e762fbf27634f99afcb5c0c1a3836604bf0a4049a73227dd06'
/** Prepared file with its SHA-256, as written by tools/prepare_browser_assets.py. */
export interface PreparedFile {
  file: string
  sha256: string
}
export interface FrameDescriptor {
  frame: number
  width: number
  height: number
  indices: string
  indices_sha256: string
}
export interface VoiceDescriptor extends PreparedFile {
  rate: number
  channels: number
  sample_bits: number
  samples: number
  pcm_sha256: string
}
/** manifest.json (schema yukon-indexed-assets-v1). Keys are original resource IDs (`CBMP:4000`). */
export interface AssetManifest {
  schema: string
  archive_sha256: string
  executable_sha256: string
  display_palette: PreparedFile
  font: PreparedFile
  journal: PreparedFile
  journal_status?: PreparedFile
  seattle_population?: PreparedFile
  cached_frames?: PreparedFile
  seattle_navigation?: Record<string, PreparedFile>
  sounds?: Record<string, VoiceDescriptor>
  trees?: Record<string, PreparedFile>
  resources: Record<string, { frames: FrameDescriptor[] }>
}
export interface SourceFrame extends Omit<FrameDescriptor, 'indices'> {
  indices: Uint8Array
}
export interface TreeAsset {
  schema: string
  resource: string
  graph: TreeGraph
}
export interface LoadedAssets {
  manifest: AssetManifest
  palette: Uint8Array
  journal: LindaJournalAssets
  journalStatus: JournalStatusAssets | null
  seattlePopulation: SeattlePopulationSource | null
  initializedFrame: CachedFrameProvider | null
  sceneHotspots(sceneId: number): Promise<HotspotRecord[]>
  frame(id: number, number: number): Promise<SourceFrame>
  tree(id: number): Promise<TreeAsset>
  voice(id: number): Promise<PreparedVoice & { resource: string }>
}
export async function loadAssets(base: string): Promise<LoadedAssets> {
  const origin = new URL(base, location.href)
  async function bytes(name: string, hash?: string): Promise<Uint8Array<ArrayBuffer>> {
    if (!/^[A-Za-z0-9_.-]+$/.test(name)) throw new Error('Unsupported asset name')
    const response = await fetch(new URL(name, origin))
    if (!response.ok) throw new Error(`Asset ${name}: HTTP${response.status}`)
    const data = new Uint8Array(await response.arrayBuffer())
    if (hash) {
      const digest = [...new Uint8Array(await crypto.subtle.digest('SHA-256', data))]
        .map((v) => v.toString(16).padStart(2, '0'))
        .join('')
      if (digest !== hash) throw new Error(`Asset identity mismatch: ${name}`)
    }
    return data
  }
  const manifest: AssetManifest = JSON.parse(new TextDecoder().decode(await bytes('manifest.json')))
  if (
    manifest.schema !== 'yukon-indexed-assets-v1' ||
    manifest.archive_sha256 !== expectedArchive ||
    manifest.executable_sha256 !== expectedExe
  )
    throw new Error('Unsupported source asset manifest')
  const palette = await bytes(manifest.display_palette.file, manifest.display_palette.sha256)
  if (palette.length !== 768) throw new Error('Invalid palette length')
  const font = await bytes(manifest.font.file, manifest.font.sha256)
  const face = new FontFace('YukonSource', font.buffer)
  await face.load()
  document.fonts.add(face)
  const journal: LindaJournalAssets = JSON.parse(
    new TextDecoder().decode(await bytes(manifest.journal.file, manifest.journal.sha256)),
  )
  let journalStatus: JournalStatusAssets | null = null
  if (manifest.journal_status) {
    journalStatus = JSON.parse(
      new TextDecoder().decode(
        await bytes(manifest.journal_status.file, manifest.journal_status.sha256),
      ),
    )
    if (
      journalStatus?.schema !== 'recovered-journal-status-v1' ||
      journalStatus.provenance?.executable_sha256 !== expectedExe
    )
      throw new Error('Unsupported journal status source')
  }
  let seattlePopulation: SeattlePopulationSource | null = null
  if (manifest.seattle_population) {
    seattlePopulation = JSON.parse(
      new TextDecoder().decode(
        await bytes(manifest.seattle_population.file, manifest.seattle_population.sha256),
      ),
    )
    if (
      seattlePopulation?.schema !== 'seattle-initial-population-source-v1' ||
      seattlePopulation.executable_sha256 !== expectedExe ||
      seattlePopulation.archive_sha256 !== expectedArchive
    )
      throw new Error('Unsupported Seattle population source')
  }
  const cached = new Map<string, Promise<SourceFrame>>()
  let initializedFrame: CachedFrameProvider | null = null
  if (manifest.cached_frames) {
    const descriptor = manifest.cached_frames
    const metadata: CachedFrameMetadata = JSON.parse(
      new TextDecoder().decode(await bytes(descriptor.file, descriptor.sha256)),
    )
    if (metadata.executable_sha256 !== expectedExe || metadata.archive_sha256 !== expectedArchive)
      throw new Error('Unsupported cached frame source')
    const buffers = new Map(
      await Promise.all(
        Object.values(metadata.frames).map(async (record): Promise<[string, Uint8Array]> => [
          record.pixels_file,
          await bytes(record.pixels_file, record.pixels_sha256),
        ]),
      ),
    )
    initializedFrame = cachedFrameProvider(metadata, buffers)
  }
  const hotspots = new Map<number, Promise<HotspotRecord[]>>()
  async function sceneHotspots(sceneId: number): Promise<HotspotRecord[]> {
    const descriptor = manifest.seattle_navigation?.[sceneId]
    if (!descriptor) throw new Error(`Unsupported scene hotspots ${sceneId}`)
    let pending = hotspots.get(sceneId)
    if (!pending) {
      pending = (async () => readHotspots(await bytes(descriptor.file, descriptor.sha256)))()
      hotspots.set(sceneId, pending)
    }
    return pending
  }
  const trees = new Map<string, Promise<TreeAsset>>()
  const voices = new Map<string, Promise<PreparedVoice & { resource: string }>>()
  async function voice(id: number): Promise<PreparedVoice & { resource: string }> {
    if (!Number.isInteger(id) || id < 0 || id > 65535)
      throw new RangeError('Original PSND resource ID required')
    const key = `PSND:${id}`
    const descriptor = manifest.sounds?.[key]
    if (!descriptor) throw new Error(`Unsupported voice ${key}`)
    let pending = voices.get(key)
    if (!pending) {
      pending = (async () => {
        const data = readPreparedVoice(await bytes(descriptor.file, descriptor.sha256))
        if (
          data.sampleRate !== descriptor.rate ||
          data.channels !== descriptor.channels ||
          data.sampleBits !== descriptor.sample_bits ||
          data.pcm.length !== descriptor.samples
        )
          throw new Error(`Invalid prepared voice ${key}`)
        const digest = [...new Uint8Array(await crypto.subtle.digest('SHA-256', data.pcm))]
          .map((v) => v.toString(16).padStart(2, '0'))
          .join('')
        if (digest !== descriptor.pcm_sha256) throw new Error(`Voice PCM identity mismatch ${key}`)
        return { ...data, resource: key }
      })()
      voices.set(key, pending)
    }
    const data = await pending
    return { ...data, pcm: data.pcm.slice() }
  }
  async function tree(id: number): Promise<TreeAsset> {
    if (!Number.isInteger(id) || id < 0 || id > 65535)
      throw new RangeError('Original TREE resource ID required')
    const key = `TREE:${id}`
    const descriptor = manifest.trees?.[key]
    if (!descriptor) throw new Error(`Unsupported dialogue ${key}`)
    let pending = trees.get(key)
    if (!pending) {
      pending = (async () => {
        const data: TreeAsset = JSON.parse(
          new TextDecoder().decode(await bytes(descriptor.file, descriptor.sha256)),
        )
        if (data.schema !== 'source-tree-graph-v1' || data.resource !== key || !data.graph)
          throw new Error(`Invalid source dialogue ${key}`)
        return data
      })()
      trees.set(key, pending)
    }
    return pending
  }
  async function frame(id: number, number: number): Promise<SourceFrame> {
    const key = `CBMP:${id}`
    const descriptor = manifest.resources[key]?.frames[number]
    if (!descriptor || descriptor.frame !== number)
      throw new Error(`Unsupported frame ${key}/${number}`)
    const cacheKey = `${key}/${number}`
    let pending = cached.get(cacheKey)
    if (!pending) {
      pending = (async () => {
        const indices = await bytes(descriptor.indices, descriptor.indices_sha256)
        if (indices.length !== descriptor.width * descriptor.height)
          throw new Error(`Invalid frame geometry ${cacheKey}`)
        return { ...descriptor, indices }
      })()
      cached.set(cacheKey, pending)
    }
    return pending
  }
  return {
    manifest,
    palette,
    journal,
    journalStatus,
    seattlePopulation,
    initializedFrame,
    sceneHotspots,
    frame,
    tree,
    voice,
  }
}
