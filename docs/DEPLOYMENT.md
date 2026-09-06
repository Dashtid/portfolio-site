# Production Deployment

Vercel serves the statically-generated frontend; Fly.io runs the FastAPI
backend next to a Fly Postgres app. Everything deploys from
`.github/workflows/ci-cd.yml` on pushes to `main` — there is no manual
deploy step in the normal path.

**Production URLs**: <https://dashti.se> (frontend), <https://api.dashti.se> (backend)

---

## Backend (Fly.io)

Configured in `backend/fly.toml`:

| Setting         | Value                                               |
| --------------- | --------------------------------------------------- |
| App name        | `dashti-portfolio-backend`                          |
| Region          | `arn` (Stockholm)                                   |
| Memory / CPU    | 1 GB, 1 shared                                      |
| Port            | 8000                                                |
| Release command | `python -m scripts.migrate` (Alembic, every deploy) |

Migrations run in a Fly release machine before new app machines start, so
a deploy whose migration fails never replaces the running version.

Secrets (set once via `fly secrets set`): `SECRET_KEY`,
`GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`, `SENTRY_DSN`,
`GITHUB_OSS_DASHBOARD_PAT`, and `DATABASE_URL` (written by
`flyctl postgres attach`).

Operational commands:

```bash
fly status                                  # machine state
fly logs -a dashti-portfolio-backend        # logs (--follow for live)
fly ssh console                             # shell in the container
curl https://api.dashti.se/api/v1/health    # liveness
```

## Frontend (Vercel)

The deploy job runs `vercel deploy --prod` from Actions; Vercel builds
from source using `vercel.json`'s `buildCommand` (`npm run build:ssg`).
CI env vars only reach that remote build when forwarded explicitly with
`--build-env`: `VITE_APP_VERSION` carries the commit SHA (it becomes the
footer build stamp and the Sentry release tag), and the `SENTRY_*` trio
powers sourcemap upload when set.

Security headers (hash-locked CSP, HSTS with preload submitted,
X-Content-Type-Options, X-Frame-Options, Permissions-Policy,
Referrer-Policy) live in `frontend/vercel.json` and are served by the
Vercel edge — the backend never sets them for the static site. The CSP's
hashes are enforced three ways before any deploy: unit tests recompute
each hash from source, `scripts/verify-dist-invariants.mjs` scans the
built pages for uncovered styling, and `scripts/csp-check.mjs` drives the
built bundle under the real policy in a browser.

Caching (also `vercel.json`): `/assets/*` one year immutable, `/images/*`
24 h + stale-while-revalidate, `/sw.js` must-revalidate.

---

## CI/CD pipeline

One workflow, `.github/workflows/ci-cd.yml`, with a `changes` filter so
frontend-only and backend-only commits run only their own lane (`cv/**`
rides the frontend lane for the CV scrub guard):

| Job                 | What it does                                                                                                                                |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| `frontend-quality`  | ESLint, vue-tsc, 610 vitest unit tests with coverage floors, vite-ssg build + dist invariants, Codecov                                      |
| `backend-quality`   | ruff lint + format, mypy, 977 pytest tests with an 83% coverage floor, Codecov                                                              |
| `e2e-tests`         | Playwright (chromium) against the built dist — functional, visual-regression and the enforced-CSP check                                     |
| `lighthouse`        | LHCI with assertion budgets (performance and accessibility are hard errors)                                                                 |
| `security-scan`     | Trivy filesystem scan (checksum-verified binary) + secret scan of the diff                                                                  |
| `dependency-review` | Blocks PRs introducing vulnerable or denied-licence dependencies                                                                            |
| `deploy-frontend`   | Vercel CLI deploy, gated on quality + e2e + lighthouse, then a post-deploy smoke asserting the live security headers                        |
| `deploy-backend`    | `flyctl deploy --remote-only`, gated on backend-quality; frontend deploys serialize behind it so the SSG bake never reads a mid-rollout API |

Python installs in CI use `--require-hashes` against the committed
lockfiles — including a hash-pinned bootstrap of pip itself
(`requirements-pip.txt`). `requirements.txt` is compiled from
`pyproject.toml` for the Linux deploy image (`--python-platform
x86_64-unknown-linux-gnu`); regenerating it on another platform silently
drops platform-markered packages like uvloop, so keep the flags.

Supporting workflows:

| Workflow              | Trigger                     | Purpose                                                              |
| --------------------- | --------------------------- | -------------------------------------------------------------------- |
| `codeql.yml`          | push + schedule             | CodeQL SAST for JS/TS + Python                                       |
| `scorecard.yml`       | push + weekly               | OpenSSF Scorecard                                                    |
| `pre-commit.yml`      | push / PR                   | The shared pre-commit hook set against the full tree                 |
| `uptime.yml`          | every 15 min                | Probes the live site and API                                         |
| `db-backup.yml`       | nightly 03:30 UTC           | Postgres dump, encrypted to a public key before storage              |
| `restore-drill.yml`   | quarterly (Jan/Apr/Jul/Oct) | Files a restore-checklist issue — backups are rehearsed, not assumed |
| `rebake-frontend.yml` | manual                      | Re-runs the SSG bake so CMS edits reach the prerendered pages        |

---

## Monitoring

- **Fly health checks**: `[[http_service.checks]]` probes
  `/api/v1/health` every 30 s; `/api/v1/health/ready` adds a DB
  round-trip and is what the uptime workflow watches.
- **Uptime**: the `uptime.yml` workflow, every 15 minutes from Actions.
- **Sentry**: active on the **backend** (`SENTRY_DSN` Fly secret; tracing
  at a 10% sample). The frontend ships Sentry init code, but the whole
  init is dead-code-eliminated at build unless `VITE_SENTRY_DSN` is
  provided to the Vercel build — that secret has never been set, so
  frontend Sentry is currently **inactive by default**, not silently on.
- **Metrics**: `/api/v1/metrics/*` (admin-gated) returns request counts,
  response times and error rates per endpoint.

## Troubleshooting

| Issue                                 | First move                                                                          |
| ------------------------------------- | ----------------------------------------------------------------------------------- |
| 502 Bad Gateway                       | `fly status` / `fly logs`; restart with `fly apps restart dashti-portfolio-backend` |
| CORS errors                           | Verify `CORS_ORIGINS` in backend config                                             |
| OAuth failure                         | Check `GITHUB_CLIENT_ID` and the callback URL                                       |
| Stale public content after a CMS edit | Run `rebake-frontend.yml` — content is baked at build time by design                |
