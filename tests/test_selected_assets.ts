// Server boundary checks for the Vite asset mount (formerly tests/test_serve_port.py).
// Only the explicitly selected directory is reachable; traversal, absolute
// paths, backslashes, bad encodings and symlink escapes fail closed.
import assert from 'node:assert/strict';
import {mkdtempSync, mkdirSync, realpathSync, rmSync, symlinkSync, writeFileSync} from 'node:fs';
import {tmpdir} from 'node:os';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {resolveSelectedAsset} from '../tools/selected-assets.ts';
const repository = fileURLToPath(new URL('../', import.meta.url));
const temp = mkdtempSync(path.join(tmpdir(), 'yukon-assets-'));
try {
  const assets = realpathSync(temp);
  writeFileSync(path.join(assets, 'manifest.json'), '{}');
  mkdirSync(path.join(assets, 'frames'));
  writeFileSync(path.join(assets, 'frames', 'a.bin'), new Uint8Array([1, 2, 3]));
  symlinkSync(path.join(repository, 'original'), path.join(assets, 'escape'), 'dir');
  const served = resolveSelectedAsset(assets, 'manifest.json');
  assert.deepEqual(served, {kind: 'file', path: path.join(assets, 'manifest.json'), size: 2});
  assert.equal(resolveSelectedAsset(assets, 'frames/a.bin').kind, 'file');
  assert.equal(resolveSelectedAsset(assets, 'frames%2Fa.bin').kind, 'file');
  assert.equal(resolveSelectedAsset(assets, 'absent.json').kind, 'missing');
  assert.equal(resolveSelectedAsset(assets, 'frames').kind, 'missing');
  for (const blocked of ['../original/iso/YUKONCD.ISO', '%2e%2e/original/iso/YUKONCD.ISO',
    '../../original/iso/YUKONCD.ISO', '/etc/passwd', '..%5coriginal', 'frames\\a.bin',
    './manifest.json', 'frames//a.bin', 'manifest.json%00', '%zz',
    'escape/README.md', 'escape/iso/YUKONCD.ISO']) {
    assert.equal(resolveSelectedAsset(assets, blocked).kind, 'blocked', blocked);
  }
  assert.equal(resolveSelectedAsset(path.join(assets, 'nope'), 'manifest.json').kind, 'blocked');
} finally {
  rmSync(temp, {recursive: true, force: true});
}
console.log('Selected asset mount serves only the chosen directory; traversal, absolute, backslash, encoding and symlink escapes are blocked');
