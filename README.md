# Archie skins

Composable styles for [athul/archie](https://github.com/athul/archie), not a fork.
Pick **one module import**; keep your content and normal Archie configuration.

| Import | Result |
| --- | --- |
| `github.com/ouankou/archie-skins` | Unmodified upstream Archie (no skin) |
| `github.com/ouankou/archie-skins/skins/retro` | Analog cassette / vintage reading layout |
| `github.com/ouankou/archie-skins/skins/washi` | 和紙 — warm paper and ink (light) |
| `github.com/ouankou/archie-skins/skins/aojashin` | 青写真 — blueprint blue (light) |
| `github.com/ouankou/archie-skins/skins/yoru` | 夜 — quiet night (dark) |
| `github.com/ouankou/archie-skins/skins/suimen` | 水面 — night water (dark) |
| `github.com/ouankou/archie-skins/skins/rinko` | 燐光 — phosphor green (dark) |
| `github.com/ouankou/archie-skins/skins/bunko` | 分光 — indigo and cyan (dark) |
| `github.com/ouankou/archie-skins/skins/denko` | 電光 — violet and electric cyan (dark) |

All styles resolve the same tested upstream commit. No upstream files are vendored or
patched. Only the retro module mounts retro templates, CSS, and JavaScript; the
root module does not mount `skins/`. Its Inua assets/helpers are opt-in and do not
change stock output. New styles are independent sibling modules.
The seven [Inua adaptations](docs/inua-skins.md) preserve its exact palettes and
shared restrained design; they are not seven unrelated template forks.

## New site

Requires **Hugo 0.157.0+** (standard edition works) and **Go 1.23+**.
This repository is currently private: configure Git authentication for your own
account/CI and `GOPRIVATE=github.com/ouankou/archie-skins`. Do not put tokens in
configuration or commit them. Private-module access is separate from public
upstream Archie access.

```sh
hugo new site notebook
cd notebook
hugo mod init example.org/notebook
```

Replace the generated `hugo.toml` with this (do not also set `theme = "archie"`):

```toml
baseURL = "https://example.org/notebook/"
title = "Field Notes"
[params]
  subtitle = "Ideas worth keeping."
  mainSections = ["posts"]
  useCDN = false
[module]
  [[module.imports]]
    path = "github.com/ouankou/archie-skins/skins/retro"
```

Then pin a reviewed commit or release and start writing:

```sh
hugo mod get github.com/ouankou/archie-skins/skins/retro@main
hugo new content posts/hello.md
hugo server -D
```

Commit your site's `go.mod` and `go.sum`. Builds use their pinned revisions;
`hugo mod get …@<revision>` is an explicit upgrade. To switch back to stock Archie,
replace the import with `github.com/ouankou/archie-skins`, run `hugo mod get` for
that module at your chosen revision, and `hugo mod tidy`. Remove any retro-specific
customCSS/customJS entries you added. Importing two visual styles together is not
supported: Hugo resolves collisions by import order, not a runtime selector.

## Retro settings

`params.mode` accepts `toggle` (default, analog-dark initially), `light`, `dark`,
or `auto` (tracks system preference). Toggle remembers Archie's `theme-storage`
key and still works when browser storage is unavailable. No JavaScript is needed
to read the page; auto mode uses dark as its no-JavaScript fallback.

Title, subtitle, copyright, menus, social links and content remain site-owned.
Optional copy overrides preserve an existing site's labels without duplicating
any module templates (omit them for generic defaults):

```toml
[params.retro]
  archiveLabel = "POSTS"      # Default: ENTRIES
  listTitle = "All articles" # Default: the current section title
  taxonomyTitle = "All tags" # Default: the current taxonomy title
```

These are plain-text labels; they do not change section selection or URLs.
The demo contains no personal blog data. Menu `pageRef` entries work under a
subdirectory baseURL. Standard Archie RSS, fonts, icons, footer, math options and
SEO head come from upstream. Retro overrides the home, article, list, taxonomy,
navigation, and table-rendering layouts; see the compatibility boundary below.

Hugo **replaces arrays**, rather than appending your entries to module defaults.
If adding custom assets, keep the required defaults first:

```toml
[params]
  customCSS = ["archie-skins/retro/skin.css", "archie-skins/retro/reading.css", "css/site.css"]
  customJS = ["archie-skins/retro/reading.js", "js/site.js"]
[markup.highlight]
  lineNumbersInTable = false # Required for inline-number soft wrapping.
```

An invalid mode or missing required skin asset fails the build with an
actionable error. Hugo itself rejects missing module paths/assets. Do not override
`lineNumbersInTable` to true: that upstream table-based representation is not the
retro code-wrapping contract. Omit `customCSS`/`customJS` entirely for defaults.

## Run the self-contained example

```sh
cd exampleSite
hugo server
```

Its `go.mod` uses a local replacement for the retro module; the real upstream
dependency is downloaded and checksum-verified. This is a development example,
not a go.mod to copy verbatim into an unrelated repository.

## Extend, test, and upgrade

See [adding a style](docs/adding-a-style.md) for a minimal independent style and
[compatibility](docs/compatibility.md) for dependencies and deliberate boundaries.

```sh
python3 -m unittest discover -s tests -v
node --test tests/theme.test.cjs
# Optional real-browser regression checks (after installing Playwright):
node tests/browser.cjs
```

CI builds the real upstream dependency with the [audited current toolchain](docs/workflow-versions.md)
and runs integration, downloaded-module, and browser checks. PRs never deploy;
the separate Pages job deploys tested main builds only.

## Licensing

Original repository code and the user-owned retro skin are **BSD-2-Clause**,
under the existing [LICENSE](LICENSE). The owner authorized distributing their
retro code from `ouankou/blog` under the same license here; the blog's content
license is not changed by this module.

Identifiable code derived from upstream Archie and Feather icons retains its
MIT notices: [Archie](skins/retro/LICENSE-Archie),
[Feather](skins/retro/LICENSE-Feather). Those third-party components are not
relicensed. See the [provenance notice](skins/retro/NOTICE.md).

The seven adapted Inua token files remain **Apache-2.0**, with full license and
change notices in both source modules and emitted CSS. Our shared adapter is
BSD-2-Clause. See [Inua provenance and boundaries](docs/inua-skins.md#provenance-and-licensing).

## Preview gallery

The [demo gallery](https://archie.ouankou.com/) compares every registered skin
using the same content, with page-preserving skin switching. It deploys from
`main` through GitHub Actions; PR builds never deploy. New draft-PR styles appear
live only after review and merge. See [gallery setup and extension](docs/demo-gallery.md).
