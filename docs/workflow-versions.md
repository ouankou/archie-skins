# Workflow dependency audit — 2026-10-30

Verified the latest non-prerelease official releases, not guessed from old action
examples. Actions follow the latest stable **major**; toolchains are exact stable
versions for reproducible builds. The Hugo minimum supported by modules remains
0.157.0; CI exercises the latest stable release below.

| Component | Workflow selection | Verified stable release |
| --- | --- | --- |
| Checkout | `actions/checkout@v7` | [v7.0.1](https://github.com/actions/checkout/releases/tag/v7.0.1) |
| Go setup | `actions/setup-go@v7` | [v7.0.0](https://github.com/actions/setup-go/releases/tag/v7.0.0) |
| Node setup | `actions/setup-node@v7` | [v7.1.0](https://github.com/actions/setup-node/releases/tag/v7.1.0) |
| Python setup | `actions/setup-python@v7` | [v7.1.0](https://github.com/actions/setup-python/releases/tag/v7.1.0) |
| Artifacts | `actions/upload-artifact@v7` | [v7.0.2](https://github.com/actions/upload-artifact/releases/tag/v7.0.2) |
| Pages config | `actions/configure-pages@v6` | [v6.0.0](https://github.com/actions/configure-pages/releases/tag/v6.0.0) |
| Pages artifact | `actions/upload-pages-artifact@v5` | [v5.0.0](https://github.com/actions/upload-pages-artifact/releases/tag/v5.0.0) |
| Pages deployment | `actions/deploy-pages@v5` | [v5.0.1](https://github.com/actions/deploy-pages/releases/tag/v5.0.1) |
| Hugo | `0.169.0` | [v0.169.0](https://github.com/gohugoio/hugo/releases/tag/v0.169.0) |
| Go | `1.27.3` | [official stable downloads](https://go.dev/dl/) |
| Node | `26.13.0` | [v26.13.0 LTS](https://github.com/nodejs/node/releases/tag/v26.13.0) |
| Playwright | `1.64.1` | [v1.64.1](https://github.com/microsoft/playwright/releases/tag/v1.64.1) |
| Python | `3.15.2` | [official stable downloads](https://www.python.org/downloads/) |

The Hugo Linux AMD64 archive SHA-256 is
`2d2f0bfe357d8cb4cec02f6bb28a3bff34978c8dda44b618029c5eb9d66765a7`.
Node 27 prereleases are intentionally excluded. No download-artifact action is
used, so there is no dormant dependency to update.

## Migration considerations

- Current GitHub-hosted Ubuntu runners provide the supported action runtime;
  old self-hosted runners are not implied to work.
- New setup-node automatic package-manager caching is explicitly disabled: this
  test harness installs pinned Playwright without a package-manager lockfile.
- Checkout's new credential-file storage is not assumed to live in `.git/config`.
  Actual private-module ZIP tests use the existing job's repository-scoped,
  contents-read-only `github.token` in a temporary Git config header scoped to
  this repository. The token/header are never printed; the file is removed by
  a trap. No PAT, new secret, or access/visibility change is required.
- Fork PRs skip only authenticated module-download validation; local isolation,
  licensing, content, navigation and browser checks still run.
- Pages security gates are unchanged: pull requests build/test but never upload
  a Pages artifact or deploy. Only the main deployment job receives Pages-write
  and OIDC permissions. Domain verification still uses the existing Pages setting.

Refresh this audit on dependency upgrades and run the full suite before changing
the selected versions; a newer major is not evidence of compatibility by itself.
