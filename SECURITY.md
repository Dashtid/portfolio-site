# Security Policy

## Reporting a Vulnerability

Please report privately. Do not open a public GitHub issue.

**Preferred — GitHub private vulnerability reporting:**
[open a draft advisory](https://github.com/Dashtid/portfolio-site/security/advisories/new).
It is enabled on this repository, it is private until published, and it gives
you a thread you can see rather than a mail you cannot tell arrived.

**Alternative:** a direct message on
[LinkedIn](https://www.linkedin.com/in/david-dashti/).

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

Reviewed **2026-11-23**, superseding the 2026-11-15, 2026-10-20, 2026-09-29
and 2026-09-20 reviews and the 2026-08-07 list before them (see the notes at
the end).

On 2026-11-23, `npm audit` reports **9 entries (all moderate), which are 2
advisories**: minimatch and glob. npm counts one advisory once per dependency
node, so the entry count is not a finding count. `npm audit --omit=dev`
reports **0** — none of this reaches the deployed frontend or the backend.

minimatch has an entry below. glob
([GHSA-3g3m-2fjr-6pw4](https://github.com/advisories/GHSA-3g3m-2fjr-6pw4), in
glob 13.0.6 and `workbox-build`'s 11.1.0) has none: GitHub auto-dismissed its
development-scope Dependabot alert, #246. No Dependabot alert is open. The
nine advisories that left the audit since 2026-11-15 are listed in the dated
note at the end.

glob's advisory needs a caller that passes glob an `AbortSignal`: an aborted
walk rejects but goes on reading directories. Nothing here passes one
(checked 2026-11-24 by searching each consumer's installed code for
`signal`). `workbox-build` 7.4.1 calls `globSync()` during `build:ssg`,
`@sentry/bundler-plugins` 10.78.0 calls it with an `ignore` list only, and
`js-beautify` 2.0.3 loads it only in its command-line tool, which nothing
here runs.

Both advisories are listed in
[`frontend/osv-scanner.toml`](frontend/osv-scanner.toml) until 2027-02-24.
OpenSSF Scorecard's Vulnerabilities check runs OSV-Scanner over
`frontend/package-lock.json`, and OSV-Scanner skips the IDs that file lists,
so the check does not count them. Each entry lapses on that date, and the
check counts its advisory again until the entry is re-checked and renewed.

Code-scanning alert 120 needs no entry: Trivy opened it on 2026-11-17 for
`picomatch` 4.0.7 and CVE-2026-112366 (ReDoS through single-branch repeated
extglob patterns such as `+(*)`), and GitHub withdrew the matching advisory,
[GHSA-fc5q-39xc-vjpf](https://github.com/advisories/GHSA-fc5q-39xc-vjpf), on
2026-11-18 as not a security issue. `npm audit` does not report it, Dependabot
opened no alert for it, and Trivy's scan of `main` on 2026-11-24, with
picomatch still at 4.0.7, the newest release, closed the alert as fixed.

### minimatch — denial of service through pattern amplification (accepted)

Checked **2026-11-23**.

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
- Seven copies are installed, and only `minimatch@10.2.6` (dev-only) is in
  range: 3.1.5 and 5.1.9 are below 7.0.0, and four 11.0.8 copies are above
  the fix. eslint 10.15.0 and `@eslint/config-array` 0.23.6 ask for `^11.0.5`
  and `@typescript-eslint/typescript-estree` 8.73.0 for `^11.0.1`, so each
  nests its own 11.0.8, and so does `glob` 14.0.6 (`^11.0.5`) under the
  `@sentry/node` that Lighthouse 13 brings with `@lhci/cli` 0.16.1. 11.0.8 is
  also past the 11.0.7 floor set by
  [GHSA-cf2h-pxjq-68xw](https://github.com/isaacs/minimatch/security/advisories/GHSA-cf2h-pxjq-68xw)
  (quadratic compile time in 11.0.0 to 11.0.6).
- At lint time nothing uses 10.2.6 any more (see the counts below). Of its
  remaining consumers, `editorconfig` 3.0.2 (under `@vue/test-utils` 2.6.0 →
  `js-beautify` 2.0.3; 2.6.0 asks for the same `js-beautify ^2.0.0` as 2.5.1)
  compiles at the default `optimizationLevel` 1, and only the `js-beautify`
  command-line tool loads it, which nothing here runs.
- The one level-2 caller is `vite-plugin-pwa` → `workbox-build@7.4.1` →
  `glob@11.1.0` during `build:ssg`. Its patterns are the `workbox.globPatterns`
  and `globIgnores` literals in `frontend/vite.config.ts`, plus `sw.js` and
  `workbox-*.js`, which `workbox-build`'s `generateSW()` adds to `globIgnores`
  itself; none contains `..`. No visitor, CMS row or API response reaches a
  pattern: the API data the build fetches for prerendering only determines
  which files exist, and file names are matched, never compiled. Checked by
  logging every `Minimatch` construction through `npm run lint`, the unit
  tests with coverage, `build:ssg`, the end-to-end suite and `verify:csp`.
  On 10.2.6 that is 0, 0, 42, 0 and 0, all from this `glob` at level 2. The
  27 that lint made on 10.2.6 before eslint 10.15.0 now go to eslint's and
  `@eslint/config-array`'s own 11.0.8.
- `glob@13.0.6` (`@sentry/bundler-plugins` 10.78.0, `js-beautify`) never loads
  the installed copy: its entry point is a bundle with its own minimatch,
  which no scanner sees and no override reaches. `vite.config.ts` imports
  `@sentry/vite-plugin`, so every `build:ssg` loads that bundle, but it
  compiles patterns only when the plugin is enabled (`SENTRY_AUTH_TOKEN` set):
  the plugin's own and `dist/**/*.map`, none with `..`.
- isaacs/minimatch's
  [GHSA-c859-jr93-m5j4](https://github.com/isaacs/minimatch/security/advisories/GHSA-c859-jr93-m5j4)
  (`escape()` output that matches more or less than the literal input; up to
  11.0.7, fixed in 11.0.8) covers 10.2.6 as well. Like GHSA-cf2h-pxjq-68xw it
  is a repository advisory that GitHub's global advisory database does not
  list on 2026-11-23, so no scanner reports it. The one `escape()` caller on
  10.2.6 is `editorconfig`, which only that command-line tool loads; `glob`
  11.1.0 only re-exports the function.
- **An override was tried and does not work.** The override
  `"minimatch@>=7.0.0 <11.0.1": "11.0.1"` moves only the 10.2.6 copy, passes
  `npm ci` and the npm 11.6.1 `ci --dry-run` gate, and leaves the lint output,
  ESLint's per-file config, the unit results and coverage unchanged. But
  minimatch 11 compiles each wildcard path segment into a `Matcher` object
  instead of a `RegExp`, and `glob@11.1.0` walks only `RegExp` segments, so
  `workbox-build`'s patterns matched no file: the service-worker precache fell
  from 25 entries to 1 and `verify-dist-invariants` failed the build. And
  minimatch 11.0.0 to 11.0.6 are inside its own GHSA-cf2h-pxjq-68xw.
- **Re-check trigger:** a `workbox-build` (or `vite-plugin-pwa`) release whose
  `glob` walks minimatch 11's `Matcher` segments; `workbox-build` 7.4.1 and
  `vite-plugin-pwa` 2.0.0 are still the newest. Retry the override then, not
  before: it already leaves lint, the unit tests and coverage unchanged, but it
  fails while `workbox-build` resolves a `glob` that walks only `RegExp`
  segments. Without an override a 10.x copy stays in the lock as long as any
  consumer asks for one: `editorconfig` 3.0.2 asks for `~10.2.4` (4.0.1 asks
  for `~11.0.5`, but `js-beautify` 2.0.3, the newest, still asks for
  `^3.0.2`), and `glob` 13.x for `^10.2.2` (under `js-beautify` and the
  `@sentry/bundler-plugins` 10.78.0 that `@sentry/vite-plugin` 5.4.1 brings).
  Re-check too when GHSA-c859-jr93-m5j4 reaches the global database, which
  would let Dependabot raise it against 10.2.6.

### Scorecard image — a tag the action's commit pin does not fix (accepted)

Checked **2026-11-26**.

- `scorecard.yml` pins `ossf/scorecard-action` by commit (v2.5.0), but the
  action's `action.yaml` at that commit runs
  `docker://ghcr.io/ossf/scorecard-action:v2.5.0`, a tag the pin does not
  fix. The workflow records the tag's digest in an `# image:` comment under
  the pin, and its `image-pin` job, which the analysis job needs, runs
  `scripts/verify_action_pins.py --only ossf/scorecard-action`: the check
  fails unless ghcr.io still serves that digest for the tag the action names.
  `security-scan` in `ci-cd.yml` runs the full check on every push to `main`
  and every pull request to it, so an action bump that leaves the comment
  behind fails there.
- A `docker://` step that names the image by digest is no way out while
  `publish_results` is on: the results API behind the README badge accepts
  the Scorecard step only as the action or as an image by tag, and only
  `uses:` steps in the analysis job, which is why the check runs in a job of
  its own.
- An image pushed to the tag between the `image-pin` check and the analysis
  job's pull would run in its place, with that job's grants:
  `id-token: write`, `security-events: write` and `contents: read`. Accepted
  because the two are minutes apart unless the analysis job is re-run on its
  own, which does not repeat the check, and because that job holds no
  repository secret and only read access to the code.
- **Re-check trigger:** a `scorecard-action` release whose `action.yaml`
  names its image by digest, which the commit pin then fixes and the check
  accepts without a comment; `publish_results` turned off; or the results
  API accepting an image by digest.

### Vercel CLI — a prebuilt binary, locked by its hash (accepted)

Checked **2026-11-26**.

- Both production deploy paths, `ci-cd.yml`'s `deploy-frontend` and
  `rebake-frontend.yml`, run the CLI from `.github/tools/vercel`. Its lock
  holds one package, `@vercel/vc-native-linux-x64` 65.16.0, the CLI's Linux
  x64 binary, with a sha512 integrity hash, and the entry lists no
  dependencies and no install script. `install.sh` installs it with
  `npm ci --ignore-scripts` under `$RUNNER_TEMP`, outside the checkout that
  `vercel deploy` uploads, and fails unless the binary prints the locked
  version. Neither the `vercel` launcher nor its JavaScript fallback,
  `@vercel/cli-support`, is installed: both deploy steps call the binary by
  its path, so no JavaScript that npm resolved runs in the process that
  holds `VERCEL_TOKEN`.
- Before `66ac1ab`, both paths ran `npm install -g vercel@65.16.0`, which
  pins the top package only: the rest of the tree resolved when the job ran,
  outside every lock and integrity hash. The first lock in that directory
  (`66ac1ab`) also held the launcher and `@vercel/cli-support`, 388 more
  packages. The launcher never loads `@vercel/cli-support` on the native
  path, and on 2026-11-25, 43 GitHub advisories covered package versions in
  its dependency tree.
- The binary is Vercel's packaged build of the CLI's own JavaScript, and no
  scanner sees what it was built from: `npm audit`, Dependabot and
  OSV-Scanner, which Scorecard's Vulnerabilities check runs over every
  lockfile, see one package and its version, so none can tell whether it
  bundles code those advisories cover. Accepted because the deploys need a
  current CLI (Vercel rejects deploys from CLIs below a server-side minimum)
  and the binary needs no other package: the integrity hash fixes its bytes,
  which change only through a bump of the lock.
- **Re-check trigger:** every bump of the pin. Dependabot checks for one
  every Monday, with a 7-day cooldown, and the `vercel-cli` job runs
  `install.sh` on the pull request with no secrets; the new lock must still
  hold the one package, with no dependencies and no install script.

### Backend base image — scanned weekly, gating no deploy (accepted)

Checked **2026-11-26**.

- `.github/workflows/image-scan.yml` scans the base of `backend/Dockerfile`'s
  runtime stage, its last `FROM`, and fails unless that names the image by
  digest. It runs grype (`ghcr.io/anchore/grype:v0.122.0`, by a digest that
  `security-scan` holds to the tag) for `linux/amd64` every Monday at 06:30
  UTC, on pushes and pull requests to `main` that change the Dockerfile or
  the workflow, and by hand. High and Critical matches that have a fix go to
  code scanning under the category `grype-image`, and the last step fails
  while one remains.
- It uses grype because Trivy's image scan lists no CPython package for this
  image. The runtime stage installs no OS package
  (`backend/tests/test_ci_workflows.py` fails on an `apt-get` there), so
  production's Debian packages and its CPython are the base's; the Python
  packages installed on top come from `backend/requirements.txt`, which the
  Trivy step in `security-scan` reads.
- No deploy waits for the scan, so a backend deploy can ship on a base the
  scan has flagged. Accepted because what a red run asks for is a digest
  refresh, which holding a deploy back would not make, and because a base
  with a fixable vulnerability must not hold up unrelated pull requests: the
  scan is not part of `security-scan`, the one status check `main` requires
  (through its classic branch protection rule, not its ruleset).
- **Re-check trigger:** a red run. Move both `FROM` lines together to the
  newest index of the tag that is at least 7 days old (Dependabot proposes
  tag bumps here, but digest refreshes land by hand), and record here, with
  its reason, any match that index still carries.

### `overrides`

`frontend/package.json` no longer has an `overrides` field. Each of the five
that stood on 2026-11-15 was dropped after the lock was written without it:

- `tmp ^0.2.7` (`1be42ba`): nothing depends on `tmp` any more. `@lhci/cli`
  0.16 dropped it, and its `inquirer` 8.2.7 uses `@inquirer/external-editor`
  1.0.3 instead of `external-editor` 3.1.0, which asked for `tmp ^0.0.33`.
  The lock is byte-identical with and without the entry.
- `uuid ^11.1.1` (`1be42ba`): its only dependent is now `@lhci/cli` 0.16.1,
  which asks for `^14.0.3`, so the entry would force a lower major. uuid
  resolves to 14.0.3, which no live advisory covers: GHSA-w5hq-g745-h8pq is
  fixed in 11.1.1, 12.0.1 and 13.0.1, and GHSA-qmq6-f8pr-cx5x (below 14.0.0)
  was withdrawn as its duplicate.
- `qs ^6.17.1` (added in `46c351a`, raised in `da44c11`): `express` 4.22.3
  and `body-parser` 1.20.9 both ask for `qs ~6.16.0`, which resolves to
  6.16.2, outside every qs advisory: GHSA-6pq8-jhm2-2vcw is fixed in 6.16.1,
  GHSA-4mjr-xmp4-gh2g and GHSA-x5fp-wj9c-mxmx in 6.16.0, and
  GHSA-q8mj-m7cp-5q26 in 6.15.2.
- `fflate ^0.8.3` (`bd4f762`, GHSA-px8p-9vwx-vf98) and the `sourcemap-codec`
  alias (`fd2f78e`) changed nothing: `@vitest/ui` 5.1.0 asks for
  `fflate ^0.8.3` itself, and nothing depends on `sourcemap-codec`; the lock
  is byte-identical without either.

### What changed since 2026-08-07, and the lesson

- **2026-11-26:** CI now installs flyctl from a sha256 committed beside its
  version, in each of the three jobs that run it, and the Vercel CLI from
  the lock above. The grype and Scorecard images are held to recorded
  digests that `scripts/verify_action_pins.py` checks against their tags
  (see the backend base image and Scorecard image entries above), and the
  same script now also fails on a `uses:` that names no full commit SHA, no
  path in this repository and no Docker image by digest. The backup job's
  PGDG apt source now trusts only the key with its published fingerprint.
  Both deploy jobs now wait for `security-scan`, which fails on a verified
  secret in the pushed commits or a pin that disagrees with its version
  comment, and for the dependency review when it runs, which on a push
  covers only the commits that push added. Each deploy job, and the rebake,
  now requires `refs/heads/main`, the one branch `ci-cd.yml` runs for, and
  [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md) says what these gates leave
  open. Neither this note nor the three entries checked on 2026-11-26
  forecast how Scorecard, Dependabot or code scanning will mark an alert:
  GitHub and the scanners set those states themselves, as when Trivy closed
  code-scanning alert 120 with `picomatch` unchanged and GitHub marked
  dismissed Dependabot alerts fixed (see 2026-11-24).
- **2026-11-24:** once the 2026-11-23 lock reached `main`, GitHub marked the
  eight Dependabot alerts #187, #200, #218, #234, #238, #241, #248 and #249
  fixed, the dismissed and auto-dismissed ones included. Trivy's scan of
  the same push closed code-scanning alert 120 (see above). The same day,
  `frontend/osv-scanner.toml` began listing glob's and minimatch's
  advisories until 2027-02-24 (see above).
- **2026-11-23:** the extract-zip, basic-ftp and deepmerge entries are
  **gone**, and so are three advisories that had none. `@lhci/cli` 0.16.1
  (Lighthouse 13.6.0, `puppeteer-core` 25.17.0, `@puppeteer/browsers` 3.2.7)
  replaced the 0.15.1 tree. `@puppeteer/browsers` 3.2.7 no longer depends on
  extract-zip: it unpacks zip archives with the system's `unzip` (`tar.exe` or
  PowerShell on Windows) or an optional `yauzl` peer that nothing here installs,
  and tar archives with `modern-tar`. So extract-zip 2.0.1 left the lock with
  both of its advisories (GHSA-jmr9-qjv8-65gv and GHSA-7pqw-9j4j-h8q3;
  their Dependabot alerts, #187 and #200, had been dismissed).
  `@lhci/cli`'s `proxy-agent` 8.0.3 → `pac-proxy-agent` 9.1.1 → `get-uri` 8.0.2
  asks for basic-ftp `^6.2.4` and resolves 6.2.6, which carries all three
  basic-ftp fixes (GHSA-c475-qrg2-pj4r, GHSA-r4jh-29pc-gfqr and
  GHSA-5pm8-86m8-9m6r; alerts #218 and #249 were auto-dismissed, and #248 was
  dismissed with that entry as the reason). `chromium-bidi`'s zod moved from
  3.25.76 to 4.6.7, past GHSA-mrhx-c7xc-m3w5 (alert #238), and body-parser
  1.20.9 and ip-address 10.7.6, moved in the lock only and inside the ranges
  their dependents declare, fixed GHSA-27r3-jxmh-p828 (#241) and
  GHSA-rxp7-6hxx-x8q5 (#234). GitHub withdrew deepmerge's GHSA-gcqx-w48m-w2h4
  on 2026-11-16, which was that entry's re-check trigger: `npm audit` no
  longer reports it, and Dependabot alert #244 now answers HTTP 410 ("Alert
  number 244 has been withdrawn"). The five `overrides` went too (see above).
- **2026-11-23, still outside the lock:** CI's `lighthouse` job runs
  `treosh/lighthouse-ci-action` 12.6.2, still its newest release, and its
  committed `node_modules` carries `@lhci/cli` 0.15.1 with extract-zip 2.0.1
  and basic-ftp 5.2.0, which Dependabot and `npm audit` cannot see. Its chain
  is the one the removed entries tested (`@puppeteer/browsers` 2.13.0,
  `proxy-agent` 6.5.0, `get-uri` 6.0.5; basic-ftp was 5.3.1 here):
  extract-zip is installed and never executed, because only a browser
  download unpacks an archive and no step downloads one, and basic-ftp is
  installed and never loaded, because only a `pac+` proxy URL loads it and
  `ci-cd.yml` configures no proxy. **Re-check trigger:** a
  `lighthouse-ci-action` release on `@lhci/cli` 0.16.1 or later.
- **2026-11-15:** sprintf-js
  ([GHSA-hp3w-g68c-fv3c](https://github.com/advisories/GHSA-hp3w-g68c-fv3c)),
  accepted here on 2026-10-20, is **gone**: GitHub withdrew the advisory on
  2026-10-22, `npm audit` no longer reports it, and Dependabot alert #223 now
  answers HTTP 410 ("Alert number 223 has been withdrawn"). Its entry was
  removed, and entries for minimatch and deepmerge were added. basic-ftp's
  entry now covers the two advisories published on 2026-11-12, and its old
  re-check trigger would not have cleared it. The overrides
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
