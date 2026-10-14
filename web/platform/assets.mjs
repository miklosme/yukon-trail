import {readPreparedVoice} from './voice.mjs';
import {cachedFrameProvider} from '../rules/cached-frames.mjs';
import {readHotspots} from '../rules/scene-resources.mjs';
const expectedArchive = '438d729386cdb2effb120ed7652d14af00fb8a0e78f4426c12b17c934c3db8b6';
const expectedExe = '9ca8f0a12f4798e762fbf27634f99afcb5c0c1a3836604bf0a4049a73227dd06';
export async function loadAssets(base) {
  const origin = new URL(base, location.href);
  async function bytes(name, hash) {
    if (!/^[A-Za-z0-9_.-]+$/.test(name)) throw new Error('Unsupported asset name');
    const response = await fetch(new URL(name, origin));
    if (!response.ok) throw new Error(`Asset ${name}: HTTP${response.status}`);
    const data = new Uint8Array(await response.arrayBuffer());
    if (hash) {
      const digest = [...new Uint8Array(await crypto.subtle.digest('SHA-256', data))]
        .map(v => v.toString(16).padStart(2,'0')).join('');
      if (digest !== hash) throw new Error(`Asset identity mismatch: ${name}`);
    }
    return data;
  }
  const manifest = JSON.parse(new TextDecoder().decode(await bytes('manifest.json')));
  if (manifest.schema !== 'yukon-indexed-assets-v1' || manifest.archive_sha256 !== expectedArchive ||
      manifest.executable_sha256 !== expectedExe) throw new Error('Unsupported source asset manifest');
  const palette = await bytes(manifest.display_palette.file, manifest.display_palette.sha256);
  if (palette.length !== 768) throw new Error('Invalid palette length');
  const font = await bytes(manifest.font.file, manifest.font.sha256);
  const face = new FontFace('YukonSource',font.buffer);
  await face.load(); document.fonts.add(face);
  const journal = JSON.parse(new TextDecoder().decode(await bytes(manifest.journal.file, manifest.journal.sha256)));
  let journalStatus=null;
  if (manifest.journal_status) {
    journalStatus=JSON.parse(new TextDecoder().decode(await bytes(manifest.journal_status.file,manifest.journal_status.sha256)));
    if (journalStatus.schema!=='recovered-journal-status-v1' || journalStatus.provenance?.executable_sha256!==expectedExe)
      throw new Error('Unsupported journal status source');
  }
  let seattlePopulation=null;
  if (manifest.seattle_population) {
    seattlePopulation=JSON.parse(new TextDecoder().decode(await bytes(manifest.seattle_population.file,manifest.seattle_population.sha256)));
    if (seattlePopulation.schema!=='seattle-initial-population-source-v1'||
        seattlePopulation.executable_sha256!==expectedExe||seattlePopulation.archive_sha256!==expectedArchive)
      throw new Error('Unsupported Seattle population source');
  }
  const cached = new Map();
  let initializedFrame=null;
  if (manifest.cached_frames) {
    const descriptor=manifest.cached_frames;
    const metadata=JSON.parse(new TextDecoder().decode(await bytes(descriptor.file,descriptor.sha256)));
    if (metadata.executable_sha256!==expectedExe || metadata.archive_sha256!==expectedArchive)
      throw new Error('Unsupported cached frame source');
    const buffers=new Map(await Promise.all(Object.values(metadata.frames).map(async record=>
      [record.pixels_file,await bytes(record.pixels_file,record.pixels_sha256)])));
    initializedFrame=cachedFrameProvider(metadata,buffers);
  }
  const hotspots=new Map();
  async function sceneHotspots(sceneId) {
    const descriptor=manifest.seattle_navigation?.[sceneId];
    if (!descriptor) throw new Error(`Unsupported scene hotspots ${sceneId}`);
    if (!hotspots.has(sceneId)) hotspots.set(sceneId,(async()=>readHotspots(await bytes(descriptor.file,descriptor.sha256)))());
    return hotspots.get(sceneId);
  }
  const trees = new Map();
  const voices = new Map();
  async function voice(id) {
    if (!Number.isInteger(id)||id<0||id>65535) throw new RangeError('Original PSND resource ID required');
    const key=`PSND:${id}`;
    const descriptor=manifest.sounds?.[key];
    if (!descriptor) throw new Error(`Unsupported voice ${key}`);
    if (!voices.has(key)) voices.set(key,(async()=> {
      const data=readPreparedVoice(await bytes(descriptor.file,descriptor.sha256));
      if(data.sampleRate!==descriptor.rate||data.channels!==descriptor.channels||
         data.sampleBits!==descriptor.sample_bits||data.pcm.length!==descriptor.samples)
        throw new Error(`Invalid prepared voice ${key}`);
      const digest=[...new Uint8Array(await crypto.subtle.digest('SHA-256',data.pcm))]
        .map(v=>v.toString(16).padStart(2,'0')).join('');
      if(digest!==descriptor.pcm_sha256) throw new Error(`Voice PCM identity mismatch ${key}`);
      return {...data,resource:key};
    })());
    const data=await voices.get(key);
    return {...data,pcm:data.pcm.slice()};
  }
  async function tree(id) {
    if (!Number.isInteger(id) || id < 0 || id > 65535) throw new RangeError('Original TREE resource ID required');
    const key = `TREE:${id}`;
    const descriptor = manifest.trees?.[key];
    if (!descriptor) throw new Error(`Unsupported dialogue ${key}`);
    if (!trees.has(key)) trees.set(key, (async () => {
      const data = JSON.parse(new TextDecoder().decode(await bytes(descriptor.file, descriptor.sha256)));
      if (data.schema !== 'source-tree-graph-v1' || data.resource !== key || !data.graph)
        throw new Error(`Invalid source dialogue ${key}`);
      return data;
    })());
    return trees.get(key);
  }
  async function frame(id, number) {
    const key = `CBMP:${id}`;
    const descriptor = manifest.resources[key]?.frames[number];
    if (!descriptor || descriptor.frame !== number) throw new Error(`Unsupported frame ${key}/${number}`);
    const cacheKey = `${key}/${number}`;
    if (!cached.has(cacheKey)) cached.set(cacheKey,(async () => {
      const indices = await bytes(descriptor.indices, descriptor.indices_sha256);
      if (indices.length !== descriptor.width * descriptor.height) throw new Error(`Invalid frame geometry ${cacheKey}`);
      return {...descriptor, indices};
    })());
    return cached.get(cacheKey);
  }
  return {manifest,palette,journal,journalStatus,seattlePopulation,initializedFrame,sceneHotspots,frame,tree,voice};
}
