# Portfolio Site Backlog

Work items for tidying up the project. No new features — bugs, CSS architecture debt, and code quality.

---

## BUG — Active

### BUG-001: Video/map embed headings don't align horizontally when title wraps
**Files:** `frontend/src/components/VideoEmbed.vue`, `frontend/src/components/MapEmbed.vue`
**Priority:** High — visually broken

On the company detail page, the video and map embeds sit side by side in a Bootstrap `row.g-4` grid.
Each has an optional heading rendered above the iframe. When one heading is short (1 line) and the
other is long (wraps to 2 lines), the iframes no longer align at the same vertical position.

The heading has no fixed height, so its natural height determines where the iframe starts. Both
`VideoEmbed.vue` and `MapEmbed.vue` have identical heading styles (`font-size: 1.5rem`, no
`min-height`). The layout needs the headings to always consume the same amount of vertical space
regardless of content length.

**Fix:** Add `min-height: calc(2 * 1.5rem * 1.5)` (= 4.5rem, accounting for 1.5 line-height) to
`.video-heading` and `.map-heading`. This reserves 2 lines for the heading, keeping iframes
horizontally aligned even when one title is shorter.

---

### BUG-002: Publications section has near-invisible text in dark mode
**Files:** `frontend/src/assets/portfolio.css`, `frontend/src/components/DocumentCard.vue`
**Priority:** High — WCAG contrast failure, text invisible

This is caused by an interaction between two design decisions:

**Root cause A — Inverted slate palette in dark mode (`variables.css` lines 203-213):**
`variables.css` inverts the `--slate-*` scale in dark mode: `--slate-50` becomes `#0f172a` (darkest)
and `--slate-900` becomes `#f8fafc` (near-white). The intent is that code using `--slate-900` for
dark text automatically gets light text in dark mode. This is a non-standard "semantic inversion"
strategy.

**Root cause B — `.bg-dark` uses slate variables for its background (`portfolio.css` line 458-461):**
```css
.bg-dark {
  background: linear-gradient(135deg, var(--slate-800) 0%, var(--slate-900) 100%) !important;
}
```
In dark mode: `--slate-800` becomes `#f1f5f9` and `--slate-900` becomes `#f8fafc`. The Publications
section renders with a NEAR-WHITE gradient background in dark mode — the opposite of its intent.

**Root cause C — `DocumentCard.vue` has hardcoded light text colors:**
`.document-title { color: #f8fafc; }` — near-white text, hardcoded, never overridden in dark mode.
When the bg-dark section is near-white in dark mode, white text on white background = invisible.

`portfolio.css` correctly handles `[data-theme='light'] .bg-dark` with an explicit light-themed
override (lines 504-520). The missing piece is an equivalent `[data-theme='dark'] .bg-dark` rule
that pins the background to dark values regardless of the slate inversion.

**Fix:**
1. Add `[data-theme='dark'] .bg-dark` to `portfolio.css` with hardcoded dark background and light text.
2. Add `[data-theme='dark'] .document-title`, `.document-description`, `.meta-item` overrides in
   `DocumentCard.vue` to ensure text is readable on the (now dark again) background.

---

### BUG-003: `.video-heading` and `.map-heading` use `var(--bs-body-color)`
**Files:** `frontend/src/components/VideoEmbed.vue:112`, `frontend/src/components/MapEmbed.vue:98`
**Priority:** Medium — incorrect in dark mode

Both components use Bootstrap's `--bs-body-color` for heading color. Bootstrap 5 is loaded from CDN
without dark mode configuration, so `--bs-body-color` does not update when `[data-theme='dark']` is
set. In dark mode, headings may render in Bootstrap's default light-mode body color instead of the
project's `--text-primary`.

**Fix:** Replace `var(--bs-body-color)` with `var(--text-primary)` in both components.

---

### BUG-004: `--border-color` is used but never defined
**Files:** `frontend/src/components/VideoEmbed.vue:143`, `frontend/src/components/MapEmbed.vue:129`
**Priority:** Low — always falls back to hardcoded value, but dark mode border is wrong

