#!/usr/bin/env python3
"""Serve only the local port and explicitly prepared assets on loopback."""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, assets, trial_assets=None, **kwargs):
        self.assets = assets
        self.trial_assets = trial_assets
        super().__init__(*args, **kwargs)

    def translate_path(self, path):
        requested = unquote(urlsplit(path).path)
        base, relative = ROOT / 'web', requested.lstrip('/')
        for prefix, selected in (('/game-assets/', self.assets),
                                 ('/emulation-assets/', getattr(self, 'trial_assets', None))):
            if requested.startswith(prefix):
                if selected is None:
                    return str(ROOT / 'web' / '__unsupported_path__')
                base, relative = selected, requested[len(prefix):]
                break
        parts = Path(relative).parts
        if any(part in ('..', '.') for part in parts) or '\\' in relative:
            return str(ROOT / 'web' / '__unsupported_path__')
        result = (base / relative).resolve()
        if result != base and base not in result.parents:
            return str(ROOT / 'web' / '__unsupported_path__')
        return str(result)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assets', type=Path, required=True)
    parser.add_argument('--port', type=int, default=8000)
    parser.add_argument('--trial-assets', type=Path,
                        help='Optional separately prepared emulator trial assets')
    args = parser.parse_args()
    assets = args.assets.resolve()
    if not (assets / 'manifest.json').is_file():
        parser.error('Prepare the source asset manifest first')
    trial_assets = args.trial_assets.resolve() if args.trial_assets else None
    if trial_assets and not (trial_assets / 'manifest.json').is_file():
        parser.error('Prepare the emulator trial manifest first')
    server = ThreadingHTTPServer(('127.0.0.1', args.port),
                                partial(Handler, assets=assets, trial_assets=trial_assets))
    print(f'Local: http://127.0.0.1:{server.server_port}/', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
