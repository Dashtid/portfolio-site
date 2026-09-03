# Security Policy

## Reporting a Vulnerability

If you believe you have found a security vulnerability in this project,
please report it privately. Do not open a public GitHub issue.

**Contact:** <dashti.dat@gmail.com>

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

Known `npm audit` findings that are consciously accepted rather than fixed,
reviewed 2026-08-07:

- **js-yaml quadratic CPU on `!!omap` (GHSA-5p4m-2wfm-xmqj, CVE-2026-59870)**
  via a single dev-only chain: `@lhci/cli@0.15.1` → `@lhci/utils` →
  `js-yaml@3.15.0`. The fix exists only in js-yaml 5.x and was explicitly NOT
  backported to 3.x or 4.x, and 4.x already removed the `safeLoad`-era API that
  `@lhci/utils` calls — so an `overrides` pin to 5.x would break Lighthouse CI
  rather than patch it. Exposure: js-yaml here parses `lighthouserc` config
  from this repo during CI only. The input is not attacker-controlled and the
  package never reaches the deployed frontend (`npm audit --omit=dev` reports
  0 vulnerabilities). Re-check when `@lhci/cli` moves off js-yaml 3.x.

- **brace-expansion OOM DoS (GHSA-mh99-v99m-4gvg)** in nested dev-only copies
  (1.1.18 / 2.1.4). `npm audit` reports this as 15 high-severity entries, but
  they are ONE advisory counted once per node along three chains:
  - `@lhci/cli` → `chrome-launcher` → `rimraf` → `glob` → `minimatch`
  - `@vue/test-utils` → `js-beautify` → `editorconfig` / `glob` → `minimatch`
  - `vite-plugin-pwa` → `workbox-build` →
    `@trickfilm400/rollup-plugin-off-main-thread` → `ejs` → `jake` →
    `filelist` → `minimatch`

  The advisory is patched only in 5.0.8+ with no 1.x/2.x backports, so the
  offered "fix" is a breaking-major downgrade of dev tooling. Exposure: the
  vulnerable code runs only in local dev / CI / build time against
  repo-controlled glob patterns — never in the deployed frontend or backend.
  Re-check when `@lhci/cli`, `js-beautify`, or `workbox-build` move off
  legacy `minimatch`/`jake` majors.

  When re-checking, confirm the count still decomposes to this single
  advisory (`npm audit --json` grouped by `via`) rather than assuming a
  changed number means new exposure.

Everything else reported by `npm audit` at review time was fixed in-range
(`body-parser`, `fast-uri`, top-level `brace-expansion`).
