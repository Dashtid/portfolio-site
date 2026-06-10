# Portfolio Site Backlog

Prioritized work items for the portfolio site. Grouped by category, ordered by severity within each group.

**Legend:** CRITICAL > HIGH > MEDIUM > LOW

---

## Open Items — Quick Reference

| ID | Category | Severity | Summary |
|----|----------|----------|---------|
| ~~CI-007~~ | ~~CI/CD~~ | ~~CRITICAL~~ | ~~`build:ssg` never runs in any workflow or Vercel config~~ — **RESOLVED** |
| ~~CI-008~~ | ~~CI/CD~~ | ~~CRITICAL~~ | ~~`deploy-backend.yml` test job missing `requirements-dev.txt`~~ — **RESOLVED** |
| ~~CI-009~~ | ~~CI/CD~~ | ~~HIGH~~ | ~~Action version tags don't exist~~ — **RESOLVED** |
| ~~BE-005~~ | ~~Security~~ | ~~HIGH~~ | ~~passlib/bcrypt incompatibility~~ — **RESOLVED** (replaced passlib with direct bcrypt) |
| ~~BE-006~~ | ~~Security~~ | ~~HIGH~~ | ~~GitHub proxy endpoints no rate limiting~~ — **RESOLVED** |
| ~~BE-007~~ | ~~Security~~ | ~~HIGH~~ | ~~Raw IP storage (GDPR)~~ — **RESOLVED** (pseudonymized) |
| ~~BE-008~~ | ~~Security~~ | ~~HIGH~~ | ~~`document.file_url` missing XSS validation~~ — **RESOLVED** |
| ~~BUILD-001~~ | ~~Build~~ | ~~HIGH~~ | ~~`vite.config.production.js` references missing deps~~ — **RESOLVED** (deleted) |
| ~~A11Y-004~~ | ~~Accessibility~~ | ~~HIGH~~ | ~~`/admin/skills` dead link~~ — **RESOLVED** |
| ~~ERR-001~~ | ~~Error handling~~ | ~~HIGH~~ | ~~HomeView silently swallows API errors~~ — **RESOLVED** |
| ~~SEO-001~~ | ~~SEO~~ | ~~HIGH~~ | ~~Sitemap stale/wrong slugs~~ — **RESOLVED** (removed invalid UUID slugs, updated dates) |
| ~~DEAD-001~~ | ~~Dead code~~ | ~~MEDIUM~~ | ~~`imageOptimization.ts`~~ — **RESOLVED** (deleted) |
| ~~DEAD-002~~ | ~~Dead code~~ | ~~MEDIUM~~ | ~~`LazyImage.vue`~~ — **RESOLVED** (deleted) |
| ~~DEAD-003~~ | ~~Dead code~~ | ~~MEDIUM~~ | ~~`useScrollAnimations.ts`~~ — **RESOLVED** (deleted) |
| ~~DEAD-004~~ | ~~Dead code~~ | ~~MEDIUM~~ | ~~`errorHandler.ts` dead exports~~ — **RESOLVED** (stripped to `getUserMessage` only) |
| ~~CI-010~~ | ~~CI/CD~~ | ~~MEDIUM~~ | ~~No SHA-pinned actions~~ — **RESOLVED** (all 17+ refs pinned) |
| ~~CI-011~~ | ~~CI/CD~~ | ~~MEDIUM~~ | ~~Vercel token as CLI arg~~ — **RESOLVED** (moved to env var) |
| ~~CI-012~~ | ~~CI/CD~~ | ~~MEDIUM~~ | ~~Node 22 vs 24 mismatch~~ — **RESOLVED** |
| ~~CI-013~~ | ~~CI/CD~~ | ~~MEDIUM~~ | ~~E2E skipped on push to main~~ — **RESOLVED** |
| ~~CI-014~~ | ~~CI/CD~~ | ~~MEDIUM~~ | ~~Trivy no checksum verification~~ — **RESOLVED** |
| ~~CI-015~~ | ~~CI/CD~~ | ~~MEDIUM~~ | ~~Deploy gate fires on skipped~~ — **RESOLVED** |
| ~~CI-016~~ | ~~CI/CD~~ | ~~MEDIUM~~ | ~~Dockerfile root + tests in image~~ — **RESOLVED** |
| ~~BE-009~~ | ~~Backend~~ | ~~MEDIUM~~ | ~~List endpoints unbounded~~ — **WON'T FIX** (portfolio data < 20 items; analytics bounded by `days` param + LIMIT) |
| ~~BE-010~~ | ~~Backend~~ | ~~MEDIUM~~ | ~~PageView missing indexes~~ — **RESOLVED** |
| ~~BE-011~~ | ~~Backend~~ | ~~MEDIUM~~ | ~~Startup migration logic~~ — **RESOLVED** (extracted to scripts/migrate_data.py) |
| ~~BE-012~~ | ~~Backend~~ | ~~MEDIUM~~ | ~~validate_safe_url duplicated~~ — **RESOLVED** (extracted to `_validators.py`) |
| ~~BE-013~~ | ~~Backend~~ | ~~MEDIUM~~ | ~~Contact model unused~~ — **RESOLVED** (deleted) |
| ~~BE-014~~ | ~~Backend~~ | ~~MEDIUM~~ | ~~No Alembic migrations~~ — **RESOLVED** (alembic init + sync migration + run_migrations removed) |
| ~~TYPE-001~~ | ~~Code quality~~ | ~~MEDIUM~~ | ~~AnalyticsService dual isEnabled~~ — **RESOLVED** |
| ~~ERR-002~~ | ~~Error handling~~ | ~~MEDIUM~~ | ~~Duplicate error handler setup~~ — **RESOLVED** (by DEAD-004) |
| ~~A11Y-005~~ | ~~Accessibility~~ | ~~MEDIUM~~ | ~~ExperienceDetail navbar toggler aria~~ — **RESOLVED** |
| ~~A11Y-006~~ | ~~Accessibility~~ | ~~MEDIUM~~ | ~~`<main>` landmark during loading~~ — **RESOLVED** |
| ~~A11Y-007~~ | ~~Accessibility~~ | ~~MEDIUM~~ | ~~Progress bar ARIA~~ — **RESOLVED** |
| ~~CSS-002~~ | ~~CSS~~ | ~~MEDIUM~~ | ~~Hardcoded rgba in gradients~~ — **RESOLVED** (CSS vars) |
| ~~BUILD-002~~ | ~~Build~~ | ~~MEDIUM~~ | ~~`tsconfig.node.json` wrong include~~ — **RESOLVED** |
| ~~SEO-002~~ | ~~SEO~~ | ~~MEDIUM~~ | ~~dateModified hardcoded~~ — **RESOLVED** (updated to 2026-04-09) |
| ~~SEO-003~~ | ~~SEO~~ | ~~MEDIUM~~ | ~~No SSR head tags per route~~ — **RESOLVED** (useHead from @unhead/vue) |
| ~~BE-015~~ | ~~Backend~~ | ~~LOW-MED~~ | ~~gunicorn worker count~~ — **RESOLVED** (WORKERS documented in .env.example) |
| ~~CI-017~~ | ~~CI/CD~~ | ~~LOW-MED~~ | ~~Vercel CLI @latest~~ — **RESOLVED** (pinned to 44.4.0) |
| ~~CI-005~~ | ~~CI/CD~~ | ~~LOW~~ | ~~Dependency-review job requires Dependency Graph enabled~~ — **RESOLVED** (2026-05-20 verified working on Dependabot PR run 26007931782: action enumerates deps, runs Scorecard, reports "no vulnerable packages") |
| ~~CI-022~~ | ~~CI/CD~~ | ~~LOW~~ | ~~Deploy gating: deploy-frontend.yml + deploy-backend.yml run in parallel with ci-cd.yml~~ — **RESOLVED** (2026-05-20 inlined both deploys as gated jobs in ci-cd.yml; standalone workflows deleted) |
| ~~CI-023~~ | ~~CI/CD~~ | ~~LOW~~ | ~~Lighthouse job runs every push but scores have never been reviewed~~ — **RESOLVED** (2026-05-14 reviewed run 25863731084; medians 97/96/96/100; tightened `lighthouserc.json` — script-size + total-size + best-practices promoted to error; spawned PERF-004 for the unused-JS opportunity surfaced during review) |
| PERF-004 | Performance | LOW | ~~three.js: tree-shaken via static named imports (181KB→120KB gzip, -34%)~~; gsap deferred — no clean tree-shake path without swapping libraries |
| ~~SEC-002~~ | ~~Security~~ | ~~LOW~~ | ~~Run `/security-review` against the last ~3 weeks of changes~~ — **RESOLVED** (2026-05-14 manual pass over commits since 2026-04-23; spawned SEC-003/004/005, three lower-priority findings noted inline) |
| ~~SEC-003~~ | ~~Security~~ | ~~MEDIUM~~ | ~~Auth tokens dual-stored in localStorage **and** HTTP-only cookies~~ — **RESOLVED** (2026-05-14, with SEC-004) |
| ~~SEC-004~~ | ~~Security~~ | ~~MEDIUM~~ | ~~`/auth/refresh` returns tokens in JSON body~~ — **RESOLVED** (2026-05-14, with SEC-003) |
| SEC-005 | Security | LOW-MED | ~~Visitor IP hashed with unsalted SHA-256~~ — **Part A RESOLVED** (2026-05-17, HMAC-SHA256 keyed on SECRET_KEY); Part B (raw IP to ipapi.co) still open pending disclosure-vs-self-host decision — concrete numbers below |
| ~~CSP-001~~ | ~~Security~~ | ~~LOW~~ | ~~Backend CSP allows `cdn.jsdelivr.net`~~ — **RESOLVED** (2026-05-20 disabled `/docs`/`/redoc`/`openapi.json` in prod + tightened CSP) |
| ~~DEAD-005~~ | ~~Dead code~~ | ~~LOW~~ | ~~Skills API services unused~~ — **RESOLVED** (deleted) |
| ~~DEAD-006~~ | ~~Dead code~~ | ~~LOW~~ | ~~Zod validation utilities dead~~ — **RESOLVED** (deleted) |
| ~~DEAD-007~~ | ~~Dead code~~ | ~~LOW~~ | ~~Vite scaffold leftovers~~ — **RESOLVED** (deleted) |
| ~~BUILD-003~~ | ~~Build~~ | ~~LOW~~ | ~~workbox-window unused devDep~~ — **RESOLVED** (removed) |
| ~~PKG-001~~ | ~~Package~~ | ~~LOW~~ | ~~@types/three in prod deps~~ — **RESOLVED** (moved to devDeps) |
| ~~A11Y-008~~ | ~~Accessibility~~ | ~~LOW~~ | ~~Section icon redundant alt~~ — **RESOLVED** (alt="") |
| ~~SEO-004~~ | ~~SEO~~ | ~~LOW~~ | ~~Missing og:image:alt~~ — **RESOLVED** |
| ~~BE-016~~ | ~~Backend~~ | ~~LOW~~ | ~~visitors endpoint no response_model~~ — **RESOLVED** |
| ~~BE-017~~ | ~~Backend~~ | ~~LOW~~ | ~~metrics response_model=dict~~ — **RESOLVED** |
| ~~BE-018~~ | ~~Backend~~ | ~~LOW~~ | ~~Documents endpoints no rate limiting~~ — **RESOLVED** |
| ~~BE-019~~ | ~~Backend~~ | ~~LOW~~ | ~~PageView nullable constraints~~ — **RESOLVED** |
| ~~CI-020~~ | ~~CI/CD~~ | ~~LOW~~ | ~~SSG build pre-renders only `/`~~ — **RESOLVED** (fallback API URL points to production `dashti.se` so Vercel/CI builds enumerate real `/experience/:id` routes) |
| ~~BE-020~~ | ~~Backend~~ | ~~HIGH~~ | ~~GitHub endpoints missing response_model~~ — **RESOLVED** (4 endpoints, new `schemas/github.py`) |
| ~~BE-021~~ | ~~Backend~~ | ~~HIGH~~ | ~~Unused to_dict() methods on 4 models~~ — **RESOLVED** (Project, Company, Skill, PageView) |
| ~~BE-022~~ | ~~Backend~~ | ~~MEDIUM~~ | ~~f-string logging (10 call sites)~~ — **RESOLVED** (lazy % formatting) |
| ~~BE-023~~ | ~~Backend~~ | ~~MEDIUM~~ | ~~python-json-logger installed but unused~~ — **RESOLVED** (removed from deps) |
| ~~FE-001~~ | ~~Frontend~~ | ~~MEDIUM~~ | ~~innerHTML in useGsapAnimations~~ — **RESOLVED** (replaced with createElement/textContent) |
| ~~SEC-001~~ | ~~Security~~ | ~~HIGH~~ | ~~CSP script-src has unnecessary `https://*.sentry.io`~~ — **RESOLVED** (removed; Sentry bundled via npm, only connect-src needed) |
| ~~CSS-003~~ | ~~CSS~~ | ~~MEDIUM~~ | ~~11x `!important` in portfolio.css~~ — **WON'T FIX** (Bootstrap defines `.bg-light`/`.bg-dark` with `!important`, so overrides must too; replaced hardcoded hex colors with CSS variables) |
| ~~BE-024~~ | ~~Backend~~ | ~~LOW~~ | ~~Bare `except Exception` in health/database~~ — **WON'T FIX** (health checks and session cleanup correctly catch any exception type) |
| ~~FE-002~~ | ~~Frontend~~ | ~~LOW~~ | ~~13 components have zero unit tests~~ — **RESOLVED** (10 new test files, 77 new tests; suite grew 520→597) |
| ~~FE-003~~ | ~~Frontend~~ | ~~MEDIUM~~ | ~~AdminProjects CRUD not implemented~~ — **RESOLVED** (2026-05-04 mirrors AdminCompanies pattern: list/create/edit/delete + featured toggle + company FK dropdown; 20 new tests) |
| FE-004 | Frontend | LOW | ~~GitHubStats~~, ~~admin trio scaffolding~~, ~~AdminDashboard~~ done. Remaining: ExperienceDetail (538), and form-field extractions for the admin trio if you want them under 500 — both diminishing returns |
| ~~FE-005~~ | ~~Frontend~~ | ~~LOW~~ | ~~Plausible/Umami helpers never called~~ — **RESOLVED** (2026-05-07 deleted `utils/analytics.ts`, `composables/useAnalytics.ts`, their tests, the `VITE_ANALYTICS_*` env vars, and tightened CSP — `plausible.io`/`umami.is` no longer allowed) |
| ~~FE-006~~ | ~~Frontend~~ | ~~LOW~~ | ~~Tighten remaining `any` usages~~ — **RESOLVED** (2026-05-08 audit found zero `any` types in `src/`; the 56 in `tests/` are legitimate mock scaffolding. Earlier refactors had quietly cleaned up the source-side `any`s.) |
| ~~BE-025~~ | ~~Backend~~ | ~~MEDIUM~~ | ~~PageView `country` never populated~~ — **RESOLVED** (ipapi.co lookup with 24h in-process cache, graceful failure) |
| ~~BE-026~~ | ~~Backend~~ | ~~LOW~~ | ~~Audit FK cascade-delete behaviour~~ — **RESOLVED** (2026-05-02 audit found only one FK in the entire model layer, already correctly configured; added SQLite FK enforcement to test conftest + cascade-delete regression test) |
| ~~CI-021~~ | ~~CI/CD~~ | ~~LOW~~ | ~~No coverage threshold enforced~~ — **RESOLVED** (2026-05-02 baseline 78%/86% baked as floors with ~2pp headroom; stricter per-glob gates for `src/api/` + `src/stores/`) |

