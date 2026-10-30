# Add a style without changing retro

A skin is a separately importable Hugo module. Its path is the selection API;
there is deliberately no global switch statement, stylesheet registry, or copied
upstream HTML head to maintain. Hugo resolves the site's own files first, then
its imports in order. Import exactly one style.

Create this sibling layout (for example `skins/blueprint`):

```
skins/blueprint/
  go.mod
  go.sum
  hugo.toml
  assets/archie-skins/blueprint/skin.css
  LICENSE
```

`go.mod` (replace the module name, retain the tested upstream pin):

```go
module github.com/ouankou/archie-skins/skins/blueprint

go 1.23.0

require github.com/athul/archie v0.0.0-20260330114547-cbc1c3aaa261
```

`hugo.toml`:

```toml
[module]
  [module.hugoVersion]
    min = "0.157.0"
  [[module.imports]]
    path = "github.com/athul/archie"
[params]
  customCSS = ["archie-skins/blueprint/skin.css"]
```

`assets/archie-skins/blueprint/skin.css`:

```css
:root { --color-primary: #245cc4; }
```

Run `hugo mod get` in that directory to populate checksums. Import the module in
a consumer and, during development, add a local `replace` in the consumer's go.mod.
This new skin uses *all* upstream templates unchanged; add only the layout overrides
it genuinely needs. Never import retro just to inherit upstream, and never copy
its files without retaining the applicable BSD-2-Clause and third-party MIT notices.
A standalone skin in another repository works identically.

Add an integration fixture and confirm: default upstream does not change; the new
skin's asset appears only for its import; retro still builds; consumer overrides
win; bad imports and required config produce useful errors. The integration suite
creates a tiny external style fixture to exercise this contract.

Nested modules need **prefixed release tags**, e.g. `skins/retro/v0.1.0`; root
releases use `v0.1.0`. Until releases exist, use commit hashes or a branch, then
commit the resolved pseudo-version. A tag on the root alone is not a retro release.
