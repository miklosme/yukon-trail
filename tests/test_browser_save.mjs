// Actual original read/write block hashes, not model-produced expectations.
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {readOriginalSave,writeOriginalSave,originalHeaderStatus} from '../web/rules/save.mjs';
const native=JSON.parse(readFileSync(new URL('../docs/save-container-recovery-evidence.json',import.meta.url)));
const hash=b=>createHash('sha256').update(b).digest('hex');
const root=new URL('../',import.meta.url);
for(const test of native.cases) {
  const data=new Uint8Array(readFileSync(new URL(test.path,root)));
  assert.equal(hash(data),test.sha256,'Original evidence save changed');
  const save=readOriginalSave(data);
  for(const [i,key] of ['signature','title','version','state','journal'].entries()) {
    assert.equal(hash(save[key]),test.read_transfers[i].sha256);
    assert.equal(hash(save[key]),test.write_transfers[i].sha256);
  }
  assert.equal(hash(writeOriginalSave(save)),test.sha256);
  // Parser must own its blocks, preserving source evidence bytes independently.
  save.state[0]^=255;
  assert.equal(hash(data),test.sha256);
  assert.notEqual(hash(writeOriginalSave(save)),test.sha256);
  assert.throws(()=>readOriginalSave(data.slice(1)),TypeError);
  const changed=data.slice();changed[69]=57;
  assert.throws(()=>readOriginalSave(changed),RangeError);
}
console.log(`Save container matches ${native.cases.length} original read/write block and full-file hashes; no browser restore claim`);

const headers=JSON.parse(readFileSync(new URL('../docs/save-header-recovery-evidence.json',import.meta.url)));
for(const test of headers.cases) {
  const header=new Uint8Array(Buffer.from(test.header_hex,'hex'));
  assert.equal(originalHeaderStatus(header),test.native_status);
  const data=new Uint8Array(11221);data.set(header);
  if(test.native_status===0) assert.deepEqual(writeOriginalSave(readOriginalSave(data)),data);
  else assert.throws(()=>readOriginalSave(data),RangeError);
}
console.log(`Header decisions match ${headers.native_cases} original cases; older-version warning/restore remains unsupported`);
