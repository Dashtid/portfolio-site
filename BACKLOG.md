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

### DEBT-011: `ExperienceDetail.vue` — unclear if active or abandoned
**File:** `frontend/src/views/experience/ExperienceDetail.vue`
**Priority:** Medium — unknown

A second experience detail view exists alongside `CompanyDetailView.vue`. Whether it is routed,
used, or a superseded earlier version is unknown without reading the router. If it is unused, it
should be deleted. If it serves a different purpose, it should be documented.

**Fix:** Read `frontend/src/router/index.ts`, determine whether this view is reachable, and either
route it correctly or delete it.

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

## Notes

**What is in good shape:**
- Security: DOMPurify sanitization, YouTube/Maps domain allowlisting, HTTPS-only embeds, no creds in localStorage
- Accessibility: skip-to-main, ARIA labels, focus-visible outlines, high-contrast mode, reduced-motion support
- Performance: Three.js lazy loaded, AVIF/WebP responsive images, service worker caching, GSAP context cleanup
- TypeScript: strong types, Zod validation, no implicit any in components reviewed
- Request lifecycle: AbortController for cancellation, race condition protection in CompanyDetailView