---

## Campaign 2026-06: Performance, Backend, Admin Interfaces

Multi-sprint campaign seeded by a 12-dimension block-by-block audit on 2026-06-07
(workflow `wf_0852eca2-522`). 130 raw findings → 6 sprints, 13 deferred/dropped.
Audit summary: 4 critical (OAuth admin fail-open, JSON log formatter drops every
`extra={}` field, Fly volume mounted but unused, untested router auth guard),
25 high, 44 medium, 50 low, 7 nit. Direction: no new outward-facing features;
focus is performance, backend correctness, observability, and admin interfaces.

**Sprint 1 — Hygiene sweep** ✅ **SHIPPED 2026-06-07** (commits `de8b8f3` + GitHub/Education endpoint deletions). 15 items, -2034 LOC net first commit, plus DEAD-07/08 in follow-up. 646 backend tests pass at 85.52%; 550 frontend tests pass.

| ID | Summary | Status |
|----|---------|--------|
| BACKEND-DEAD-01 | Delete unused `cleanup_expired_states` | ✅ done |
| BACKEND-DEAD-02 | Drop `ANALYTICS_SITE_ID`/`ANALYTICS_URL` settings | ✅ done |
| BACKEND-DEAD-03 | Remove `rate_limit_strict` + `RATE_LIMIT_STRICT` | ✅ done |
| BACKEND-DEAD-04 | Drop password helpers + `bcrypt` dep | ✅ done |
| BACKEND-DEAD-07 | Delete 3 unused GitHub endpoints | ✅ done (orphaned service methods `get_project_stats`/`get_repo_details`/`get_repo_commits` deferred — see DEAD-07b) |
| BACKEND-DEAD-08 | Delete `/degrees` + `/certifications` | ✅ done |
| BACKEND-DEAD-09 | Remove `/api/health` and `/api/v1/test` duplicates | ✅ done |
| FRONTEND-DEAD-06 | Delete unused `LoadingSpinner.vue` | ✅ done |
| FRONTEND-DEAD-07 | Delete unused `ProjectCard.vue` | ✅ done |
| FRONTEND-DEAD-02 | Delete `useMicroInteractions` (all 5 exports unused) | ✅ done (entire file deleted) |
| FRONTEND-DEAD-03 | Prune `useGsapAnimations` to single used export | ✅ done |
| FRONTEND-DEAD-04 | Delete `utils/storage.ts` | ✅ done |
| FRONTEND-DEAD-05 | Remove dead auth store actions | ✅ done |
| FRONTEND-TESTS-11 | Delete stale duplicate `NavBar.test.ts` | ✅ done |
| FRONTEND-TESTS-10 | Update MEMORY.md | ✅ done |

**Sprint 1 follow-ups identified during execution:**

- **DEAD-07b** (LOW, deferred): `github_service.py` carries three now-orphaned methods (`get_project_stats`, `get_repo_details`, `get_repo_commits`) plus their unit-test classes in `test_github_service.py`. Deleted alongside endpoints would have created significant test churn (>200 lines across multiple classes); deferring as a focused follow-up.
- **CONTENT-001** (HIGH, ✅ done): dashti.se experience card showed "Security Specialist & System Developer / Sep 2022 - Present" — wrong title and start date. Root cause: HomeView.vue's static fallback was stale and the live SSG build is rendering it because the production API fetch is failing (see INFRA-002 below). Updated the fallback to match the resume (Hermes May 2024 - present, QA/RA & Security Specialist + Philips 2022-2024 + Karolinska 2021); added an education fallback that includes Security+ (Jan 2026). Job-search liability resolved.
- **INFRA-002** (HIGH, partially addressed): The SSG build at Vercel is shipping empty `__INITIAL_STATE__.pinia.portfolio.companies/skills/projects/education` arrays — meaning the `includedRoutes()` and pre-render fetches against the production API are failing silently. Sprint 2's INFRA-CONFIG-01 fix (wiring `DATABASE_URL` to the Fly volume) likely resolves part of this: previously every redeploy wiped the production DB to empty, so even when SSG did reach the API it got empty arrays back. After deploy, verify whether the SSG `__INITIAL_STATE__` populates; if it still doesn't, investigate `VITE_API_URL` in Vercel + whether the backend is reachable from Vercel's build environment + whether `includedRoutes` swallows fetch errors.
- **INFRA-003** (MEDIUM, open): Long-term OAuth domain alignment — host the backend API at `api.dashti.se` instead of `dashti-portfolio-backend.fly.dev` so the frontend (`dashti.se`) and backend share the registrable domain. With same-eTLD+1, cookies can return to `SameSite=Lax` (Sprint 2 ships `SameSite=None+Secure` as a short-term fix). Requires DNS work (Cloudflare or wherever DNS is hosted) + Fly cert provisioning for `api.dashti.se`. Estimated ~1-2 hours; not blocking anything.

**Sprint 2 — Security & correctness** ✅ **SHIPPED 2026-06-08**. 10 items + new `refresh_tokens` table + 2 alembic migrations + 5 new auth test cases. 648 backend tests pass at 84.83% coverage.

| ID | Summary | Status |
|----|---------|--------|
| BACKEND-BUGS-01 | OAuth admin gate fails closed when `ADMIN_GITHUB_ID` unset (503); `is_admin` derived from the gate not hardcoded | ✅ done |
| BACKEND-BUGS-03 | `CacheControlMiddleware` now defaults to `private, no-store + Vary: Cookie, Authorization` for API responses; explicit allowlist of anonymous-read prefixes (`/projects`, `/companies`, `/skills`, `/education`, `/documents`, `/github/stats`, `/health`) | ✅ done |
| BACKEND-BUGS-04 | `_auth_cookie_kwargs()` helper centralises cookie attrs: `SameSite=None+Secure` in production (dashti.se ↔ *.fly.dev), `SameSite=Lax` in dev/test where HTTP is OK | ✅ done |
| BACKEND-BUGS-05 | Logout `delete_cookie` mirrors the original Secure/SameSite/HttpOnly attrs; belt-and-braces explicit `max_age=0 set_cookie` follows | ✅ done |
| BACKEND-BUGS-07 | OAuth state consumption is now a single `DELETE ... RETURNING` that bundles state + expiry + IP-binding into one atomic WHERE clause | ✅ done |
| BACKEND-BUGS-02 | New `RefreshToken` model + alembic migration; `create_refresh_token` returns `(token, jti, exp)`; `/refresh` looks up jti server-side, detects revoked/expired reuse, revokes all of user's tokens on reuse; `/logout` revokes the presented jti | ✅ done |
| BACKEND-DB-04 | `User.is_admin` now `nullable=False, server_default=sa.false()` + alembic migration backfills `NULL → False` | ✅ done |
| BACKEND-BUGS-06 | `BodySizeLimitMiddleware` falls back to a streaming byte counter when `Content-Length` is missing/invalid (chunked-encoding bypass closed) | ✅ done |
| BACKEND-BUGS-08 | `github_service.get_repo_commits` now uses `datetime.now(UTC)` and explicit `Z` ISO suffix; window no longer drifts by local UTC offset | ✅ done |
| INFRA-CONFIG-01 | `DATABASE_URL = sqlite+aiosqlite:////data/portfolio.db` added to fly.toml `[env]` — DB now persists across deploys (was on ephemeral container FS) | ✅ done |

