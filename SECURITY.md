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

Reviewed **2026-09-29**, superseding the 2026-09-20 review and the 2026-08-07
list before it (see the notes at the end).

`npm audit` currently reports **6 high entries, which are 2 advisories**: npm
counts one advisory once per dependency node, so the entry count is not a
finding count. `npm audit --omit=dev` reports **0** — none of this reaches the
deployed frontend or the backend.

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

### Standing `overrides` that must not be pruned

`frontend/package.json` pins `tmp ^0.2.7`, `uuid ^11.1.1`, `qs ^6.16.0`,
`fflate ^0.8.3` and aliases `sourcemap-codec`. They look unrelated to each other
and are all in the same dormant `@lhci/cli` tree; dropping any of them reopens an
advisory that `1be42ba` / `bd4f762` closed. **Re-check trigger:** an `@lhci/cli`
release above 0.15.1 whose published deps no longer name `tmp ^0.1.0`.

### What changed since 2026-08-07, and the lesson

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
