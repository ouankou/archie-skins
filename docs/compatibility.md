# Compatibility and maintenance

- Hugo minimum: 0.157.0 standard (the source blog's version); CI now uses 0.169.0.
- Go module directive: 1.23.0; CI uses Go 1.27.3.
- See the dated [workflow version audit](workflow-versions.md) for all toolchains.
- Archie: `cbc1c3aaa2615fa348b85ef39eb4570cd3ac6414`,
  pseudo-version `v0.0.0-20260330114547-cbc1c3aaa261`.
- Source blog snapshot: `e4d2cbef8572fd0dd48790723431bb65653adb2f`,
  following its vintage PR #60 and code-wrap / upstream update PR #61.

The root module's default rendering is upstream's. It also carries namespaced,
opt-in Inua assets/helpers, which are unused by stock and retro.
Retro owns only its style-specific layouts and namespaced assets. Its templates
call upstream `header.html` (the HTML head), `footer.html`, pagedescription and
paginator. That is the explicit integration boundary: upstream has no generic
head hook, so upstream's supported customCSS/customJS settings load the skin.
The upstream HTML head and scripts are not forked.

Retro's article layout is for content/reading sites. It does not reproduce every
upstream article feature (notably the Disqus partial). Opt into or implement such
features intentionally rather than assuming all upstream templates are inherited.
English UI labels are currently built in; language-specific content and menu URL
resolution work, but a full translated skin UI is a future enhancement.

To upgrade Archie, run `hugo mod get github.com/athul/archie@<commit>` in **both**
root and `skins/retro`, update each checksum file, then run integration and browser
checks. Review changes in upstream header/head/footer/index/single and its CSS
variables; an upgrade can change the layout contracts even if Hugo builds. Keep
the pins aligned unless explicitly testing different compatibility ranges. Do not
vendor or edit the upstream checkout. To test a future Hugo, run the same suite
with that binary; a minimum-version declaration is not a promise about untested
future versions.

After changing the root module, explicitly advance the Inua siblings' pinned root
revision and checksums if they should consume that change. Their fixed dependency
does not float with root main; the actual downloaded-module CI test verifies it.

Site configuration wins over module defaults. In particular, arrays replace:
see README before overriding customCSS/customJS. The site can override any
layout or asset with an identically named project file. Do not import the plain
root alongside a skin, or multiple skins together; first-import precedence is not
a supported style selection mechanism.

Pull requests build disposable examples and run checks; they never deploy.
The Pages workflow deploys the gallery only from main, to its existing custom
domain. No workflow alters the separate blog repository or its deployment.
