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

> [!] Do not use `security@dashti.se`. It was published in this repository's
> `security.txt` until 2026-09-20 and it bounced the whole time — the domain has
> no MX record. Both files now point at the channels above.

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

Reviewed **2026-10-20**, superseding the 2026-09-29 and 2026-09-20 reviews and
the 2026-08-07 list before them (see the notes at the end).

`npm audit` currently reports **13 entries (10 high, 3 moderate), which are 4
advisories**: extract-zip twice, basic-ftp and sprintf-js. npm counts one
advisory once per dependency node, so the entry count is not a finding count.
`npm audit --omit=dev` reports **0** — none of this reaches the deployed
frontend or the backend. All four sit in the dormant `@lhci/cli` 0.15.1 tree,
and none has a fix that tree can take.

### extract-zip — arbitrary file write / symlink path traversal (accepted)

Re-checked **2026-09-27**.

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
  `extract-zip`'s entry point with a tripwire in a scratch install of this
  lockfile: a direct `unpackArchive()` call set it off; a full `lhci autorun`
  did not.
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
  from 0.15.1 to 0.12.0 (Lighthouse 10).
- **Re-check trigger:** an `@lhci/cli` release above 0.15.1, or a
  `lighthouse-ci-action` release, whose tree reaches `@puppeteer/browsers` 3.x
  without `proxy-agent` 6.x. On 2026-09-27 every 3.x release up to 3.2.3 still
  declares the `proxy-agent >=8.0.1` peer, and `@lhci/cli` has not published
  since 2025-06-25. Do not retry the override before checking
  `npm view @puppeteer/browsers@<v> peerDependencies`.

### sprintf-js — denial of service through unbounded precision (accepted)

Checked **2026-10-20**.

- [GHSA-hp3w-g68c-fv3c](https://github.com/advisories/GHSA-hp3w-g68c-fv3c)
  (CVE-2026-97058), moderate: sprintf-js through 1.1.3 passes unbounded
  precision values to `toFixed`, `toExponential` and `toPrecision`, so whoever
  controls a FORMAT STRING can make it throw. **No patched version exists**:
  1.1.3 is the newest release. Dependabot alert #223 is dismissed with this
  entry as the reason.
- One dev-only chain: `@lhci/cli` → `@lhci/utils` → `js-yaml@3.15.2` →
  `argparse@1.0.10` → `sprintf-js@1.0.3`. **It is installed, never executed.**
  js-yaml requires `argparse` only in its own command-line tool
  (`bin/js-yaml.js`); `@lhci/utils` loads js-yaml as a library, and nothing
  here runs the js-yaml CLI. Even inside argparse, the format strings are
  argparse's own, not input.
- **Re-check trigger:** an `@lhci/cli` release above 0.15.1 (a move to js-yaml
  4 brings argparse 2, which has no dependencies), or a sprintf-js release
  above 1.1.3.

### basic-ftp — quadratic-time FTP directory-listing parse (accepted)

Checked **2026-10-20**.

- [GHSA-c475-qrg2-pj4r](https://github.com/advisories/GHSA-c475-qrg2-pj4r)
  (CVE-2026-102990), high: `Client.list()` parses a Unix directory listing
  with a regex that backtracks quadratically, so a hostile FTP server can burn
  CPU. Fixed in basic-ftp 6.2.1, which is outside the `^5` range `get-uri`
  requires, so it cannot be taken in place. No Dependabot alert is open for it.
- One dev-only chain: `@lhci/cli` → `proxy-agent@6.5.0` →
  `pac-proxy-agent@7.2.0` → `get-uri@6.0.5` → `basic-ftp@5.3.1`. `get-uri`
  uses basic-ftp only to fetch `ftp://` URLs, and `pac-proxy-agent` fetches a
  proxy auto-config file only when a PAC proxy is configured. Nothing here
  configures one, so no FTP listing is ever parsed.
- **Re-check trigger:** the same `@lhci/cli` release that moves it off
  `proxy-agent` 6.x (see extract-zip above).

### Standing `overrides` that must not be pruned

`frontend/package.json` pins `tmp ^0.2.7`, `uuid ^11.1.1`, `qs ^6.16.0`,
`fflate ^0.8.3` and aliases `sourcemap-codec`. They look unrelated to each other
and are all in the same dormant `@lhci/cli` tree; dropping any of them reopens an
advisory that `1be42ba` / `bd4f762` closed. **Re-check trigger:** an `@lhci/cli`
release above 0.15.1 whose published deps no longer name `tmp ^0.1.0`.

### What changed since 2026-08-07, and the lesson

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
