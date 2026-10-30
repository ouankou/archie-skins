# Archie skins

Simple styles layered over [Archie](https://github.com/athul/archie), without changing upstream files.
[Browse the gallery](https://archie.ouankou.com/).

## Use a skin

With Hugo installed, run these commands from your site's directory:

```sh
git clone https://github.com/athul/archie.git themes/archie
git clone https://github.com/ouankou/archie-skins.git themes/archie-skins
```

In `hugo.toml`, select a skin before its shared styles and upstream Archie:

```toml
baseURL = "https://example.org/"
title = "Field Notes"
theme = ["archie-skins/skins/washi", "archie-skins/common", "archie"]
```

Run `hugo server` to preview. Keep your content, menus, and normal Archie settings.

## Choose a style

- **Stock Archie** — the unchanged upstream theme.
- **Analog Retro** — cassette colors and a spacious reading layout.
- **Washi** — warm paper and ink; light.
- **Aojashin** — cool paper and blueprint blue; light.
- **Yoru** — quiet night; dark.
- **Suimen** — night water and cyan; dark.
- **Rinko** — phosphor green; dark.
- **Bunko** — indigo and cyan; dark.
- **Denko** — violet and electric cyan; dark.

For another Inua style, replace `washi` with its lowercase name; keep `archie-skins/common` and `archie` after it. These seven styles use their native light or dark palette; omit `params.mode` to use the default.

For Retro, use `theme = ["archie-skins/skins/retro", "archie"]`; its light/dark toggle is enabled by default. For stock, use `theme = ["archie"]`. Remove any previous skin-specific settings when switching.

## Run the gallery locally

From this repository's directory:

```sh
git clone https://github.com/athul/archie.git vendor/archie
python3 demo/build.py --destination _site --base-url http://localhost:8000/
python3 -m http.server 8000 --directory _site
```

Open http://localhost:8000/ to compare all nine styles with the same content.

## Licenses

Our code and Retro are [BSD-2-Clause](LICENSE). The seven Inua palettes are adapted from [Inua](https://github.com/lyricat/inua) under Apache-2.0; each skin carries its license and provenance notice. Archie and the retained Feather icon code are MIT-licensed; their notices remain intact. No Inua artwork or font files are bundled.