The fallback containers for both embed components use `var(--border-color, #e2e8f0)`. Neither
`variables.css` nor `portfolio.css` defines `--border-color` — the project uses `--border-primary`
and `--color-border` for borders. The fallback `#e2e8f0` is the light-mode border color and is
always used, meaning dark mode gets a light border on a dark fallback box.

**Fix:** Replace `var(--border-color, #e2e8f0)` with `var(--border-primary)` in both components.
The dark mode value is already correctly defined in `variables.css` as `#334155`.

---

## DEBT — CSS Architecture

### DEBT-001: Duplicate `:root` variable definitions across two CSS files
**Files:** `frontend/src/assets/portfolio.css` (lines 4-69), `frontend/src/styles/variables.css`
**Priority:** High — source of bugs, values diverge

Both files define a `:root` block covering the same variables: `--primary-*`, `--slate-*`, spacing
tokens, border radii, shadows, and typography. They have conflicting values in some cases:

| Variable | `variables.css` | `portfolio.css` |
|---|---|---|
| `--radius-md` | `0.375rem` | `0.5rem` |
| `--radius-lg` | `0.5rem` | `0.75rem` |
| `--radius-xl` | `0.75rem` | `1rem` |
| `--shadow-md` | `0 4px 6px -1px rgb(0 0 0 / 0.07)...` | `0 4px 6px -1px rgba(0,0,0,10%)...` |
| `--bg-primary` | `#ffffff` | `var(--primary-50)` (= `#eff6ff`) |
| `--bg-secondary` | `#f8fafc` | `#fff` |

Whichever file is loaded last wins. The effective values depend on CSS load order, which is fragile.
This also means dark mode overrides in one file may be silently overridden by the other.

**Fix:** Remove the entire `:root` block from `portfolio.css`. `variables.css` is the single source
of truth. Audit all usages to make sure nothing breaks after removal.

---

### DEBT-002: Slate palette inversion strategy is risky and undocumented
**Files:** `frontend/src/styles/variables.css` (lines 203-213)
**Priority:** Medium — already caused BUG-002, likely to cause more

The `--slate-*` variables are fully inverted in dark mode: `--slate-50` (lightest in light mode)
becomes the darkest color in dark mode, and vice versa. The idea is to allow code to write
`color: var(--slate-900)` for "always dark text" and get "always light text" in dark mode for free.

Problems:
- Any component that uses a slate variable expecting a specific shade gets the opposite in dark mode
- It has already silently broken `.bg-dark` (see BUG-002)
- It is not documented anywhere — future contributors will not know about this
- There is no test coverage for "does this look right in both themes"

**Fix:** Add a prominent comment block in `variables.css` explaining the inversion strategy and its
implications. Audit all direct `--slate-*` usages in components and templates to verify they
behave correctly in both modes. Where the inversion causes problems, switch to semantic variables
(`--text-primary`, `--bg-secondary`, etc.) which are already defined without inversion.

---

### DEBT-003: `scroll-padding-top` defined twice with different values
**Files:** `frontend/src/style.css:15`, `frontend/src/assets/portfolio.css:268`
**Priority:** Low

`style.css` sets `scroll-padding-top: 80px`. `portfolio.css` sets `scroll-padding-top: 72px`.
The navbar is 72px tall. The effective value depends on load order.

**Fix:** Remove the `80px` declaration from `style.css`. Keep the `72px` in `portfolio.css` which
matches the actual navbar height.

---

### DEBT-004: `body` styles defined twice with conflicting variables
**Files:** `frontend/src/style.css:28-38`, `frontend/src/assets/portfolio.css:271-284`
**Priority:** Low

`style.css` sets `body { color: var(--color-gray-900); background: linear-gradient(#f5f7fa, #c3cfe2); }`.
`portfolio.css` sets `body { color: var(--text-primary); background-color: var(--bg-primary); }`.

These use different variable names for the same purpose, and the background values differ (gradient
vs solid color token). The effective value depends on load order.

**Fix:** Keep only the `portfolio.css` body declaration (it uses semantic variables). Remove the
body block from `style.css` or reduce it to only properties not covered by `portfolio.css`.

---

