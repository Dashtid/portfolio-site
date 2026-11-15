# Security Policy

## Reporting a Vulnerability

Please report privately. Do not open a public GitHub issue.

**Preferred — GitHub private vulnerability reporting:**
[open a draft advisory](https://github.com/Dashtid/portfolio-site/security/advisories/new).
It is enabled on this repository, it is private until published, and it gives
you a thread you can see rather than a mail you cannot tell arrived.

**Alternative:** a direct message on
[LinkedIn](https://www.linkedin.com/in/david-dashti/), or
<dashti.dat@gmail.com> if you would rather use email.

> [!] Do not use `security@dashti.se`. The site's `security.txt` listed it
> until 2026-09-20 and the API's copy at `api.dashti.se` until 2026-11-06,
> and it bounced the whole time — the domain has no MX record. Both
> `security.txt` copies now list the GitHub and LinkedIn channels above.

Include in your report:

- A description of the issue and the potential impact
- Steps to reproduce, or a proof-of-concept where possible
- Any relevant version, branch, or commit information

You can expect an initial acknowledgement within a few business days.
If the report is valid, a fix will be prepared on a private branch and
disclosed publicly together with the patch release.

## Scope

This repository powers a personal portfolio site, not a product. Reports
are welcome for:

- The frontend (`frontend/`) — Vue 3 application deployed to Vercel
- The backend (`backend/`) — FastAPI service deployed to Fly.io
- The CI/CD configuration (`.github/workflows/`)

The live site is **[dashti.se](https://dashti.se)** and the backend API is at
`api.dashti.se`.

## Out of Scope

- Vulnerabilities in third-party services this site uses (Vercel, Fly.io,
  GitHub OAuth, ipapi.co) — please report those upstream.
- Social engineering attempts.
- Denial-of-service issues that require an unrealistic traffic profile
  for a single-author portfolio site.

## Supported Versions

Only the current `main` branch is supported. Older versions are not patched.

## Accepted Dependency-Audit Residuals

Reviewed **2026-11-15**, superseding the 2026-10-20, 2026-09-29 and 2026-09-20
reviews and the 2026-08-07 list before them (see the notes at the end).

On 2026-11-15, `npm audit` reports **32 entries (13 high, 17 moderate, 2 low),
which are 11 advisories**: extract-zip twice, basic-ftp three times,
minimatch, deepmerge, body-parser, zod, glob and ip-address. npm counts one
advisory once per dependency node, so the entry count is not a finding count.
`npm audit --omit=dev` reports **0** — none of this reaches the deployed
frontend or the backend.

The first seven have an entry below, and none has a fix its tree can take:
extract-zip and basic-ftp sit in the dormant `@lhci/cli` 0.15.1 tree,
minimatch in the lint, test and build tooling, and deepmerge in the
service-worker build. The other four have no entry: GitHub auto-dismissed their
development-scope Dependabot alerts (body-parser #241, zod #238, glob #246,
ip-address #234).

### extract-zip — arbitrary file write / symlink path traversal (accepted)

Re-checked **2026-11-15**.

- [GHSA-jmr9-qjv8-65gv](https://github.com/advisories/GHSA-jmr9-qjv8-65gv) and
  [GHSA-7pqw-9j4j-h8q3](https://github.com/advisories/GHSA-7pqw-9j4j-h8q3),
  both high, both with **no patched version of `extract-zip` at any release**
  (2.0.1 is still the newest; nothing has been published since). Dependabot
  alerts #187 and #200 are dismissed with this entry as the reason.
- One dev-only chain: `@lhci/cli` → `lighthouse` → `puppeteer-core` →
  `@puppeteer/browsers@2.13.0` → `extract-zip@2.0.1`. **It is installed, never
  executed.** `@puppeteer/browsers` loads `extract-zip` only through a dynamic
  `import()` inside `unpackArchive()`, and only its browser-download
  `install()` calls that. `puppeteer-core` never imports `install`, Lighthouse
  CI finds an installed Chrome through `chrome-launcher` and downloads nothing,
  and nothing here runs the package's `browsers` CLI. Checked by replacing
  `extract-zip`'s entry point with a tripwire in a scratch install: on
  2026-09-27 a direct `unpackArchive()` call set it off and a full
  `lhci autorun` did not; on 2026-11-15, on this lockfile, a direct `require`
  of the entry point set it off and a full `lhci autorun` again did not.
- [!] Until 2026-09-27 this entry said the code "runs when Lighthouse CI
  downloads a Chrome build". It never did — no step in this repository
  downloads Chrome.
- **CI does not run this copy either.** The `lighthouse` job uses
  `treosh/lighthouse-ci-action`, whose committed `node_modules` carries its own
  `@lhci/cli` 0.15.1 and the same `extract-zip@2.0.1`; the job log resolves
  `lhci` from `_actions/treosh/…`. The devDependency serves only the local
  `npm run lighthouse` scripts. Dropping it would close the alert and leave the
  same unused code on the runner, inside the action.
- **A fix exists in the parent and it was tried and reverted.**
  `@puppeteer/browsers` 3.x drops `extract-zip` entirely, so an override to
  `^3.2.2` would have removed the package rather than patched it. It broke the
  Vercel deploy and nothing else: 3.x declares `proxy-agent >=8.0.1` as a
  **peer**, `@lhci/cli` in the same tree requires `proxy-agent ^6.4.0`, and that
  peer is unsatisfiable. npm locally and in Actions both install a lockfile with
  the peer unmet; Vercel rebuilds the ideal tree and fails `npm ci` with
  "Missing: proxy-agent@8.0.2 from lock file". Reverted in `9da88ff`.
  `npm audit fix` is worse still — it proposes walking `@lhci/cli` *backwards*
  from 0.15.1 to 0.13.0 (Lighthouse 11).
- **Re-check trigger:** an `@lhci/cli` release above 0.15.1, or a
  `lighthouse-ci-action` release, whose tree reaches `@puppeteer/browsers` 3.x
  without `proxy-agent` 6.x. Every 3.x release (3.0.2 to 3.2.7) declares the
  `proxy-agent >=8.0.1` peer. `@lhci/cli` 0.16.0 (2026-11-02) reaches 3.x but
  keeps `proxy-agent ^6.5.0`; 0.16.1 (2026-11-11) asks `proxy-agent ^8.0.2` and
  meets this trigger; it is not taken yet because it is inside the seven-day
  cooldown `.github/dependabot.yml` sets (until 2026-11-18).
  `lighthouse-ci-action` has not released since 12.6.2, the pinned version. Do
  not retry the override before checking
  `npm view @puppeteer/browsers@<v> peerDependencies`.

### basic-ftp — denial of service in the FTP client (accepted)

Checked **2026-11-15**.

- [GHSA-c475-qrg2-pj4r](https://github.com/advisories/GHSA-c475-qrg2-pj4r)
  (CVE-2026-102990), high: `Client.list()` parses a Unix directory listing
  with a regex that backtracks quadratically, so a hostile FTP server can burn
  CPU. Fixed in 6.2.1. GitHub auto-dismissed its Dependabot alert, #218, as
  development-scope.
- [GHSA-5pm8-86m8-9m6r](https://github.com/advisories/GHSA-5pm8-86m8-9m6r)
  (CVE-2026-126345), moderate: an MLSD listing line with the fact name
  `__proto__` makes `Client.list()` reject with a `TypeError` that its retry
  logic does not catch, so a hostile FTP server can crash a process that
  leaves the rejection unhandled. Fixed in 6.2.4. Dependabot alert #248 is
  dismissed with this entry as the reason.
- [GHSA-r4jh-29pc-gfqr](https://github.com/advisories/GHSA-r4jh-29pc-gfqr)
  (CVE-2026-126346), moderate: a password, or the remote path of a resumed
  download, that contains CR, LF or NUL makes basic-ftp throw inside a socket
  event handler, an uncaught exception that ends the process. Fixed in 6.2.3.
  GitHub auto-dismissed its Dependabot alert, #249, as development-scope.
- All three fixes are in 6.x only: 5.3.1 is the last 5.x release, `get-uri`
  6.0.5 here asks for basic-ftp `^5.0.2`, and `get-uri` 8.0.1, the newest,
  still asks for `^5.3.1`. None can be taken in place.
- Dev-only, inside the `@lhci/cli` 0.15.1 tree: `proxy-agent@6.5.0` →
  `pac-proxy-agent@7.2.0` → `get-uri@6.0.5` → `basic-ftp@5.3.1`, where
  `proxy-agent` is required both by `@lhci/cli` and by its
  `@puppeteer/browsers@2.13.0`. **It is installed, never loaded.**
  `proxy-agent` loads `pac-proxy-agent`, and with it `get-uri` and basic-ftp,
  only for a `pac+` proxy URL, and nothing here configures a proxy. Checked
  with a tripwire on basic-ftp's entry point and on `Client.list()` in a
  scratch install of this lockfile: a direct `list()` call set it off; a full
  `lhci autorun`, with uploads written to disk, did not load the package.
  CI's `lighthouse` job uses the `@lhci/cli` inside
  `lighthouse-ci-action` instead, whose `node_modules` holds basic-ftp 5.2.0,
  older still; `ci-cd.yml` configures no proxy either.
- [!] Until 2026-11-15 the re-check trigger here was "the same `@lhci/cli`
  release that moves it off `proxy-agent` 6.x". That release is 0.16.1, and it
  does not remove basic-ftp: its `proxy-agent` 8.0.2 → `pac-proxy-agent` 9.1.0
  → `get-uri` 8.0.1 still resolves basic-ftp 5.3.1.
- **Re-check trigger:** a 5.x release of basic-ftp with all three fixes, or a
  `get-uri` release on basic-ftp 6.2.4 or later that this tree's
  `proxy-agent` reaches.

### minimatch — denial of service through pattern amplification (accepted)

Checked **2026-11-15**.

- [GHSA-g3hv-75wg-m249](https://github.com/advisories/GHSA-g3hv-75wg-m249)
  (CVE-2026-118764), moderate: from 7.0.0, at `optimizationLevel: 2`, each
  `**/../<p>/<p>` run in a pattern doubles the rows `firstPhasePreProcess()`
  builds, and `secondPhasePreProcess()` then compares the rows pairwise, so
  whoever writes the PATTERN can make compiling it burn CPU and memory. Fixed
  in 11.0.1, which stops splitting at `braceExpandMax` rows (default 100,000)
  and skips the pairwise pass above 1,000 rows. **No 10.x release carries the
  fix** and none is planned (upstream treats every release before 11 as
  unsupported, isaacs/minimatch#333). Dependabot alert #247 is dismissed with
  this entry as the reason.
- Three copies are installed, and only `minimatch@10.2.6` (dev-only) is in
  range; 3.1.5 and 5.1.9 are below 7.0.0. Four of its consumers compile at the
  default `optimizationLevel` 1 and never reach the flaw: eslint 10.14.0 and
  `@eslint/config-array` 0.23.5 at lint time,
  `@typescript-eslint/typescript-estree` 8.72.1, and `editorconfig` 3.0.2,
  which only the `js-beautify` command-line tool loads and nothing runs.
- The one level-2 caller is `vite-plugin-pwa` → `workbox-build@7.4.1` →
  `glob@11.1.0` during `build:ssg`. Its patterns are the `workbox.globPatterns`
  and `globIgnores` literals in `frontend/vite.config.ts`, plus `sw.js` and
  `workbox-*.js`, which `workbox-build`'s `generateSW()` adds to `globIgnores`
  itself; none contains `..`. No visitor, CMS row or API response reaches a
  pattern: the API data the build fetches for prerendering only determines
  which files exist, and file names are matched, never compiled. Checked by
  logging every `Minimatch` construction through `npm run lint`, the unit
  tests with coverage and `build:ssg`: 27, 0 and 42, all on patterns written
  here or in the tools.
- `glob@13.0.6` (`@sentry/bundler-plugins`, `js-beautify`) never loads the
  installed copy: its entry point is a bundle with its own minimatch, which no
  scanner sees and no override reaches. `vite.config.ts` imports
  `@sentry/vite-plugin`, so every `build:ssg` loads that bundle, but it
  compiles patterns only when the plugin is enabled (`SENTRY_AUTH_TOKEN` set):
  the plugin's own and `dist/**/*.map`, none with `..`.
- **An override was tried and does not work.** The override
  `"minimatch@>=7.0.0 <11.0.1": "11.0.1"` moves only the 10.2.6 copy, passes
  `npm ci` and the npm 11.6.1 `ci --dry-run` gate, and leaves the lint output,
  ESLint's per-file config, the unit results and coverage unchanged. But
  minimatch 11 compiles each wildcard path segment into a `Matcher` object
  instead of a `RegExp`, and `glob@11.1.0` walks only `RegExp` segments, so
  `workbox-build`'s patterns matched no file: the service-worker precache fell
  from 25 entries to 1 and `verify-dist-invariants` failed the build. And
  minimatch 11.0.0 to 11.0.6 are inside its own
  [GHSA-cf2h-pxjq-68xw](https://github.com/isaacs/minimatch/security/advisories/GHSA-cf2h-pxjq-68xw)
  (quadratic compile time, fixed in 11.0.7).
- **Re-check trigger:** a `workbox-build` (or `vite-plugin-pwa`) release whose
  `glob` walks minimatch 11's `Matcher` segments; `workbox-build` 7.4.1 and
  `vite-plugin-pwa` 2.0.0 are still the newest. Retry the override then, not
  before: it already leaves lint, the unit tests and coverage unchanged, but it
  fails while `workbox-build` resolves a `glob` that walks only `RegExp`
  segments. Without an override a 10.x copy stays in the lock as long as any
  consumer asks for one: eslint 10.15.0 and `@eslint/config-array` 0.23.6
  (2026-11-13) ask for `^11.0.5`, but `@typescript-eslint/typescript-estree`
  8.72.2, `editorconfig` 3.0.2 (`~10.2.4`, under `@vue/test-utils` →
  `js-beautify` 2.0.3, the newest) and `glob` 13.x (under
  `@sentry/bundler-plugins` and `js-beautify`) still ask for 10.x.

### deepmerge — prototype poisoning of a merged object (accepted)

Checked **2026-11-15**.

- [GHSA-gcqx-w48m-w2h4](https://github.com/advisories/GHSA-gcqx-w48m-w2h4)
  (CVE-2026-93753), low: `mergeObject()` skips its `__proto__` guard where the
  target holds `null`, `undefined`, a primitive or a null-prototype object at
  a key (or is itself one), so an own `__proto__` key that the source has
  there (as `JSON.parse` produces) becomes the prototype of an object
  deepmerge returns; an own `__proto__` key in the target is copied
  unguarded. Merging into a plain object, or at a key the target lacks, keeps
  the guard working, and `Object.prototype` is never modified. **No patched
  version exists**: 4.3.1 (2023) is the newest release, and the fix pull
  request (TehShrike/deepmerge#274) was closed unmerged. The CVE was rejected
  by its CNA on 2026-11-02 as not describing a vulnerability; the GitHub
  advisory is still published. Dependabot alert #244 is dismissed with this
  entry as the reason.
- One dev-only chain: `vite-plugin-pwa` → `workbox-build@7.4.1` →
  `@rollup/plugin-node-resolve@16.0.3` → `deepmerge@4.3.1`. The plugin's only
  call is at module load, `deepFreeze(deepMerge({}, defaults))`: an
  empty-object target, which keeps the guard working, and its own constant
  defaults, which carry no `__proto__` key. `workbox-build` loads the plugin
  when it bundles the service worker during `build:ssg`. No visitor, CMS row or
  API response is ever merged. Checked by logging every `deepmerge()` call
  through `npm run lint`, the unit tests and `build:ssg`: one call per build
  (plus five recursions into the defaults' arrays), none at lint or test time.
- No newer `@rollup/plugin-node-resolve`, `workbox-build` or `vite-plugin-pwa`
  release drops it (16.0.3, 7.4.1 and 2.0.0 are the newest).
- **Re-check trigger:** GitHub withdrawing GHSA-gcqx-w48m-w2h4 (the alert is
  then withdrawn with it, as sprintf-js's #223 was, and this entry can go), a
  deepmerge release above 4.3.1, or a `@rollup/plugin-node-resolve` release
  without it.

### Standing `overrides`

`frontend/package.json` has five. Three must stay while `@lhci/cli` is 0.15.1,
because they hold its dormant tree on patched versions: `tmp ^0.2.7` and
`uuid ^11.1.1` (`1be42ba`), and `qs ^6.17.1` (added in `46c351a`, raised in
`da44c11`). `@lhci/cli` asks for `tmp ^0.1.0` and `uuid ^8.3.1`, its
`inquirer` → `external-editor` for `tmp ^0.0.33`, and its `express` and
`body-parser` for `qs ~6.15.1`. Written without one of them, the lock brings
back tmp 0.1.0 and 0.0.33 (GHSA-52f5-9888-hmc6, GHSA-ph9p-34f9-6g65), uuid
8.3.2 (GHSA-w5hq-g745-h8pq) or qs 6.15.4 (GHSA-4mjr-xmp4-gh2g,
GHSA-6pq8-jhm2-2vcw). The other two change nothing today, and the lock
written without either is byte-identical: `fflate ^0.8.3` (`bd4f762`,
GHSA-px8p-9vwx-vf98) sits under `@vitest/ui`, whose 5.1.0 asks for `^0.8.3`
itself, and the `sourcemap-codec` alias (`fd2f78e`) replaced a deprecated
package that nothing in the tree depends on any more. **Re-check trigger:**
the move to `@lhci/cli` 0.16.x, which no longer depends on `tmp` and asks for
`uuid ^14.0.3` and `express ^4.22.3` (`qs ~6.16.0`): write the lock without
each override again then.

### What changed since 2026-08-07, and the lesson

- **2026-11-15:** sprintf-js
  ([GHSA-hp3w-g68c-fv3c](https://github.com/advisories/GHSA-hp3w-g68c-fv3c)),
  accepted here on 2026-10-20, is **gone**: GitHub withdrew the advisory on
  2026-10-22, `npm audit` no longer reports it, and Dependabot alert #223 now
  answers HTTP 410 ("Alert number 223 has been withdrawn"). Its entry was
  removed, and entries for minimatch and deepmerge were added. basic-ftp's
  entry now covers the two advisories published on 2026-11-12, and its old
  re-check trigger would not have cleared it (see the entry). The overrides
  paragraph credited all five overrides to `1be42ba` / `bd4f762` and placed
  them all in the `@lhci/cli` tree; `fflate` and the `sourcemap-codec` alias
  sit outside it and change nothing.
- **2026-10-12:** brace-expansion
  ([GHSA-q2hr-2g5m-vwhr](https://github.com/advisories/GHSA-q2hr-2g5m-vwhr))
  was fixed in-range in all three copies (`cbf49af`), and compression,
  fast-uri, postcss-selector-parser, proxy-addr and source-map-js were moved to
  patched releases (`a24986e`). source-map-js was the only finding that had
  reached `npm audit --omit=dev`.
- **brace-expansion (GHSA-mh99-v99m-4gvg)** — the old list's "15 high entries,
  one advisory" item is **gone**, fixed in-range. It is not accepted any more; it
  no longer exists.
- **extract-zip** was never listed, despite being the repository's only open code
  scanning alert and the one with no patch at all.
- **js-yaml (GHSA-2883-xcg3-v3hh)**, listed on 2026-09-20 as "being fixed", is
  **gone**: `4085646` moved the `@lhci/utils` copy to the patched 3.15.2
  (superseding Dependabot PR #180). It had replaced a different js-yaml advisory
  ([GHSA-5p4m-2wfm-xmqj](https://github.com/advisories/GHSA-5p4m-2wfm-xmqj),
  CVE-2026-59870), which genuinely had no 3.x backport and was accepted here for
  that reason. Same package, different advisory, opposite conclusion — which is
  the argument for dating these entries.

So the previous list simultaneously accepted something already fixed and omitted
something still open. When re-checking, group `npm audit --json` by `via` rather
than trusting the entry count, confirm each advisory ID is still the same one,
and record the *real* blocker (here: an unsatisfiable peer) — otherwise the next
reader cannot tell a considered acceptance from an unexamined one.
