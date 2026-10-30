"""Build real, isolated consumer sites. Run: python3 -m unittest discover -s tests -v."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
HUGO = os.environ.get('HUGO_BIN', 'hugo')
UPSTREAM = 'github.com/athul/archie'
VERSION = 'v0.0.0-20260330114547-cbc1c3aaa261'


class ModuleIntegration(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)

    def build(self, name, module, replacement=None, extra='', expect_success=True):
        site = self.base / name
        (site / 'content/posts').mkdir(parents=True)
        (site / 'content/posts/hello.md').write_text('---\ntitle: Hello\ndate: 2026-01-01\ntags: [notes]\ntoc: true\n---\n\n## Heading\n\n```python {linenos=inline}\n    print("hello")\n```\n\n| A | B |\n|---|---|\n| 1 | 2 |\n')
        version = VERSION if module == UPSTREAM else 'v0.0.0'
        gomod = f'module example.org/test-{name}\n\ngo 1.23.0\n\nrequire {module} {version}\n'
        if replacement:
            gomod += f'replace {module} => {replacement}\n'
        (site / 'go.mod').write_text(gomod)
        (site / 'hugo.toml').write_text('baseURL = "https://example.org/demo/"\ntitle = "Test notebook"\n[params]\n  mainSections = ["posts"]\n  useCDN = false\n' + extra + f'\n[module]\n  [[module.imports]]\n    path = "{module}"\n')
        result = subprocess.run([HUGO, '--source', str(site), '--destination', str(site / 'public')], capture_output=True, text=True)
        if expect_success:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        return site, result

    def test_neutral_is_upstream_output_and_assets(self):
        neutral, _ = self.build('neutral', 'github.com/ouankou/archie-skins', ROOT)
        upstream, _ = self.build('upstream', UPSTREAM)
        for relative in ['index.html', 'posts/hello/index.html', 'tags/notes/index.html', 'js/themetoggle.js']:
            self.assertEqual((neutral/'public'/relative).read_bytes(), (upstream/'public'/relative).read_bytes(), relative)
        self.assertFalse((neutral/'public/archie-skins').exists())
        self.assertNotIn('tape-', (neutral/'public/index.html').read_text())

    def test_retro_composes_and_supports_subpaths(self):
        site, _ = self.build('retro', 'github.com/ouankou/archie-skins/skins/retro', ROOT/'skins/retro')
        html = (site/'public/index.html').read_text()
        self.assertIn('tape-hero', html)
        self.assertIn('Test notebook', html)
        self.assertIn('class="wordmark" href="/demo/"', html)
        self.assertIn('/demo/archie-skins/retro/skin.', html)
        self.assertIn('/demo/css/main.', html)
        self.assertIn('/demo/archie-skins/retro/theme.js', html)
        article = (site/'public/posts/hello/index.html').read_text()
        self.assertIn('table-scroll', article)
        self.assertIn('TableOfContents', article)
        self.assertNotIn('blog.ouankou.com', html)
        self.assertNotIn('Anjia', html)

    def test_future_sibling_style_needs_no_retro_or_dispatch_edits(self):
        style = self.base/'new-style'
        (style/'assets/css').mkdir(parents=True)
        (style/'go.mod').write_text(f'module example.org/blue-style\n\ngo 1.23.0\n\nrequire {UPSTREAM} {VERSION}\n')
        (style/'hugo.toml').write_text(f'[params]\n  customCSS = ["css/blue.css"]\n[module]\n  [[module.imports]]\n    path = "{UPSTREAM}"\n')
        (style/'assets/css/blue.css').write_text(':root { --color-primary: blue; }')
        site, _ = self.build('blue', 'example.org/blue-style', style)
        html = (site/'public/index.html').read_text()
        self.assertIn('/demo/css/blue.', html)
        self.assertNotIn('tape-', html)
        self.assertFalse((site/'public/archie-skins').exists())

    def test_consumer_can_preserve_existing_archive_and_taxonomy_copy(self):
        site, _ = self.build('legacy-copy', 'github.com/ouankou/archie-skins/skins/retro', ROOT/'skins/retro', extra='[params.retro]\n  archiveLabel = "POSTS"\n  listTitle = "All articles"\n  taxonomyTitle = "All tags"\n')
        self.assertIn('1 POSTS</span>', (site/'public/index.html').read_text())
        self.assertIn('>All articles</h1>', (site/'public/posts/index.html').read_text())
        self.assertIn('>All tags</h1>', (site/'public/tags/index.html').read_text())
        default_site, _ = self.build('generic-copy', 'github.com/ouankou/archie-skins/skins/retro', ROOT/'skins/retro')
        self.assertIn('1 ENTRIES</span>', (default_site/'public/index.html').read_text())
        self.assertIn('>Tags</h1>', (default_site/'public/tags/index.html').read_text())
        css = (ROOT/'skins/retro/assets/archie-skins/retro/skin.css').read_text()
        self.assertIn('.tape-hero-main > div { min-width: 0; }', css)

    def test_missing_style_fails_instead_of_silently_using_upstream(self):
        _, result = self.build('missing', 'example.org/missing-style', self.base/'does-not-exist', expect_success=False)
        self.assertIn('does-not-exist', result.stderr + result.stdout)

    def test_missing_custom_asset_is_a_build_error(self):
        _, result = self.build('bad-css', 'github.com/ouankou/archie-skins/skins/retro', ROOT/'skins/retro', extra='  customCSS = ["css/does-not-exist.css"]\n', expect_success=False)
        self.assertIn('error', (result.stdout + result.stderr).lower())

    def test_replaced_default_scripts_fail_clearly(self):
        _, result = self.build('bad-js', 'github.com/ouankou/archie-skins/skins/retro', ROOT/'skins/retro', extra='  customJS = ["js/local.js"]\n', expect_success=False)
        self.assertIn('params.customJS replaces module defaults', result.stderr + result.stdout)

    def test_all_color_modes_and_invalid_configuration(self):
        for mode in ['light', 'dark', 'auto', 'toggle']:
            site, _ = self.build('mode-' + mode, 'github.com/ouankou/archie-skins/skins/retro', ROOT/'skins/retro', extra=f'  mode = "{mode}"\n')
            html = (site/'public/index.html').read_text()
            self.assertIn(f'data-color-mode="{mode}"', html)
            self.assertEqual('id="dark-mode-toggle"' in html, mode == 'toggle')
        _, result = self.build('mode-invalid', 'github.com/ouankou/archie-skins/skins/retro', ROOT/'skins/retro', extra='  mode = "unknown"\n', expect_success=False)
        self.assertIn('params.mode', result.stderr + result.stdout)

    def test_consumer_assets_extend_defaults_in_order(self):
        # A consumer can append assets explicitly, preserving the skin prerequisites.
        site = self.base/'extended'
        (site/'assets/css').mkdir(parents=True)
        (site/'assets/css/local.css').write_text('body { font-size: 17px; }')
        site, _ = self.build('extended', 'github.com/ouankou/archie-skins/skins/retro', ROOT/'skins/retro', extra='  customCSS = ["archie-skins/retro/skin.css", "archie-skins/retro/reading.css", "css/local.css"]\n')
        html = (site/'public/index.html').read_text()
        self.assertLess(html.index('/retro/skin.'), html.index('/retro/reading.'))
        self.assertLess(html.index('/retro/reading.'), html.index('/css/local.'))

    def test_pins_are_identical_and_no_upstream_head_copy(self):
        for path in [ROOT/'go.mod', ROOT/'skins/retro/go.mod']:
            self.assertIn(f'{UPSTREAM} {VERSION}', path.read_text())
        self.assertFalse((ROOT/'skins/retro/layouts/partials/header.html').exists())
        # Root may carry namespaced opt-in helpers, never overrides of Archie.
        self.assertEqual([p.relative_to(ROOT/'layouts').as_posix() for p in (ROOT/'layouts').rglob('*.html')],
                         ['partials/archie-skins/inua/navigation.html'])


if __name__ == '__main__':
    unittest.main()