### DEBT-005: Custom `.container` class defined twice, conflicts with Bootstrap
**Files:** `frontend/src/style.css:168`, `frontend/src/assets/portfolio.css:879`
**Priority:** Low

Both files define `.container { max-width: 1200px; }` with slightly different padding (16px vs 15px).
Bootstrap 5 (loaded from CDN) also defines `.container` with responsive breakpoint behaviour. The
custom declarations may override Bootstrap's responsive padding at certain breakpoints.

**Fix:** Remove both custom `.container` blocks. Bootstrap's `.container` already provides
responsive behaviour. If a fixed 1200px max-width is needed, use Bootstrap's `.container-xl` or
set `--bs-container-xl` in the theme configuration.

---

## DEBT — Component Code Quality

### DEBT-006: `DocumentCard.vue` uses hardcoded hex colors throughout
**File:** `frontend/src/components/DocumentCard.vue`
**Priority:** Medium

The component has ~12 hardcoded hex color values instead of CSS variable references:
- `.document-title: #f8fafc` (should be a variable like `--text-on-dark` or `--slate-50`)
- `.document-type: #93c5fd` (should be `--primary-300` or similar)
- `.document-description: #cbd5e1` (should be `--text-secondary-on-dark`)
- `.meta-item: #94a3b8`, `.icon: #94a3b8` (should be `--text-tertiary-on-dark`)
- `.document-link: #93c5fd`, hover `#bfdbfe` (should be primary variables)

This hardcoding is what made BUG-002 difficult to catch — the dark background shifted to light
but the text colors had no mechanism to follow. Using CSS variables would allow the cascade to
handle theme changes automatically.

**Fix:** Define dark-section-specific text variables (or use the existing `--text-primary`,
`--text-secondary`, `--text-tertiary` which already adapt per theme) and replace all hardcoded
colors in `DocumentCard.vue`.

---

### DEBT-007: `ErrorBoundary.vue` component exists but is not used
**File:** `frontend/src/components/ErrorBoundary.vue`
**Priority:** Low

The component exists but is not referenced in `App.vue` or any view. Vue ErrorBoundary components
are only effective when they wrap content — sitting unused they provide no safety net.

**Fix:** Either wrap the main router view in `App.vue` with `<ErrorBoundary>`, or delete the
component if there is no plan to use it.

---

### DEBT-008: `VideoEmbed.vue` and `MapEmbed.vue` are near-identical
**Files:** `frontend/src/components/VideoEmbed.vue`, `frontend/src/components/MapEmbed.vue`
**Priority:** Low

Both components share identical structure: heading, ratio wrapper, iframe, fallback UI, and the
same CSS layout/fallback styles. The only differences are the allowed domain list, the path
validation logic, and CSS class names (`.video-*` vs `.map-*`). This duplication means bug fixes
and style changes must be applied twice (as seen with BUG-001, BUG-003, BUG-004 above).

**Fix (optional refactor):** Extract a shared `BaseEmbed.vue` component that accepts a validator
function as a prop (or via a composable). `VideoEmbed` and `MapEmbed` become thin wrappers that
only define their allowed domains/paths. Only do this if more embed types are anticipated — for
just two, the duplication is manageable.

---

## DEBT — Housekeeping

### DEBT-009: Multiple stale artifact directories not excluded from the repo
**Files:** `frontend/.coverage/`, `frontend/coverage/`, `frontend/.playwright-report/`,
`frontend/playwright-report/`, `backend/htmlcov/`
**Priority:** Low

Several generated artifact directories appear to be present in the working tree:
- Two frontend coverage dirs (`coverage/` and `.coverage/`) from different vitest config runs
- Two Playwright report dirs (`.playwright-report/` and `playwright-report/`)
- Backend Python coverage HTML report (`htmlcov/`)

None of these belong in the repository. Check `.gitignore` at both root and `frontend/` level to
confirm they are excluded, delete the directories from the working tree, and standardise on a
single output path per tool in the respective config files.

---

### DEBT-010: Backend has three virtual environments
**Files:** `backend/.venv/`, `backend/.venv-new/`, `backend/.venv-pip/`
**Priority:** Low — waste and confusion

