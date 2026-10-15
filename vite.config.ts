import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {defineConfig, loadEnv} from 'vite';
import {selectedAssetsPlugin} from './tools/selected-assets.ts';

// The port is served from web/ on the documented loopback origin. Prepared,
// Git-ignored asset packages are never part of the source tree or the build:
// the dev/preview server mounts one explicitly selected directory per prefix,
// exactly as tools/serve_port.py did (YUKON_ASSETS, optional YUKON_TRIAL_ASSETS).
const repository = fileURLToPath(new URL('.', import.meta.url));

export default defineConfig(({command, mode}) => {
  const env = loadEnv(mode, repository, 'YUKON_');
  const selected = (name: string) => env[name] ? path.resolve(repository, env[name]) : undefined;
  return {
    root: 'web',
    publicDir: false,
    envDir: repository,
    // Unknown paths are 404s, not an index.html fallback, and the dev server may
    // read only web/ (no /@fs/ access to original/, local/ or generated/).
    appType: 'mpa',
    server: {host: '127.0.0.1', port: 8000, strictPort: true,
      fs: {strict: true, allow: [path.join(repository, 'web')]}},
    preview: {host: '127.0.0.1', port: 8000, strictPort: true},
    build: {
      outDir: '../dist',
      emptyOutDir: true,
      target: 'esnext',
      rolldownOptions: {
        input: {
          main: path.join(repository, 'web/index.html'),
          'emulation-trial': path.join(repository, 'web/emulation-trial/index.html'),
        },
      },
    },
    plugins: command === 'serve' ? [selectedAssetsPlugin({
      mounts: {
        '/game-assets/': selected('YUKON_ASSETS'),
        '/emulation-assets/': selected('YUKON_TRIAL_ASSETS'),
      },
      required: ['/game-assets/'],
    })] : [],
  };
});
