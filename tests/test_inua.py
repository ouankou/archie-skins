"""Real consumer and extracted-module tests for the seven Inua palette adapters.

Run with Hugo >= 0.157.0 and Go on PATH:
    python3 -m unittest discover -s tests -p test_inua.py -v

Expected colors are independently recorded from Inua's Apache-2.0 palette files;
tests do not need the research checkout or the rest of this monorepo at runtime.
"""
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
HUGO = os.environ.get('HUGO_BIN', 'hugo')
MODULE = 'github.com/ouankou/archie-skins'
SKINS = ('washi', 'aojashin', 'yoru', 'suimen', 'rinko', 'bunko', 'denko')
KEYS = 'app panel surface surface2 sb t0 t1 t2 line accent sbaccent primary danger ok warn field'.split()
# Same order as KEYS. Do not derive expected values from the implementation.
PALETTES = {
    'washi': 'F2EDE2 EEE8DB FAF7F0 E9E3D6 1E1E20 1E1E20 4A4843 696662 D6CFBF 2F4A6D 9FB6D6 1E1E20 B8412D 3F6D5E B7791F BDB7AC',
    'aojashin': 'F1F4F8 EBF0F6 F9FBFD E4EBF4 E6EDF6 0E2C57 34507A 566A8A C8D4E4 2463AE 2463AE 2463AE B8412D 2F7A62 A86A12 B8C9E2',
    'yoru': '0B1012 0D1315 121A1C 172124 070B0C E7E4DA B3B6AF 7F8F8C 243134 9FC3C9 9FC3C9 E7E4DA E0694F 7FB89E D9A441 44504E',
    'suimen': '041417 05181B 082125 0B2A2E 021013 D6FFF6 9CCFC6 5FA79C 12403F 22F2D0 22F2D0 22F2D0 FF3D7F 22F2D0 FFC857 12403F',
    'rinko': '03100E 041311 061A16 08211C 020B0A CFFFE8 8FD9B6 4E9C7C 0F3A32 7CFFC4 7CFFC4 7CFFC4 FF6B5B 7CFFC4 FFB547 0F3A32',
    'bunko': '07080F 090B14 0E111D 121629 05060B F2F7FF AEB6CC 7D85A1 1C2342 1FE5FF 1FE5FF F2F7FF FF2E8A 1FE5FF FFC24D 1C2342',
    'denko': '0B0A1A 0D0B20 13102A 1A1636 07061A E6F9FF A9B6D6 8380A4 2A2046 4DF3FF 4DF3FF 4DF3FF FF4D8D 4DF3FF FFC24D 34204A',
}


def native_mode(skin):
    return 'light' if skin in ('washi', 'aojashin') else 'dark'