Three Python virtual environments exist side by side. The `-new` and `-pip` suffixes suggest
migration attempts that were never cleaned up. Only one should be active. Keeping multiple venvs
wastes disk space and creates ambiguity about which one is canonical (CI, Fly.io deployment, and
local dev may all resolve differently).

**Fix:** Determine which venv is in use by checking `pyproject.toml` / `Makefile` / CI config.
Delete the other two. Add all three patterns to `.gitignore` if not already there.

---

### DEBT-011: Two experience detail views with overlapping purpose — decide canonical route
**Files:** `frontend/src/views/ExperienceDetail.vue` (`/experience/:id`),
`frontend/src/views/CompanyDetailView.vue` (`/company/:id`)
**Priority:** Low — both work, but two routes for the same content is confusing

Both routes are active and intentional with distinct UX:
- `/company/:id` → `CompanyDetailView.vue`: standard detail page linked from the main portfolio
- `/experience/:id` → `ExperienceDetail.vue`: "browse mode" — has a secondary navbar listing all
  companies for quick lateral navigation

The issue is neither route is clearly canonical. All links from the home page use `/company/:id`.
`/experience/:id` appears to be an earlier iteration that gained a browse-mode navbar but was never
removed when `CompanyDetailView` was built. Two maintained views means bug fixes must be applied
twice (BUG-001 was applied to both, but future bugs may be missed).

**Fix:** Decide which UX pattern to keep. Options:
1. Add the browse-mode navbar to `CompanyDetailView.vue`, delete `ExperienceDetail.vue`
2. Redirect `/company/:id` to `/experience/:id` and retire `CompanyDetailView.vue`
3. Keep both intentionally but add clear internal documentation explaining the split

---

### DEBT-012: `public/sw.js` may conflict with Vite PWA plugin's generated service worker
**File:** `frontend/public/sw.js`
**Priority:** Medium

The project uses `vite-plugin-pwa` (with Workbox) which auto-generates a service worker at build
time. A hand-written `sw.js` also exists in `public/`. Both would be served at the same path
(`/sw.js`) and the plugin's generated file would overwrite the manual one at build time, or vice
versa. This needs verification: if `public/sw.js` is the primary service worker, the Vite PWA
plugin config may be redundant or misconfigured.

**Fix:** Read both files and the PWA plugin config in `vite.config.ts` to determine which service
worker is actually active in production. Remove or consolidate the duplicate.

---

---

## DEBT — CI/CD

### CI-001: `security-scan` used compromised `aquasecurity/trivy-action@0.29.0` — FIXED
**File:** `.github/workflows/ci-cd.yml`
**Status:** Fixed in PR #49 (merged 2026-03-25)

The Trivy GitHub Action had 75 of 76 version tags force-pushed in March 2026 to serve malicious
payloads that exfiltrate CI/CD secrets. Replaced with a direct binary download from GitHub Releases
pinned to v0.62.0.

---

### CI-002: `npm run lint --if-present` uses an invalid npm flag
**File:** `.github/workflows/ci-cd.yml:68`
**Priority:** Low — currently masked by `|| echo` fallback, but semantically wrong

`npm run --if-present` is a valid flag for `npm run` but `npm run lint --if-present` passes
`--if-present` as an argument to the script rather than to npm. The intent is to skip silently if
the script doesn't exist. The correct form is `npm run --if-present lint`.

Since the repo does have a `lint` script, the bug is currently hidden. It will matter if the
script is ever removed.

**Fix:** Change line 68 to `npm run --if-present lint || true`

---

### CI-003: Python dependency cache only covers `requirements.txt`, misses dev requirements
**File:** `.github/workflows/ci-cd.yml:109`
**Priority:** Low

`cache-dependency-path: backend/requirements.txt` means the pip cache is invalidated only when
`requirements.txt` changes. If `requirements-dev.txt` (if it exists) changes independently, the
cache is stale. Should use a glob pattern.

**Fix:** Change to `cache-dependency-path: backend/requirements*.txt`

---

