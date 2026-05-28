# Security Policy

## Reporting a Vulnerability

If you believe you have found a security vulnerability in this project,
please report it privately. Do not open a public GitHub issue.

**Contact:** dashti.dat@gmail.com

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
`dashti-portfolio-backend.fly.dev`.

## Out of Scope

- Vulnerabilities in third-party services this site uses (Vercel, Fly.io,
  GitHub OAuth, ipapi.co) — please report those upstream.
- Social engineering attempts.
- Denial-of-service issues that require an unrealistic traffic profile
  for a single-author portfolio site.

## Supported Versions

Only the current `main` branch is supported. Older versions are not patched.
