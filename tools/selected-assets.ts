// Serve explicitly selected, Git-ignored asset directories on fixed URL
// prefixes from the Vite dev/preview server. This replaces the asset mounts of
// the former tools/serve_port.py; Vite itself serves web/. Original media and
// guest directories are never mounted, and every path fails closed.
import {createReadStream, realpathSync, statSync} from 'node:fs';
import type {IncomingMessage, ServerResponse} from 'node:http';
import path from 'node:path';
import type {Plugin} from 'vite';

export type SelectedAssetResolution =
  | {kind: 'blocked'}
  | {kind: 'missing'}
  | {kind: 'file'; path: string; size: number};

/** Mount prefix (with trailing slash) → selected directory, or undefined when unmounted. */
export type SelectedAssetMounts = Record<string, string | undefined>;

const contentTypes: Record<string, string> = {
  '.json': 'application/json',
  '.js': 'text/javascript',
  '.mjs': 'text/javascript',
  '.wasm': 'application/wasm',
  '.wav': 'audio/wav',
  '.ttf': 'font/ttf',
  '.bin': 'application/octet-stream',
  '.zip': 'application/zip',
  '.png': 'image/png',
  '.txt': 'text/plain; charset=utf-8',
};

function isMissing(error: unknown): boolean {
  return typeof error === 'object' && error !== null &&
    ['ENOENT', 'ENOTDIR'].includes(String((error as {code?: unknown}).code));
}

/**
 * Resolve the part of a request path after its mount prefix inside `base`.
 * Dot segments, empty segments, backslashes, absolute paths, decoding errors
 * and symlinks that leave the real base directory are blocked rather than
 * served; nonexistent files and directories are reported as missing.
 */
export function resolveSelectedAsset(base: string, relative: string): SelectedAssetResolution {
  let decoded: string;
  try { decoded = decodeURIComponent(relative); } catch { return {kind: 'blocked'}; }
  if (decoded.includes('\\') || decoded.includes('\0') || decoded.startsWith('/')) return {kind: 'blocked'};
  const parts = decoded.split('/');
  if (parts.some(part => part === '' || part === '.' || part === '..')) return {kind: 'blocked'};
  let baseReal: string;
  try { baseReal = realpathSync.native(base); } catch { return {kind: 'blocked'}; }
  let real: string;
  try { real = realpathSync.native(path.join(baseReal, ...parts)); }
  catch (error) { return isMissing(error) ? {kind: 'missing'} : {kind: 'blocked'}; }
  if (real !== baseReal && !real.startsWith(baseReal + path.sep)) return {kind: 'blocked'};
  const stats = statSync(real);
  return stats.isFile() ? {kind: 'file', path: real, size: stats.size} : {kind: 'missing'};
}

export function selectedAssetsMiddleware(mounts: SelectedAssetMounts) {
  return (request: IncomingMessage, response: ServerResponse, next: () => void): void => {
    const pathname = (request.url ?? '').split('?')[0];
    const prefix = Object.keys(mounts).find(candidate => pathname.startsWith(candidate));
    if (prefix === undefined) return next();
    if (request.method !== 'GET' && request.method !== 'HEAD') {
      response.statusCode = 405; response.end(); return;
    }
    const base = mounts[prefix];
    const resolution: SelectedAssetResolution = base === undefined
      ? {kind: 'blocked'} : resolveSelectedAsset(base, pathname.slice(prefix.length));
    if (resolution.kind !== 'file') {
      response.statusCode = 404;
      response.setHeader('Content-Type', 'text/plain; charset=utf-8');
      response.end('Unsupported path'); return;
    }
    response.statusCode = 200;
    response.setHeader('Content-Type',
      contentTypes[path.extname(resolution.path).toLowerCase()] ?? 'application/octet-stream');
    response.setHeader('Content-Length', String(resolution.size));
    response.setHeader('Cache-Control', 'no-store');
    if (request.method === 'HEAD') { response.end(); return; }
    createReadStream(resolution.path).on('error', () => response.destroy()).pipe(response);
  };
}

export interface SelectedAssetsOptions {
  mounts: SelectedAssetMounts;
  /** Prefixes whose directory must be selected for the server to start. */
  required?: string[];
}

export function selectedAssetsPlugin(options: SelectedAssetsOptions): Plugin {
  return {
    name: 'yukon-selected-assets',
    configResolved() {
      for (const [prefix, directory] of Object.entries(options.mounts)) {
        if (directory === undefined) {
          if (options.required?.includes(prefix)) {
            throw new Error(`Select a prepared asset directory for ${prefix} (YUKON_ASSETS, see docs/PORT-RUN.md)`);
          }
          continue;
        }
        if (!statSync(path.join(directory, 'manifest.json'), {throwIfNoEntry: false})?.isFile()) {
          throw new Error(`${prefix} directory ${directory} has no manifest.json; prepare the assets first`);
        }
      }
    },
    configureServer(server) { server.middlewares.use(selectedAssetsMiddleware(options.mounts)); },
    configurePreviewServer(server) { server.middlewares.use(selectedAssetsMiddleware(options.mounts)); },
  };
}