class InuaModules(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.serial = 0

    def build(self, skin, *, root=ROOT, skin_directory=None, params='', success=True):
        self.serial += 1
        site = self.base / f'consumer-{skin}-{self.serial}'
        (site/'content/posts').mkdir(parents=True)
        (site/'content/posts/hello.md').write_text('---\ntitle: Shared article\ndate: 2026-01-01\ntags: [notes]\ntoc: true\n---\n\n## Details\n\nA reusable theme.\n\n```python\n    print("hello")\n```\n')
        module = f'{MODULE}/skins/{skin}'
        skin_directory = skin_directory or ROOT/'skins'/skin
        (site/'go.mod').write_text(f'module example.org/inua-consumer\n\ngo 1.23.0\n\nrequire {module} v0.0.0\n\nreplace {module} => {skin_directory}\nreplace {MODULE} => {root}\n')
        (site/'hugo.toml').write_text('baseURL = "https://example.org/notebook/"\ntitle = "Independent notebook"\n[params]\n  mainSections = ["posts"]\n  useCDN = false\n' + params + f'\n[module]\n  [[module.imports]]\n    path = "{module}"\n\n[[menu.main]]\n  name = "Posts"\n  pageRef = "/posts"\n')
        result = subprocess.run([HUGO, '--source', str(site), '--destination', str(site/'public')], capture_output=True, text=True, timeout=120)
        output = result.stdout + result.stderr
        if success:
            self.assertEqual(result.returncode, 0, output)
        else:
            self.assertNotEqual(result.returncode, 0, output)
        return site/'public', output

    def test_all_seven_real_consumers_build_with_native_palette(self):
        for skin in SKINS:
            with self.subTest(skin=skin):
                public, _ = self.build(skin)
                home = (public/'index.html').read_text()
                article = (public/'posts/hello/index.html').read_text()
                self.assertIn('Independent notebook', home)
                self.assertIn('/notebook/archie-skins/inua/base.', home)
                self.assertIn(f'/notebook/archie-skins/{skin}/tokens.', home)
                self.assertIn('href="/notebook/"', home)
                self.assertIn('href="/notebook/posts/"', home)
                self.assertIn('Shared article', article)
                self.assertNotIn('id="dark-mode-toggle"', home)
                self.assertNotIn('archie-skins/retro/', home)
                for other in set(SKINS)-{skin}:
                    self.assertNotIn(f'archie-skins/{other}/', home)
                tokens = list((public/f'archie-skins/{skin}').glob('tokens.*.css'))
                self.assertEqual(len(tokens), 1)
                emitted_css = tokens[0].read_text()
                self.assertRegex(emitted_css, rf'color-scheme:\s*{native_mode(skin)}\s*;')
                self.assertIn('Apache License', emitted_css)
                self.assertIn('Version 2.0', emitted_css)
                self.assertLess(home.index('/inua/base.'), home.index(f'/{skin}/tokens.'))

    def test_exact_original_sixteen_palette_tokens(self):
        for skin in SKINS:
            with self.subTest(skin=skin):
                css = (ROOT/f'skins/{skin}/assets/archie-skins/{skin}/tokens.css').read_text()
                expected = dict(zip(KEYS, PALETTES[skin].split()))
                declarations = re.findall(r'--inua-([a-z0-9]+)\s*:\s*#([0-9a-fA-F]{6})\s*;', css)
                self.assertEqual(len(declarations), 16)
                actual = {key: value.upper() for key, value in declarations}
                self.assertEqual(len(expected), 16)
                self.assertEqual(actual, expected)
                self.assertIn('Apache-2.0', css)

    def test_each_distributed_skin_has_license_and_provenance(self):
        for skin in SKINS:
            with self.subTest(skin=skin):
                directory = ROOT/'skins'/skin
                license_files = [p for p in directory.iterdir() if p.is_file() and p.name.startswith('LICENSE')]
                notice_files = [p for p in directory.iterdir() if p.is_file() and p.name.startswith('NOTICE')]
                self.assertTrue(license_files, f'{skin} is missing distributed license text')
                self.assertTrue(notice_files, f'{skin} is missing distributed provenance notice')
                self.assertTrue(any('Apache License' in p.read_text() and 'Version 2.0' in p.read_text() for p in license_files))
                notice = '\n'.join(p.read_text() for p in notice_files)
                self.assertIn('Inua', notice)
                self.assertIn('github.com', notice)
                self.assertIn('Apache', notice)

    def test_explicit_native_modes_work_and_other_modes_fail(self):
        for skin in SKINS:
            with self.subTest(skin=skin):
                self.build(skin, params=f'  mode = "{native_mode(skin)}"\n')
                opposite = 'dark' if native_mode(skin) == 'light' else 'light'
                for invalid in (opposite, 'auto', 'toggle', 'unknown'):
                    _, output = self.build(skin, params=f'  mode = "{invalid}"\n', success=False)
                    self.assertIn('native', output)
                    self.assertIn('params.mode', output)

    def test_replaced_asset_lists_fail_with_actionable_errors(self):
        for skin in SKINS:
            with self.subTest(skin=skin):
                # Each asset must remain; checking one missing asset at a time avoids
                # masking the validation behind a generic resources.Get failure.
                for retained in ('archie-skins/inua/base.css', f'archie-skins/{skin}/tokens.css'):
                    _, output = self.build(skin, params=f'  customCSS = ["{retained}"]\n', success=False)
                    self.assertIn('params.customCSS replaces module defaults', output)
                    self.assertIn('required Inua asset', output)

    def test_zip_shaped_separate_modules_build_without_monorepo_siblings(self):
        # Go module ZIPs exclude nested modules. Reconstruct that boundary rather
        # than testing a checkout where ../sibling references accidentally work.
        isolated_root = self.base/'isolated-root-module'
        shutil.copytree(ROOT, isolated_root, ignore=shutil.ignore_patterns('.git', 'skins', 'demo', 'exampleSite', 'tests', '.test-output', 'node_modules', 'public', 'resources'))
        self.assertFalse((isolated_root/'skins').exists())
        for skin in SKINS:
            with self.subTest(skin=skin):
                isolated_skin = self.base/f'standalone-{skin}-module'
                shutil.copytree(ROOT/'skins'/skin, isolated_skin, ignore=shutil.ignore_patterns('.git', 'public', 'resources'))
                self.assertFalse((isolated_skin.parent/'skins').exists())
                for config in (isolated_skin/'hugo.toml', isolated_root/'hugo.toml'):
                    self.assertNotRegex(config.read_text(), r'source\s*=\s*[\"\'][^\"\']*\.\./')
                public, _ = self.build(skin, root=isolated_root, skin_directory=isolated_skin)
                self.assertIn(f'/archie-skins/{skin}/tokens.', (public/'index.html').read_text())
                self.assertIn('/archie-skins/inua/base.', (public/'index.html').read_text())


if __name__ == '__main__':
    unittest.main()
