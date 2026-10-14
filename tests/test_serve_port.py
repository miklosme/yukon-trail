import tempfile
import unittest
from pathlib import Path
from tools.serve_port import Handler, ROOT


class LocalServePaths(unittest.TestCase):
    def setUp(self):
        self.handler = Handler.__new__(Handler)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.handler.assets = Path(self.temp.name).resolve()

    def test_only_port_root_is_served(self):
        self.assertEqual(Path(self.handler.translate_path('/main.mjs?version=1')), ROOT / 'web' / 'main.mjs')
        self.assertEqual(Path(self.handler.translate_path('/original/iso/YUKONCD.ISO')),
                         ROOT / 'web' / 'original' / 'iso' / 'YUKONCD.ISO')

    def test_selected_assets_are_separate_from_source_tree(self):
        self.assertEqual(Path(self.handler.translate_path('/game-assets/manifest.json')),
                         self.handler.assets / 'manifest.json')

    def test_trial_assets_require_explicit_mount_and_cannot_escape(self):
        blocked = ROOT / 'web' / '__unsupported_path__'
        self.assertEqual(Path(self.handler.translate_path('/emulation-assets/manifest.json')), blocked)
        self.handler.trial_assets = self.handler.assets
        self.assertEqual(Path(self.handler.translate_path('/emulation-assets/manifest.json')),
                         self.handler.assets / 'manifest.json')
        for path in ('/emulation-assets/../original/iso/YUKONCD.ISO',
                     '/emulation-assets//etc/passwd', '/emulation-assets/..%5coriginal'):
            self.assertEqual(Path(self.handler.translate_path(path)), blocked)
        (self.handler.assets / 'escape').symlink_to(ROOT / 'original', target_is_directory=True)
        self.assertEqual(Path(self.handler.translate_path('/emulation-assets/escape/iso/YUKONCD.ISO')), blocked)

    def test_traversal_and_absolute_asset_paths_fail_closed(self):
        blocked = ROOT / 'web' / '__unsupported_path__'
        for path in ('/../original/iso/YUKONCD.ISO', '/%2e%2e/original/iso/YUKONCD.ISO',
                     '/game-assets/../../original/iso/YUKONCD.ISO', '/game-assets//etc/passwd',
                     '/game-assets/..%5coriginal'):
            self.assertEqual(Path(self.handler.translate_path(path)), blocked)

    def test_symlink_cannot_escape_selected_assets(self):
        (self.handler.assets / 'escape').symlink_to(ROOT / 'original', target_is_directory=True)
        self.assertEqual(Path(self.handler.translate_path('/game-assets/escape/iso/YUKONCD.ISO')),
                         ROOT / 'web' / '__unsupported_path__')
