# Seven Inua palettes, one Archie presentation

These independently maintained adaptations draw from [Inua](https://inua.one/),
a Linux desktop project, not from an invented collection of neon effects. Its
seven [theme files](https://github.com/lyricat/inua/tree/d677a83cac983e2ba549c4ea52a67362a3b7eb98/ui/themes)
are deliberately **color tokens only** over a shared design language.

| Module suffix | Name | Native scheme | Character |
| --- | --- | --- | --- |
| `washi` | 和紙 Washi | light | Warm paper, ink text |
| `aojashin` | 青写真 Aojashin | light | Cool paper, blueprint blue |
| `yoru` | 夜 Yoru | dark | Night neutrals, quiet blue-grey |
| `suimen` | 水面 Suimen | dark | Night water, cyan |
| `rinko` | 燐光 Rinko | dark | Phosphor green |
| `bunko` | 分光 Bunko | dark | Indigo, cyan |
| `denko` | 電光 Denko | dark | Violet, electric cyan |

All 16 color values per skin are preserved exactly. The original browser adapter
uses generous whitespace, hairline sections, restrained square current-page
indicators, small mono metadata, and sans-serif running text. No gradients,
glow, wallpaper, logos, or imitation application controls are added. Headings,
article content, taxonomies, search and footer continue to use upstream Archie
templates. Only the navigation partial is replaced, to validate configuration
and provide native-scheme navigation with correct site-prefix home links.

## Use a skin

```toml
[module]
  [[module.imports]]
    path = "github.com/ouankou/archie-skins/skins/washi"
```

```sh
# The repository is private for now: authenticate Git and set GOPRIVATE first.
# Use the reviewed PR revision until merged; use @main or a release afterward.
hugo mod get github.com/ouankou/archie-skins/skins/washi@<reviewed-revision>
```

Commit your consumer's resolved `go.mod` and `go.sum`. Import **one** skin only.
Switch the module path and tidy dependencies to select another; remove retro
customCSS/customJS and mode settings when migrating from retro.

Each module carries its native mode as a default. Omit `params.mode`, or use
`light` for Washi/Aojashin and `dark` for the other five. Opposite schemes,
`auto`, and `toggle` intentionally fail with an actionable error: those are not
additional upstream palettes, and changing a single palette behind the user's
back would misrepresent the source. There is no theme JavaScript or stored state
in these seven skins. Gallery switching remains a demo-only feature.

To append custom CSS, preserve both required files in this order:

```toml
[params]
  customCSS = ["archie-skins/inua/base.css", "archie-skins/washi/tokens.css", "css/local.css"]
```

The browser font stacks prefer Zen Kaku Gothic New / IBM Plex Sans / Geist Mono
when already installed, with system sans/CJK and monospace fallbacks. No third-
party font binary or external font request is added. Therefore typography is
consistent in role, not promised pixel-identical across operating systems.
Archie's italic-only IBM Plex Mono face is deliberately not selected for normal
metadata. Code uses native ink rather than inherited, low-contrast syntax colors.
The tested reading colors meet normal-text contrast on their native surfaces;
the source's decorative hairlines are not interactive boundaries. Focus outlines
use the source accent. The source token values themselves are not silently
altered to satisfy a contrast target.

## Package and extension design

The root module hosts only **opt-in** `assets/archie-skins/inua/base.css` and
`layouts/partials/archie-skins/inua/navigation.html`; it still renders stock
Archie unchanged. Each sibling imports a pinned root module, supplies its
namespaced token asset and defaults, and delegates navigation through a tiny
partial. No sibling-relative filesystem mounts or seven template copies.

The dependency is pinned to the earlier shared-implementation logical commit,
not an unpublished placeholder or the branch tip. This makes each downloaded
module independently reproducible. Local tests replace both selected sibling
and root; packaging tests place their module contents in separate extracted
directories, excluding nested modules from the root, before building a consumer.

To add another palette in this family, create a new sibling with this same
contract, supply all 16 `--inua-*` properties, set its native mode, and register
its preview in `demo/skins.json`. Broader styles need not inherit this layer; the
[standalone style contract](adding-a-style.md) still applies.

## Provenance and licensing

Source: Inua revision `d677a83cac983e2ba549c4ea52a67362a3b7eb98`,
`ui/themes/*.css`, Apache-2.0. The GTK declarations have been converted into
namespaced browser custom properties and a native `color-scheme` added. Source
comments and all values are retained. Every adapted token file includes a
prominent change notice and the **complete Apache license**, which also remains
in the generated stylesheet served to website visitors. Each module includes
`LICENSE-Apache-2.0` and its own provenance notice; upstream has no NOTICE file
at this revision. This adaptation's notice is not represented as upstream's.

Our new Hugo glue and common CSS are BSD-2-Clause. Upstream Archie remains MIT;
its artwork and font dependencies retain their upstream notices. No Inua logo,
font file, screenshot, or application source is redistributed, and no affiliation
or endorsement is claimed. Apache material is **not** relicensed to BSD.
