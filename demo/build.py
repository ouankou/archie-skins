#!/usr/bin/env python3
"""Build isolated skin previews; gallery chrome never enters a consuming module."""
import argparse
import html
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import tomllib
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]


def load_skins(manifest):
    skins = json.loads(Path(manifest).read_text())
    if not isinstance(skins, list) or not skins:
        raise ValueError('skins manifest must be a nonempty list')
    ids = set()
    for skin in skins:
        identifier = skin.get('id', '')
        if not re.fullmatch(r'[a-z][a-z0-9-]*', identifier) or identifier in ids:
            raise ValueError('skin IDs must be unique lowercase URL slugs')
        ids.add(identifier)
        source = (ROOT / skin['path']).resolve()
        if not source.is_relative_to(ROOT) or not (source / 'go.mod').is_file():
            raise ValueError('skin path must identify a module inside this repository')
        if not skin.get('name') or not skin.get('module') or not skin.get('description'):
            raise ValueError('each skin needs name, module, and description')
    return skins


def page_url(path):
    value = path.as_posix()
    return value[:-10] if value.endswith('index.html') else value


def build(destination, base_url, manifest):
    parsed = urlsplit(base_url)
    if parsed.scheme not in ('https', 'http') or not parsed.netloc or parsed.query or parsed.fragment:
        raise ValueError('base URL must be an absolute HTTP(S) URL without query or fragment')
    base_url = base_url.rstrip('/') + '/'
    base_path = urlsplit(base_url).path
    destination = Path(destination).resolve()
    # Never delete an existing directory or overwrite source files accidentally.
    if destination.exists() and any(destination.iterdir()):
        raise ValueError('destination must be empty; choose a fresh output directory')
    destination.mkdir(parents=True, exist_ok=True)
    skins = load_skins(manifest)
    config = tomllib.loads((ROOT / 'exampleSite/hugo.toml').read_text())
    config.pop('module', None)
    inventories = {}
    for skin in skins:
        identifier = skin['id']
        with tempfile.TemporaryDirectory(prefix='archie-gallery-') as temporary:
            site = Path(temporary)
            shutil.copytree(ROOT / 'exampleSite/content', site / 'content')
            module = skin['module']
            (site / 'go.mod').write_text('module example.org/archie-gallery\n\ngo 1.23.0\n\n'
                + f'require {module} v0.0.0\nreplace {module} => {json.dumps(str((ROOT / skin["path"]).resolve()))}\n')
            variant = dict(config, baseURL=base_url + identifier + '/', module={'imports': [{'path': module}]})
            (site / 'hugo.json').write_text(json.dumps(variant))
            subprocess.run([os.environ.get('HUGO_BIN', 'hugo'), '--source', str(site),
                '--destination', str(destination / identifier)], check=True)
        inventories[identifier] = {path.relative_to(destination / identifier) for path in (destination / identifier).rglob('*.html')}

    def links(current=None, page=Path('index.html')):
        result = []
        for skin in skins:
            equivalent = page in inventories[skin['id']]
            target = page_url(page) if equivalent else ''
            href = base_path + skin['id'] + '/' + target
            active = ' aria-current="true"' if skin['id'] == current else ''
            result.append(f'<a data-skin-id="{skin["id"]}" data-equivalent="{str(equivalent).lower()}" href="{html.escape(href, quote=True)}"{active}>{html.escape(skin["name"])}</a>')
        return ''.join(result)

    for skin in skins:
        for relative in inventories[skin['id']]:
            path = destination / skin['id'] / relative
            markup = path.read_text()
            if not re.search(r'<body\b', markup):
                continue  # Hugo redirect aliases should remain redirects.
            # Archie's absLangURL("/") wordmark ignores a baseURL subpath.
            # Fix only this generated demo link; upstream/module files stay unchanged.
            origin_home = f'{parsed.scheme}://{parsed.netloc}/'
            markup = markup.replace(f'href="{origin_home}"', f'href="{base_path}{skin["id"]}/"')
            # Older upstream tag links can also escape a subpath. Rewrite only
            # root-relative URLs that correspond to an actual variant output.
            def scoped_link(match):
                target = urlsplit(html.unescape(match[1]))
                if target.netloc:
                    return match[0]
                candidate = destination / skin['id'] / target.path.lstrip('/')
                if candidate.is_file() or (candidate / 'index.html').is_file():
                    return 'href="' + html.escape(base_path + skin['id'] + html.unescape(match[1]), quote=True) + '"'
                return match[0]
            markup = re.sub(r'href="(/[^"]*)"', scoped_link, markup)
            chrome = '<nav class="skin-gallery" aria-label="Preview skin"><a class="skin-gallery-home" href="' + base_path + '">Skin gallery</a><span>Preview:</span>' + links(skin['id'], relative) + '</nav>'
            markup = markup.replace('</head>', f'<link rel="stylesheet" href="{base_path}gallery.css"><script defer src="{base_path}gallery.js"></script></head>')
            markup = re.sub(r'(<body\b[^>]*>)', lambda match: match[0] + chrome, markup, count=1)
            path.write_text(markup)

    cards = ''.join(f'<a class="gallery-card" href="{base_path}{skin["id"]}/"><h2>{html.escape(skin["name"])}</h2><p>{html.escape(skin["description"])}</p><span>Explore this skin →</span></a>' for skin in skins)
    def document(title, body):
        return f'<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title} · Archie skins</title><link rel="stylesheet" href="{base_path}gallery.css"></head><body class="gallery-index"><main><p class="gallery-eyebrow">One notebook. Different personalities.</p><h1>{title}</h1>{body}<footer>Built from the same representative content. Preview controls belong only to this demo.</footer></main></body></html>'
    (destination / 'index.html').write_text(document('Archie skin gallery', '<p>Choose a style, then switch while reading to compare the same page.</p><div class="gallery-cards">' + cards + '</div>'))
    (destination / '404.html').write_text(document('Page not found', '<p>This preview page does not exist. Return to the <a href="' + base_path + '">gallery</a> or choose a skin:</p><nav class="skin-gallery" aria-label="Choose a skin">' + links() + '</nav>'))
    for asset in ('gallery.css', 'gallery.js'):
        shutil.copyfile(ROOT / 'demo' / asset, destination / asset)
    (destination / '.nojekyll').touch()
    (destination / 'gallery.json').write_text(json.dumps([{'id': s['id'], 'name': s['name']} for s in skins]))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', required=True)
    parser.add_argument('--base-url', default='https://archie.ouankou.com/')
    parser.add_argument('--manifest', default=str(ROOT / 'demo/skins.json'))
    args = parser.parse_args()
    build(args.destination, args.base_url, args.manifest)