**Sprint 3 — Observability & DB foundations** ✅ **SHIPPED 2026-06-10**. 13 items + 1 new alembic migration (idempotent per DB-07) + 3 new logger tests + 3 new request-ID propagation tests. 657 backend tests pass at 84.92% coverage.

| ID | Summary | Status |
|----|---------|--------|
| BACKEND-OBSERVABILITY-01 | `CustomJsonFormatter` now serialises every `extra={}` field (and Filter-injected attribute) onto the top-level JSON object; reserved LogRecord attrs guarded against; non-JSON-native values fall back to `repr()` | ✅ done |
| BACKEND-OBSERVABILITY-05 | Per-request correlation ID via `request_id_var: ContextVar`. `LoggingMiddleware` accepts an upstream `X-Request-ID` (whitelisted `[A-Za-z0-9_-]{1,64}` against log injection) and mints a UUID otherwise; `RequestIdFilter` auto-injects the value onto every emitted record so call sites don't need explicit `extra=` | ✅ done |
| BACKEND-OBSERVABILITY-02 | Sentry init now passes explicit `integrations=[Starlette, FastApi, Sqlalchemy, Httpx, Asyncio]` — deterministic across SDK versions and visible in code review | ✅ done |
| BACKEND-OBSERVABILITY-04 | `ErrorTrackingMiddleware._capture_to_sentry()` belt-and-braces fires `sentry_sdk.capture_exception` on every 5xx HTTPException and every unhandled exception with `request_id`/`method`/`path` tags; `track_error()` helper also captures with extras as scope context | ✅ done |
| BACKEND-OBSERVABILITY-03 | SQLAlchemy `before_cursor_execute`/`after_cursor_execute` event listeners log a structured `slow_query=true` line at WARNING for queries exceeding `SLOW_QUERY_THRESHOLD_MS` (default 250ms); SQL preview truncated at 500 chars; new `DB_STATEMENT_TIMEOUT_MS` setting (default 5s) wires `statement_timeout` through asyncpg `server_settings` in Postgres (silently no-op on SQLite) | ✅ done |
| BACKEND-PERF-02 | `OAuthState.expires_at` indexed; the periodic `cleanup_oauth_states_periodically()` 5-min sweep no longer scans the full table | ✅ done |
| BACKEND-PERF-03 | Composite `ix_page_views_(created_at, page_path)` and `ix_page_views_(created_at, country)` — both analytics aggregation queries in `app/api/v1/analytics.py` now drive their WHERE+GROUP-BY off an index | ✅ done |
| BACKEND-DB-01 | `server_default=func.now()` added to `users.updated_at`, `companies.updated_at`, `projects.updated_at` — INSERTs now populate the column instead of leaving it NULL until first UPDATE | ✅ done |
| BACKEND-DB-02 | `Education.is_certification` indexed — small index, but the public listing splits on this column on every page load | ✅ done |
| BACKEND-DB-06 | `OAuthState.created_at` gets `server_default=func.now()` alongside its existing Python-side `default=` — out-of-band INSERTs are now correct | ✅ done |
| BACKEND-DB-05 | `User.github_id` bounded to `String(20)`, `username` to `String(39)` (GitHub policy max), `email` to `String(254)` (RFC 5321), `name` to `String(255)`, `avatar_url` to `String(500)` — prevents accidental multi-MB inserts on Postgres | ✅ done |
| BACKEND-DB-07 | New `c3f1d96a4b27_sprint_3_schema.py` is fully idempotent via `_create_index_if_absent` / `_drop_index_if_present` / column existence guards driven by the SQLAlchemy inspector; safe to re-run against fresh DBs (where `Base.metadata.create_all` already created the indexes) and stamped DBs alike | ✅ done |
| BACKEND-DB-09 | Dropped redundant explicit `index=True` from `OAuthState.state`, `Education.id`, `Document.id` — all are PKs and the implicit PK index was duplicated by Postgres as a second btree | ✅ done |

**Sprint 4 — Backend performance** ✅ **SHIPPED 2026-06-10**. 9 backend + 3 frontend items. 657 backend tests pass at 84.74% coverage; 550 frontend tests pass.

