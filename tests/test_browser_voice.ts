import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {readPreparedVoice,unsigned8ToFloat32} from '../web/platform/voice.ts';
if(!process.argv[2]) throw new Error('Pass prepared Seattle voice asset directory');
const directory=process.argv[2];
const manifest=JSON.parse(readFileSync(`${directory}/manifest.json`, 'utf8'));
const native=JSON.parse(readFileSync(process.argv[3] ?? new URL('../docs/seattle-sound-set-recovery-evidence.json',import.meta.url), 'utf8'));
assert.equal(manifest.archive_sha256,native.archive_sha256);
assert.equal(manifest.executable_sha256,native.executable_sha256);
const hash=data=>createHash('sha256').update(data).digest('hex');
let total=0;
for(const [key,expected] of Object.entries<any>(native.sounds)) {
  const asset=manifest.sounds[key];assert(asset,`Missing original voice ${key}`);
  const wav=new Uint8Array(readFileSync(`${directory}/${asset.file}`));
  assert.equal(hash(wav),asset.sha256);
  const voice=readPreparedVoice(wav);
  assert.equal(hash(voice.pcm),expected.native_pcm_sha256,'Imported samples differ from original native converter');
  assert.equal(hash(voice.pcm),asset.pcm_sha256);
  assert.equal(voice.pcm.length,expected.sample_bytes);
  assert.equal(asset.raw_sha256,expected.raw_sha256);
  assert.equal(asset.offset,expected.offset);
  total+=voice.pcm.length;
  const corrupt=wav.slice();corrupt[24]=0;
  assert.throws(()=>readPreparedVoice(corrupt),RangeError);
  assert.throws(()=>readPreparedVoice(wav.slice(1)),RangeError);
}
assert.equal(total,native.sample_bytes);
// Independently specified unsigned PCM endpoints/neutral point for Web Audio.
assert.deepEqual([...unsigned8ToFloat32(Uint8Array.of(0,64,128,192,255))],[-1,-.5,0,.5,127/128]);
assert.throws(()=>unsigned8ToFloat32(new Uint8Array()),TypeError);
console.log(`Prepared voice adapter preserves ${Object.keys(native.sounds).length} original voices /${total} native sample bytes; no browser/audio-output claim`);