### CI-004: `MishaKav/pytest-coverage-comment@main` uses floating `@main` ref
**File:** `.github/workflows/ci-cd.yml:129`
**Priority:** Medium — supply chain risk

Pinning to `@main` means any future push to that repo's main branch is automatically trusted and
executed in CI. The trivy-action compromise used exactly this vector. Should pin to a specific
commit SHA or tagged release.

**Fix:** Pin to latest tagged release, e.g. `MishaKav/pytest-coverage-comment@v1.3.2`

---

### CI-005: `dependency-review` job requires GitHub Dependency Graph (not enabled)
**File:** `.github/workflows/ci-cd.yml:213-226`
**Priority:** Medium — job always fails, adds noise, blocks PRs

`actions/dependency-review-action@v4` requires the repository to have Dependency graph enabled
in GitHub Settings → Security & Analysis. The feature is not enabled, so this job fails on every
PR with "Dependency review is not supported on this repository."

**Fix:** Either enable Dependency graph in repo settings (recommended — it's free and adds
vulnerability scanning to the dependency tab), or remove the job if not wanted.

---

### CI-006: `vitest-coverage-report-action` fails because coverage files are never generated
**File:** `.github/workflows/ci-cd.yml:73-78`
**Priority:** Medium — `frontend-quality` job always fails on PRs

The coverage report action expects `frontend/coverage/coverage-summary.json` and
`coverage-final.json`. These are only generated if Vitest is configured with a coverage provider.
Check `vite.config.ts` — if `test.coverage` is not configured, `npm test -- --run --coverage`
will run tests without coverage output and the action will fail with "file not found."

**Fix:** Verify `vite.config.ts` has:
```ts
test: {
  coverage: {
    provider: 'v8',
    reporter: ['json-summary', 'json', 'html']
  }
}
```
If coverage is not desired, remove the `--coverage` flag and the action step.

---

## DEBT — Performance

### PERF-001: Three.js imported statically — loads unconditionally in main bundle (~172KB gzipped)
**File:** `frontend/src/components/ThreeHeroBackground.vue:7`
**Priority:** Medium — biggest single avoidable cost on initial page load

Line 7: `import * as THREE from 'three'` is a static top-level import. This bundles all of
Three.js into the main chunk, which is parsed and executed on every page load even if WebGL is
unavailable or the hero section never renders.

The component itself is well-written: it checks for WebGL availability, handles visibility changes,
cleans up properly, and respects `prefers-reduced-motion`. The only problem is the static import.

**Fix:** Convert to a dynamic import inside `onMounted`:
```ts
onMounted(async () => {
  const THREE = await import('three')
  initScene(THREE)
  // ...
})
```
This moves Three.js into a separate async chunk that only loads when the hero section mounts.
Saves ~172KB from the initial parse cost. No visual change.

---

### PERF-002: GitHubStats component fetches data unconditionally on mount
**File:** `frontend/src/components/GitHubStats.vue`
**Priority:** Low

The component fetches GitHub API data as soon as it mounts, regardless of whether it is visible
in the viewport. On slow connections, this consumes bandwidth before the user has scrolled to the
section. Should use an `IntersectionObserver` to defer the fetch until the component is near the
viewport.

**Fix:** Wrap the initial fetch in an `IntersectionObserver` callback. The composable pattern
already used elsewhere in the codebase (AbortController) can be extended for this.

---

### PERF-003: No `font-display: swap` configured for web fonts
**File:** `frontend/src/styles/variables.css`
**Priority:** Low — risk of FOIT (Flash of Invisible Text) on slow connections

Font families are declared but if any web fonts are loaded (via Google Fonts CDN or `@font-face`),
there is no `font-display: swap` directive. Without it, browsers may show invisible text while the
font loads (FOIT). `swap` shows a fallback font immediately and swaps when ready (FOUT, which is
preferable).

**Fix:** Add `font-display: swap` to any `@font-face` declarations. If fonts are loaded via
Google Fonts CDN link, add `&display=swap` to the URL. Audit `index.html` for any font links.

---

## DEBT — Accessibility

### A11Y-001: Focus not moved to main content on route change (WCAG 2.2 SPA requirement)
**File:** `frontend/src/router/index.ts`
**Priority:** Medium — #1 most commonly missed accessibility requirement in Vue SPAs

