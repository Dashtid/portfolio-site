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
| CI-005 | CI/CD | LOW | Dependency-review job requires Dependency Graph enabled in repo settings |
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
| FE-003 | Frontend | MEDIUM | AdminProjects CRUD not implemented — placeholder only |
| FE-004 | Frontend | LOW | Five components/views > 500 lines (AdminCompanies, GitHubStats, AdminEducation, AdminDashboard, ExperienceDetail) |
| FE-005 | Frontend | LOW | `utils/analytics.ts` (Plausible/Umami) initialised but `useAnalytics` helpers never called by any view |
| FE-006 | Frontend | LOW | 33 `any` usages — tighten the handful that aren't Web API casts |
| BE-025 | Backend | MEDIUM | PageView `country`/`city` columns never populated — admin Top Countries section always empty |
| CI-021 | CI/CD | LOW | No coverage threshold enforced — PRs can drop coverage silently |

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
**Files:** `.github/workflows/ci-cd.yml`, `frontend/package.json`
**Priority:** LOW

Frontend has 597 unit tests via vitest and `@vitest/coverage-v8` is already
installed, but no coverage threshold is enforced — PRs can drop coverage
silently. Backend test job similarly has no min-coverage gate.

**Scope:**
- Run `vitest run --coverage` in CI (frontend) and `pytest --cov` (backend,
  already runs but no threshold).
- Capture a baseline once and bake into the workflow as a min threshold.
- Fail PRs that drop overall coverage by more than ~2 percentage points.
- Optional: stricter thresholds for `src/stores/` and `src/api/`.

**Estimated effort:** 1–2 hours.

---

### CI-005: `dependency-review` job requires Dependency Graph enabled
**Files:** `.github/workflows/ci-cd.yml:218-231`
**Priority:** LOW
**Status:** Open (requires GitHub repo setting, not a code change)

The workflow code is correct, but requires enabling Dependency Graph in repo Settings > Security
& analysis. Without it, the job silently fails on every PR.

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
**Files:** `frontend/src/views/admin/AdminProjects.vue`
**Priority:** MEDIUM

The admin Projects view is a styled placeholder. Projects on the public site
are seeded via `backend/app/seed_data.py` and edited there.

**Scope:**
- Build the same shape as `AdminCompanies.vue` (table + create/edit modal).
- Reuse the existing `/api/v1/projects` CRUD endpoints.
- Acceptance: admin can list, create, edit, delete, reorder, and toggle
  `featured` on projects without touching the database directly.

**Estimated effort:** ~1 focused day.

---

### FE-004: Split oversized admin components
**Files:**
- `frontend/src/views/admin/AdminCompanies.vue` (859 lines)
- `frontend/src/components/GitHubStats.vue` (733 lines)
- `frontend/src/views/admin/AdminEducation.vue` (570 lines)
- `frontend/src/views/admin/AdminDashboard.vue` (562 lines)
- `frontend/src/views/experience/ExperienceDetail.vue` (538 lines)

**Priority:** LOW

Not bugs — testability and readability concern. Extract sub-components
(table rows, form sections, repo cards) so the routed file becomes a thin
orchestrator.

**Estimated effort:** ~half day per file.

---

### FE-005: Decide fate of `utils/analytics.ts` (Plausible/Umami)
**Files:** `frontend/src/utils/analytics.ts`, `frontend/src/composables/useAnalytics.ts`, `frontend/src/main.ts`
**Priority:** LOW

`utils/analytics.ts` initialises a Plausible/Umami script in `main.ts` based on
`VITE_ANALYTICS_*` env vars, and `composables/useAnalytics.ts` wraps it with named
helpers (`trackButtonClick`, `trackThemeToggle`, etc.) — but **nothing in the
app currently calls those helpers**. The internal `services/analytics.ts`
(admin dashboard data source) is the path that's actually wired up.

**Scope:** Pick one:
- (a) Wire `useAnalytics` helpers into NavBar, ThemeToggle, ProjectCard click
  events, etc. so Plausible/Umami actually receives signal.
- (b) Delete `utils/analytics.ts`, `composables/useAnalytics.ts`, and the init
  call in `main.ts` to stay on self-hosted analytics only.

---

### FE-006: Tighten remaining `any` usages
**Files:** `frontend/src/composables/useToast.ts`, `frontend/src/api/services.ts`, `frontend/src/schemas/api.schemas.ts`, others
**Priority:** LOW

33 `any` occurrences across 11 files. Most are defensible Web API casts
(`as PerformanceXXXTiming`, `as HTMLElement | null`); a handful in toast
state, analytics schemas, and config objects could become real interfaces.

**Estimated effort:** 1–2 hours total.

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
