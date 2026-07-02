# CV — single source of truth (FEAT-001 seed)

This folder is the starting point for **FEAT-001** (see `../BACKLOG.md`): one structured
CV that renders to both a PDF and the site's `/cv` route, replacing the paid CV builder.

## Files

- **`resume.json`** — the source of truth, in [JSON Resume](https://jsonresume.org/) schema.
  Transcribed from the existing PDF (Jun 2026). Edit this; everything else is generated.
- **`source/`** — the original `cv-david-dashti.pdf`, kept locally as a reference.
  **Git-ignored on purpose** (see `.gitignore`) — see the PII note below.

## PII / public-repo note (read before committing)

This repository is **public** (it powers dashti.se). So:

- `source/` (the raw PDF) is git-ignored — it contains a phone number, personal email,
  and a photo that should not be published to a public git history.
- `resume.json` deliberately leaves **`basics.phone` blank**. Keep it that way in the
  committed file. If you want the phone on the *PDF*, inject it at render time from a
  local/private overlay rather than committing it here.
- `basics.email` is included (it is already on your public CV/site) — your call.
- The public `/cv` route should render contact via the site's existing form, not expose
  phone/address.

## Building (when FEAT-001 is implemented)

Recommended renderer: [RenderCV](https://github.com/rendercv/rendercv) (Python, matches the
FastAPI backend) or any JSON Resume theme. Sketch:

1. `resume.json` → PDF via the chosen renderer (wire as a `scripts/` step + CI artifact).
2. `/cv` route fetches the same `resume.json` and renders it, so PDF and site never drift.
3. LinkedIn stays a **manual mirror** — its 2026 API has no profile-write; do not automate.

## Note on content

The `projects` section was **added** (it is not on the source PDF), then **trimmed Jul 2026**:
dicom-fuzzer, sbom-sentinel and medtech-ai-security are employer-IP-tainted (Hermes work-product
clause) — repos made private, DICOM Fuzzer card removed from the live site, and all three removed
from this file. Only IP-clean work goes here. Next addition: **oidc-reach**, once v0.1 ships.
The work itself may still be *described* in experience bullets ("a protocol fuzzer I built in my
current role") — see career-plan/BACKLOG.md "Defensible-claims register" for the vetted phrasings.
