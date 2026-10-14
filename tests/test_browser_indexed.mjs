import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {copyIndexedRectangle, windowsDisplayIndices, rgbaFromIndices} from '../web/render/indexed.mjs';
const native = JSON.parse(readFileSync(new URL('../docs/image-copy-browser-evidence.json', import.meta.url)));
const rows = [];
for (const [entry, reverse, unconditional] of [[0x344, false, false], [0x4fc, true, false], [0x42a, false, true]]) {
  for (let width = 1; width <= 9; width++) {
    for (const height of [1, 2, 3]) {
      for (const key of [0, 37, 255]) {
        const stride = width + 3;
        const source = Uint8Array.from({length: stride * height}, (_, i) => i % 3 === 0 ? key : (i * 17 + 5) % 256);
        const destination = new Uint8Array(stride * height).fill(203);
        copyIndexedRectangle(source, destination, {width, height, sourceStride: stride,
          destinationStride: stride, sourceOffset: 0, destinationOffset: 0, reverse,
          excludedIndex: unconditional ? null : key});
        rows.push([entry, reverse, unconditional, width, height, key,
          createHash('sha256').update(destination).digest('hex')]);
      }
    }
  }
}
assert.equal(rows.length, native.cases);
assert.equal(createHash('sha256').update(JSON.stringify(rows)).digest('hex'), native.output_matrix_rows_sha256);
// Native normalization expectations independently retained in its source proof.
const normalized = windowsDisplayIndices(Uint8Array.from({length:256},(_,i)=>i));
assert.deepEqual([...normalized.slice(0,11)], [0,120,120,120,120,120,120,120,120,120,10]);
assert.deepEqual([...normalized.slice(244)], [244,120,120,120,120,120,120,120,120,120,120,120]);
const palette = new Uint8Array(768); palette.set([255,128,3],3);
assert.deepEqual([...rgbaFromIndices(new Uint8Array([0,1]),palette)], [0,0,0,255,255,130,0,255]);
assert.throws(() => copyIndexedRectangle(new Uint8Array(1), new Uint8Array(1),
  {width:2,height:1,sourceStride:2,destinationStride:2,sourceOffset:0,destinationOffset:0,
    reverse:false,excludedIndex:null}), RangeError);
console.log(`Browser indexed copy matches ${rows.length} original x86 cases`);
