"""CI: consume actual GitHub-downloaded module zips, never local replacements.

Uses the existing checkout's repository-scoped read authentication supplied by
the workflow. No token argument, new secret, proxy shortcut, or visibility change.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
MODULE = 'github.com/ouankou/archie-skins'


def run(*args, cwd):
    return subprocess.check_output(args, cwd=cwd, text=True, timeout=180)


def main():
    revision = os.environ['SKINS_REVISION']
    skins = [s for s in json.loads((ROOT/'demo/skins.json').read_text())
             if s['id'] not in ('stock', 'retro')]
    with tempfile.TemporaryDirectory(prefix='published-skins-') as temporary:
        base = Path(temporary)
        for skin in skins:
            site = base/skin['id']
            site.mkdir()
            run('go', 'mod', 'init', 'example.org/published-check', cwd=site)
            downloaded = json.loads(run('go', 'mod', 'download', '-json', skin['module']+'@'+revision, cwd=site))
            if downloaded.get('Error'):
                raise RuntimeError(downloaded['Error'])
            run('go', 'mod', 'edit', '-require='+skin['module']+'@'+downloaded['Version'], cwd=site)
            module_source = Path(downloaded['Dir'])
            pin = next(line.split()[2] for line in (module_source/'go.mod').read_text().splitlines()
                       if line.startswith('require '+MODULE+' '))
            shared = json.loads(run('go', 'mod', 'download', '-json', MODULE+'@'+pin, cwd=site))
            if shared.get('Error'):
                raise RuntimeError(shared['Error'])
            shared_source = Path(shared['Dir'])
            expected = next(line.split()[2] for line in (module_source/'go.sum').read_text().splitlines()
                            if line.startswith(MODULE+' '+pin+' '))
            assert shared['Sum'] == expected, 'recorded root module checksum does not match downloaded ZIP'
            assert (shared_source/'assets/archie-skins/inua/base.css').is_file()
            assert not (shared_source/'skins/retro/go.mod').exists(), 'nested module leaked into root zip'
            assert 'replace ' not in (module_source/'go.mod').read_text()
            shutil.copytree(ROOT/'exampleSite/content', site/'content')
            (site/'hugo.toml').write_text('baseURL="https://example.org/published/"\ntitle="Downloaded module"\n'
                '[params]\nmainSections=["posts"]\n[module]\n[[module.imports]]\npath="'+skin['module']+'"\n'
                # Hugo filters child-process env; allow the temporary config path,
                # not GH_TOKEN or all environment variables. Ordinary user auth
                # in ~/.gitconfig does not require this test-only setting.
                '[security.exec]\nosEnv = ["(?i)^(PATH|HOME|TMP|TEMP|GO.*|GIT_CONFIG_GLOBAL)$"]\n')
            run(os.environ.get('HUGO_BIN', 'hugo'), '--source', str(site), cwd=site)
            markup = (site/'public/posts/hello/index.html').read_text()
            assert '/archie-skins/'+skin['id']+'/tokens.' in markup
            assert '/archie-skins/inua/base.' in markup
            assert 'replace ' not in (site/'go.mod').read_text()
            print('PASS actual GitHub module ZIP:', skin['id'], downloaded['Version'], 'root', pin, flush=True)


if __name__ == '__main__':
    main()