| ID | Summary | Status |
|----|---------|--------|
| BACKEND-PERF-07 | `LoggingMiddleware` skips request/response log pairs for `/api/v1/health*` + `/api/health` (Fly's load balancer polls every few seconds; was ~80% of log volume). Failures still log, X-Request-ID still set/returned. | ✅ done |
| BACKEND-PERF-06 | Dropped `threading.Lock` from `PerformanceMetrics` — async event loop has no true concurrency inside a worker, dict/deque ops are GIL-atomic, and gunicorn workers are separate processes (need redis for cross-worker, not a lock). Removes lock-acquire on every request. | ✅ done |
| BACKEND-PERF-05 | `PerformanceMetrics` now keys by **templated** route (`GET /api/v1/companies/{company_id}`) instead of resolved URL — 100 GETs against `/companies/abc`, `/companies/def`… now aggregate to one stat row. Resolved via `request.scope["app"].router.routes` walk inside the metrics middleware. | ✅ done |
| BACKEND-OBSERVABILITY-06 | `get_stats()` now also returns `p50`/`p95`/`p99` per endpoint (linear-interpolation percentile matching NumPy default) computed on-demand from the bounded response-time deque. New `metrics.incr("name")` for business counters exposed under `counters` in the schema. | ✅ done |
| BACKEND-OBSERVABILITY-09 | `rate_limit_exceeded_handler` bumps `rate_limit.hits` + `rate_limit.hits.{method}` counters so admins can see rate-limit pressure on `/metrics` without grepping logs. Lazy import to dodge the middleware circular. | ✅ done |
| BACKEND-PERF-01 | `track_pageview` no longer awaits the `ipapi.co` lookup — it inserts the row with `country=NULL` and schedules a `BackgroundTask` to back-fill. Response goes from ~150-1500ms tail latency to pure-DB ~5ms. The analytics aggregations filter `country IS NOT NULL` so the back-fill window only misses geo aggregation, not visit count. | ✅ done |
| BACKEND-PERF-04 | `get_portfolio_stats(username)` is now cached per-username for 300s in-process; per-username `asyncio.Lock` collapses cache-miss stampede. Cuts a 3-5 round-trip GitHub fan-out to one fetch per 5 min per username. | ✅ done |
| BACKEND-PERF-10 | Shared module-level `httpx.AsyncClient` for OAuth callback (`get_oauth_client()`); lazy-init on first call, closed in app lifespan shutdown. The two round-trips (token exchange + user info) now reuse the TLS session, ~200ms median saving on the round-trip. | ✅ done |
| BACKEND-PERF-08 | Optional `limit`/`offset` query params (1-100, default 100; 0) on `/api/v1/companies`, `/projects`, `/skills`, `/education`. Centralised in `app/core/db_helpers.py::Pagination` + `pagination_params`. Non-breaking — defaults preserve current single-page behaviour. | ✅ done |
| FRONTEND-PERF-04 | Added explicit `width`/`height` to `card-logo` (64×64) and `section-icon` (32×32) `<img>` tags in HomeView — browser reserves the box before image load, eliminating CLS shift. | ✅ done |
| FRONTEND-PERF-07 | Replaced four `<i class="bi bi-*">` tags in `ExperienceDetail.vue` with inline Bootstrap-Icons SVGs (geo-alt, calendar, globe, arrow-left). Fixes a latent rendering bug — `bootstrap-icons` was never bundled, so the icons were invisible — and locks the icon source into the chunk. | ✅ done |
| FRONTEND-PERF-08 | Deleted unused 854KB `public/images/profile.png`; swapped the `<picture>` fallback `<img>` src to `/images/optimized/cropped.png` (343KB). ~97% of clients hit AVIF/WebP branches above so this is the rare-fallback path; still applies to Lighthouse's total-payload budget. | ✅ done |

**Sprint 5 — Admin console part 1** (3 sessions). Skills, Metrics, Errors UIs +
admin bug cluster.

| ID | Summary | Effort |
|----|---------|--------|
| BACKEND-ADMIN-02 | Add `AdminEducation` to admin nav | xs |
| BACKEND-ADMIN-01 | Build `AdminSkills.vue` (backend CRUD already exists) | m |
| BACKEND-ADMIN-03 | Build `AdminMetrics.vue` | m |
| ~~BACKEND-ADMIN-05~~ | ~~Frontend-errors persistence~~ — **DROPPED** (covered by Sprint 3 BACKEND-OBSERVABILITY-04 wiring Sentry properly per Q4 decision) | — |
| FRONTEND-BUGS-01 | `isSaving` guard on admin Save buttons | s |
| FRONTEND-BUGS-11 | `deletingIds` guard on `AdminCompanies` delete | xs |
| FRONTEND-BUGS-02 | Client-side validation on `AdminEducation` form | s |
| FRONTEND-BUGS-03 | Fix `AdminEducation` `order` → `order_index` field name | xs |
| FRONTEND-BUGS-04 | Disable `GitHubStats` Retry button while loading | xs |
| FRONTEND-BUGS-07 | Fix `useFocusTrap` + `AdminFormModal` watcher | xs |
| BACKEND-ADMIN-07 / FRONTEND-TESTS-01 | `AdminAnalytics.spec.ts` (combined) | m |

**Sprint 6 — Admin part 2 + frontend perf + test backfill** (3 sessions).

| ID | Summary | Effort |
|----|---------|--------|
| ~~BACKEND-ADMIN-06~~ | ~~Audit log + admin browser~~ — **DEFERRED** per Q5 decision (single-operator site) | — |
| ~~BACKEND-ADMIN-09~~ | ~~Sessions admin~~ — **DEFERRED** per Q5 decision (revoke infra in Sprint 2 is enough) | — |
| BACKEND-ADMIN-04 | Documents admin CRUD + upload UI | l |
| BACKEND-ADMIN-10 | Sentry deep-link panel on dashboard | s |
| FRONTEND-TESTS-02 | Router auth guard unit tests | m |
| FRONTEND-TESTS-03 | E2E admin login/refresh/logout | l |
| FRONTEND-TESTS-04 | E2E admin CRUD round-trip | l |
| FRONTEND-PERF-01 | Slim Bootstrap CSS — **scope tight** per Q6 (drop unused utilities only, no SCSS rewrite) | s |
| ~~FRONTEND-PERF-02~~ | ~~Replace three.js hero~~ — **DEFERRED (sacred cow)** per Q7 decision; lazy-loaded, off critical path | — |
| FRONTEND-PERF-03 | Replace gsap entrance animations with IntersectionObserver | m |
| FRONTEND-BUGS-05 | Fix `useGsapBatchAnimation` global kill bug | s |
| FRONTEND-BUGS-06 | Fix portfolio store parallel-fetch error overwrite | s |
| FRONTEND-DEAD-01 | Decide `api/services.ts`: migrate admin views or delete | s |
| BACKEND-TESTS-01 | OAuth state IP-binding mismatch test | s |
| BACKEND-TESTS-02 | OAuth state TTL expiry + cleanup tests | s |
| BACKEND-TESTS-04 | `validate_safe_url` XSS schema tests | s |
| BACKEND-TESTS-05 | Non-admin escalation tests on PUT/PATCH | s |
| BACKEND-TESTS-10 | Fix `seed_data` 0% coverage (pytest-asyncio fixture) | m |

**Deferred / dropped** (13 items): rate-limit override admin (speculative),
multi-user management (single-operator YAGNI), `geo_ip` O(n log n) eviction (nit),
TruffleHog base-SHA edge case (theoretical), MapEmbed + NavBar a11y nits
(roll into general a11y pass if/when), respx contract test (duplicative),
unicode round-trip test (no specific risk), real axios round-trip via msw
(duplicative), `unhead` direct dep removal (SSG peer-chain risk > savings),
path-filter optimisation for security scans (CI minute saving not constraining).

**Open questions resolved 2026-06-07** (decisions affect Sprints 2-6):

| Q | Decision |
|---|---|
| Documents admin | **Build full upload UI** (Sprint 6 BACKEND-ADMIN-04 stays in scope) |
| GitHub endpoints | **Delete** (shipped in Sprint 1 follow-up) |
| Education `/degrees` + `/certifications` | **Delete** (shipped in Sprint 1 follow-up) |
| Frontend errors | **Wire Sentry properly** (BACKEND-ADMIN-05 dropped from Sprint 5; covered by Sprint 3's BACKEND-OBSERVABILITY-04) |
| Audit log (ADMIN-06) | **Defer indefinitely** (single-operator site; revisit on delegation/abuse) |
| Sessions admin (ADMIN-09) | **Defer indefinitely** (Sprint 2's revoke infra is what matters; UI is sugar) |
| Bootstrap CSS | **Scope tight** — drop only unused utilities (~30-50KB), no SCSS rewrite |
| three.js hero | **Sacred cow** — leave it (already lazy-loaded, off critical path, 61KB already shaved via PERF-004) |
| Fly volume | **Open** — defer decision to when INFRA-CONFIG-01 is picked up in Sprint 2; will choose SQLite-on-volume vs managed Postgres then |
| OAuth domain | **Open** — defer to Sprint 2 BACKEND-BUGS-04 pick-up (short-term `SameSite=None+Secure` vs `api.dashti.se` long-term) |
| Admin nav order | **Open** — defer to Sprint 5 build (decide when AdminSkills/AdminMetrics land) |

---

## CI/CD

### CI-007: `build:ssg` never runs in any workflow or Vercel config
**Files:** `.github/workflows/ci-cd.yml:81,152,256`, `.github/workflows/deploy-frontend.yml:51`, `frontend/vercel.json:2`
**Priority:** CRITICAL
**Status:** RESOLVED (2026-03-30) — also fixed `sessionStorage` SSR guard in `services/analytics.ts`

EVAL-001 (commit `ccef203`) implemented vite-ssg with `includedRoutes()` for pre-rendering public
routes. But every CI/CD touchpoint still runs `npm run build` (plain SPA), not `npm run build:ssg`:

- `ci-cd.yml:81` (frontend-quality): `npm run build`
- `ci-cd.yml:152` (e2e): `npm run build`
- `ci-cd.yml:256` (lighthouse): `npm run build`
- `deploy-frontend.yml:51`: `npm run build`
- `vercel.json:2`: `"buildCommand": "npm run build"`

The deployed site is a blank SPA shell — search engines get `<div id="app"></div>`, no pre-rendered
HTML, no SEO benefit. The entire SSG implementation is inert.

**Fix:** Replace `npm run build` with `npm run build:ssg` in all five locations. Note: `build:ssg`
requires the backend API to be reachable at build time for `includedRoutes()` to enumerate
`/experience/:id` paths (graceful fallback already exists in `main.ts:142-146`).

---

### CI-008: `deploy-backend.yml` test job missing `requirements-dev.txt`
**Files:** `.github/workflows/deploy-backend.yml:28-34`
**Priority:** CRITICAL
**Status:** RESOLVED (2026-03-31)

Line 29 installs only `requirements.txt`:
```yaml
pip install -r requirements.txt
```

`pytest`, `pytest-cov`, `pytest-asyncio`, `aiosqlite` are in `requirements-dev.txt` only. The test
step (`pytest --cov=app`) at line 34 fails with `ModuleNotFoundError`. The `test` job always fails,
blocking `deploy` on every push to `main` affecting `backend/**`.

The main `ci-cd.yml:114` correctly installs both files.

**Fix:** Change to `pip install -r requirements.txt -r requirements-dev.txt`.

---

### CI-009: Action versions reference non-existent tags
**Files:** `.github/workflows/ci-cd.yml:58,105,286`, `.github/workflows/deploy-frontend.yml:22,64`
**Priority:** HIGH

Several actions use version tags that don't exist yet:
- `actions/setup-node@v6` (current latest: v4) — lines 58, 244 in ci-cd.yml; lines 22, 64 in deploy-frontend.yml
- `actions/setup-python@v6` (current latest: v5) — line 105 in ci-cd.yml
- `actions/download-artifact@v7` (current latest: v4) — line 286 in ci-cd.yml

GitHub Actions silently falls back to the most recent available version when a tag doesn't exist,
making the resolved version unpredictable and potentially different from what's tested.

**Fix:** Pin to actual existing versions (e.g., `@v4` for setup-node, `@v5` for setup-python,
`@v4` for download-artifact) and ideally pin to full commit SHAs.

---

### CI-010: No actions are SHA-pinned — supply chain risk
**Files:** All four workflow files
**Priority:** MEDIUM

Every action reference across all workflows uses a mutable version tag (`@v4`, `@v6`, `@v12`,
`@1.5`), not an immutable commit SHA. As demonstrated by the Trivy incident (CI-001) and the
March 2025 `tj-actions/changed-files` attack, force-pushing a tag is the primary supply chain
attack vector.

17+ action references across four files are affected. `MishaKav/pytest-coverage-comment@v1.7.1`
has a SHA in a comment but the `@` reference still uses the mutable tag.

**Fix:** Resolve each tag to its current SHA and use `@<sha> # tag` format. Dependabot's
`github-actions` ecosystem will still open PRs for updates.

---

### CI-011: Vercel token passed as CLI argument
**Files:** `.github/workflows/deploy-frontend.yml:74`
**Priority:** MEDIUM

```yaml
run: vercel deploy --prod --token=${{ secrets.VERCEL_TOKEN }}
```

Token visible in process list and potentially in verbose logs. The Vercel CLI supports the
`VERCEL_TOKEN` env var — `VERCEL_ORG_ID` and `VERCEL_PROJECT_ID` already use the `env:` pattern.

**Fix:** Move token to env block: `env: VERCEL_TOKEN: ${{ secrets.VERCEL_TOKEN }}`.

---

### CI-012: Node.js version mismatch between CI and deploy
**Files:** `.github/workflows/deploy-frontend.yml:24,66`, `.github/workflows/ci-cd.yml:21`
**Priority:** MEDIUM

`ci-cd.yml` uses `NODE_VERSION: '24'`. `deploy-frontend.yml` hardcodes `node-version: '22'`.
The app is tested on Node 24 but deployed on Node 22.

**Fix:** Align to a single version. Use `.nvmrc` or `engines.node` in `package.json`.

---

### CI-013: E2E tests skipped on direct push to `main`
**Files:** `.github/workflows/ci-cd.yml:135`
**Priority:** MEDIUM

```yaml
if: github.event_name == 'pull_request'
```

If a direct push to `main` bypasses PRs, E2E tests never run but deploy proceeds.

**Fix:** Either run E2E on push to `main` as well, or ensure branch protection blocks direct pushes.

---

### CI-014: Trivy binary download has no checksum verification
**Files:** `.github/workflows/ci-cd.yml:193-197`
**Priority:** MEDIUM

The Trivy binary is downloaded via `curl` without verifying against Aqua's published checksums.
A MITM or CDN compromise would execute arbitrary code.

**Fix:** Download `trivy_${VERSION}_checksums.txt` alongside and run `sha256sum --check`.

---

### CI-015: Deploy gate fires when quality jobs are skipped
**Files:** `.github/workflows/ci-cd.yml:269-275`
**Priority:** MEDIUM

The deploy condition uses `always()` and checks for `failure`/`cancelled` but not `skipped`.
When a push to `main` changes only docs/config, quality jobs are skipped and deploy proceeds
without validation.

**Fix:** Add `!contains(needs.*.result, 'skipped')` or require explicit `success`.

---

### CI-016: Dockerfile runs as root; `tests/` copied into prod image
**Files:** `backend/Dockerfile`, `backend/.dockerignore`
**Priority:** MEDIUM

**Issue A:** No `USER` directive — container runs as UID 0 (root). Any RCE in the FastAPI app
has full container privileges.

**Issue B:** `.dockerignore` does not exclude `tests/` or `requirements-dev.txt`. Test files
(including mock credential strings) are copied into the production image.

**Fix:**
- Add `USER appuser` after creating a non-root user.
- Add `tests/`, `requirements-dev.txt`, `scripts/` to `.dockerignore`.

---

### CI-017: Vercel CLI installed as `@latest` (unpinned)
**Files:** `.github/workflows/deploy-frontend.yml:71`
**Priority:** LOW-MEDIUM

`npm install -g vercel@latest` resolves at runtime. A breaking CLI release could silently cause
deploy failures.

**Fix:** Pin to a specific version: `npm install -g vercel@44.4.0`.

---

### CI-021: No coverage threshold enforced in CI
**Files:** `frontend/vite.config.ts`, `backend/pyproject.toml`, `.github/workflows/ci-cd.yml`
**Priority:** LOW
**Status:** RESOLVED (2026-05-02)

Baselines captured at 78.18% (frontend, 589 tests) and 85.86% (backend, 660
tests). Floors baked at ~2pp below baseline:

- **Frontend** — `vite.config.ts` `test.coverage.thresholds`: 76 stmts /
  67 branches / 76 funcs / 77 lines globally; per-glob stricter floors for
  `src/api/**` and `src/stores/**`.
- **Backend** — `pyproject.toml` `[tool.pytest.ini_options].addopts` now
  includes `--cov-fail-under=83`.
- **CI** — removed the `|| echo "No tests found"` swallow on the backend
  test step in `ci-cd.yml`; pytest's non-zero exit now actually fails the
  job. The frontend job already runs `npm test -- --run --coverage`, which
  picks up the new vitest thresholds with no workflow change.

---

### CI-005: `dependency-review` job requires Dependency Graph enabled
**Files:** `.github/workflows/ci-cd.yml`
**Priority:** LOW
**Status:** RESOLVED (2026-05-20)

Verified by inspecting the job log for run 26007931782 (Dependabot PR
`da6ba905`, push event was the wrong query target — the job only fires on PRs
per its `if:` condition). The action successfully enumerated dependencies,
reported "Dependency review did not detect any vulnerable packages with
severity level high or higher", checked denied licenses, and ran the OpenSSF
Scorecard pass. Dependency Graph IS enabled in repo Settings — no toggle was
ever needed in this repo, the backlog item just predated the verification.

Also bumped `actions/dependency-review-action@v4` → v5.0.0 in the same
sweep because v4 runs on Node 20, which GitHub deprecates June 2, 2026.

---

### CI-020: Start backend service in CI for full SSG route pre-rendering
**Files:** `.github/workflows/ci-cd.yml`, `frontend/src/main.ts:126-150`
**Priority:** LOW
**Status:** Open — depends on CI-007 being resolved first
**Prerequisite:** CI-007

With CI-007 resolved, `build:ssg` runs in CI but the backend API is not available at build time.
`includedRoutes()` gracefully degrades — only `/` is pre-rendered; `/experience/:id` routes
fall back to SPA hydration at runtime. This is acceptable but leaves SEO value on the table for
experience detail pages.

**Option A (lightweight):** Add a `services:` container or `docker-compose up -d` step in the
`frontend-quality` and `lighthouse` jobs to start the backend with a seeded SQLite database.
`VITE_API_URL` would point to `http://localhost:8000`.

**Option B (decoupled):** A prior workflow step fetches company slugs from the production API
(or a staging endpoint) and writes them to a `routes.json` file. `includedRoutes()` reads from
this file instead of making a live API call. This avoids coupling the frontend build to backend
availability.

**Fix:** Choose an approach and implement. Option B is more resilient for Vercel builds (where
adding a backend service container is not possible).

---

### CI-022: Deploy workflows run in parallel with quality gates rather than after them
**Files:** `.github/workflows/ci-cd.yml`
**Priority:** LOW
**Status:** RESOLVED (2026-05-20)

**Final shape**: deploy workflows inlined into `ci-cd.yml` as two new jobs
(`deploy-frontend`, `deploy-backend`), each with explicit `needs:` chains:

- `deploy-frontend` needs `[changes, frontend-quality, e2e-tests, lighthouse]`,
  fires only when `changes.outputs.frontend == 'true'` and all three quality
  jobs succeed. Vercel CLI invocation unchanged.
- `deploy-backend` needs `[changes, backend-quality]`, fires only when
  `changes.outputs.backend == 'true'` and `backend-quality` succeeds. Fly
  CLI invocation unchanged.

The two standalone files (`deploy-frontend.yml`, `deploy-backend.yml`) are
deleted. No branch-protection updates needed (no `required_status_checks`
were configured against the old workflow names). No `workflow_dispatch`
loss in practice — both standalone workflows had **zero manual triggers**
in the last 30 runs.

The dormant `deploy:` job stub that was sitting in `ci-cd.yml` since the
beginning (just echoed "configure based on hosting provider") is now gone,
replaced by the two real jobs.

History below kept for context.

---

**Earlier partial resolution:**

Originally logged because three jobs did near-identical frontend work per push
(lint/type-check/unit-tests 2×, `build:ssg` 3×). It also surfaced that
`type-check` was only running in `deploy-frontend.yml`'s `test` job, so a
TypeScript error wouldn't fail the main `CI/CD Pipeline` — borderline
breakage, not just waste. The backend had the same shape: `deploy-backend.yml`
re-ran pytest in parallel with `ci-cd.yml`'s `backend-quality`.

**Resolved:**
- **bb16507** — deleted `deploy-frontend.yml`'s `test` job; added `Run type check` to `ci-cd.yml`'s `frontend-quality`. Lint, type-check, and unit-tests now run exactly once each (in `ci-cd.yml`), and type-check actually gates the main pipeline.
- **c925b94** — deleted `deploy-backend.yml`'s `test` job (its env vars weren't even consumed — conftest defines its own `TEST_DATABASE_URL` and `app/config.py` has defaults). `backend-quality` is now the single gate.
- **b1c9e7d** — `e2e-tests` downloads the `frontend-dist` artifact from `frontend-quality` instead of rebuilding; `playwright.config.ts`'s `webServer.command` is now conditional on `process.env.CI`, so `build:ssg` runs once in CI (was 2×) while devs running `npm run test:e2e` locally still get a build out of the box.

**Still open:**
Both `deploy-frontend.yml` and `deploy-backend.yml` run on the same push as `ci-cd.yml`, not after it — so a broken e2e or a failing backend test doesn't block the deploy of that same commit. Branch protection should require both workflows' statuses, but bypasses are possible. Proper gating needs either:

- **`workflow_run`** — chain deploy workflows to fire on successful completion of the CI/CD Pipeline. Operationally finicky (runs in the default-branch context, status-check plumbing is awkward, can re-trigger on multiple completions).
- **Inline the deploy jobs into `ci-cd.yml`** — cleanest end state. `deploy-frontend` becomes a job that `needs: [frontend-quality, e2e-tests, lighthouse]`; `deploy-backend` becomes a job that `needs: [backend-quality]`. Loses the separate-workflow status checks (which some branch-protection rules reference by name), and loses the `workflow_dispatch` ability per deploy.

Worth a deliberate decision; not blocking anything today.

---

### CI-023: Lighthouse job runs every push but scores have never been reviewed
**Files:** `.github/workflows/ci-cd.yml` (`lighthouse`), `.github/lighthouse/lighthouserc.json`
**Priority:** LOW
**Status:** RESOLVED (2026-05-14)

Pulled the `lighthouse-results` artifact from CI run 25863731084 (latest
lighthouse-ran run on `main`). Three runs of Lighthouse 12.6.1 on the home
page; **medians**:

- **Categories** — perf 97%, a11y 96%, best-practices 96%, SEO 100%
- **Core Web Vitals** — FCP 0.8s, LCP 1.2s, CLS 0, TBT 20ms
- **Resource summary** — total 691KB / 37 reqs; scripts 318KB / 8 reqs; images 221KB; fonts 97KB; CSS 48KB
- **LCP element** — the hero `<div>` (good — text, not the three.js canvas)
- **Outlier**: run 1 had TBT 380ms → perf 80%; runs 2 & 3 had TBT 10-20ms → perf 97%. Normal CI-runner noise, not signal.

**One real consistent finding**: `resource-summary:script:size` was breaching
the 300,000-byte warn budget on every run (317,808 bytes) — silently warning
for ~3 weeks because the assertion was at `warn` level. Dominant cost:
`three.js` (181KB transfer of which 106KB unused) + `gsap` (45KB / 34KB unused).
Both are already in `defineAsyncComponent` chunks but loaded on initial render
because they're in the hero / global-animation path.

**Changes to `lighthouserc.json`**:
- `resource-summary:script:size`: `warn 300_000` → **`error 325_000`** — locks in current (317,808) with ~2% headroom. Future bundle growth fails CI.
- `resource-summary:total:size`: `warn 1_000_000` → **`error 1_000_000`** — current 691KB has ~30% headroom; promotion costs nothing now and catches genuine bloat.
- `categories:best-practices`: `warn 0.9` → **`error 0.9`** — current 0.96 has 6pp headroom; promoting is free.
- Left as `warn`: `categories:performance` (current 97% medians but a single noisy run dropped to 80%; promoting would cause flakes), Core Web Vitals (currently far below thresholds, no urgency to tighten).

Spawned **PERF-004** for the unused-JS opportunity surfaced during review.

---

### PERF-004: ~140KB of unused JS shipped to home page
**Files:** `frontend/src/components/ThreeHeroBackground.vue`, `frontend/src/composables/useGsapAnimations.ts`
**Priority:** LOW
**Status:** Partially RESOLVED (2026-05-14) — three.js done, gsap deferred

Lighthouse `unused-javascript` audit (CI run 25863731084) flagged:
- `three-B8KczbbG.js`: **106,471 / 180,628 bytes unused** (59%)
- `gsap-ZjT3yFBT.js`: **34,231 / 45,218 bytes unused** (76%)

**three.js — RESOLVED**: `ThreeHeroBackground.vue` was using
`await import('three')` (dynamic barrel import) and accessing classes via
`_THREE.Scene`, `_THREE.WebGLRenderer`, etc. Rollup cannot tree-shake dynamic
namespace access, so the whole barrel was bundled. Switched to static named
imports for the 8 actually-used symbols (`Scene`, `PerspectiveCamera`,
`WebGLRenderer`, `BufferGeometry`, `BufferAttribute`, `PointsMaterial`,
`Points`, `AdditiveBlending`). The component is still in an async chunk via
`defineAsyncComponent`, so three.js stays off the critical path either way —
this just lets Rollup drop unused exports.

Result: `three.js` chunk dropped from 732KB raw / 181KB gzip → 496KB raw /
120KB gzip. **~61KB transfer saved**. Home-page script payload drops from
317,808 → ~257,000 bytes, well below the new 325KB error budget from CI-023.

**gsap — DEFERRED**: gsap's package.json declares `sideEffects: false` but our
usage (`gsap.to`, `gsap.from`, `gsap.set`, `gsap.context`, `gsap.registerPlugin`)
is all on the default-export object — there are no top-level named exports for
these methods to import individually. Tree-shaking can't help when the entry
point is a single object containing all the public surface. Real options:

- Switch to `motion` (Framer's vanilla lib) or hand-roll CSS animations for the
  simpler cases — that's a feature/refactor, not a tree-shake.
- Hand-cherry-pick from `gsap/src/...` internal paths — fragile, unsupported by
  GreenSock, breaks on minor version bumps.

Not worth the maintenance cost for ~34KB. Closing as deferred unless we
revisit animation choices for other reasons.

---

### SEC-002: Run `/security-review` against the recent diff
**Files:** N/A — review task
**Priority:** LOW
**Status:** RESOLVED (2026-05-14)

Manual pass over the ~50 commits since 2026-04-23 (the cut-off the backlog
named as "three weeks of changes"). Focus areas as scoped by the backlog
entry: Pinia auth-store hydration, CSP scopes (post-FE-005), Vercel deploy
workflow, admin-CRUD additions, the new ipapi.co geo lookup, and the markdown
extraction.

**Findings:**

1. **SEC-003 (MEDIUM)** — dual-storage of auth tokens (cookies + localStorage)
2. **SEC-004 (MEDIUM)** — `/auth/refresh` returns tokens in JSON body
3. **SEC-005 (LOW-MED)** — unsalted SHA-256 IP hash + raw-IP exposure to ipapi.co

Each is a separate backlog entry below.

**Non-findings (reviewed and OK):**
- **OAuth CSRF** — `backend/app/api/v1/auth.py:43-82` uses `secrets.token_urlsafe(32)`, single-use, 5-minute TTL, IP-bound, DB-backed, cleaned up by background task. Solid.
- **Admin CRUD endpoints** — POST/PUT/DELETE on `projects.py`, `companies.py`, `education.py` all gated by `AdminUser` dependency; PUTs use explicit field whitelists (defense-in-depth).
- **Markdown rendering** — `frontend/src/utils/markdown.ts` escapes HTML *before* emitting the only-ever `<strong>`/`<em>` tags it controls. `v-html` callsites (`ExperienceDetail.vue:91,98`) route through this. Safe.
- **Pinia hydration** — `main.ts:28-32` serialises *all* store state into the page HTML during SSG. At build time the auth store is all-nulls (no localStorage, no `/auth/me` call), so the leaked state is empty. If that ever changes (e.g. SSG starts hydrating auth from a build-time identity), revisit.
- **CSP** — `vercel.json` `script-src` keeps `'unsafe-inline'` (required for vite-ssg's serialised initial-state `<script>`), `connect-src` is clean after FE-005, no orphaned third-party hosts.
- **SQL queries** — only `text("SELECT 1")` literals in health checks; everything else parameterised via SQLAlchemy.
- **Committed secrets** — only `.env.example` templates in git; trufflehog scan in `ci-cd.yml` covers the live diff.
- **Vercel deploy** — token via env var, expanded as quoted CLI arg ~30s on the runner. Brief exposure window; Vercel CLI offers no env-only auth path. Accepted.

---

### SEC-003: Auth tokens dual-stored in localStorage AND HTTP-only cookies
**Files:** `frontend/src/stores/auth.ts`, `frontend/src/api/client.ts`, `frontend/src/api/services.ts`
**Priority:** MEDIUM
**Status:** RESOLVED (2026-05-14, paired with SEC-004)

The comment at `auth.ts:39` says "Auth is based on user presence (tokens are
in HTTP-only cookies)" — but the same store ALSO writes `accessToken` and
`refreshToken` to `localStorage` via `storage.setItem(STORAGE_KEYS.*)` in
three places (`setTokens`, `refreshAccessToken`, `initializeAuth`). It also
sets an `Authorization: Bearer ${accessToken}` header on the axios default
config.

The XSS-resistance benefit of HTTP-only cookies is defeated: an XSS payload
running on the page can read both `localStorage` and the axios default
header. The cookie is a redundant defense-in-depth layer, not a primary
control.

**Origin:** the comments call this out as "backwards compatibility (localStorage-based auth)".
If no live deploy path actually still uses localStorage auth, this is dead code that
materially weakens the security model.

**Fix (recommended sequence):**
1. Verify no callers rely on `state.accessToken` / `state.refreshToken` being populated. Grep for `authStore.accessToken` and `authStore.refreshToken` outside `auth.ts` itself.
2. Remove `accessToken` + `refreshToken` from `AuthState`. Drop the two `storage.setItem` calls in `setTokens` and `refreshAccessToken`. Drop the `apiClient.defaults.headers.common['Authorization'] = ...` lines.
3. In `logout()`, drop the `storage.removeMultiple` and the axios header delete.
4. In `initializeAuth`, drop the localStorage-token reload (lines 182-194); just call `fetchUser()` and let the cookie do the work.
5. Optional: delete `STORAGE_KEYS.ACCESS_TOKEN` / `STORAGE_KEYS.REFRESH_TOKEN` from `utils/storage` if no other code uses them.

Pairs with SEC-004 — if you keep returning tokens in the response body but
don't store them anywhere, the body return becomes inert; cleaner to fix
both together.

---

### SEC-004: `/auth/refresh` returns access+refresh tokens in JSON response body
**Files:** `backend/app/api/v1/auth.py`, `backend/app/schemas/auth.py`
**Priority:** MEDIUM
**Status:** RESOLVED (2026-05-14, paired with SEC-003)

Frontend now relies exclusively on HTTP-only cookies for auth state. The
auth Pinia store no longer carries `accessToken`/`refreshToken` fields, the
axios client no longer reads or writes them from localStorage or its default
headers, and the dead `setTokens` action + dead `/api/v1/auth/login` service
helper were removed. The refresh endpoint always sets cookies and returns
`{"refreshed": True}` — the new `RefreshSuccess` schema replaces the old
`Token` schema for that path. Three backend tests that asserted on body
tokens now read the rotated cookies from `response.cookies`. 617 frontend
tests + 661 backend tests green (85.93% coverage).

The refresh endpoint sets HTTP-only cookies for both tokens (lines 304-321,
gated on `if request.cookies.get("refresh_token")`), AND returns the same
tokens in the JSON response body (lines 323-327). The body return is
described as "for backwards compatibility" but means an XSS payload can do
`fetch('/api/v1/auth/refresh', {method: 'POST'}).then(r => r.json())` and
walk away with both tokens — completely bypassing the HTTP-only protection.

**Fix:**
1. Confirm no live client reads `access_token` / `refresh_token` from the response body — grep frontend for `response.data.access_token` and `response.data.refresh_token`. (Currently `frontend/src/stores/auth.ts:104-115` does read them, but only because of SEC-003; fixing SEC-003 first removes the dependency.)
2. Change the response schema to either return `{}` (or `{"refreshed": true}`) or define a new Pydantic model that excludes the tokens.
3. Update the OpenAPI doc and any client typings to match.
4. Keep the cookie-set behaviour as-is; that's the actual auth transport.

---

### SEC-005: Unsalted SHA-256 IP hash + raw IP exposure to ipapi.co
**Files:** `backend/app/utils/ip_hash.py`, `backend/app/api/v1/analytics.py`, `backend/app/core/geo_ip.py`
**Priority:** LOW-MED
**Status:** Part A RESOLVED (2026-05-17); Part B Open

**Part A — RESOLVED**: IP pseudonymisation now goes through HMAC-SHA256 keyed
on `SECRET_KEY` with a `"ip-hash-v1:"` domain-separation prefix, in the new
`backend/app/utils/ip_hash.py:hash_ip()` helper. Both call sites in
`analytics.py` (the anonymous-session fallback and the `ip_address` column)
were switched over. Rainbow-table reconstruction is no longer feasible
without also stealing `SECRET_KEY`, which by that point implies a deeper
compromise than the IP recovery would matter for.

We reuse `SECRET_KEY` rather than introducing a separate `IP_HASH_SECRET`
because:
- The two would leak together in practice (same env, same Fly secrets store)
- Operational cost of a second secret > marginal security gain
- The domain-separation prefix prevents collisions with other HMAC uses

Existing PageView rows keep their old (unsalted) hashes. For ~30 days after
deploy, returning visitors look "new" in unique-visitor counts as the new
keyed hashes don't match the old ones. One-time analytics rebaseline,
acceptable.

**Part B — raw IP sent to ipapi.co (Open)**:
Every uncached page-view triggers a GET to `https://ipapi.co/{ip}/country/`.
ipapi.co sees the visitor's real IP. The DB stores only the hash, but the
third party sees the original. This may need a privacy-policy disclosure
under GDPR / ePrivacy depending on your legal framing.

**Concrete numbers (researched 2026-05-20):**

| Dimension | ipapi.co (current) | MaxMind GeoLite2 self-host |
|---|---|---|
| **DB / wire** | HTTP per uncached IP | ~2MB `.mmdb` file, mmap'd in-process |
| **Lookup latency** | 50-200ms + 1.5s timeout | Microseconds (in-memory) |
| **Account / key** | None | MaxMind account + license key |
| **Refresh** | Live API | EULA: delete within 30 days of new release; ≤30 downloads/day free tier |
| **Refresh mechanism** | N/A | `geoipupdate` cron with license key |
| **Code change** | N/A | ~10 LOC swap in `geo_ip.py` |
| **Thread-safety** | Stateless per request | Reader is concurrent-read-safe |
| **Fly.io storage** | None | Bake into Docker image (2MB; rebuild for updates) OR Fly volume (~50MB min) |
| **Privacy disclosure** | Required (sub-processor) | None — IP never leaves your infra |
| **Effort to ship** | ~5 min (policy text) | ~3-4 hours |

**Hybrid worth flagging**: a community jsdelivr-mirrored GeoLite2 ([wp-statistics/GeoLite2-Country](https://github.com/wp-statistics/GeoLite2-Country))
drops the MaxMind account step. Cuts effort to ~30 min, but you're trusting a third-party CDN to serve unmodified MaxMind data — defeats most of the supply-chain benefit. Skip unless you have specific reason.

**Decision framing**:
- **Disclose** is right if your privacy policy already lists sub-processors (adding one is routine) OR if you don't expect EU regulators to inspect closely
- **Self-host** is right if zero third-party data flow is a principle OR if ipapi.co free-tier limits become a real ceiling at higher traffic

Sources: [MaxMind DB-Reader Python](https://github.com/maxmind/MaxMind-DB-Reader-python), [GeoLite2 docs](https://dev.maxmind.com/geoip/geolite2-free-geolocation-data/)

---

### CSP-001: Backend CSP cleaned up; production /docs disabled
**Files:** `backend/app/main.py`
**Priority:** LOW
**Status:** RESOLVED (2026-05-20)

The backend's response CSP allowed `cdn.jsdelivr.net` in `script-src`,
`style-src`, `font-src`, and `connect-src` — necessary because FastAPI's
`/api/docs` (Swagger UI) and `/api/redoc` load their assets from jsdelivr
by default. Both endpoints were exposed in production.

Since this API is consumed exclusively by the same-origin frontend (no
third-party API consumers), the public endpoint catalogue at `/api/docs`
was information disclosure with no upside. Killed two birds:

- `docs_url`, `redoc_url`, `openapi_url` now all `None` when
  `ENVIRONMENT == "production"`; the dev/test default of `/api/docs`,
  `/api/redoc`, `/openapi.json` is preserved everywhere else.
- Production CSP drops `https://cdn.jsdelivr.net` from all four directives.
- Root `/` endpoint's `"docs"` field reflects the actual state (`None`
  in prod, `/api/docs` otherwise).

---

---

## Security (Backend)

### BE-005: `passlib 1.7.4` incompatible with `bcrypt 5.x` — password hashing broken
**Files:** `backend/pyproject.toml:19`, `backend/requirements.txt:18,78`
**Priority:** HIGH

`passlib 1.7.4` (last released 2020) does not support `bcrypt >= 4.x` API changes. The test
suite explicitly documents this: `test_security.py:23-24` says "these tests use mocks to avoid
bcrypt/passlib compatibility issues with Python 3.13." Production calls `pwd_context.verify()`
and `pwd_context.hash()` without mocks — these will raise `AttributeError` or silently malfunction.

**Fix:** Either pin `bcrypt<4.0.0`, or migrate from passlib to `bcrypt` directly or `pwdlib`.

---

### BE-006: GitHub proxy endpoints have no rate limiting
**Files:** `backend/app/api/v1/github.py:53,71,89,112`
**Priority:** HIGH

All four `GET /github/*` endpoints have no `@rate_limit_public` decorator. These make outbound
HTTP calls to GitHub on every request. A single IP can trigger unlimited upstream calls, exhausting
the GitHub API rate limit and acting as a bandwidth amplifier.

**Fix:** Add `@rate_limit_public` decorator matching other public endpoints.

---

### BE-007: `PageView` stores raw IP address (GDPR)
**Files:** `backend/app/api/v1/analytics.py:75`
**Priority:** HIGH

`ip_address=client_ip` stores the full IP directly in the `PageView` model. GDPR and ePrivacy
treat IP addresses as personal data. The same endpoint already generates an anonymized hash for
`session_id` — the raw IP should receive similar treatment.

**Fix:** Hash + salt the IP before storage, or drop it entirely and rely on the existing
anonymized session ID. Add a documented retention policy.

---

### BE-008: `document.file_url` has no URL validation — XSS vector
**Files:** `backend/app/schemas/document.py:18-20`
**Priority:** HIGH

`file_url` and `file_path` accept arbitrary strings. Every other URL-holding schema (`project.py`,
`company.py`, `education.py`) applies `validate_safe_url` to block `javascript:` and `data:` vectors.
`DocumentBase` is the exception. A malicious admin could store a `javascript:` URL rendered as a
download link.

**Fix:** Add `validate_safe_url` to `file_url` and `file_path` fields.

---

## Build Configuration

### BUILD-001: `vite.config.production.js` references missing dependencies
**Files:** `frontend/vite.config.production.js:4,117`
**Priority:** HIGH
**Status:** RESOLVED (2026-03-31) — file deleted, dead scripts removed from package.json

Line 4: `import viteCompression from 'vite-plugin-compression'` — not in `package.json`.
Line 117: `manualChunks` references `@headlessui/vue` — not in `package.json`.

`npm run build:prod` and `npm run analyze` will crash with module-not-found errors. This file is
also never used in any CI workflow (`build:prod` is never called).

**Fix:** Delete `vite.config.production.js` entirely — its useful settings (if any) should be
merged into `vite.config.ts`. Remove `build:prod` and `analyze` scripts from `package.json`.

---

### BUILD-002: `tsconfig.node.json` includes wrong filename
**Files:** `frontend/tsconfig.node.json:12`
**Priority:** MEDIUM

`"include": ["vite.config.js"]` — but the actual file is `vite.config.ts`. The node tsconfig
is not type-checking the Vite config.

**Fix:** Change to `"include": ["vite.config.ts", "vitest.config.ts"]`.

---

### BUILD-003: `workbox-window` devDependency never imported
**Files:** `frontend/package.json:82`
**Priority:** LOW

`"workbox-window": "^7.4.0"` is in `devDependencies` but never imported. VitePWA handles
Workbox integration automatically.

**Fix:** Remove from `devDependencies`.

---

### PKG-001: `@types/three` in production dependencies
**Files:** `frontend/package.json:39`
**Priority:** LOW

Type definitions are build-time only. Should be in `devDependencies`.

**Fix:** Move to `devDependencies`.

---

## Dead Code

### DEAD-001: `imageOptimization.ts` — never imported
**Files:** `frontend/src/utils/imageOptimization.ts` (~396 lines)
**Priority:** MEDIUM

Exports `generateImageSrcSet`, `getOptimalImageFormat`, `preloadImage`, `createPlaceholder`,
`optimizeImage`, `ImageLazyLoader`, etc. Zero import sites anywhere in the codebase.

**Fix:** Delete the file.

---

### DEAD-002: `LazyImage.vue` — never used
**Files:** `frontend/src/components/LazyImage.vue` (~196 lines)
**Priority:** MEDIUM

Full IntersectionObserver-based lazy image component with blur placeholders and retry states.
Never imported by any view or parent component.

**Fix:** Delete the file.

---

### DEAD-003: `useScrollAnimations.ts` — superseded
**Files:** `frontend/src/composables/useScrollAnimations.ts` (~354 lines)
**Priority:** MEDIUM

Exports `useScrollAnimation`, `useStaggeredAnimation`, `useBatchAnimation`, `useParallax`.
The project uses `useGsapAnimations.ts` instead. This is a complete duplicate system.

**Fix:** Delete the file. Remove the mock in `HomeView.spec.ts:56-58`.

---

### DEAD-004: `errorHandler.ts` — mostly dead
**Files:** `frontend/src/utils/errorHandler.ts` (~342 lines)
**Priority:** MEDIUM

Only `getUserMessage` is imported (by `HomeView.vue:278`). All other exports
(`setupGlobalErrorHandlers`, `handleError`, `clearError`, `retryOperation`,
`showErrorNotification`, `useErrorHandler`, etc.) are never used. The global error handler in
`main.ts` is a separate implementation.

**Fix:** Extract `getUserMessage` to a small utility. Delete the rest.

---

### DEAD-005: Skills API services unused
**Files:** `frontend/src/api/services.ts` (skills-related exports)
**Priority:** LOW

`getSkills`, `getSkillById`, `createSkill`, `updateSkill`, `deleteSkill` are exported but never
imported. The portfolio store calls `apiClient` directly.

**Fix:** Remove unused skill service functions.

---

### DEAD-006: Zod validation utilities never called at runtime
**Files:** `frontend/src/schemas/api.schemas.ts`
**Priority:** LOW

`validateApiResponse`, `safeValidateApiResponse`, `createValidator` are exported but never called.
API responses are passed directly to state without validation. The schemas exist but provide zero
runtime protection.

**Fix:** Either wire the validators into store actions (ideal) or remove the dead functions.

---

### DEAD-007: Vite scaffold leftover files
**Files:** `frontend/src/assets/vue.svg`, `frontend/public/vite.svg`
**Priority:** LOW

Default Vite project template assets. Neither is imported or referenced.

**Fix:** Delete both files.

---

## Accessibility

### A11Y-004: `/admin/skills` route link leads to blank page
**Files:** `frontend/src/views/admin/AdminDashboard.vue:39,41,127`, `frontend/src/router/index.ts`
**Priority:** HIGH

AdminDashboard has three links/references to `/admin/skills` but this route does not exist in
the router. Clicking navigates to a blank page with no error.

**Fix:** Either add the route with a Skills admin view, or remove the dead links.

---

### A11Y-005: `ExperienceDetail.vue` navbar toggler missing aria attributes
**Files:** `frontend/src/views/experience/ExperienceDetail.vue:8-15`
**Priority:** MEDIUM

The inline Bootstrap navbar toggler has no `aria-expanded`, `aria-controls`, or `aria-label`.
Screen readers cannot identify it as a navigation toggle or report its state. The main `NavBar.vue`
handles this correctly.

**Fix:** Add `aria-expanded`, `aria-controls="navbarNav"`, and `aria-label="Toggle navigation"`.

---

### A11Y-006: `<main>` landmark absent during loading/error states
**Files:** `frontend/src/views/experience/ExperienceDetail.vue:43-61`
**Priority:** MEDIUM

The `<main id="main-content">` element only renders when `company` data is loaded (`v-else-if`).
During loading and error states, there is no `<main>` landmark. The router's `afterEach` hook
tries to focus `#main-content` after navigation, which silently fails during loading.

**Fix:** Wrap the entire view (including loading/error states) in `<main id="main-content">`.

---

### A11Y-007: Language progress bars missing ARIA
**Files:** `frontend/src/components/GitHubStats.vue:86-95`
**Priority:** MEDIUM

Progress bars render as styled `<div>` elements with no `role="progressbar"`, `aria-valuenow`,
`aria-valuemin`, or `aria-valuemax`. Screen readers cannot convey the percentage values.

**Fix:** Add `role="progressbar"` and appropriate `aria-value*` attributes.

---

### A11Y-008: Section icon alt text redundant with heading
**Files:** `frontend/src/views/HomeView.vue:30,99,166,189,202`
**Priority:** LOW

Section icons use alt text like "Experience Icon" immediately before the "Experience" heading.
Screen readers announce both redundantly. These are decorative in context.

**Fix:** Change to `alt=""` (decorative image).

---

## Error Handling

### ERR-001: Portfolio API errors silently swallowed in HomeView
**Files:** `frontend/src/views/HomeView.vue:344-348`
**Priority:** HIGH

`portfolioStore.fetchAllData().catch(error => { logger.error(...) })` — errors are logged but
the template never reads `portfolioStore.error` to show a user-facing error banner. Experience,
education, and skills sections silently show empty content if the API is down.

**Fix:** Add error state display using `portfolioStore.error`.

---

### ERR-002: Duplicate global error handler setup
**Files:** `frontend/src/main.ts:89-107`, `frontend/src/utils/errorHandler.ts:261`
**Priority:** MEDIUM

`main.ts` sets `app.config.errorHandler` to its own implementation. `errorHandler.ts` exports
`setupGlobalErrorHandlers` which would overwrite it if called. Currently safe because
`setupGlobalErrorHandlers` is never called (DEAD-004), but a latent bug.

**Fix:** Remove `setupGlobalErrorHandlers` as part of DEAD-004 cleanup.

---

## Backend

### BE-009: All list endpoints are unbounded — no pagination
**Files:** `backend/app/api/v1/` — `projects.py:29`, `companies.py:29`, `skills.py:28`, `education.py:29`, `documents.py:25`, `analytics.py:92,154`
**Priority:** MEDIUM

Every list endpoint returns `result.scalars().all()` with no `limit`/`offset`. The analytics
endpoints are especially concerning — `PageView` is append-only and can grow to millions of rows.

**Fix:** Add `skip` and `limit` query params with sensible defaults. Priority: analytics endpoints.

---

### BE-010: `PageView` model missing indexes
**Files:** `backend/app/models/analytics.py:12-26`
**Priority:** MEDIUM

Analytics endpoints filter/group by `created_at` and `session_id` on every request. Neither column
has an index. Full sequential scans on any non-trivial dataset.

**Fix:** Add `index=True` to `created_at` and `session_id` columns.

---

### BE-011: ~600 lines of migration/seed data runs on every startup
**Files:** `backend/app/main.py:276-713`
**Priority:** MEDIUM

`migrate_company_data()`, `migrate_education_data()`, `migrate_skill_proficiency()`, and
`cleanup_duplicate_scania_entries()` contain hardcoded company names, dates, YouTube URLs, etc.
These run inside the lifespan handler on every cold start, executing dozens of UPDATE statements.

**Fix:** Move to a one-time Alembic migration or standalone seed script.

---

### BE-012: `validate_safe_url` duplicated across 3 schema modules
**Files:** `backend/app/schemas/project.py:11-25`, `company.py:11-21`, `education.py:6-16`
**Priority:** MEDIUM

Identical regex pattern and helper function copy-pasted. Drift risk (e.g., `education.py` has
a slightly different function signature).

**Fix:** Extract to a shared `app/schemas/_validators.py` module.

---

### BE-013: `Contact` model defined but unused
**Files:** `backend/app/models/contact.py`, `backend/app/models/__init__.py`
**Priority:** MEDIUM

The model is registered and its table is created by `Base.metadata.create_all`, but there is no
API endpoint, no test file, and no frontend form that uses it.

**Fix:** Either implement a contact form endpoint (with anti-spam) or delete the model.

---

### BE-014: No Alembic migrations despite Alembic being a dependency
**Files:** `backend/pyproject.toml:14`, `backend/app/main.py:220-273`
**Priority:** MEDIUM

Alembic is pinned as a dependency but there's no `alembic/` directory or `alembic.ini`. Schema
changes use a bespoke `run_migrations()` function with raw `ALTER TABLE` SQL on every startup.
No migration history, no rollback, silent failure on error.

**Fix:** Initialize Alembic and create proper migration files. Remove raw SQL migrations from `main.py`.

---

### BE-015: `gunicorn_conf.py` worker count uses host CPU count
**Files:** `backend/gunicorn_conf.py:14`
**Priority:** LOW-MEDIUM

`workers = int(os.getenv("WORKERS", multiprocessing.cpu_count() * 2 + 1))` — in a container,
`cpu_count()` returns the host machine's physical count, not the container's limit. Could spawn
17-33 workers, each with its own DB connection pool, exhausting `max_connections`.

**Fix:** Document `WORKERS` env var in `.env.example`. Default to `min(cpu_count() * 2 + 1, 4)`.

---

### BE-016: `GET /analytics/stats/visitors` has no response_model
**Files:** `backend/app/api/v1/analytics.py:154`
**Priority:** LOW

Returns a raw dict. Response shape not validated, not in OpenAPI docs. Contains stub values
(`returning_visitors: 0`, `new_visitors: total_sessions`).

**Fix:** Define a `VisitorStats` Pydantic model and set as `response_model`.

---

### BE-017: `GET /api/v1/metrics/` uses `response_model=dict`
**Files:** `backend/app/api/v1/endpoints/metrics.py:15`
**Priority:** LOW

No OpenAPI schema documentation for the metrics response.

**Fix:** Define a typed response model.

---

### BE-018: Documents endpoints have no rate limiting
**Files:** `backend/app/api/v1/endpoints/documents.py:25,46`
**Priority:** LOW

Both `GET /documents/` and `GET /documents/{id}` have no `@rate_limit_public` decorator,
unlike every other public endpoint.

**Fix:** Add `@rate_limit_public` decorator.

---

### BE-019: `PageView.page_path` and `session_id` lack `nullable=False`
**Files:** `backend/app/models/analytics.py:16,22`
**Priority:** LOW

The Pydantic schema requires these fields, but the SQLAlchemy column allows NULL. A direct DB
insert could create rows that cause NoneType errors in analytics aggregation.

**Fix:** Add `nullable=False` to both columns.

---

## SEO

### SEO-001: Sitemap hardcoded and stale
**Files:** `frontend/public/sitemap.xml`
**Priority:** HIGH

Sitemap has `<lastmod>2025-10-19</lastmod>` (5+ months stale). Experience detail URLs use
hardcoded slugs (`/experience/hermes`, etc.) that may not match the dynamic IDs that
`includedRoutes()` fetches from the API.

**Fix:** Generate sitemap dynamically during SSG build, or create a pre-deploy script that
fetches current company IDs and writes `sitemap.xml`.

---

### SEO-002: Structured data `dateModified` hardcoded
**Files:** `frontend/index.html:133`
**Priority:** MEDIUM

`"dateModified": "2025-01-01"` — never updated. Googlebot uses this to judge recency.

**Fix:** Update at build time via a Vite plugin or pre-deploy script.

---

### SEO-003: Experience detail pages have no SSR meta tags
**Files:** `frontend/src/router/index.ts`, `frontend/src/main.ts:62-65`
**Priority:** MEDIUM

`document.title` is set client-side in the router `afterEach`. With SSG not running in CI
(CI-007), pre-rendered HTML has no unique `<title>` or canonical tag per page. Even with SSG,
`<meta>` tags in `<head>` are not set per-route.

**Fix:** Use `@unhead/vue` or `vite-ssg`'s `useHead()` to set per-route head tags during SSG.

---

### SEO-004: Missing `og:image:alt` meta tag
**Files:** `frontend/index.html:20`
**Priority:** LOW

OpenGraph accessibility recommendation. `og:image` is set but `og:image:alt` is missing.

**Fix:** Add `<meta property="og:image:alt" content="David Dashti Portfolio Preview" />`.

---

## CSS

### CSS-002: Stockholm-background overlay gradients use hardcoded rgba
**Files:** `frontend/src/assets/portfolio.css:173,177,194,197,211,214,228,231,249-253`
**Priority:** MEDIUM
**Status:** Partially fixed (commit `407224f` fixed hero accent gradient, overlay gradients remain)

8 lines still use `rgba(37, 99, 235, 0.1)`, `rgba(20, 184, 166, 0.1)`, and
`rgba(248, 250, 252, 0.15)` instead of CSS variable equivalents.

**Fix:** Map to `--color-primary-rgb` / `--color-teal-rgb` alpha variants.

---

## Frontend Features / Tech Debt

### FE-003: AdminProjects CRUD not implemented
**Files:** `frontend/src/views/admin/AdminProjects.vue`, `frontend/tests/unit/views/admin/AdminProjects.spec.ts`
**Priority:** MEDIUM
**Status:** RESOLVED (2026-05-04)

Replaced the placeholder with a full CRUD view mirroring `AdminCompanies.vue`:
list with featured-badge cards + tech pills + resolved company name; modal
form covering all 14 editable fields grouped into Basics / Links / Media /
Lists / Meta sections; company FK rendered as a dropdown populated from
`/api/v1/companies` (parallel `Promise.all` on mount). Test file expanded
from 3 placeholder tests to 20, mirroring `AdminCompanies.spec.ts`. The
existing `projectService` factory and zod-derived `Project` type meant no
new API or type plumbing was needed.

---

### FE-004: Split oversized components
**Priority:** LOW

Not bugs — testability and readability concern. Extract sub-components
(table rows, form sections, repo cards) so the routed file becomes a thin
orchestrator.

**Progress:**
- 2026-05-04 — `GitHubStats.vue` split: extracted `RepoCard.vue`,
  `LanguageBar.vue`, and `utils/githubLanguageColors.ts` with their own
  unit tests. Parent went from 733 → 286 lines; existing parent tests
  pass unchanged because the rendered DOM is identical. Also dropped
  ~75 lines of dead CSS (`.stats-grid` / `.stat-card`) that no template
  referenced.
- 2026-05-06 — admin trio cross-cutting refactor: extracted
  `<AdminFormModal>` (modal overlay + focus trap + escape handler),
  `<AdminCardActions>` (edit/delete button pair), and
  `useCommaSeparatedList` (string[] ↔ comma-separated input adapter).
  Triplicated modal scaffolding and triplicated comma-separated
  computeds collapse to one source of truth. AdminCompanies 859 → 702,
  AdminProjects 951 → 791, AdminEducation 570 → 518. Existing parent
  test suites (68 tests across the trio) pass unchanged.
- 2026-05-08 — `AdminDashboard.vue` split: extracted
  `<DashboardOverview>` (stats grid + quick actions + error/retry
  alert). Parent dropped 582 → 302 — under the 500 threshold. Existing
  AdminDashboard tests pass unchanged because the child re-emits the
  same `.stat-*` / `.action-*` classes via slotted-equivalent rendering.

**Remaining files (still > 500 lines):**
- `frontend/src/views/admin/AdminCompanies.vue` (702)
- `frontend/src/views/admin/AdminProjects.vue` (791)
- `frontend/src/views/admin/AdminEducation.vue` (518)
- `frontend/src/views/experience/ExperienceDetail.vue` (538)

The admin trio's remaining size is mostly form-field markup. Pushing
under 500 would require per-section sub-components
(`<CompanyDateRange>`, `<ProjectMediaSection>`, etc.) — diminishing
returns vs. the readability of top-to-bottom form code. ExperienceDetail
is unrelated and would be its own pass.

**Estimated effort:** ~half day per remaining file.

---

### FE-005: Decide fate of `utils/analytics.ts` (Plausible/Umami)
**Status:** RESOLVED (2026-05-07) — chose path (b), delete.

`utils/analytics.ts` initialised Plausible/Umami via `init()` in `main.ts`,
but no code ever called the `track*` helpers — the only wired-up analytics
path was `services/analytics.ts` (self-hosted, admin-dashboard data source).
Removed the dead module + its composable wrapper + their tests + the four
`VITE_ANALYTICS_*` env vars in `.env.example`. Also tightened `vercel.json`
CSP to drop `https://analytics.umami.is` and `https://plausible.io` from
`script-src` and `connect-src` since they're no longer needed.

---

### FE-006: Tighten remaining `any` usages
**Status:** RESOLVED (2026-05-08, audit) — no code change required.

The "33 occurrences" estimate was stale. A re-grep across `src/` found
zero TypeScript `any` types — earlier refactors (DEAD-* cleanups,
Plausible/Umami deletion, admin trio + GitHubStats extractions, the
`projectService` factory) had quietly stripped them. The 56 `any`
usages remaining in `tests/` are legitimate mock scaffolding
(`as any` on partial axios responses, header shims, etc.) that aren't
worth the cost of typing fully.

---

## Backend Tech Debt

### BE-025: PageView `country` / `city` never populated — Top Countries always empty
**Files:** `backend/app/api/v1/analytics.py`, `backend/app/models/analytics.py`
**Priority:** MEDIUM

`PageView.country` and `PageView.city` exist as columns but no geo-IP lookup
runs at write time. The admin Analytics view's "Top Countries" section will
always show the empty state.

**Scope:** Either integrate a free GeoIP database (MaxMind GeoLite2 via the
`maxminddb` Python lib) at write time, or call a geo-IP HTTP service. The IP
hash is already stored, so privacy can be preserved by storing only the
country code (no city).

**Estimated effort:** 2–3 hours including provider choice and lookup caching.

---

## Code Quality

### TYPE-001: `AnalyticsService` has two conflicting `isEnabled` sources
**Files:** `frontend/src/services/analytics.ts:40,134`
**Priority:** MEDIUM

Constructor sets `this.isEnabled = true`. `isAnalyticsEnabled()` reads from `localStorage`.
`trackPageView`/`trackEvent` check `this.isEnabled` (instance property), not `localStorage`.
`setEnabled(false)` persists to both, but initial state can diverge.

**Fix:** Use a single source of truth — either the instance property initialized from
`localStorage`, or always read from `localStorage`.

---

## Resolved Items (Previous Sessions)

All items below were resolved in commits between 2025-10 and 2026-03-30.

| ID | Summary | Commit |
|----|---------|--------|
| BUG-001 | Video/map embed heading alignment | PR #48 |
| BUG-002 | Publications dark mode invisible text | PR #48 |
| BUG-003 | Heading color uses `--bs-body-color` | PR #48 |
| BUG-004 | `--border-color` never defined | PR #48 |
| DEBT-001 | Duplicate `:root` variable definitions | `b8ef301` |
| DEBT-002 | Slate palette inversion strategy | `2b6504c` |
| DEBT-003 | `scroll-padding-top` defined twice | `5b123a4` |
| DEBT-004 | `body` styles defined twice | `5b123a4` |
| DEBT-005 | `.container` class conflicts with Bootstrap | `c921f50` |
| DEBT-006 | `DocumentCard.vue` hardcoded hex colors | `40f4581` |
| DEBT-007 | `ErrorBoundary.vue` unused | `40f4581` |
| DEBT-008 | `VideoEmbed`/`MapEmbed` near-identical | `fed194e` |
| DEBT-009 | Stale artifact directories | `2abfae` |
| DEBT-010 | Backend three virtual environments | manual cleanup |
| DEBT-011 | Duplicate experience detail views | `5cc6848` |
| DEBT-012 | `public/sw.js` conflict with VitePWA | `0e34023` |
| CI-001 | Trivy compromised action | direct binary download |
| CI-002 | `npm run lint --if-present` flag order | ci-cd.yml fix |
| CI-003 | pip cache misses `requirements-dev.txt` | ci-cd.yml fix |
| CI-004 | `pytest-coverage-comment` floating ref | version-pinned |
| CI-006 | `vitest-coverage-report-action` config | vite.config.ts fix |
| PERF-001 | Three.js imported statically | `012ac8d` |
| PERF-002 | GitHubStats unconditional fetch | `0da4667` |
| PERF-003 | Missing preload for Inter font | `450f60b` |
| A11Y-001 | Focus not moved on route change | `895d77e` |
| A11Y-002 | Focus ring minimum requirements | `efd90b0` |
| A11Y-003 | ProjectCard links ambiguous | `0579c75` |
| BE-001 | `Project.technologies` no schema validation | `b712e6f` |
| BE-002 | N+1 query on company endpoints | `ff907c5` |
| BE-003 | CSP `frame-src` overly broad | `057a95a` |
| BE-004 | Dev/CI tools in production requirements | `39cb5a5` |
| CSS-001 | Z-index hardcoded as `9999` | `01c9f5f` |
| EVAL-001 | SSG implementation (vite-ssg) | `ccef203` |
| EVAL-002 | GitHub username hardcoded | `0579c75` |
