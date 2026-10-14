import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {cachedFrameProvider} from '../web/rules/cached-frames.mjs';
import {spritePixelHit} from '../web/rules/seattle-navigation.mjs';
const directory = process.argv[2], metadata = JSON.parse(fs.readFileSync(path.join(directory, 'cached-frames.json')));
const oracle = JSON.parse(fs.readFileSync(new URL('../docs/cached-frame-recovery-evidence.json', import.meta.url)));
const buffers = new Map(Object.values(metadata.frames).map(r => [r.pixels_file, new Uint8Array(fs.readFileSync(path.join(directory, r.pixels_file)))]));
const provider = cachedFrameProvider(metadata, buffers);
let hits = 0;
for (const c of oracle.cases) {
  const f = provider(c.bitmap_id, c.frame);
  assert.equal(crypto.createHash('sha256').update(f.pixels).digest('hex'), c.original_buffer_sha256);
  assert.deepEqual([f.width, f.height, f.stride, f.allocatedHeight], [c.width, c.height, c.stride, c.allocated_height]);
  const sprite = {...f, rectangleTLBR: [10, 20, 10 + f.height, 20 + f.width]};
  for (const h of c.original_hits) {
    // Original manager only admits inclusive-bbox points. Extra padding samples
    // past the right edge characterize e78a alone, not manager dispatch.
    if (h.x > f.width || h.y > f.height) continue;
    assert.equal(spritePixelHit(sprite, h.x + 20, h.y + 10), h.original_hit); hits++;
  }
}
assert.throws(() => provider(9999, 0), /outside/);
console.log(`${oracle.cases.length} complete original buffers and ${hits} real-frame manager-admissible hit samples matched`);