The router's `afterEach` hook updates `document.title` (line 147, correct) and tracks analytics,
but does not move keyboard focus after navigation. For sighted users this is invisible — but
screen reader users navigate an SPA by listening for page load announcements. Without focus
management, they have no indication that the page changed and no efficient way to reach new
content.

WCAG 2.2 Success Criterion 2.4.3 requires that focus order is logical after navigation.

**Fix:** In `router.afterEach`, after the title update, focus the main `<h1>` or `<main>` element:
```ts
router.afterEach(() => {
  document.title = ...
  nextTick(() => {
    const main = document.querySelector('main, h1, [tabindex="-1"]')
    if (main instanceof HTMLElement) main.focus()
  })
})
```
The target element should have `tabindex="-1"` to be focusable without appearing in tab order.

---

### A11Y-002: WCAG 2.2 § 2.4.11 Focus Appearance — focus ring may not meet new requirements
**Files:** `frontend/src/assets/portfolio.css`, `frontend/src/style.css`
**Priority:** Low — WCAG 2.2 AA (new requirement, browsers vary in enforcement)

WCAG 2.2 introduced Success Criterion 2.4.11 (Focus Appearance) requiring focus indicators to:
- Have at least 3:1 contrast ratio between focused and unfocused states
- Enclose the component with a minimum area (perimeter × 2px)

The project has `focus-visible` styles (good) but they may not meet the new area/contrast
thresholds on all backgrounds, especially over the gradient hero and dark sections.

**Fix:** Audit focus ring styles against WCAG 2.2 § 2.4.11. Run axe-core or Deque's accessibility
checker on both light and dark mode with keyboard navigation. Common fix: increase focus outline
to `outline: 3px solid var(--link-color); outline-offset: 2px`.

---

### A11Y-003: ProjectCard icon-only links missing descriptive `aria-label`
**File:** `frontend/src/components/ProjectCard.vue`
**Priority:** Low

Links to GitHub and live demo use icon SVGs with `aria-hidden="true"` (correct), but the link
text "View Code" / "Live Demo" may not convey the project name to screen readers. A user tabbing
through multiple project cards will hear "View Code, View Code, View Code" with no context.

**Fix:** Add `aria-label` to each link:
```html
<a :aria-label="`View code for ${project.name} on GitHub`" ...>
```

---

## DEBT — Backend

### BE-001: `Project.technologies` JSON column has no schema validation
**File:** `backend/app/models/project.py`
**Priority:** Medium — malformed API response crashes frontend rendering

The `technologies` column is `Column(JSON)`, which accepts any JSON value. If a bad record is
inserted with `technologies: "javascript"` (string instead of array), the frontend's
`v-for="tech in project.technologies"` will iterate over individual characters and render "j",
"a", "v", "a", "s" as separate badge elements.

**Fix:** Add a Pydantic validator on the schema layer to ensure `technologies` is always a list.
Alternatively, add a SQLAlchemy column default: `Column(JSON, nullable=False, default=list)`.

---

### BE-002: N+1 query risk on company endpoints
**File:** `backend/app/api/v1/companies.py`
**Priority:** Low — portfolio traffic is low, but worth fixing for correctness

If `Company` has a `projects` relationship and `company.to_dict()` accesses it, the list endpoint
triggers one query per company to load projects. With 10 companies this is 11 queries instead of 1.

**Fix:** Use SQLAlchemy `selectinload` or `joinedload` on the list query:
```python
select(Company).options(selectinload(Company.projects)).order_by(Company.order_index)
```

---

### BE-003: CSP `frame-src` allows `https://www.google.com` (overly broad)
**File:** `backend/app/main.py`
**Priority:** Low — allows any Google-served content in iframes, not just Maps

The Content-Security-Policy `frame-src` directive includes `https://www.google.com` which allows
any Google-hosted page to be embedded, not just Maps embeds. Should be restricted to the Maps
embed path.

**Fix:** Replace `https://www.google.com` with `https://www.google.com/maps` in the CSP header.

---

