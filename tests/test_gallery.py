"""Build and inspect the demo-only gallery with real Hugo modules."""
from html.parser import HTMLParser
from pathlib import Path
import json
import importlib.util
import os
import subprocess
import shutil
from unittest.mock import patch
import sys
import tempfile
import unittest
from urllib.parse import urljoin, urlparse, unquote

ROOT = Path(__file__).resolve().parents[1]
BASE_URL = 'https://gallery.example.test/preview/'


class Document(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.links = []
        self.resources = []
        self.switches = {}
        self.gallery_count = 0
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'nav' and 'skin-gallery' in attrs.get('class', '').split():
            self.gallery_count += 1
        if tag == 'a' and 'href' in attrs:
            self.links.append(attrs['href'])
            if 'data-skin-id' in attrs:
                self.switches[attrs['data-skin-id']] = attrs
        if tag in ('link', 'script', 'img'):
            value = attrs.get('href' if tag == 'link' else 'src')
            if value:
                self.resources.append(value)


class GalleryIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.output = Path(cls.tmp.name) / 'public'
        result = subprocess.run(
            [sys.executable, str(ROOT/'demo/build.py'), '--destination', str(cls.output), '--base-url', BASE_URL],
            capture_output=True, text=True, env=os.environ.copy())
        if result.returncode:
            cls.tmp.cleanup()
            raise AssertionError(result.stdout + result.stderr)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def read(self, relative):
        return (self.output/relative).read_text()

    def test_separate_builds_share_content_but_not_skin_assets(self):
        stock = self.read('stock/posts/hello/index.html')
        retro = self.read('retro/posts/hello/index.html')
        for content in (stock, retro):
            self.assertIn('A notebook for the curious', content)
            self.assertIn('Keep the details', content)
            self.assertIn('Compare ideas', content)
        self.assertNotIn('/archie-skins/retro/skin.', stock)
        self.assertIn('/preview/retro/archie-skins/retro/skin.', retro)
        self.assertFalse((self.output/'stock/archie-skins/retro').exists())
        self.assertIn('/preview/stock/css/main.', stock)
        self.assertIn('/preview/retro/css/main.', retro)

    def test_switching_links_keep_equivalent_pages(self):
        for relative in ['index.html', 'posts/hello/index.html', 'tags/notes/index.html']:
            suffix = relative.removesuffix('index.html')
            for current in ['stock', 'retro']:
                doc = Document(self.read(f'{current}/{relative}'))
                self.assertEqual(doc.gallery_count, 1)
                self.assertEqual(set(doc.switches), {'stock', 'retro'})
                for target, attrs in doc.switches.items():
                    self.assertEqual(urlparse(attrs['href']).path, f'/preview/{target}/{suffix}')
                    if target == current:
                        self.assertIn(attrs.get('aria-current'), ['true', 'page'])

    def test_landing_and_missing_page_offer_valid_recovery(self):
        for relative in ['index.html', '404.html']:
            doc = Document(self.read(relative))
            paths = [urlparse(href).path for href in doc.links]
            self.assertIn('/preview/stock/', paths)
            self.assertIn('/preview/retro/', paths)
        self.assertTrue((self.output/'gallery.css').is_file())
        self.assertTrue((self.output/'gallery.js').is_file())

    def test_all_local_html_links_and_assets_resolve_under_prefix(self):
        for page in self.output.rglob('*.html'):
            relative = page.relative_to(self.output).as_posix()
            page_url = urljoin(BASE_URL, relative)
            doc = Document(page.read_text())
            for href in doc.links + doc.resources:
                if href.startswith(('mailto:', 'tel:', 'data:', 'javascript:', '#')):
                    continue
                target = urlparse(urljoin(page_url, href))
                if target.netloc != 'gallery.example.test':
                    continue
                self.assertTrue(target.path.startswith('/preview/'), (relative, href))
                candidate = self.output / unquote(target.path.removeprefix('/preview/'))
                if candidate.is_dir():
                    candidate /= 'index.html'
                self.assertTrue(candidate.is_file(), f'{relative}: broken link/asset {href}')

    def test_public_output_contains_no_private_repository_source(self):
        forbidden = {'go.mod', 'go.sum', 'LICENSE', 'LICENSE-Archie', 'LICENSE-Feather', 'README.md', 'skins.json', 'build.py'}
        for entry in self.output.rglob('*'):
            self.assertNotIn(entry.name, forbidden)
            self.assertNotIn('.git', entry.relative_to(self.output).parts)
            self.assertNotIn('.github', entry.relative_to(self.output).parts)
            self.assertFalse(entry.is_symlink())


class GalleryConfiguration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('gallery_builder', ROOT/'demo/build.py')
        cls.builder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.builder)

    def test_manifest_rejects_invalid_slugs_duplicates_and_external_paths(self):
        valid = {'id': 'stock', 'name': 'Stock', 'module': 'github.com/ouankou/archie-skins', 'path': '.', 'description': 'Unmodified Archie'}
        invalid_manifests = [[], [dict(valid, id='../escape')], [valid, valid], [dict(valid, path='/tmp')], [dict(valid, description='')]]
        with tempfile.TemporaryDirectory() as directory:
            manifest = Path(directory)/'skins.json'
            for value in invalid_manifests:
                with self.subTest(value=value):
                    manifest.write_text(json.dumps(value))
                    with self.assertRaises(ValueError):
                        self.builder.load_skins(manifest)

    def test_builder_refuses_destructive_destination_and_invalid_base_url(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)/'existing'
            output.mkdir()
            marker = output/'keep.txt'
            marker.write_text('do not delete')
            with self.assertRaises(ValueError):
                self.builder.build(output, BASE_URL, ROOT/'demo/skins.json')
            self.assertEqual(marker.read_text(), 'do not delete')
            for invalid in ['file:///tmp/site', '/relative/', 'https://example.org/?bad=1', 'https://example.org/#fragment']:
                with self.subTest(base_url=invalid), self.assertRaises(ValueError):
                    self.builder.build(Path(directory)/'new', invalid, ROOT/'demo/skins.json')

    def test_switch_falls_back_when_renderer_does_not_emit_equivalent_page(self):
        # Exercise a future style with a genuinely different output inventory;
        # do not imply Hugo inherits unsupported module disableKinds settings.
        real_run = subprocess.run
        def render_with_missing_taxonomy(command, **kwargs):
            result = real_run(command, **kwargs)
            rendered = Path(command[command.index('--destination') + 1])
            if rendered.name == 'limited':
                shutil.rmtree(rendered/'tags')
            return result
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            skins = json.loads((ROOT/'demo/skins.json').read_text())
            skins.append({'id': 'limited', 'name': 'Limited output', 'module': 'github.com/ouankou/archie-skins', 'path': '.', 'description': 'Synthetic missing-page inventory'})
            manifest = directory/'skins.json'
            manifest.write_text(json.dumps(skins))
            output = directory/'public'
            with patch.object(self.builder.subprocess, 'run', side_effect=render_with_missing_taxonomy):
                self.builder.build(output, BASE_URL, manifest)
            fallback = Document((output/'retro/tags/notes/index.html').read_text()).switches['limited']
            self.assertEqual(urlparse(fallback['href']).path, '/preview/limited/')
            self.assertEqual(fallback['data-equivalent'], 'false')

    def test_manifest_addition_extends_gallery_without_dispatch_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            directory = Path(directory)
            skins = json.loads((ROOT/'demo/skins.json').read_text())
            skins.append({'id': 'future-style', 'name': 'Future style', 'module': 'github.com/ouankou/archie-skins', 'path': '.', 'description': 'A third independently built variant'})
            manifest = directory/'skins.json'
            manifest.write_text(json.dumps(skins))
            output = directory/'public'
            result = subprocess.run([sys.executable, str(ROOT/'demo/build.py'), '--destination', str(output), '--base-url', BASE_URL, '--manifest', str(manifest)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            future = (output/'future-style/posts/hello/index.html').read_text()
            self.assertNotIn('/archie-skins/retro/skin.', future)
            doc = Document((output/'retro/posts/hello/index.html').read_text())
            self.assertEqual(urlparse(doc.switches['future-style']['href']).path, '/preview/future-style/posts/hello/')


if __name__ == '__main__':
    unittest.main()
