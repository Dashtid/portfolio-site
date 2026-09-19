# CV — the public reference copy

This folder holds the scrubbed, public JSON Resume record. It is **not** what the CV
export renders from: the generated CV assembles from the database the admin CMS curates
(`companies`, `education`, `skills`, `cv_profile`), via the admin-only
`/api/v1/admin/cv/export` endpoint and the `/admin/cv` screen. A keyword added only here never reaches a document
that gets sent anywhere.

There is no public `/cv` route — the site itself is the CV.

## Files

- **`resume.json`** — the scrubbed public record, in [JSON Resume](https://jsonresume.org/)
  schema. Hand-maintained; keep it in step with the CMS when the two drift.
- **`source/`**, **`exports/`** — the original PDF and the printed exports, kept locally
  only. **Git-ignored on purpose** (`.gitignore`) — see the PII note below.

## PII / public-repo note (read before committing)

This repository is **public** (it powers dashti.se). So:

- `source/` and `exports/` are git-ignored: they carry a phone number, a personal email
  and a photo that must not enter a public git history.
- `resume.json` leaves **`basics.email` and `basics.phone` empty**, and
  `frontend/tests/unit/cvPublicScrub.spec.ts` asserts both stay that way, that `cv/`
  tracks exactly three files (`.gitignore`, `README.md`, `resume.json`), and that no
  string in `resume.json` looks like an email, a phone number or a personnummer. There is
  no contact form: contact is LinkedIn, and `security.txt` for security reports.
- If you want contact details on a rendered PDF, inject them at render time from a local
  overlay rather than committing them here.

## Note on content

The `projects` section was **added** (it is not on the source PDF), then **trimmed Jul 2026**.

**Inclusion rule: a project appears here only if it is public, independently authored, and safe to
link.** Anything that fails one of those is simply absent — from this file, from `resume.json`, and
from the seed data. Next addition: **oidc-reach**, once v0.1 ships.

Deliberately not recorded here: which projects were removed, or why. This file is world-readable,
and an explanation of an omission re-publishes the thing the omission exists to keep out of it.