### BE-004: Dev/CI tools bundled in production `requirements.txt`
**File:** `backend/requirements.txt`
**Priority:** Low — increases production image size and attack surface

Tools only needed in CI or locally (`bandit`, `mypy`, `pip-audit`, `pre-commit`, `ruff`) are in
the same requirements file as production dependencies. This means production deployments install
linters and security auditors unnecessarily.

**Fix:** Split into `requirements.txt` (runtime only) and `requirements-dev.txt` (CI + local).
Update CI to `pip install -r requirements.txt -r requirements-dev.txt` and Dockerfile to only
install `requirements.txt`.

---

## DEBT — CSS (Additional)

### CSS-001: Z-index values hardcoded as `9999` instead of using defined tokens
**Files:** `frontend/src/App.vue:43`, `frontend/src/components/LoadingSpinner.vue:57`
**Priority:** Low

`variables.css` defines `--z-index-*` tokens but at least two components hardcode `z-index: 9999`:
- `.skip-link` in `App.vue`
- `.loading-container.full-screen` in `LoadingSpinner.vue`

**Fix:** Use the defined tokens, e.g. `z-index: var(--z-index-tooltip)` or add a
`--z-index-overlay: 9999` token and reference it.

---

### CSS-002: Hardcoded hex colors in `portfolio.css` that should use CSS variables
**File:** `frontend/src/assets/portfolio.css`
**Priority:** Low — these won't break but undermine the token system

Lines 424 and 432 use hardcoded `#3b82f6` and `#60a5fa` in gradients instead of
`var(--primary-500)` and `var(--primary-400)`. If the primary brand color is ever updated in
`variables.css`, these won't follow.

**Fix:** Replace hardcoded primary hex values with `var(--primary-500)` / `var(--primary-400)`.

---

## EVAL — Architecture Evaluations

### EVAL-001: Evaluate SSG (Static Site Generation) for performance
**Priority:** Medium — significant TTFB improvement possible

For a portfolio site, the content is largely static (loaded from the API at admin time, then
unchanged for days). Switching to static site generation would pre-render pages at build time,
dropping TTFB from ~280ms to ~12ms.

Options:
- **Vite SSG** (`vite-ssg` plugin): minimal change, keeps current Vue/Vite setup, generates static
  HTML for each route at build time
- **Nuxt 3 with `nuxt generate`**: full migration, more ecosystem support, more complex

Tradeoffs to evaluate:
- Admin panel still needs to be a dynamic SPA (auth-gated routes)
- API data that changes (admin edits) would require a rebuild to reflect — acceptable for a
  portfolio, but needs a trigger (GitHub Actions on content change, webhook, etc.)
- Vercel already does edge caching of the SPA, so real-world gains may be smaller than theoretical

**Action:** Spike `vite-ssg` on a branch to assess migration effort before committing.

---

### EVAL-002: GitHub username in `GitHubStats.vue` — move to `config.ts`
**File:** `frontend/src/components/GitHubStats.vue`
**Priority:** Low — cosmetic, no functional impact

The GitHub username `'Dashtid'` is hardcoded in the component. The project already has a
`frontend/src/config.ts` file with site-level constants. Moving this there is a 5-minute cleanup
that separates configuration from component logic.

**Fix:** Add `githubUsername: 'Dashtid'` to `config.ts` and import it in `GitHubStats.vue`.

---

## Notes

**What is in good shape:**
- Security: DOMPurify sanitization, YouTube/Maps domain allowlisting, HTTPS-only embeds, no creds in localStorage
- Router: `document.title` updated on every route change (line 147 of `router/index.ts`), analytics tracking
- Accessibility: skip-to-main, ARIA labels, focus-visible outlines, high-contrast mode, reduced-motion support
- Performance: AVIF/WebP responsive images, service worker caching, GSAP context cleanup, visibility-aware Three.js pause
- TypeScript: strong types, Zod validation, no implicit any in components reviewed
- Request lifecycle: AbortController for cancellation, race condition protection in CompanyDetailView
- Three.js: WebGL availability check, proper geometry/material/renderer disposal in `onBeforeUnmount`
