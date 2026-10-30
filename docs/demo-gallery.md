# Demo gallery and workflow-based Pages

The demo target is **https://archie.ouankou.com/**. Source repository visibility
stays private. Generated HTML, CSS, JavaScript and font assets are public as part
of the demo. The artifact excludes repository history, content outside the generic
example, Go module files, templates, and credentials.

## Architecture

`demo/skins.json` is the extensible catalog. Each entry selects exactly one local
Hugo module and gets its own build/output prefix (`/stock/`, `/retro/`). Every build
uses the same representative `exampleSite/content` and configuration. No skin is
layered over another. To add a skin, add its module and a catalog entry with a
unique lowercase ID, label, local module path, module import and description.

After Hugo builds, `demo/build.py` adds a **demo-only** navigation bar to generated
HTML. It is not mounted into either module; ordinary consumers never get it.
Navigation preserves equivalent article/taxonomy paths, and JavaScript also
preserves query strings and heading anchors. Native links work without JavaScript.
If a future skin omits a page, its switch link falls back to that skin's homepage.
Root `404.html` links back to the gallery and each skin. Unknown deep links receive
that page from GitHub Pages. Skin assets are isolated under their own prefixes;
only the demo navigation stylesheet/script are shared.

## Local preview

```sh
python3 demo/build.py --destination /tmp/archie-gallery --base-url http://localhost:8000/
python3 -m http.server 8000 --directory /tmp/archie-gallery
```

Choose a new/empty output directory for each build; the builder refuses to delete
existing files. Use `--base-url http://localhost:8000/preview/` and serve its parent
with the generated output at `preview/` to test an extra hosting prefix.

```sh
python3 -m unittest discover -s tests -p test_gallery.py -v
node tests/gallery-browser.cjs # requires Playwright + Chromium
```

## GitHub Pages setup and safety

The user has configured DNS and selected GitHub Actions as the Pages source.
The repository's **Settings → Pages → Custom domain** must also be
`archie.ouankou.com`, with HTTPS enabled once GitHub provisions its certificate.
For workflow-based publishing, GitHub ignores `CNAME` files: the repository setting
is authoritative. We deliberately do not commit a misleading CNAME or modify
repository visibility, domain verification, access controls, or DNS automatically.
See [GitHub's custom-domain documentation](https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/managing-a-custom-domain-for-your-github-pages-site).

`pages.yml` builds and browser-tests pull requests **without deploying them**.
Only successful `main` builds (push/manual dispatch) can upload/deploy the Pages
artifact. The build job has read-only contents/Pages permissions; only the deploy
job has `pages: write` and `id-token: write`, behind the `github-pages` environment.
Concurrency serializes deployments; the artifact contains only generated `_site`.
The workflow checks Pages' reported base URL before deploying, failing clearly if
the custom-domain/HTTPS setting does not match. No token for another repository
is needed: local replacements build the current checked-out modules, fetching
only public upstream Archie.

The first deployment requires this PR to be merged into `main`; no merge is
performed automatically. The project uses logical commits and rebase merging only.
The existing blog's deployment is separate and is not touched by this workflow.
