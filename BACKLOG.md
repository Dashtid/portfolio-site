# Portfolio Site Backlog

Work items for tidying up the project. No new features — bugs, CSS architecture debt, and code quality.

---

## BUG — Resolved

### BUG-001: Video/map embed headings don't align horizontally when title wraps
**Files:** `frontend/src/components/VideoEmbed.vue`, `frontend/src/components/MapEmbed.vue`
**Priority:** High — visually broken
**Status: FIXED** in PR #48 (2026-03-25)

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
**Status: FIXED** in PR #48 (2026-03-25)

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
**Status: FIXED** in PR #48 (2026-03-25)

Both components use Bootstrap's `--bs-body-color` for heading color. Bootstrap 5 is loaded from CDN
without dark mode configuration, so `--bs-body-color` does not update when `[data-theme='dark']` is
set. In dark mode, headings may render in Bootstrap's default light-mode body color instead of the
project's `--text-primary`.

**Fix:** Replace `var(--bs-body-color)` with `var(--text-primary)` in both components.

---

### BUG-004: `--border-color` is used but never defined
**Files:** `frontend/src/components/VideoEmbed.vue:143`, `frontend/src/components/MapEmbed.vue:129`
**Priority:** Low — always falls back to hardcoded value, but dark mode border is wrong
**Status: FIXED** in PR #48 (2026-03-25)

The fallback containers for both embed components use `var(--border-color, #e2e8f0)`. Neither
`variables.css` nor `portfolio.css` defines `--border-color` — the project uses `--border-primary`
and `--color-border` for borders. The fallback `#e2e8f0` is the light-mode border color and is
always used, meaning dark mode gets a light border on a dark fallback box.

**Fix:** Replace `var(--border-color, #e2e8f0)` with `var(--border-primary)` in both components.
The dark mode value is already correctly defined in `variables.css` as `#334155`.

---

## DEBT — CSS Architecture

### DEBT-001: Duplicate `:root` variable definitions across two CSS files
**Files:** `frontend/src/assets/portfolio.css:4-69`, `frontend/src/styles/variables.css`
**Priority:** Medium | **Effort:** 1-2 hours
**Risk:** Medium — removing the block changes effective values for `--radius-sm`, `--shadow-md`

#### Current code

`frontend/src/assets/portfolio.css` lines 4–69 defines a full `:root` block duplicating tokens
already in `variables.css`. Confirmed collisions with differing values:

| Token | `variables.css` (canonical) | `portfolio.css` (wins, loaded last) |
|---|---|---|
| `--radius-sm` | `0.125rem` | `0.375rem` |
| `--radius-md` | `0.375rem` | `0.5rem` |
| `--radius-lg` | `0.5rem` | `0.75rem` |
| `--radius-xl` | `0.75rem` | `1rem` |
| `--shadow-md` | `rgb(0 0 0 / 0.07)` opacity | `rgba(0,0,0,10%)` opacity |
| `--bg-primary` | `#ffffff` | `var(--primary-50)` = `#eff6ff` |
| `--bg-secondary` | `#f8fafc` | `#fff` |

Import order in `frontend/src/main.ts`:
```ts
import './style.css'           // imports variables.css via @import
import './assets/portfolio.css' // loaded second — wins all conflicts
```

`portfolio.css` is always loaded last so its values silently override `variables.css` for every
colliding token. Any change made to `variables.css` for a colliding token has no effect.

#### Problem

1. `--radius-sm` in `variables.css` is `0.125rem` (2px) but components receive `0.375rem` (6px).
2. Dark mode overrides defined in `variables.css`'s `[data-theme='dark']` block for `--bg-primary`
   and `--bg-secondary` are silently cancelled by `portfolio.css`'s re-declaration.
3. Vite's `manualChunks` config can cause CSS extraction ordering regressions in production builds
   (vitejs/vite#6375, #20995) — making source-order reliance fragile in production.

#### Web research findings

- Best practice (2025): CSS custom properties should follow a strict single-source-of-truth
  pattern. All primitive tokens live in exactly one file; all other files only consume tokens, never
  redefine them. (DevToolbox Complete Guide, Smashing Magazine)
- `postcss-discard-duplicates` only removes identical property+value pairs. It cannot detect the
  same token name with different values across files — manual audit is required.
- Vite CSS extraction can change ordering relative to dev mode when `manualChunks` is configured,
  documented as a known issue. Production behavior should never depend on CSS load order.

#### Fix

**Step 1** — Verify which tokens in `portfolio.css:4-69` are absent from `variables.css`.
The following tokens exist in `portfolio.css` but not `variables.css` and must be added before
removing the block:
```css
/* Add to variables.css :root block */
--primary-50:  #eff6ff;
--primary-100: #dbeafe;
--primary-200: #bfdbfe;
--primary-300: #93c5fd;
--primary-900: #1e3a8a;
```

**Step 2** — Delete lines 4–69 (the entire `:root` block) from `portfolio.css`.

**Step 3** — Keep `portfolio.css`'s `[data-theme='dark']` block (lines ~72–87) only for tokens
not covered by `variables.css`'s dark-mode block. Cross-reference and remove any overlaps.

#### Testing

1. Run `npm run build` — no Vite CSS warnings.
2. DevTools → Computed → `--radius-sm`: confirm `0.125rem` (was `0.375rem`).
3. DevTools → Computed → `--shadow-md`: confirm `rgb(0 0 0 / 0.07)` syntax.
4. Toggle dark mode — `--bg-primary` resolves to `#0f172a`.
5. Visual regression: screenshot card components before and after — corner radii will visibly
   change since `--radius-*` values change throughout.

---

### DEBT-002: Slate palette inversion strategy is risky and undocumented
**Files:** `frontend/src/styles/variables.css:203-213`
**Priority:** High | **Effort:** 2-3 hours
**Risk:** High (Option A — remove inversion) | Low (Option B — document only)

#### Current code

`frontend/src/styles/variables.css` lines 203–213 inside `[data-theme='dark']`:
```css
/* Slate Aliases - Dark Mode (inverted for proper contrast) */
--slate-50: #0f172a;   /* was #f8fafc in light mode */
--slate-100: #1e293b;
--slate-200: #334155;
--slate-300: #475569;
--slate-400: #64748b;
--slate-500: #94a3b8;
--slate-600: #cbd5e1;
--slate-700: #e2e8f0;
--slate-800: #f1f5f9;
--slate-900: #f8fafc;  /* was #0f172a in light mode */
```

The numeric scale is fully reversed: light-mode `--slate-50` (near-white) becomes dark-mode
`#0f172a` (near-black), and vice versa.

#### Problem

1. **Semantic meaning breaks.** Code using `--slate-700` for body text gets `#334155` (dark, readable)
   in light mode but `#e2e8f0` (very light, near-invisible on dark bg) in dark mode — unless the
   developer knows about the inversion.
2. **Already caused BUG-002.** `.bg-dark` uses `var(--slate-800)` for background, which becomes
   `#f1f5f9` (near-white) in dark mode — the exact opposite of the intended dark section.
3. **Two parallel systems with no documented rule.** `variables.css` also defines semantic tokens
   (`--text-primary`, `--bg-primary`) that explicitly invert correctly. Components using semantic
   tokens are fine; those using raw `--slate-N` may break in dark mode silently.
4. **Dark Reader incompatibility.** The browser extension Dark Reader specifically misfires on
   inverted CSS variables, causing double-inversion for users who rely on it as an assistive tool.

#### Web research findings

- Mechanical palette inversion "cannot preserve color semantic relationships" — inverting `--slate-50`
  to `--slate-900` does not account for perceptual uniformity, so contrast ratios are unpredictable.
  (Medium: Color tokens guide for design systems)
- GitLab Pajamas, Tailwind v4, and all major design systems in 2025 use separate semantic token
  definitions per mode rather than inversion. The `--text-primary`/`--bg-primary` layer already in
  this codebase is the correct pattern; the `--slate-N` inversion is a competing second system.
  (GitLab Pajamas design tokens, Tailwind CSS v4 docs)
- Lea Verou's "Inverted Lightness Variables" technique (2021) describes the intent but explicitly
  warns it requires all consumers to use only the inverted tokens — mixing raw and semantic usages
  is the failure mode this codebase is experiencing.

#### Fix

**Option A (recommended): Remove the numeric slate inversion entirely.**

Delete `variables.css` lines 203–213 (the 10 `--slate-*` overrides in `[data-theme='dark']`).

Before removing: run `grep -rn "var(--slate-" frontend/src` and audit every hit. For each:
- If the usage is a background or text color: replace with the corresponding semantic token
  (`--text-primary`, `--bg-secondary`, etc.)
- If the usage is a border or shadow: check whether the semantic `--border-primary` covers it

After removal, add a comment above the dark-mode block:
```css
/*
 * Dark Mode Token Strategy
 * Only semantic tokens (--text-*, --bg-*, --border-*, --color-*) are
 * overridden here. Raw palette steps (--slate-N, --primary-N) keep
 * their light-mode numeric values in dark mode.
 * Components MUST use semantic tokens — never reference --slate-N
 * directly for color or background in component CSS.
 */
```

**Option B (lower risk): Document only, no behavior change.**

Add the same comment block without removing any code. Treat as a stopgap while auditing usages.

#### Testing

1. `grep -rn "var(--slate-" frontend/src` — produce a complete usage list.
2. For each hit, toggle dark mode and verify WCAG AA contrast (≥4.5:1) using DevTools color picker.
3. Run `npx axe-core` against the built app in dark mode — zero contrast failures.
4. Re-run BUG-002 scenario: Publications section must remain dark in dark mode.

---

### DEBT-003: `scroll-padding-top` defined twice with different values
**Files:** `frontend/src/style.css:15`, `frontend/src/assets/portfolio.css:266-269`
**Priority:** Low | **Effort:** 30 minutes
**Risk:** Low — `portfolio.css` value already wins; no visual change expected

#### Current code

`frontend/src/style.css` line 15:
```css
html {
  font-size: 16px;
  scroll-behavior: smooth;
  scroll-padding-top: 80px;   /* dead — overridden by portfolio.css */
}
```

`frontend/src/assets/portfolio.css` lines 266–269:
```css
html {
  scroll-behavior: smooth;
  scroll-padding-top: 72px;   /* effective value */
}
```

`portfolio.css` loads after `style.css`, so `72px` wins. The `80px` in `style.css` is permanently
dead code. `scroll-behavior: smooth` is also duplicated across both files.

#### Problem

`scroll-padding-top` controls how far the viewport scrolls when jumping to an anchor link
(`/#experience`, `/#projects`, etc.). It must equal the navbar height so section headings are not
hidden under the sticky navbar after scroll. Two values exist with no documentation indicating
which is correct. If the navbar height changes, both values must be updated independently.

#### Web research findings

- `scroll-padding-top` is Level 1 Scroll Snap, supported in all modern browsers (Chrome 69+,
  Firefox 68+, Safari 14.1+). The longhand is safe for 2025 targets. (MDN)
- Best practice: tie `scroll-padding-top` to the same CSS variable that controls navbar height
  (`--navbar-height`), so any navbar height change propagates automatically. (CSS-Tricks)
- Chrome DevTools shows overridden properties with strikethrough — this class of bug is trivially
  visible in any browser inspection session.

#### Fix

**Step 1** — Add `--navbar-height: 72px` to `variables.css` `:root` block:
```css
/* Layout */
--navbar-height: 72px;
```

**Step 2** — `frontend/src/style.css` lines 12–16:
```css
/* Before */
html {
  font-size: 16px;
  scroll-behavior: smooth;
  scroll-padding-top: 80px;
}

/* After */
html {
  font-size: 16px;
  scroll-behavior: smooth;
  scroll-padding-top: var(--navbar-height, 72px);
}
```

**Step 3** — Remove `scroll-padding-top` and the duplicate `scroll-behavior` from `portfolio.css`
lines 266–269 (or remove the `html` block entirely from `portfolio.css` once DEBT-004 is done).

**Step 4** — Update the navbar component's height rule to use the same token:
```css
.navbar { height: var(--navbar-height); }
```

#### Testing

1. Navigate to `/#experience`, `/#projects`, `/#education` via anchor links.
2. Confirm section headings are fully visible below the navbar (not hidden under it).
3. DevTools → Computed on `html` → `scroll-padding-top`: confirm `72px`.
4. Temporarily set `--navbar-height: 100px` in DevTools and confirm anchor offset updates live.

---

### DEBT-004: `body` styles defined twice with conflicting variables
**Files:** `frontend/src/style.css:28-38`, `frontend/src/assets/portfolio.css:271-284`
**Priority:** Medium | **Effort:** 1 hour
**Risk:** Medium — `font-synthesis`, `text-rendering`, `-webkit-font-smoothing` from `style.css`
must be preserved in the merged block

#### Current code

`frontend/src/style.css` lines 28–38:
```css
body {
  font-family: var(--font-family-base);
  line-height: var(--line-height-base);
  color: var(--color-gray-900);                                     /* dead */
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);  /* dead */
  min-height: 100vh;
  font-synthesis: none;
  text-rendering: optimizeLegibility;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
```

`frontend/src/assets/portfolio.css` lines 271–284 (wins — loaded last):
```css
body {
  font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, 'Roboto', sans-serif;
  font-size: var(--font-size-base);
  line-height: 1.5;
  color: var(--text-primary);
  background-color: var(--bg-primary);
  margin: 0;
  padding: 0;
}
```

Active (from `portfolio.css`) vs dead (from `style.css`) properties per merge:

| Property | `style.css` | `portfolio.css` (wins) |
|---|---|---|
| `font-family` | `var(--font-family-base)` resolves to system-ui | `'Segoe UI', -apple-system...` hardcoded |
| `color` | `var(--color-gray-900)` = `#0f172a` always | `var(--text-primary)` — correct in dark mode |
| `background` | gradient `#f5f7fa → #c3cfe2` | `var(--bg-primary)` solid token |
| `font-synthesis` | `none` — active, not overridden | absent |
| `-webkit-font-smoothing` | `antialiased` — active | absent |

#### Problem

The gradient background in `style.css` is permanently dead. `color: var(--color-gray-900)` is dead
and would have been broken in dark mode (raw palette token, not semantic). The `font-synthesis`
and `-webkit-font-smoothing` declarations survive only because `portfolio.css` doesn't redeclare
them — if someone adds them to `portfolio.css`, they could be accidentally changed.

#### Web research findings

- Vue 3 global `body` styles belong in one unscoped location. Splitting across multiple imported
  CSS files requires developers to check every file to understand the complete declaration.
  (DEV Community: Vue3 styling best practices)
- When multiple stylesheets define the same selector at equal specificity, each property is resolved
  independently — it is possible for different properties on the same element to come from different
  files with no single authoritative source. (MDN: Handling conflicts)

#### Fix

**Consolidate into `style.css`, delete `body` block from `portfolio.css`.**

Replace `style.css` lines 28–38 with the merged block:
```css
body {
  font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, 'Roboto', sans-serif;
  font-size: var(--font-size-base);
  line-height: var(--line-height-base);
  color: var(--text-primary);
  background-color: var(--bg-primary);
  margin: 0;
  padding: 0;
  min-height: 100vh;
  font-synthesis: none;
  text-rendering: optimizeLegibility;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
```

Delete lines 271–284 from `portfolio.css`.

The merged block uses `var(--text-primary)` (correct in dark mode) not `var(--color-gray-900)`
(always dark), and the semantic `var(--bg-primary)` (adapts per theme) not the hardcoded gradient
(permanently dead before this fix).

#### Testing

1. DevTools → body → Computed: confirm `font-family` starts with `"Segoe UI"`.
2. Confirm `background-color` is the semantic value (`#ffffff` light / `#0f172a` dark).
3. Confirm `-webkit-font-smoothing: antialiased` is present.
4. Toggle dark mode — `color` updates to `#f8fafc`.
5. No strikethrough rules on `body` in the Styles pane.

---

### DEBT-005: Custom `.container` class conflicts with Bootstrap
**Files:** `frontend/src/style.css:168-172`, `frontend/src/assets/portfolio.css:888-893`
**Priority:** Medium | **Effort:** 1-2 hours
**Risk:** High (rename option) | Low (consolidate option)

#### Current code

Bootstrap 5.3.3 loaded via CDN in `frontend/index.html:62` sets `.container` with responsive
`max-width` values per breakpoint (1140px at xl, 1320px at xxl). Three `.container` rules active:

`frontend/src/style.css` lines 168–172:
```css
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 var(--spacing-4);   /* = 16px */
}
```

`frontend/src/assets/portfolio.css` lines 888–893 (wins — loaded last):
```css
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 15px;
}
```

Bootstrap's responsive max-widths (1140px at xl, 1320px at xxl) are entirely overridden to a
fixed 1200px. Bootstrap's `--bs-gutter-x` (0.75rem = 12px) horizontal padding is overridden to
15px without referencing the Bootstrap variable.

#### Problem

1. Bootstrap's `.container` responsive narrowing (1140px at xl) is permanently overridden. Any
   Bootstrap grid (`row`/`col-*`) that lives inside a `.container` loses the intended gutter
   compensation at xl+ viewports.
2. The padding differs between the two custom declarations (16px vs 15px), and neither references
   Bootstrap's `--bs-gutter-x` variable, so Bootstrap's grid gutters may not align with the
   container padding at all viewport sizes.
3. Three competing `.container` rules with no clear canonical owner.

#### Web research findings

- Bootstrap 5 namespaces its CSS variables with `--bs-` to allow overrides. The recommended
  approach for changing `.container` padding is overriding `--bs-gutter-x`, not redeclaring the
  entire class. (Bootstrap 5.3 Containers docs)
- Redefining `.container` after Bootstrap silently makes grid column classes unreliable because
  Bootstrap's column math is designed for `--bs-gutter-x`. (Bootstrap CSS variables docs)
- The `.container` name collision is a well-known Bootstrap pitfall. The recommended avoidance
  strategy: rename custom page-width wrappers (e.g. `.site-container`) to eliminate the conflict.
  (copyprogramming: override Bootstrap container)

#### Fix

**Option A (recommended): Rename to `.site-container` — eliminates the conflict entirely.**

In both `style.css` and `portfolio.css`:
```css
/* Before */
.container { max-width: 1200px; margin: 0 auto; padding: 0 15px; }

/* After — in style.css only, delete portfolio.css version */
.site-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 var(--spacing-4);
}
```

Then grep all `.vue` files: elements that are page-width wrappers (not parents of `col-*` children)
should use `.site-container`. Elements that are Bootstrap grid containers keep `.container`.

**Option B (lower risk): Consolidate to one rule, add explanatory comment.**

Delete `style.css`'s `.container`. In `portfolio.css` replace with a single documented rule:
```css
/* Intentionally overrides Bootstrap .container max-width to 1200px.
   Bootstrap xl (1140px) and xxl (1320px) breakpoints are replaced. */
.container {
  max-width: 1200px;
  margin-right: auto;
  margin-left: auto;
  padding-right: var(--spacing-4);
  padding-left: var(--spacing-4);
}
```

#### Testing

**Option A:** Grep for `class="container"` in all `.vue` files. Verify every Bootstrap grid
structure keeps `.container`, every page-width wrapper becomes `.site-container`. Test at 1199px,
1200px, 1400px viewport widths.

**Option B:** DevTools → select a `.container` element → Styles: confirm only one `.container`
rule active (no strikethrough). `max-width` computed = `1200px`. `padding-left` = `16px`.

---

## DEBT — Component Code Quality

### DEBT-006: `DocumentCard.vue` uses hardcoded hex colors throughout
**File:** `frontend/src/components/DocumentCard.vue`
**Priority:** Medium
**Risk:** Low

#### Current code

`frontend/src/components/DocumentCard.vue` lines 141-276 (base styles and theme override blocks):

```css
/* line 144 */
.document-title       { color: #f8fafc; }         /* hardcoded slate-50 */
/* line 153 */
.document-type        { color: #93c5fd; }         /* hardcoded primary-300 */
/* line 161 */
.document-description { color: #cbd5e1; }         /* hardcoded slate-300 */
/* line 178 */
.meta-item            { color: #94a3b8; }         /* hardcoded slate-400 */
/* line 184 */
.icon                 { color: #94a3b8; }         /* hardcoded slate-400 */
/* line 197 */
.document-link        { color: #93c5fd; }         /* hardcoded primary-300 */
/* line 210 */
.document-link:hover  { color: #bfdbfe; }         /* hardcoded primary-200 */

/* light theme overrides -- lines 248-276 */
[data-theme='light'] .document-title        { color: #1e293b; }  /* slate-800 */
[data-theme='light'] .document-type         { color: #2563eb; }  /* primary-600 */
[data-theme='light'] .document-description  { color: #475569; }  /* slate-600 */
[data-theme='light'] .meta-item,
[data-theme='light'] .icon                  { color: #64748b; }  /* slate-500 */
[data-theme='light'] .document-link         { color: #2563eb; }  /* primary-600 */
[data-theme='light'] .document-link:hover   { color: #1d4ed8; }  /* primary-700 */
```

There are 13 distinct hardcoded hex values. The base styles assume a dark background (the
component lives inside the `.bg-dark` Publications section); the light-theme block overrides
every color individually. The project already defines all needed tokens in
`frontend/src/assets/portfolio.css`: `--slate-50` through `--slate-900`, `--primary-200`
through `--primary-700`.

#### Problem

Hardcoded hex values break the cascade: they do not respond to `[data-theme]` changes unless
explicitly overridden in every theme selector block. The `[data-theme='light']` block
demonstrates the tax -- every color property needs a redundant rule. CSS custom properties
eliminate this: one token update in `portfolio.css` propagates to all references automatically.

This hardcoding is also the reason BUG-002 was hard to catch. When `.bg-dark` rendered with a
light background in dark mode (slate palette inversion bug), the hardcoded `#f8fafc` title color
had no mechanism to respond -- it stayed near-white on a near-white background. A token-based
color would have made the relationship explicit and auditable.

#### Web research findings

- CSS custom properties resolve at computed-value time. A `[data-theme='dark']` on `:root`
  automatically re-resolves all `var()` references in child elements. Hardcoded values cannot
  participate in this mechanism (MDN, CSS-Tricks).
- The semantic token pattern (`--text-primary` -> `--slate-900` / `--slate-50`) is the current
  industry standard. This component lives on a `.bg-dark` surface always, so using `--slate-*`
  palette tokens directly is more explicit than `--text-primary` (which is a page-level token
  that flips with the theme, not with the surface background).
- Smashing Magazine CSS strategy guide: "If you find yourself writing the same hex value more
  than once, it belongs in a custom property."

#### Fix

Replace each hardcoded value with the equivalent palette token. The `[data-theme='light']`
override block can remain for the white-card styling but should also reference tokens.

Before (`frontend/src/components/DocumentCard.vue` line 144):
```css
color: #f8fafc; /* slate-50 - always light for dark bg */
```

After:
```css
color: var(--slate-50);
```

Full substitution map:

| Location | Before | After |
|---|---|---|
| `.document-title` (line 144) | `#f8fafc` | `var(--slate-50)` |
| `.document-type` color (line 153) | `#93c5fd` | `var(--primary-300)` |
| `.document-description` (line 161) | `#cbd5e1` | `var(--slate-300)` |
| `.meta-item` (line 178) | `#94a3b8` | `var(--slate-400)` |
| `.icon` (line 184) | `#94a3b8` | `var(--slate-400)` |
| `.document-link` color (line 197) | `#93c5fd` | `var(--primary-300)` |
| `.document-link:hover` (line 210) | `#bfdbfe` | `var(--primary-200)` |
| `[data-theme='light'] .document-title` (line 249) | `#1e293b` | `var(--slate-800)` |
| `[data-theme='light'] .document-type` (line 253) | `#2563eb` | `var(--primary-600)` |
| `[data-theme='light'] .document-description` (line 258) | `#475569` | `var(--slate-600)` |
| `[data-theme='light'] .meta-item, .icon` (line 261) | `#64748b` | `var(--slate-500)` |
| `[data-theme='light'] .document-link` (line 271) | `#2563eb` | `var(--primary-600)` |
| `[data-theme='light'] .document-link:hover` (line 275) | `#1d4ed8` | `var(--primary-700)` |

Note: `rgba(96, 165, 250, 0.2)` semi-transparent backgrounds (lines 152, 206, 211) cannot
reference a hex token inside `rgba()`. Leave those as-is or define `--primary-alpha-20` tokens
in a future CSS cleanup.

#### Testing

1. Toggle `[data-theme='dark']` / `[data-theme='light']` on `<html>` in DevTools. All card
   text must remain readable in both modes.
2. After BUG-002 is fixed (dark bg stays dark in dark mode), confirm title text is legible on
   the dark Publications section -- `var(--slate-50)` resolves correctly in both modes via the
   slate palette inversion strategy.
3. Verify no contrast-ratio Lighthouse warnings for card text in either theme.

---

### DEBT-007: `ErrorBoundary.vue` component exists but is not used
**File:** `frontend/src/components/ErrorBoundary.vue`
**Priority:** Low
**Risk:** Low

#### Current code

`frontend/src/components/ErrorBoundary.vue` is a complete, well-implemented component (304
lines):
- Uses `onErrorCaptured` (line 88) to catch descendant render/lifecycle errors
- Shows fallback UI with "Try Again" and "Go to Homepage" buttons (lines 28-31)
- Exposes `showError()` and `hasError` via `defineExpose` for manual triggering (lines 128-131)
- Returns `false` from `onErrorCaptured` (line 103) to stop propagation to parent components
- Logs to `errorLogger` (line 89) and optionally to `window.analytics` (lines 95-100)

`frontend/src/App.vue` lines 19-27 -- no `<ErrorBoundary>` in template, not imported:
```html
<template>
  <a href="#main-content" class="skip-link">Skip to main content</a>
  <router-view v-slot="{ Component, route }">
    <Transition name="page-fade" mode="out-in">
      <component :is="Component" :key="route.path" />
    </Transition>
  </router-view>
  <ToastContainer />
</template>
```

`frontend/src/main.ts` lines 32-52 -- a global `app.config.errorHandler` reports all Vue errors
to `errorTracker` and Sentry. `ErrorBoundary.vue` is imported nowhere in the codebase (confirmed:
zero references across all `.vue` and `.ts` files).

#### Problem

A component that is not mounted provides zero protection. `onErrorCaptured` only fires for errors
in the mounted component's descendant subtree during Vue render or lifecycle phase.

The global `app.config.errorHandler` handles logging and Sentry reporting -- it cannot render a
fallback UI in place of a broken component. Without `ErrorBoundary`, a render-time throw in any
view leaves the user with a blank white screen and no error feedback.

Known limitation: `onErrorCaptured` does NOT catch errors in DOM event handlers (e.g. `@click`
methods). It covers: `setup()`, lifecycle hooks, watchers, template render functions, and
component event emitter handlers. Async errors require explicit handling inside the boundary.

#### Web research findings

- Vue 3 docs: "errorCaptured is called when an error propagating from a descendant component
  is captured." Subtree mechanism only -- the component must be in the tree.
- Established pattern (enterprisevue.dev, Vue School): use `app.config.errorHandler` for
  centralized logging; use `<ErrorBoundary>` for sections where a render failure should show an
  inline fallback rather than a blank page.
- The two mechanisms complement each other. `ErrorBoundary.vue` calls `errorLogger.error`
  (line 89) before `return false` -- the global handler is NOT invoked after `return false`,
  so the boundary handles its own logging. This is correct behavior.

#### Fix

**Option A (recommended): wrap the router-view as a global catch-all.**

Before (`frontend/src/App.vue` -- script section and template):
```html
<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuthStore } from './stores/auth'
import ToastContainer from './components/ToastContainer.vue'
</script>
<template>
  <router-view v-slot="{ Component, route }">
    <Transition name="page-fade" mode="out-in">
      <component :is="Component" :key="route.path" />
    </Transition>
  </router-view>
</template>
```

After:
```html
<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuthStore } from './stores/auth'
import ToastContainer from './components/ToastContainer.vue'
import ErrorBoundary from './components/ErrorBoundary.vue'
</script>
<template>
  <ErrorBoundary>
    <router-view v-slot="{ Component, route }">
      <Transition name="page-fade" mode="out-in">
        <component :is="Component" :key="route.path" />
      </Transition>
    </router-view>
  </ErrorBoundary>
</template>
```

**Option B (delete):** If `app.config.errorHandler` + Sentry is deemed sufficient and no inline
fallback UI is wanted, delete `ErrorBoundary.vue`. Dead code that is never executed creates false
confidence.

**Option C (targeted):** Mount `<ErrorBoundary>` around specific high-risk sections (Publications
card grid, GitHub stats widget) instead of the entire router-view.

#### Testing

1. Temporarily add `throw new Error('test boundary')` inside any view's `onMounted`.
2. Verify fallback UI ("Oops! Something went wrong", retry and home buttons) renders instead of
   a blank screen.
3. Verify the error is logged via `errorLogger` (line 89 runs before `return false`).
4. Verify "Try Again" reloads the page (default when no `onRetry` prop is provided).
5. Verify "Go to Homepage" navigates to `/` and clears `hasError` to `false`.
6. Remove the test throw and confirm normal navigation resumes.

---

### DEBT-008: `VideoEmbed.vue` and `MapEmbed.vue` are near-identical
**Files:** `frontend/src/components/VideoEmbed.vue`, `frontend/src/components/MapEmbed.vue`
**Priority:** Low
**Risk:** Low

#### Current code

`VideoEmbed.vue` (166 lines) and `MapEmbed.vue` (152 lines) share the following identical blocks:

**Props interface** -- VideoEmbed.vue lines 43-47, MapEmbed.vue lines 34-38 (byte-for-byte):
```ts
interface Props {
  url: string
  title?: string
  heading?: string | null
}
```

**URL validation logic** -- VideoEmbed.vue lines 63-99, MapEmbed.vue lines 49-86. Structurally
identical; only the allowed host list and path prefix differ:
```ts
// VideoEmbed: ALLOWED_VIDEO_HOSTS, parsed.pathname.startsWith('/embed/')
// MapEmbed:   ALLOWED_MAP_HOSTS,   parsed.pathname.startsWith('/maps/embed')
```
The entire `try/catch` block, HTTPS protocol check, host allowlist check, path prefix check,
and DEV-only warning pattern are byte-for-byte identical across both files.

**CSS** -- VideoEmbed.vue lines 103-165, MapEmbed.vue lines 89-151. Byte-for-byte identical
except class name prefixes (`.video-*` vs `.map-*`). The `.ratio`, `.fallback-icon`,
`.fallback-text`, and `[data-theme='dark']` fallback blocks contain the same declarations.

This duplication has already caused maintenance drag: BUG-001 (heading alignment), BUG-003
(heading color), and BUG-004 (border variable) each required the same fix applied to both files.

#### Problem

- Any future bug fix or style change must be applied twice.
- The scoped `.ratio` CSS is defined in both files -- identical redundancy.
- A new embed type would require a full copy of both components.

#### Web research findings

- Vue 3 Composition API best practice: extract shared stateful logic into composables. Composables
  compose; base component inheritance couples structure.
- For two components with nearly identical validation logic but legitimately different templates
  (video `<iframe>` needs `allow="accelerometer; autoplay; ..."` and `referrerpolicy=
  "strict-origin-when-cross-origin"`; map iframe needs `referrerpolicy="no-referrer-when-downgrade"`
  and no `allow` attribute), a shared composable is the correct minimum refactor without forcing
  a single template.
- A `BaseEmbed.vue` slot-based approach adds value only when templates are also structurally
  identical. These two diverge enough in iframe attributes to justify keeping separate templates.

#### Fix

**Step 1 -- Extract URL validation into a composable.**

Create `frontend/src/composables/useEmbedValidator.ts`:
```ts
import { computed, type Ref } from 'vue'

export function useEmbedValidator(
  url: Ref<string>,
  allowedHosts: string[],
  requiredPathPrefix: string,
  debugLabel: string
) {
  return computed<string | null>(() => {
    if (!url.value) return null
    try {
      const parsed = new URL(url.value)
      if (parsed.protocol !== 'https:') {
        if (import.meta.env.DEV)
          console.warn(`[${debugLabel}] Blocked non-https URL: ${url.value}`)
        return null
      }
      if (!allowedHosts.includes(parsed.hostname)) {
        if (import.meta.env.DEV)
          console.warn(`[${debugLabel}] Blocked disallowed host: ${url.value}`)
        return null
      }
      if (!parsed.pathname.startsWith(requiredPathPrefix)) {
        if (import.meta.env.DEV)
          console.warn(`[${debugLabel}] Blocked non-embed path: ${url.value}`)
        return null
      }
      return url.value
    } catch {
      if (import.meta.env.DEV)
        console.warn(`[${debugLabel}] Invalid URL: ${url.value}`)
      return null
    }
  })
}
```

**Step 2 -- Update `VideoEmbed.vue` script** (replace lines 34-100):
```ts
import { toRef } from 'vue'
import { useEmbedValidator } from '@/composables/useEmbedValidator'

const ALLOWED_VIDEO_HOSTS = [
  'www.youtube.com', 'youtube.com',
  'www.youtube-nocookie.com', 'youtube-nocookie.com'
]
const safeUrl = useEmbedValidator(
  toRef(props, 'url'), ALLOWED_VIDEO_HOSTS, '/embed/', 'VideoEmbed'
)
```

**Step 3 -- Update `MapEmbed.vue` script** (replace lines 24-86):
```ts
import { toRef } from 'vue'
import { useEmbedValidator } from '@/composables/useEmbedValidator'

const ALLOWED_MAP_HOSTS = ['www.google.com', 'google.com', 'maps.google.com']
const safeUrl = useEmbedValidator(
  toRef(props, 'url'), ALLOWED_MAP_HOSTS, '/maps/embed', 'MapEmbed'
)
```

**Step 4 -- Extract shared CSS.** Move `.ratio`, `.fallback-icon`, `.fallback-text`, and
`[data-theme='dark'] .X-fallback` rules into `portfolio.css` or a shared `embed.css` partial,
using a single `.embed-fallback` class referenced in both templates.

The templates (iframe `allow` attributes, `referrerpolicy`, aria-labels) stay as separate `.vue`
files -- they legitimately differ.

#### Testing

1. Existing unit tests for both components must pass unchanged.
2. YouTube URL validation: `https://www.youtube.com/embed/abc` passes; `http://` blocked;
   `https://evil.com/embed/abc` blocked; `https://youtube.com/watch?v=abc` blocked (wrong path).
3. Google Maps URL validation: `https://www.google.com/maps/embed?pb=...` passes;
   `https://www.google.com/search?...` blocked (wrong path prefix).
4. Fallback UI (`v-else` block) renders when `safeUrl` returns `null`.
5. No `console.warn` in production builds -- guarded by `import.meta.env.DEV`.

---

## DEBT -- Housekeeping

### DEBT-009: Multiple stale artifact directories not excluded from the repo
**Files:** `frontend/.coverage/`, `frontend/coverage/`, `frontend/.playwright-report/`,
`frontend/playwright-report/`, `backend/htmlcov/`
**Priority:** Low
**Risk:** Low

#### Current state (verified)

All five directories exist in the working tree with generated content:

- `frontend/coverage/` -- Vitest HTML report (stale; pre-dates `reportsDirectory: '.coverage'`
  config in `vitest.config.ts` line 23; never auto-cleaned by Vitest)
- `frontend/.coverage/` -- Vitest HTML report (current; configured in `vitest.config.ts` line 23)
- `frontend/playwright-report/` -- Playwright HTML report (stale; Playwright default before
  `outputFolder: '.playwright-report'` was configured in `playwright.config.ts` line 16)
- `frontend/.playwright-report/` -- Playwright HTML report (current; `playwright.config.ts` line 16)
- `backend/htmlcov/` -- pytest-cov HTML report (current; generated by `--cov-report=html` in
  `backend/pyproject.toml` lines 155-156, no explicit path, defaults to `htmlcov/`)

Gitignore coverage -- all five ARE covered:
- `frontend/.gitignore` lines 15-19: `.coverage/`, `.playwright-report/`
- Root `.gitignore` lines 77-87: `coverage/`, `playwright-report/`, `frontend/.coverage/`,
  `frontend/coverage/`, `frontend/.playwright-report/`, `frontend/playwright-report/`, `htmlcov/`

The directories are untracked but clutter the working tree. Root cause: config changes moved the
output paths without cleaning old locations.

#### Problem

1. `vitest.config.ts` sets `reportsDirectory: '.coverage'`. Vitest's `coverage.clean: true`
   (default) deletes only `.coverage/` before each run -- `frontend/coverage/` (old default path)
   is never cleaned and grows stale.
2. `playwright.config.ts` sets `outputFolder: '.playwright-report'`. Playwright created the new
   dir but left `frontend/playwright-report/` (its default when `outputFolder` was unset).
3. `backend/pyproject.toml` line 155 uses `"--cov-report=html"` without a path argument --
   the `htmlcov/` output path is implicit.

#### Web research findings

- Vitest docs: `coverage.clean` (default `true`) deletes only the configured `reportsDirectory`.
  Stale paths at old locations persist forever and require manual deletion.
- Playwright docs: the HTML reporter's `outputFolder` defaults to `playwright-report/` in the CWD.
  Overriding in config creates the new path but does not remove the old one.
- pytest-cov: `--cov-report=html` without a colon writes to `htmlcov/`. Using
  `--cov-report=html:htmlcov` makes the path explicit with no behavior change.

#### Fix

**Step 1 -- Delete all five stale directories:**
```bash
rm -rf frontend/coverage frontend/.coverage \
       frontend/playwright-report frontend/.playwright-report \
       backend/htmlcov
```

**Step 2 -- Make the pytest-cov output path explicit.**

Before (`backend/pyproject.toml` line 155):
```toml
"--cov-report=html",
```

After:
```toml
"--cov-report=html:htmlcov",
```

No behavior change -- same output path. Documents intent explicitly.

**Step 3 -- Verify single output location per tool after deletion:**
- `cd frontend && npx vitest --coverage --run` -> only `frontend/.coverage/` created
- `cd frontend && npx playwright test` -> only `frontend/.playwright-report/` created
- `cd backend && python -m pytest` -> only `backend/htmlcov/` created

#### Testing

1. Delete all five directories. Run `git status` -- none should appear as untracked.
2. Run each test tool and verify only the configured output directory is created.
3. Run `git status` again -- generated dirs should remain untracked (gitignored).

---

### DEBT-010: Backend has three virtual environments
**Files:** `backend/.venv/`, `backend/.venv-new/`, `backend/.venv-pip/`
**Priority:** Low
**Risk:** Low

#### Current state (verified)

Three virtual environments exist side-by-side in `backend/`:

| Directory | Size | Created |
|---|---|---|
| `backend/.venv/` | 180 MB | Dec 1 (original uv environment) |
| `backend/.venv-new/` | 48 MB | Dec 14 (migration experiment) |
| `backend/.venv-pip/` | 137 MB | Dec 14 (pip-based experiment) |

Total: 365 MB. The project has `backend/uv.lock` (confirmed in directory listing), meaning `uv`
is the intended package manager. The uv default environment path is `.venv/`. Neither
`pyproject.toml` nor CI config overrides this. Root `.gitignore` lines 163-166 cover all three.

`.venv-new/` at 48 MB is significantly smaller than `.venv/` at 180 MB -- incomplete package
set. Activating it instead of `.venv/` would produce import errors during tests.

#### Problem

- 365 MB for one project's local environments.
- Ambiguity: `uv run` always uses `.venv/`, but a developer manually sourcing `.venv-new/` or
  `.venv-pip/` would silently use the wrong environment and see confusing failures.
- The `-new` and `-pip` suffixes indicate a pip-to-uv migration that was never completed.
- The Fly.io `Dockerfile` installs directly into the container -- none of these affect production.

#### Web research findings

- uv docs: uv creates and manages `.venv/` automatically. `uv sync` synchronizes the environment
  to `uv.lock`. No supported workflow exists for maintaining multiple named environments per project.
- 2026 best practice (Astral, Real Python): one `.venv/` per project, managed exclusively by
  `uv sync`. Use `uv sync --group dev` for optional dependency sets -- not separate venv dirs.
- The `python -m venv .venv-pip` + `pip install` workflow is the legacy pattern that `uv` replaces.
  Keeping the pip venv alongside the uv venv is a sign of an incomplete migration.

#### Fix

**Step 1 -- Verify `.venv/` is complete:**
```bash
cd backend
uv sync       # sync all deps per uv.lock
uv run pytest # confirm tests pass in .venv/
```

**Step 2 -- Delete the stale environments:**
```bash
rm -rf backend/.venv-new backend/.venv-pip
```

Reclaims 185 MB (48 + 137 MB).

**Step 3 -- Confirm gitignore coverage.** Root `.gitignore` lines 163-166 already cover all three.
No new entries needed.

**Step 4 -- Optional: document the canonical workflow** as a comment in `pyproject.toml`:
```toml
# Development: uv sync && uv run pytest
# Never use: python -m venv or pip install directly
```

#### Testing

1. Delete `.venv-new/` and `.venv-pip/`.
2. Run `uv sync` -- should complete without errors.
3. Run `uv run pytest` -- all tests should pass.
4. Run `git status` -- deleted directories should not appear.

---

### DEBT-011: Two experience detail views with overlapping purpose -- decide canonical route
**Files:** `frontend/src/views/experience/ExperienceDetail.vue` (`/experience/:id`),
`frontend/src/views/CompanyDetailView.vue` (`/company/:id`)
**Priority:** Low
**Risk:** Low (both functional; risk is future divergence and a security gap in ExperienceDetail)

#### Current code

`frontend/src/router/index.ts` lines 35-48 -- both routes registered simultaneously:
```ts
{
  path: '/company/:id',
  name: 'company-detail',
  component: CompanyDetailView,
  props: true,
  meta: { title: 'Experience | David Dashti' }
},
{
  path: '/experience/:id',
  name: 'experience-detail',
  component: ExperienceDetail,
  props: true,
  meta: { title: 'Experience | David Dashti' }
},
```

**`CompanyDetailView.vue`** (linked from home page): breadcrumb nav, company header, video/map
grid using `<VideoEmbed>` / `<MapEmbed>` with URL validation, description, technologies list.

**`ExperienceDetail.vue`**: adds a sticky Bootstrap navbar (lines 4-40) listing all companies
as router-links for lateral navigation. However, the media section (lines 62-100) renders raw
`<iframe>` elements directly, bypassing `<VideoEmbed>` / `<MapEmbed>`:

```html
<!-- ExperienceDetail.vue lines 68-83: raw iframe, NO URL validation -->
<iframe
  :src="company.video_url"
  :title="company.video_title || `${company.name} Video`"
  allow="accelerometer; autoplay; ..."
  allowfullscreen
  loading="lazy"
></iframe>
```

`CompanyDetailView.vue` uses `<VideoEmbed :url="company.video_url" .../>` which validates the
URL against `ALLOWED_VIDEO_HOSTS` and requires `parsed.pathname.startsWith('/embed/')`.
`ExperienceDetail.vue` bypasses this entirely.

Additional issue -- hardcoded hex in `ExperienceDetail.vue` line 437:
```css
.nav-link.active {
  background-color: #2563eb !important;  /* should be var(--primary-600) */
  border-color: #2563eb !important;
}
```

`vitest.config.ts` lines 37-38 excludes both views from coverage:
```ts
'src/views/CompanyDetailView.vue',
'src/views/experience/ExperienceDetail.vue'
```

#### Problem

1. **Security gap**: `ExperienceDetail.vue` bypasses the domain allowlist and path validation.
   A malformed or malicious `video_url` or `map_url` from the API would render directly in an
   `<iframe>` without the HTTPS-only, host allowlist, or path prefix checks.

2. **Maintenance tax**: BUG-001 (heading alignment) was fixed in the embed components, but
   `ExperienceDetail.vue` renders its own headings and iframes -- the visual bug independently
   exists there and has not been fixed.

3. **Coverage gap compounds the risk**: both views are excluded from unit tests, so the iframe
   security bypass is untested.

4. **Identical metadata**: same `meta.title`, same `:id` param, same data source.

#### Web research findings

- Vue Router supports `alias` as a first-class feature for multiple URL paths on one component.
  An alias does not redirect (no 301) -- both URLs resolve to the same component transparently.
- Vue Router docs: "An alias of /a as /b means when the user visits /b, the URL remains /b but
  it will be matched as if the user is visiting /a."
- "Browse mode" lateral navigation is standard to implement as an optional navbar slot or layout
  component in the canonical view, not as a separate duplicated view.

#### Fix

**Recommended: consolidate into `ExperienceDetail.vue` (it has the lateral nav), add
`/company/:id` as an alias to preserve existing links without a redirect.**

Step 1 -- In `ExperienceDetail.vue` lines 64-100, replace raw iframes with validated components:

Before:
```html
<div v-if="company.video_url" class="media-item">
  <h2>{{ company.video_title || `${company.name} Video` }}</h2>
  <div class="ratio ratio-16x9">
    <iframe :src="company.video_url" ...></iframe>
  </div>
</div>
```

After:
```html
<div v-if="company.video_url" class="media-item">
  <VideoEmbed
    :url="company.video_url"
    :title="company.video_title || `${company.name} Video`"
    :heading="company.video_title || `${company.name} Video`"
  />
</div>
```

Apply the same substitution for the map iframe.

Step 2 -- Fix the hardcoded hex in `ExperienceDetail.vue` line 437:

Before:
```css
.nav-link.active {
  background-color: #2563eb !important;
  color: white !important;
  border-color: #2563eb !important;
}
```

After:
```css
.nav-link.active {
  background-color: var(--primary-600) !important;
  color: white !important;
  border-color: var(--primary-600) !important;
}
```

Step 3 -- In `frontend/src/router/index.ts`, replace both route records with one using alias:

Before (lines 35-48):
```ts
{
  path: '/company/:id',
  name: 'company-detail',
  component: CompanyDetailView,
  ...
},
{
  path: '/experience/:id',
  name: 'experience-detail',
  component: ExperienceDetail,
  ...
},
```

After:
```ts
{
  path: '/experience/:id',
  name: 'experience-detail',
  alias: '/company/:id',
  component: ExperienceDetail,
  props: true,
  meta: { title: 'Experience | David Dashti' }
},
```

Step 4 -- Remove the `CompanyDetailView` import from `router/index.ts` (line 15).

Step 5 -- Delete `frontend/src/views/CompanyDetailView.vue`.

Step 6 -- Remove both views from the `vitest.config.ts` coverage exclusion list (lines 37-38)
once the raw iframe code is replaced.

#### Testing

1. Navigate to `/company/1` -- URL stays `/company/1`, `ExperienceDetail` renders (alias, no
   redirect). Navigate to `/experience/1` -- identical content, lateral nav present.
2. Verify the lateral navbar links use `/experience/:id` paths.
3. Verify video/map embeds now reject invalid URLs: pass `http://evil.com/embed/x` as
   `video_url` -- fallback UI renders, not a raw iframe.
4. Verify home page links (which use `/company/:id`) still resolve correctly.

---

### DEBT-012: `public/sw.js` may conflict with Vite PWA plugin's generated service worker
**File:** `frontend/public/sw.js`, `frontend/vite.config.ts`
**Priority:** Medium
**Risk:** Medium -- hand-written SW is dead code in production; cache strategies and versions diverge

#### Current code

`frontend/vite.config.ts` lines 15-118 -- VitePWA with default `generateSW` strategy (no
`strategies` key is set):
```ts
VitePWA({
  registerType: 'autoUpdate',
  workbox: {
    globPatterns: ['**/*.{js,css,html,ico,svg,woff2}'],
    runtimeCaching: [ /* 4 entries: API, images, fonts, Google Fonts */ ],
    skipWaiting: true,
    clientsClaim: true,
    cleanupOutdatedCaches: true
  },
  devOptions: { enabled: false }
})
```

`frontend/public/sw.js` (471 lines) -- hand-written service worker with:
- Own cache names: `dashti-portfolio-v4.3.0` / `dashti-api-v4.3.0` (lines 3-4, manual version)
- Own `STATIC_CACHE_URLS` precache list (lines 20-46)
- Install/activate/fetch/message/sync event handlers
- Request coalescing via `pendingRequests` Map (lines 19, 153-175)
- Navigation preload support (lines 93-98)
- Debug toggle via `postMessage` (lines 443-456)
- Background sync handler (lines 459-470)

#### Problem

With `generateSW` (current config), Workbox generates a complete `sw.js` in `dist/sw.js` at
build time. Vite also copies `public/sw.js` to `dist/sw.js` as a static asset. The Workbox-
generated file overwrites `public/sw.js` because the plugin's build step runs after Vite's
static file copy. **`public/sw.js` is dead code in production.** Any changes to it have no
effect on production behavior.

Additional consequences:

1. **Cache name mismatch.** The hand-written SW uses `dashti-portfolio-v4.3.0`. Workbox uses
   its own cache naming format. `cleanupOutdatedCaches: true` only removes Workbox-managed caches
   -- the hand-written cache names persist as orphans if a user has them from a dev session.

2. **Feature gap.** The hand-written SW implements request coalescing, navigation preload, a
   debug toggle, and background sync. None of these are in the Workbox config. The production SW
   silently lacks these features.

3. **Manual versioning.** `public/sw.js` line 2: `CACHE_VERSION = '4.3.0'` is manually bumped.
   The Workbox SW auto-versions via content hash. Two incompatible versioning strategies.

4. `devOptions: { enabled: false }` disables the plugin in development, meaning neither SW runs
   locally -- the hand-written SW cannot be tested in its intended environment.

#### Web research findings

- vite-plugin-pwa docs: in `generateSW` mode the plugin fully generates `sw.js` from Workbox
  config. `public/sw.js` is the source file only in `injectManifest` mode, where the plugin
  injects `self.__WB_MANIFEST` (the versioned precache manifest) into a developer-supplied file.
- vite-pwa/vite-plugin-pwa GitHub issue #268 confirms: using `public/sw.js` as source requires
  `strategies: 'injectManifest'`, `srcDir: 'public'`, `filename: 'sw.js'` in plugin config.
- `injectManifest` is the correct strategy when custom logic (coalescing, background sync,
  navigation preload, message handlers) is needed -- all of which `public/sw.js` implements.
  `generateSW` is for projects that want Workbox to handle everything with no custom code.

#### Fix

**Option A (recommended): switch to `injectManifest` to activate `public/sw.js`.**

Step 1 -- Add `self.__WB_MANIFEST` placeholder to `public/sw.js` after line 46:
```js
// Workbox injects the versioned precache manifest here at build time.
const WB_MANIFEST = self.__WB_MANIFEST || []
```

Merge into the install handler (around line 56):
```js
return cache.addAll([...STATIC_CACHE_URLS, ...WB_MANIFEST.map(e => e.url)])
```

Step 2 -- Update `frontend/vite.config.ts`:

Before (line 15):
```ts
VitePWA({
  registerType: 'autoUpdate',
  workbox: { ... },
```

After:
```ts
VitePWA({
  registerType: 'autoUpdate',
  strategies: 'injectManifest',
  srcDir: 'public',
  filename: 'sw.js',
  injectManifest: {
    globPatterns: ['**/*.{js,css,html,ico,svg,woff2}'],
    globIgnores: ['**/images/stockholm*', '**/images/optimized/*'],
    maximumFileSizeToCacheInBytes: 3 * 1024 * 1024,
  },
```

Remove the `workbox:` key entirely -- it is a `generateSW`-only option.

**Option B: delete `public/sw.js`, rely on the Workbox-generated SW.**

The Workbox config covers: API network-first, images cache-first, fonts cache-first, Google Fonts
stale-while-revalidate. Request coalescing, navigation preload, and the debug toggle are lost.

Step 1 -- Delete `frontend/public/sw.js`. No `vite.config.ts` changes needed.

#### Testing

1. Run `npm run build`. Inspect `dist/sw.js`:
   - Option A: contains hand-written code with an injected `self.__WB_MANIFEST = [...]` block.
   - Option B: Workbox boilerplate with precache manifest only.
2. Open built app in Chrome DevTools -> Application -> Service Workers. Confirm exactly one SW
   registered at `/sw.js`.
3. Application -> Cache Storage: confirm no orphaned `dashti-portfolio-v*` caches.
4. Disconnect network and reload -- static pages and API fallback should work.
5. Run `npm run build && npx lighthouse http://localhost:4173 --only-categories=pwa` -- PWA audit
   should pass, service worker detected.

---

---

## DEBT — CI/CD

### CI-001: `security-scan` used compromised `aquasecurity/trivy-action` — FIXED
**File:** `.github/workflows/ci-cd.yml` (lines 190–210)
**Status:** Fixed — direct binary download, merged 2026-03-25
**Risk:** N/A (resolved)

**What was there (before fix):**
```yaml
# OLD — do not restore
- uses: aquasecurity/trivy-action@0.29.0
  with:
    scan-type: fs
    format: sarif
    output: trivy-results.sarif
```

**What happened:**
On 2026-03-19 (~17:43 UTC), the threat actor "TeamPCP" used a stolen privileged GitHub token
(retained after an incomplete credential rotation from a February 2026 initial breach) to
force-push 75 of 76 version tags in the `aquasecurity/trivy-action` repository and all 7 tags in
`aquasecurity/setup-trivy`. Each redirected to a malicious commit that exfiltrated CI/CD
environment variables — including `GITHUB_TOKEN`, repository secrets, and cloud credentials — to
`scan.aquasecurtiy[.]org` (typosquat domain). The attack simultaneously weaponised the GitHub
Action, the `setup-trivy` action, and the core scanner binary (v0.69.4 on GitHub Releases).

**Confirmed fix in place** (lines 190–210):
```yaml
- name: Install Trivy CLI
  # Avoids aquasecurity/trivy-action which had a supply chain compromise in March 2026
  # (75 of 76 version tags force-pushed to serve malicious payloads)
  # Direct binary download from GitHub Releases is unaffected.
  env:
    TRIVY_VERSION: '0.62.0'
  run: |
    curl -sSfL "https://github.com/aquasecurity/trivy/releases/download/v${TRIVY_VERSION}/trivy_${TRIVY_VERSION}_Linux-64bit.tar.gz" -o trivy.tar.gz
    tar -xzf trivy.tar.gz trivy
    sudo mv trivy /usr/local/bin/trivy
    rm trivy.tar.gz
```

`v0.62.0` predates the compromise window. The malicious binary release was v0.69.4 only; earlier
releases are unaffected. The comment in the YAML correctly documents the reason.

**Web research findings:**
- 75/76 `trivy-action` tags and all 7 `setup-trivy` tags were compromised; the binary release
  channel was separately affected for v0.69.4 only — earlier releases are unaffected
  ([GHSA-69fq-xp46-6x23](https://github.com/aquasecurity/trivy/security/advisories/GHSA-69fq-xp46-6x23),
  [The Hacker News](https://thehackernews.com/2026/03/trivy-security-scanner-github-actions.html))
- Microsoft guidance recommends direct binary download or cosign verification as the mitigation
  ([Microsoft Security Blog 2026-03-24](https://www.microsoft.com/en-us/security/blog/2026/03/24/detecting-investigating-defending-against-trivy-supply-chain-compromise/))
- Wiz analysis: malicious code scanned environment variables, encrypted them, and exfiltrated via
  HTTP POST to a typosquat domain
  ([Wiz Blog](https://www.wiz.io/blog/trivy-compromised-teampcp-supply-chain-attack))
- GitGuardian: floating tags (`@main`, `@v1`, version tags without SHA pinning) are the primary
  attack surface for GitHub Actions supply chain compromises
  ([GitGuardian](https://blog.gitguardian.com/trivys-march-supply-chain-attack-shows-where-secret-exposure-hurts-most/))

**Testing:** Confirm the `security-scan` job passes on every push. Verify no `aquasecurity/trivy-action`
reference appears in `.github/workflows/`. SARIF output should appear in the repository Security tab.

---

### CI-002: `npm run lint --if-present` passes flag to the script instead of npm
**File:** `.github/workflows/ci-cd.yml:68`
**Priority:** Low — masked by `|| echo` fallback, semantically wrong, masks real lint failures

**Current code:**
```yaml
- name: Lint code
  run: npm run lint --if-present || echo "No lint script found"
```

**Problem:**
`npm run lint --if-present` passes `--if-present` as a command-line argument to the `lint`
script itself, not to npm. npm's `--if-present` flag — which silently exits 0 when the named
script does not exist — must appear before the script name: `npm run --if-present lint`.

In the current form: (a) `--if-present` is passed to ESLint as an unknown argument (ignored,
harmless today), and (b) genuine lint failures are silently swallowed by `|| echo`, meaning a
broken `.vue` or `.ts` file produces a green CI step. This is both semantically wrong and actively
hides regressions.

**Web research findings:**
- npm docs confirm the flag order: `npm run --if-present <script>` — the flag is a run-script
  option, not a script argument
  ([npm-run-script docs v11](https://docs.npmjs.com/cli/v11/commands/npm-run/))
- `--if-present` has been stable since npm v6; no behaviour change across v7–v11
- The `|| echo` pattern is a common anti-pattern: it prevents the step from failing on any non-zero
  exit, including genuine errors
  ([kollitsch.dev](https://kollitsch.dev/blog/2023/how-to-run-npm-scripts-without-issues-when-they-dont-exist/))

**Fix:**
```yaml
# Before (line 68):
run: npm run lint --if-present || echo "No lint script found"

# After:
run: npm run --if-present lint
```
Remove the `|| echo` fallback entirely. `--if-present` handles the missing-script case; a real
lint failure now correctly fails the step.

**Testing:**
1. Confirm `package.json` has a `lint` script — step runs and passes.
2. Temporarily rename the `lint` script to confirm the step exits 0 (no error) when absent.
3. Introduce a deliberate lint error in a `.ts` file and push — confirm CI now fails (it would
   not have before this fix due to the `|| echo` masking).

---

### CI-003: Python pip cache only hashes `requirements.txt`, misses `requirements-dev.txt`
**File:** `.github/workflows/ci-cd.yml:109`
**Priority:** Low — stale cache risk when dev dependencies change independently

**Current code:**
```yaml
- name: Setup Python
  uses: actions/setup-python@v6
  with:
    python-version: ${{ env.PYTHON_VERSION }}
    cache: 'pip'
    cache-dependency-path: backend/requirements.txt
```

**Problem:**
`cache-dependency-path` is the file whose hash forms the cache key. With a single explicit path,
the cache is only invalidated when `requirements.txt` changes. The install step (line 115) also
installs `pytest pytest-cov flake8` as bare strings — version changes to those packages are
invisible to the cache key. Once BE-004 splits the file into `requirements.txt` and
`requirements-dev.txt`, changes to only the dev file would restore a stale cache and skip
reinstalling updated packages, running tests against wrong versions.

**Web research findings:**
- `cache-dependency-path` accepts glob patterns and multi-line path lists
  ([actions/setup-python README](https://github.com/actions/setup-python))
- Official advanced usage example:
  ```yaml
  cache-dependency-path: |
    **/setup.cfg
    **/requirements*.txt
  ```
- A single-line glob `backend/requirements*.txt` matches both `requirements.txt` and
  `requirements-dev.txt` with no structural changes needed today; forward-compatible with BE-004
  ([GitHub Actions dependency caching docs](https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching))

**Fix:**
```yaml
# Before (line 109):
cache-dependency-path: backend/requirements.txt

# After:
cache-dependency-path: backend/requirements*.txt
```

**Testing:**
1. Modify `backend/requirements.txt` — Actions log should show "Cache miss" and reinstall.
2. After BE-004: modify only `requirements-dev.txt` — cache should also miss and reinstall.
3. An unmodified run should show "Cache hit" and skip the install network calls.

---

### CI-004: `MishaKav/pytest-coverage-comment@main` floating branch ref — supply chain risk
**File:** `.github/workflows/ci-cd.yml:129`
**Priority:** Medium — any commit to that repo's `main` executes here with `pull-requests: write`

**Current code:**
```yaml
- name: Comment coverage on PR
  if: github.event_name == 'pull_request'
  uses: MishaKav/pytest-coverage-comment@main
  with:
    pytest-xml-coverage-path: ./backend/coverage.xml
    junitxml-path: ./backend/pytest-report.xml
```

**Problem:**
`@main` is a mutable ref. Any commit pushed to `MishaKav/pytest-coverage-comment`'s `main`
branch is immediately trusted and executed in this workflow — with `pull-requests: write`
permission granted at the top of `ci-cd.yml`. This is structurally identical to the trivy-action
and `tj-actions/changed-files` (March 2025) attack vectors: a compromised upstream or malicious
maintainer pushes to `main` and gains write access to PR comments and all available secrets.

**Web research findings:**
- SHA pinning is the only immutable reference in GitHub Actions; tags and branches can be
  force-pushed
  ([StepSecurity guide](https://www.stepsecurity.io/blog/pinning-github-actions-for-enhanced-security-a-complete-guide),
  [blog.rafaelgss.dev](https://blog.rafaelgss.dev/why-you-should-pin-actions-by-commit-hash))
- GitHub added org-level SHA pinning enforcement in August 2025
  ([GitHub Changelog 2025-08-15](https://github.blog/changelog/2025-08-15-github-actions-policy-now-supports-blocking-and-sha-pinning-actions/))
- Best practice: pin to full commit SHA with a version comment so Dependabot can still detect
  upgrades; version tags (`@v1.9.0`) are an acceptable intermediate step
- `MishaKav/pytest-coverage-comment` publishes individual version tags; verify the current latest
  on the Releases page before pinning
  ([GitHub Marketplace](https://github.com/marketplace/actions/pytest-coverage-comment))

**Fix — option A (version tag, minimum acceptable):**
```yaml
# Before:
uses: MishaKav/pytest-coverage-comment@main

# After — verify current latest tag at github.com/MishaKav/pytest-coverage-comment/releases:
uses: MishaKav/pytest-coverage-comment@v1.9.0
```

**Fix — option B (commit SHA, recommended):**
```yaml
# Obtain SHA: git ls-remote https://github.com/MishaKav/pytest-coverage-comment refs/tags/v1.9.0
uses: MishaKav/pytest-coverage-comment@<full-40-char-sha>  # v1.9.0
```
Option B is recommended given the Trivy incident context. Use option A if Dependabot auto-updates
are preferred and org policy does not enforce SHA pinning.

**Testing:**
Open a PR after the change — confirm the coverage comment still appears. Verify the Actions log
shows the pinned ref rather than resolving `@main`.

---

### CI-005: `dependency-review` job requires Dependency Graph enabled (likely failing every PR)
**File:** `.github/workflows/ci-cd.yml` (lines 221–233)
**Priority:** Medium — job fails on every PR, adds noise, may block merges

**Current code:**
```yaml
dependency-review:
  runs-on: ubuntu-latest
  timeout-minutes: 5
  if: github.event_name == 'pull_request'
  steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Dependency Review
      uses: actions/dependency-review-action@v4
      with:
        fail-on-severity: high
        deny-licenses: GPL-3.0, AGPL-3.0
```

**Problem:**
`actions/dependency-review-action` calls the GitHub Dependency Review API, which requires the
Dependency graph feature to be enabled on the repository. For a public repository this is free
but opt-in — it is not enabled by default. When disabled, every PR fails with
`"Dependency review is not supported on this repository."`, blocking merges or producing a
persistent red check.

**Web research findings:**
- Dependency graph must be enabled at Settings → Security & analysis → Dependency graph
  ([GitHub Docs: configuring dependency review action](https://docs.github.com/en/code-security/supply-chain-security/understanding-your-software-supply-chain/configuring-the-dependency-review-action))
- For public repositories: Dependency graph is free; no GitHub Advanced Security (GHAS) license
  required — GHAS is only required for private repos
  ([About dependency review](https://docs.github.com/code-security/supply-chain-security/understanding-your-software-supply-chain/about-dependency-review))
- When enabled, the action compares the PR's dependency diff against the GitHub Advisory Database
  and blocks merges on high/critical CVEs — a meaningful control given `fail-on-severity: high`
- The `deny-licenses: GPL-3.0, AGPL-3.0` setting blocks accidental introduction of copyleft
  dependencies into this MIT-licensed project

**Fix:**
Enable the feature in GitHub repository settings (no code change required):
1. Go to the repository on GitHub.
2. Settings → Security & analysis.
3. Under "Dependency graph", click **Enable**.

The workflow is already correctly configured. If Dependency graph cannot be enabled, remove the
entire job rather than leave it silently failing:
```yaml
# Remove lines 221-233 (the entire dependency-review job block).
```

**Testing:**
After enabling: open a test PR and confirm the `dependency-review` job passes (green). To verify
blocking: add a package with a known high CVE to `package.json` in a test PR branch and confirm
the job fails as expected.

---

### CI-006: `vitest-coverage-report-action` fails — `test.coverage` block missing from `vite.config.ts`
**Files:** `.github/workflows/ci-cd.yml` (lines 70–78), `frontend/vite.config.ts`
**Priority:** Medium — `frontend-quality` fails on every PR because required JSON coverage files are never produced

**Current CI code (lines 70–78):**
```yaml
- name: Run unit tests
  run: npm test -- --run --coverage

- name: Comment coverage on PR
  if: github.event_name == 'pull_request'
  uses: davelosert/vitest-coverage-report-action@v2
  with:
    working-directory: ./frontend
    vite-config-path: ./vite.config.ts
```

**Current `frontend/vite.config.ts`:** No `test:` block exists anywhere in the file.

**Problem:**
`npm test -- --run --coverage` passes `--coverage` to Vitest. Without a `test.coverage` block,
Vitest has no configured coverage provider and generates no coverage files on disk. The
`davelosert/vitest-coverage-report-action@v2` action looks for `coverage/coverage-summary.json`
(default path, relative to `working-directory`) and fails with "file not found" on every PR.

Additionally, passing `--coverage` without `@vitest/coverage-v8` installed causes Vitest to exit
with an error prompting installation.

**Web research findings:**
- `davelosert/vitest-coverage-report-action@v2` requires the `json-summary` reporter; `json` is
  recommended for per-file detail; without both, the action has no data to comment with
  ([action README](https://github.com/davelosert/vitest-coverage-report-action))
- Default expected paths: `coverage/coverage-summary.json` and `coverage/coverage-final.json`
  (relative to `working-directory`)
- `@vitest/coverage-v8` must be installed as a dev dependency
  ([Vitest coverage guide](https://vitest.dev/guide/coverage))
- `reportOnFailure: true` is essential for CI: without it, a test failure also suppresses
  coverage file generation, causing a double failure
  ([Vitest config reference](https://vitest.dev/config/coverage))
- The action uses regex to parse `test.coverage.thresholds` directly from `vite-config-path`

**Fix — Step 1: install coverage provider**
```bash
cd frontend && npm i -D @vitest/coverage-v8
```

**Fix — Step 2: add `test.coverage` block to `frontend/vite.config.ts`**
Inside the `defineConfig({...})` call, after `optimizeDeps`:
```ts
// Before: no test block in vite.config.ts

// After — add inside defineConfig({...}):
test: {
  coverage: {
    provider: 'v8',
    reporter: ['text', 'json-summary', 'json', 'html'],
    reportsDirectory: './coverage',
    reportOnFailure: true,
  },
},
```

**Fix — Step 3: verify `.gitignore`**
Confirm `frontend/.gitignore` excludes `coverage/` (see also DEBT-009).
No change to the CI workflow is required; lines 73–78 are correct once the files exist.

**Testing:**
1. Run `cd frontend && npm test -- --run --coverage` locally; confirm `frontend/coverage/coverage-summary.json` is created.
2. Open a PR; confirm `frontend-quality` passes and a coverage comment appears.
3. Confirm `frontend/coverage/` is absent from `git status` (excluded by `.gitignore`).

---
## DEBT — Performance

### PERF-001: Three.js imported statically — loads unconditionally in main bundle (~172KB gzipped)
**File:** `frontend/src/components/ThreeHeroBackground.vue:7`
**Priority:** Medium | **Effort:** 1 hour
**Risk:** Medium — `THREE.*` type annotations at module scope must be replaced with `any`

#### Current code

`frontend/src/components/ThreeHeroBackground.vue:7`:
```ts
import * as THREE from 'three'
```

`vite.config.ts:165` has a `manualChunks: { 'three': ['three'] }` entry — this splits Three.js
into a separate chunk for cache-busting, but the chunk is still **eagerly linked** because
`ThreeHeroBackground.vue` has a static import. Vite cannot defer an eagerly-imported chunk. The
Three.js chunk is downloaded and parsed on every page load.

`three@0.183.2` installed (`package.json:44`): ~172KB gzipped, ~600KB raw.

#### Problem

- Static `import * as THREE from 'three'` at the top of the file forces Three.js into the
  critical dependency graph, parsed before any content renders.
- Users whose devices fail the WebGL check or have `prefers-reduced-motion: reduce` (where the
  canvas is hidden via CSS) still pay the full 172KB parse cost.
- Three.js is not reliably tree-shakeable — confirmed by three.js maintainers in issue #24199.
  `import * as THREE` pulls the entire module regardless of what's actually used.
- The `manualChunks` config isolates it for cache purposes only; it does not make it lazy.

#### Web research findings

- Vue 3 official docs: `onMounted` is the correct boundary for client-only/browser-only code.
  A dynamic `import()` inside `onMounted` triggers Vite's code-splitting and produces an async
  chunk downloaded only when the hook fires. (Vue.js Performance Guide)
- `defineAsyncComponent` is for lazy-loading Vue components, not third-party libraries.
  Dynamic `import()` inside `onMounted` is the correct tool here. (Vue 3 docs)
- Vite dynamic import docs confirm: any `import()` not at the module graph root produces a
  separate async chunk. The existing `manualChunks: { 'three': ... }` is preserved automatically.
- Three.js maintainers confirmed in GitHub issue #25855 that esbuild tree-shaking of three.js
  does not work reliably. ~172KB gzipped is the realistic floor for `import * as THREE`.

#### Fix

Before (`ThreeHeroBackground.vue:6-7`):
```ts
import { ref, onMounted, onBeforeUnmount } from 'vue'
import * as THREE from 'three'
```

Module-scope typed variables (lines 11-14):
```ts
let scene: THREE.Scene
let camera: THREE.PerspectiveCamera
let renderer: THREE.WebGLRenderer
let particles: THREE.Points
```

After — remove static import, use `any` at module scope, dynamic import in `onMounted`:
```ts
import { ref, onMounted, onBeforeUnmount } from 'vue'
import type * as THREE from 'three'  // type-only: erased at compile time, no bundle impact

let scene: any
let camera: any
let renderer: any
let particles: any
```

In `onMounted`:
```ts
onMounted(async () => {
  const THREE = await import('three')
  initScene(THREE)
  animate()
  window.addEventListener('resize', handleResize, { passive: true })
  window.addEventListener('mousemove', handleMouseMove, { passive: true })
  document.addEventListener('visibilitychange', handleVisibilityChange)
  const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
  mediaQuery.addEventListener('change', handleReducedMotionChange)
})
```

`initScene` and `createParticles` receive `THREE` as a parameter. The `onBeforeUnmount` type cast
`(particles.material as THREE.Material).dispose()` becomes `(particles.material as any).dispose()`.

#### Testing

1. `npm run build` — inspect `dist/assets/js/`. The `three-[hash].js` chunk must be absent from
   the HTML `<script type="module">` src list (it must be an async import, not a direct script).
2. Run `ANALYZE=true npm run build` to open `dist/stats.html` — confirm `three` chunk is not
   listed as a synchronous dependency of the entry chunk.
3. Lighthouse on built site: initial JS parse cost drops by ~172KB. FCP/TTI improve on throttled
   connections.
4. Particle background still renders in Chrome, Firefox, Safari.
5. Disable WebGL in DevTools — graceful `console.warn` fallback, no crash, no unhandled rejection.

---

### PERF-002: GitHubStats component fetches data unconditionally on mount
**File:** `frontend/src/components/GitHubStats.vue`
**Priority:** Low | **Effort:** 45 minutes
**Risk:** Low — `@vueuse/core` already installed, `stop()` ensures single fetch

#### Current code

`frontend/src/components/GitHubStats.vue` (lines ~223-226):
```ts
onMounted(() => {
  isMounted = true
  fetchGitHubStats()
})
```

No `IntersectionObserver` usage in this file. `@vueuse/core@14.2.1` is already a dependency
(`package.json:39`) and `useIntersectionObserver` is available without adding anything.

#### Problem

`fetchGitHubStats()` fires as soon as the component mounts regardless of scroll position. The
GitHub stats section is well below the fold. On slow connections this consumes bandwidth before
the user has scrolled there. The GitHub unauthenticated API allows 60 req/hour per IP — portfolio
visitors sharing the backend IP reduce this budget unconditionally on every page load.

#### Web research findings

- VueUse `useIntersectionObserver` accepts a target ref and callback, returns `stop()`. Calling
  `stop()` after first intersection fires the fetch exactly once. Cleanup on unmount is automatic.
  (vueuse.org)
- GitHub REST API docs recommend caching with `ETag` / `304 Not Modified` and avoiding polling.
  Deferring until visible eliminates wasted requests for users who never scroll to the section.
- `rootMargin: '200px'` gives a 200px head-start before the section enters view, so data loads
  before the user sees the section on a mid-tier connection.

#### Fix

```ts
/* Before */
import { ref, computed, onMounted, onUnmounted } from 'vue'
// ...
onMounted(() => {
  isMounted = true
  fetchGitHubStats()
})

/* After */
import { ref, computed, onUnmounted } from 'vue'
import { useIntersectionObserver } from '@vueuse/core'
```

In the template root element, add `ref="sectionRef"`:
```html
<div ref="sectionRef" class="github-stats">
```

Replace `onMounted` with intersection logic:
```ts
const sectionRef = ref<HTMLElement | null>(null)

const { stop } = useIntersectionObserver(
  sectionRef,
  ([entry]) => {
    if (entry.isIntersecting) {
      isMounted = true
      fetchGitHubStats()
      stop() // fire once only
    }
  },
  { rootMargin: '200px' }
)
```

#### Testing

1. DevTools → Network → filter GitHub: confirm zero requests on page load.
2. Scroll to GitHub Stats section — confirm exactly one request fires.
3. Scroll away and back — confirm no second request.
4. Throttle to Slow 3G: loading spinner appears only when section is near viewport.
5. Navigate away mid-fetch — confirm no console errors after unmount (AbortController cleanup).

---

### PERF-003: Missing `<link rel="preload">` for Inter font — FOUT causes CLS
**File:** `frontend/index.html:54`, `frontend/src/styles/variables.css:59`
**Priority:** Low | **Effort:** 30 minutes
**Risk:** Low — `&display=swap` already correct; preload URL may need periodic verification

#### Current code

`frontend/index.html:54`:
```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@500;600;700&display=swap"
      rel="stylesheet" />
```

`frontend/index.html:45-46`:
```html
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
```

`frontend/src/styles/variables.css:59`:
```css
--font-family-display: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
```

`frontend/src/style.css` — no `@font-face` declarations.

#### Problem

**`&display=swap` is already present and correct** — FOIT is not an issue. The actual remaining
gap is narrower than the original stub described:

The `preconnect` hints speed up DNS/TLS for fonts.googleapis.com and fonts.gstatic.com, but the
browser still must: fetch the CSS → parse it → discover the `.woff2` URL → fetch the woff2.
That is 2 sequential round-trips after the preconnect. On a slow connection, Inter may arrive
late enough to cause a visible layout reflow (FOUT → CLS) on headings using
`--font-family-display` (`h1`–`h6` via `style.css:47`).

#### Web research findings

- `font-display: swap` eliminates FOIT but does not eliminate FOUT. FOUT causes CLS when the
  fallback font metrics differ from Inter. Google Fonts research confirms: `preconnect` +
  `display=swap` + `preload` of the woff2 is the optimal combination. (CSS-Tricks "Fastest Google
  Fonts", PerfPerfPerf)
- Google Fonts `&display=swap` is already correct. The missing piece is a `rel="preload"` for the
  actual woff2 file — this reduces the fetch from 2 sequential round-trips to 1. (DebugBear 2025)
- `size-adjust` + `ascent-override` CSS font metrics matching is the more robust alternative:
  makes the system-font fallback match Inter's dimensions exactly so the swap causes zero visible
  reflow (zero CLS). Supported in Chromium 92+, Firefox 89+, Safari 17+. (web.dev)
- Core Web Vitals 2025: CLS caused by font swap is a Lighthouse ranking signal. `font-display:
  optional` (no swap after 100ms) is theoretically best for CLS but means Inter may never load
  on slow connections — not appropriate for a portfolio where Inter is part of the design.

#### Fix

**Option A — `rel="preload"` for the specific Inter woff2 (simpler but URL-fragile):**

Retrieve the current woff2 URL from the Google Fonts CSS response (fetch
`https://fonts.googleapis.com/css2?family=Inter:wght@500;600;700&display=swap` and find the
woff2 src URL for the latin subset). Add to `index.html` after the preconnect lines:

```html
<link
  rel="preload"
  as="font"
  type="font/woff2"
  href="https://fonts.gstatic.com/s/inter/v18/UcCO3FwrK3iLTeHuS_nVMrMxCp50SjIw2boKoduKmMEVuLyfAZ9hiA.woff2"
  crossorigin
/>
```

Risk: Google occasionally updates the font file URL. If it changes, the preload becomes a wasted
request. Verify the URL matches the current Google Fonts CSS response before deploying.

**Option B — `size-adjust` font metrics matching (robust, no URL fragility):**

Add a fallback `@font-face` in `variables.css` or `style.css`:
```css
@font-face {
  font-family: 'Inter-fallback';
  src: local('BlinkMacSystemFont'), local('Segoe UI'), local('-apple-system');
  size-adjust: 100%;
  ascent-override: 90%;
  descent-override: 22%;
  line-gap-override: 0%;
}
```

Update `--font-family-display` to lead with the fallback:
```css
--font-family-display: 'Inter', 'Inter-fallback', -apple-system, ...;
```

This makes the system-font fallback metrically match Inter so the swap is visually imperceptible.

#### Testing

1. Lighthouse → Performance: check CLS score specifically for font-related shifts.
2. DevTools → Network → Slow 3G throttle → filmstrip: headings must not visibly reflow between
   frames when Inter loads (Option B) or Inter must load before first paint (Option A).
3. WebPageTest filmstrip: confirm no layout shift on hero `h1` between frames.
4. Confirm text is always visible from frame 1 (`display=swap` — already correct).

---

## DEBT — Accessibility

### A11Y-001: Focus not moved to main content on route change (WCAG 2.2 SPA requirement)
**File:** `frontend/src/router/index.ts`
**Priority:** Medium — #1 most commonly missed accessibility requirement in Vue SPAs
**Risk:** Medium — screen reader users cannot detect page changes; keyboard users retain position on old content

#### Current code

`frontend/src/router/index.ts` lines 143–151:
```ts
router.afterEach((to: RouteLocationNormalized, _from: RouteLocationNormalized) => {
  // Update document title from route meta
  const title = to.meta.title as string | undefined
  document.title = title || DEFAULT_TITLE

  // Track the page view
  analytics.trackPageView(to.path, to.name as string | undefined)
})
```

`frontend/src/views/HomeView.vue` line 7:
```html
<main id="main-content" role="main">
```

The `<main>` element has `id="main-content"` (referenced by the skip link in `App.vue`) but no
`tabindex` attribute, so it cannot receive programmatic focus via `.focus()`.

`frontend/src/App.vue` lines 20–26 use a `<Transition name="page-fade">` wrapping
`<component :is="Component" :key="route.path" />`. The transition fires after `afterEach`, so any
focus call made synchronously in `afterEach` targets the DOM before the incoming component has
mounted. A `nextTick` call is required to defer until after Vue has flushed the update.

#### Problem

**WCAG 2.4.3 Focus Order (Level A):** When a user navigates sequentially and navigation sequences
affect meaning or operation, focusable components must receive focus in an order that preserves
meaning and operability. In a SPA, client-side navigation does not trigger the browser's native
page-load focus reset — focus silently remains on the link or control that triggered navigation.
Screen reader users receive no announcement that the page changed and must search the entire page
to find new content.

**Compounding issue — WCAG 2.4.2 Page Titled (Level A):** `document.title` is already updated
correctly (line 147), but title updates alone are not read aloud by all screen readers unless
focus is moved to cause a context change. Without focus movement the title update provides no
practical signal.

The `afterEach` hook currently handles title and analytics only. There is no `nextTick`, no
`document.querySelector`, and no `.focus()` call anywhere in the router or `App.vue` setup.

#### Web research findings

From W3C WCAG 2.4.3 Understanding document and multiple SPA accessibility audits:

- Screen readers (NVDA, JAWS, VoiceOver) do not announce `document.title` changes after SPA
  navigation unless a focus shift triggers a context update.
- User research (Orange Digital Accessibility, Nolan Lawson 2019, BBC GEL) shows screen reader
  users strongly prefer focus moved to the new page `<h1>` over focus moved to `<body>`, a
  wrapper `<div>`, or the skip link.
- The `<h1>` or `<main>` target must have `tabindex="-1"` to be focusable programmatically
  without entering the tab order — a plain `<main>` without `tabindex` silently ignores `.focus()`.
- Vue's `nextTick` must be awaited after `afterEach` fires because the `<Transition>` component
  completes DOM insertion asynchronously; calling `.focus()` synchronously targets the outgoing
  component's DOM node (which Vue is in the process of removing).
- An `aria-live="polite"` region announcing the new page title is an optional complementary
  pattern but is not a substitute for focus movement — it does not reposition the screen reader's
  reading cursor.
- The existing skip link (`<a href="#main-content">`) in `App.vue` is correct for keyboard bypass
  but does not help after route changes because the skip link itself is not focused post-navigation.

#### Fix

**Step 1 — Add `tabindex="-1"` to `<main>` in `HomeView.vue` (and any other view with a `<main>`):**

Before (`frontend/src/views/HomeView.vue` line 7):
```html
<main id="main-content" role="main">
```

After:
```html
<main id="main-content" role="main" tabindex="-1">
```

`tabindex="-1"` allows `.focus()` to target the element without adding it to the sequential tab
order. Without this the `.focus()` call is a silent no-op in all major browsers.

**Step 2 — Add focus management and `nextTick` import to `frontend/src/router/index.ts`:**

Before (lines 1–9):
```ts
import {
  createRouter,
  createWebHistory,
  type RouteRecordRaw,
  type NavigationGuardNext,
  type RouteLocationNormalized
} from 'vue-router'
import { useAuthStore } from '../stores/auth'
import analytics from '../services/analytics'
```

After:
```ts
import {
  createRouter,
  createWebHistory,
  type RouteRecordRaw,
  type NavigationGuardNext,
  type RouteLocationNormalized
} from 'vue-router'
import { nextTick } from 'vue'
import { useAuthStore } from '../stores/auth'
import analytics from '../services/analytics'
```

Before (`afterEach` block, lines 143–151):
```ts
router.afterEach((to: RouteLocationNormalized, _from: RouteLocationNormalized) => {
  const title = to.meta.title as string | undefined
  document.title = title || DEFAULT_TITLE

  analytics.trackPageView(to.path, to.name as string | undefined)
})
```

After:
```ts
router.afterEach((to: RouteLocationNormalized, _from: RouteLocationNormalized) => {
  const title = to.meta.title as string | undefined
  document.title = title || DEFAULT_TITLE

  analytics.trackPageView(to.path, to.name as string | undefined)

  // Move focus to main content after route change so screen readers announce the new page.
  // nextTick defers until Vue has finished mounting the incoming component (required with
  // <Transition> because DOM insertion is asynchronous relative to afterEach).
  // The target must have tabindex="-1" to be focusable without entering the tab order.
  nextTick(() => {
    const target = document.getElementById('main-content') as HTMLElement | null
    target?.focus({ preventScroll: false })
  })
})
```

`preventScroll: false` (the default) allows the browser to scroll the main element into view if
needed — this is correct behaviour for a page navigation. Only modals/drawers need
`preventScroll: true`.

#### Testing

1. **axe-core / browser extension:** Run [axe DevTools](https://www.deque.com/axe/) after each
   route change. The rule `bypass` (WCAG 2.4.1) and focus-related rules will flag missing focus
   management if the fix is absent.
2. **NVDA + Firefox (Windows):** Navigate between routes using a router-link. Before the fix,
   NVDA does not announce anything. After the fix, NVDA reads the `<main>` element's accessible
   name (none by default, so it reads "main landmark") and repositions the virtual cursor.
3. **VoiceOver + Safari (macOS/iOS):** Same test — VO should read "main" and position the
   reading cursor at the top of the new content.
4. **Keyboard-only (Tab key only, no screen reader):** Confirm focus is visible on the `<main>`
   element after navigation. Note: `tabindex="-1"` elements receive a focus ring from browsers
   unless `outline: none` is set — verify the skip link or global `focus-visible` rules do not
   suppress it on `<main>`.
5. **Playwright test:** Assert `document.activeElement` is `document.getElementById('main-content')`
   after `router.push()` resolves and `nextTick` fires.

---

### A11Y-002: WCAG 2.2 § 2.4.11 Focus Appearance — focus ring may not meet minimum requirements
**Files:** `frontend/src/assets/portfolio.css`, `frontend/src/style.css`
**Priority:** Low — WCAG 2.2 AA, new requirement since October 2023; no browser auto-enforcement
**Risk:** Low — styles are present and use `:focus-visible` correctly; specific measurements need audit

#### Current code

`frontend/src/style.css` lines 89–94 (global anchor focus):
```css
a:focus-visible {
  outline: 2px solid var(--color-primary, #3b82f6);
  outline-offset: 2px;
  border-radius: 2px;
  transition: outline-offset 0.15s var(--ease-smooth, ease);
}
```

`frontend/src/style.css` lines 131–134 (button focus):
```css
button:focus-visible {
  outline: 2px solid var(--color-primary, #3b82f6);
  outline-offset: 2px;
}
```

`frontend/src/assets/portfolio.css` lines 202–207 (btn variants):
```css
.btn:focus-visible,
.btn-primary:focus-visible,
.btn-outline-primary:focus-visible {
  outline: 2px solid var(--primary-500, #3b82f6);
  outline-offset: 2px;
}
```

`frontend/src/assets/portfolio.css` lines 209–214 (project and contact links):
```css
.project-link:focus-visible,
.contact-link:focus-visible {
  outline: 2px solid var(--primary-500, #3b82f6);
  outline-offset: 2px;
  border-radius: 4px;
}
```

`frontend/src/assets/portfolio.css` lines 224–229 (high-contrast / forced-colors):
```css
@media (forced-colors: active) {
  :focus-visible {
    outline: 3px solid CanvasText;
    outline-offset: 3px;
  }
```

#### Problem

**WCAG 2.4.11 is labeled in the codebase comment as "SC 2.4.13" (line 201 of portfolio.css).
This is a numbering error.** The actual criteria are:

- **WCAG 2.4.11 Focus Not Obscured (Minimum) — Level AA:** The focused component must not be
  entirely hidden by author-created content (sticky headers, banners, etc.). Sticky navbar is
  72px tall; if a focused element is within 72px of the viewport top the navbar may fully obscure
  the focus ring.
- **WCAG 2.4.13 Focus Appearance — Level AAA (not Level AA):** The focus indicator area must be
  at least as large as a 2px-thick perimeter of the unfocused component, with 3:1 contrast between
  focused and unfocused states, and 3:1 contrast against adjacent colors.

The existing `2px solid #3b82f6` outline does satisfy the WCAG 2.4.13 area formula (a 2px outline
around the perimeter meets the "2px thick perimeter" requirement), but **contrast is conditional**:

- `#3b82f6` (primary-500, blue) against a **white background** has contrast ratio ~3.0:1 — this
  is exactly at the 3:1 threshold and may fail if background is off-white (`var(--bg-primary)` is
  `#eff6ff` in light mode, which reduces the contrast slightly).
- On the **gradient hero section** (dark image background) the blue outline at 3.0:1 on white
  does not apply; the ring is visible but unmeasured.
- On **dark-mode** cards (`background: rgba(255,255,255,0.8)` in light, dark card bg in dark
  mode), the blue ring contrast needs independent verification.
- `button:focus` (line 119–122) uses `rgba(var(--color-primary-rgb), 0.4)` — a **40% opacity
  outline**. A semi-transparent outline cannot reliably meet the 3:1 contrast requirement across
  backgrounds. This rule fires for `:focus` (not just `:focus-visible`) and may be the effective
  style in browsers that do not support `:focus-visible`.

The `transition: outline-offset 0.15s` on anchor focus (style.css line 93) animates the outline
into place. This is fine for users without `prefers-reduced-motion`, but the animation is not
gated by a `@media (prefers-reduced-motion: no-preference)` block — it will fire even for users
who have requested reduced motion. The `App.vue` page transition _is_ correctly gated; the focus
transition is not.

#### Web research findings

From W3C WCAG 2.4.13 Understanding document and Sara Soueidan's focus indicator guide:

- The minimum focus area formula: `(2 × perimeter_px)` CSS pixels. For a `200×40px` button the
  minimum indicator area is `2 × (200+40) × 2 = 960px²`. A `2px` solid outline fully around the
  element satisfies this.
- Contrast requirement: 3:1 between the outline color in focused vs unfocused state, AND 3:1
  between the outline color and adjacent background. Primary-500 (`#3b82f6`) vs white (`#ffffff`)
  is approximately 3.0:1 — borderline. Using `--primary-600` (`#2563eb`) gives ~4.5:1 against
  white — a safer choice.
- `outline-offset: 2px` is recommended. A 0 offset causes the outline to sit on the element
  border, which reduces perceived contrast against the element's own background color.
- WCAG 2.4.11 (not 2.4.13) is the AA-level criterion and is about focus not being _obscured_ by
  sticky UI — a `scroll-padding-top` or `scroll-margin-top` guard is the typical fix.
- `forced-colors: active` media query is already correctly handled (lines 224–229). This covers
  Windows High Contrast mode.

#### Fix

**Fix 1 — Correct the comment label** in `frontend/src/assets/portfolio.css` line 201:

Before:
```css
/* Focus States - Accessibility (WCAG 2.2 SC 2.4.13) */
```
After:
```css
/* Focus States - Accessibility (WCAG 2.2 SC 2.4.11 / 2.4.13) */
```

**Fix 2 — Replace semi-transparent `:focus` rule** in `frontend/src/style.css` lines 119–122:

Before:
```css
button:focus {
  outline: 2px solid rgba(var(--color-primary-rgb), 0.4);
  outline-offset: 2px;
}
```
After:
```css
button:focus {
  outline: 2px solid var(--color-primary, #3b82f6);
  outline-offset: 2px;
}
```

The 40%-opacity variant cannot meet 3:1 contrast reliably. The `:focus-visible` rule already
overrides this for pointer users in modern browsers — keeping them consistent avoids confusion.

**Fix 3 — Gate the outline transition behind reduced-motion media query**
in `frontend/src/style.css` lines 89–94:

Before:
```css
a:focus-visible {
  outline: 2px solid var(--color-primary, #3b82f6);
  outline-offset: 2px;
  border-radius: 2px;
  transition: outline-offset 0.15s var(--ease-smooth, ease);
}
```
After:
```css
a:focus-visible {
  outline: 2px solid var(--color-primary, #3b82f6);
  outline-offset: 2px;
  border-radius: 2px;
}

@media (prefers-reduced-motion: no-preference) {
  a:focus-visible {
    transition: outline-offset 0.15s var(--ease-smooth, ease);
  }
}
```

**Fix 4 — Increase outline color from primary-500 to primary-600** (optional, improves margin
above 3:1 against near-white backgrounds). Apply to all focus rules:

```css
/* Change #3b82f6 / var(--primary-500) to var(--primary-600, #2563eb) in all focus rules */
outline: 2px solid var(--primary-600, #2563eb);
```

This is optional if the audit confirms primary-500 passes on all actual page backgrounds.

**Fix 5 — WCAG 2.4.11 obscurement:** Verify `scroll-padding-top` covers the navbar height.
`portfolio.css` line 268 sets `scroll-padding-top: 72px` which matches the navbar. No change
required here, but confirm this rule is not overridden by the `80px` value in `style.css`
(see DEBT-003).

#### Testing

1. **axe-core browser extension:** Tab through all interactive elements in both light and dark
   mode. axe rule `focus-visible` will flag missing outlines; manual contrast check needed for
   borderline values.
2. **Colour Contrast Analyser (TPGi):** Sample the outline color (`#3b82f6`) against the page
   background at each focus location — hero gradient, card backgrounds, dark sections. Target ≥3:1.
3. **Windows High Contrast Mode:** Enable via Settings → Accessibility → Contrast Themes. Verify
   the `forced-colors: active` block renders a visible system outline.
4. **Sticky navbar obscurement:** Tab to a link near the top of a section. Confirm the focused
   element is fully visible below the 72px navbar (WCAG 2.4.11).
5. **Reduced motion:** Set `prefers-reduced-motion: reduce` in OS settings or DevTools. Verify
   the outline-offset transition does not fire after Fix 3 is applied.

---

### A11Y-003: ProjectCard links lack project name in accessible name — ambiguous across cards
**File:** `frontend/src/components/ProjectCard.vue`
**Priority:** Low — affects screen reader and speech-input users when multiple cards are present
**Risk:** Low — links function correctly; only the accessible name lacks context

#### Current code

`frontend/src/components/ProjectCard.vue` lines 17–50:
```html
<a
  v-if="project.github_url"
  :href="project.github_url"
  target="_blank"
  rel="noopener noreferrer"
  class="project-link github-link"
>
  <svg class="link-icon" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
    <path d="M8 0C3.58 0 0 3.58 ..." />
  </svg>
  <span>View Code</span>
</a>

<a
  v-if="project.live_url"
  :href="project.live_url"
  target="_blank"
  rel="noopener noreferrer"
  class="project-link live-link"
>
  <svg ... aria-hidden="true">
    <path d="M10 6H6a2 2 0 ..." />
  </svg>
  <span>Live Demo</span>
</a>
```

The SVGs correctly use `aria-hidden="true"` so the icon is excluded from the accessibility tree.
The link's accessible name is derived solely from the visible `<span>` text: "View Code" and
"Live Demo".

#### Problem

**WCAG 2.4.4 Link Purpose (In Context) — Level A:** The purpose of each link must be determinable
from the link text alone or from the link text together with its programmatically determined
context. When multiple `ProjectCard` components are rendered on the same page, every GitHub link
announces as "View Code" and every live-demo link announces as "Live Demo". A screen reader user
listening to a links list (NVDA: `INSERT+F7`; VoiceOver: `VO+U` → Links) hears an
undifferentiated list with no way to identify which project each link belongs to.

**WCAG 2.5.3 Label in Name — Level A:** When a visible text label exists on an interactive
component, the accessible name must contain that visible text. An `aria-label` that does not
start with or include the visible text ("View Code") violates this criterion because it breaks
speech input: a Dragon NaturallySpeaking user who says "click View Code" will activate the first
matching element regardless of context.

**Secondary concern — new tab warning:** Both links open in `target="_blank"`. WCAG advisory
technique G201 recommends warning users before opening a new window. Screen readers do not
announce `target="_blank"` automatically.

#### Web research findings

From W3C ARIA Technique ARIA8, MDN `aria-label` docs, W3C WCAG 2.4.4 Understanding, and the
AllAccessible 2025 ARIA guide:

- For links with visible text, the correct pattern under WCAG 2.5.3 is for `aria-label` to
  _start with_ the visible text and append additional context:
  `aria-label="View Code for Portfolio Site on GitHub (opens in new tab)"`. This satisfies both
  2.4.4 (purpose determinable from link text + context) and 2.5.3 (accessible name contains
  visible label).
- An alternative to `aria-label` is to use a visually hidden `<span class="sr-only">` appended
  inside the link. This is more robust because it uses real DOM text rather than an attribute,
  and is trivially testable. Vue official accessibility guide and Radix Vue both recommend this
  pattern.
- The `sr-only` CSS pattern (`position: absolute; width: 1px; height: 1px; overflow: hidden;
  clip: rect(0 0 0 0); clip-path: inset(100%); white-space: nowrap;`) is already implicitly
  supported by the project's CSS architecture; no new utility class is needed if one is added
  globally.
- New-tab announcements: appending "(opens in new tab)" to the accessible name is the current
  industry standard. Alternatively, a visually hidden global warning icon with `aria-label` can
  be placed next to each external link. The `aria-label` approach is simpler for this use case.

#### Fix

**Preferred fix — dynamic `aria-label` containing visible text plus project name and new-tab
notice:**

Before (`frontend/src/components/ProjectCard.vue` lines 17–30):
```html
<a
  v-if="project.github_url"
  :href="project.github_url"
  target="_blank"
  rel="noopener noreferrer"
  class="project-link github-link"
>
  <svg class="link-icon" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
    ...
  </svg>
  <span>View Code</span>
</a>
```

After:
```html
<a
  v-if="project.github_url"
  :href="project.github_url"
  :aria-label="`View Code for ${project.name} on GitHub (opens in new tab)`"
  target="_blank"
  rel="noopener noreferrer"
  class="project-link github-link"
>
  <svg class="link-icon" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
    ...
  </svg>
  <span aria-hidden="true">View Code</span>
</a>
```

Before (lines 32–50):
```html
<a
  v-if="project.live_url"
  :href="project.live_url"
  target="_blank"
  rel="noopener noreferrer"
  class="project-link live-link"
>
  <svg ... aria-hidden="true">
    ...
  </svg>
  <span>Live Demo</span>
</a>
```

After:
```html
<a
  v-if="project.live_url"
  :href="project.live_url"
  :aria-label="`Live Demo for ${project.name} (opens in new tab)`"
  target="_blank"
  rel="noopener noreferrer"
  class="project-link live-link"
>
  <svg ... aria-hidden="true">
    ...
  </svg>
  <span aria-hidden="true">Live Demo</span>
</a>
```

The `aria-label` starts with the visible text ("View Code" / "Live Demo") to satisfy WCAG 2.5.3.
The `<span>` receives `aria-hidden="true"` to prevent the browser from constructing an accessible
name from both the `aria-label` and the span text (which would cause duplication in some screen
reader/browser combinations — e.g., "View Code for Portfolio Site on GitHub View Code").

Note: `aria-label` overrides the visible text in the accessibility tree. Dragon NaturallySpeaking
users who speak "click View Code" will still activate the link because the label starts with "View
Code". Users who speak the full label will also activate it.

#### Testing

1. **axe-core:** Run on the projects section. The rule `link-name` (maps to WCAG 2.4.4 / 4.1.2)
   will flag "View Code" links as ambiguous if they share the same accessible name across cards.
   After the fix, names must be unique per card.
2. **NVDA links list (`INSERT+F7`) + Firefox:** Open the links list dialog. Before the fix: all
   GitHub links read "View Code". After: "View Code for [project name] on GitHub (opens in new
   tab)" for each unique project.
3. **VoiceOver rotor (macOS — `VO+U`, select Links):** Same check — unique names per card.
4. **Dragon NaturallySpeaking:** Say "click View Code". Verify the first matching link activates.
   Say "click View Code for Portfolio Site on GitHub". Verify the specific link activates.
5. **Manual: tab navigation on projects section:** Confirm focus ring is visible on each link and
   the accessible name announced by the screen reader uniquely identifies the project.

---

## DEBT — Backend

### BE-001: `Project.technologies` JSON column has no schema validation
**Files:** `backend/app/models/project.py:20`, `backend/app/schemas/project.py:32`
**Priority:** Medium — malformed DB record crashes frontend `v-for` rendering

#### Current code

`backend/app/models/project.py:20`:
```python
technologies = Column(JSON)  # List of technologies used
```

`backend/app/schemas/project.py:32`:
```python
technologies: list[str] | None = Field(default=[], max_length=MAX_TECHNOLOGIES)
```

#### Problem

`Column(JSON)` has no DB-level constraint — it accepts any JSON value (string, number, object,
null). A record written directly to the DB (e.g. via a migration script) with
`technologies = "javascript"` (bare string) bypasses the Pydantic schema entirely. On the
frontend, `v-for="tech in project.technologies"` on a string iterates characters and renders
"j", "a", "v", "a", "s" as separate badge elements.

Additionally, `ProjectBase` and `ProjectUpdate` declare `technologies: list[str] | None` with no
`@field_validator`. Pydantic v2 in lax/ORM mode coerces list elements to `str` silently, so
`{"technologies": [123, null]}` passes validation. `Field(max_length=MAX_TECHNOLOGIES)` on a
`list` enforces item *count*, not per-item string length.

`ProjectResponse` has `validate_technologies` for output deserialization (comma-split fallback)
but there is no equivalent input-path validator on `ProjectCreate` / `ProjectUpdate`.

#### Web research findings

- SQLAlchemy 2.0 `Column(JSON)` stores whatever Python object is passed — no DB-level type
  enforcement exists for JSON columns in SQLite or PostgreSQL. Enforcement must happen at the
  application layer.
- The correct pattern for a guaranteed-list JSON column: `default=list` (callable, not `[]` —
  mutable default is evaluated fresh per row), `server_default='[]'` for rows inserted outside
  the ORM, and `nullable=False` to prevent SQL NULL. Per SQLAlchemy docs, Python `None` is
  treated as SQL NULL unless `none_as_null=False`; `nullable=False, server_default='[]'` is the
  reliable approach.
- In Pydantic v2, `@field_validator(..., mode="before")` on input schemas is the correct place
  to enforce item-level constraints (type + length) before storage. The `mode="before"` validator
  receives the raw input value before Pydantic's own type coercion.
- Per-item string length must be validated explicitly in a `@field_validator` — `Field(max_length=N)`
  on a `list` field enforces the collection size, not element size.

#### Fix

1. Harden the model column — add `nullable=False`, `default=list`, and `server_default`:

   `backend/app/models/project.py:20`
   ```python
   # Before
   technologies = Column(JSON)  # List of technologies used

   # After
   technologies = Column(JSON, nullable=False, default=list, server_default="[]")
   ```

2. Add a `@field_validator` to `ProjectBase` (covers `ProjectCreate`) that rejects non-list
   inputs and validates each item's type and length:

   `backend/app/schemas/project.py` — inside `ProjectBase`:
   ```python
   # Before
   technologies: list[str] | None = Field(default=[], max_length=MAX_TECHNOLOGIES)
   # (no validator on input path)

   # After
   technologies: list[str] = Field(default_factory=list, max_length=MAX_TECHNOLOGIES)

   @field_validator("technologies", mode="before")
   @classmethod
   def validate_technologies_input(cls, v):
       """Ensure technologies is always a list of non-empty strings, each max 100 chars."""
       if v is None:
           return []
       if not isinstance(v, list):
           raise ValueError("technologies must be a list")
       for item in v:
           if not isinstance(item, str):
               raise ValueError("each technology must be a string")
           if len(item) > 100:
               raise ValueError("technology name exceeds 100 characters")
       return v
   ```

3. Apply the same validator pattern to `ProjectUpdate.technologies`.

   The model column change (`nullable=False, server_default`) requires an Alembic migration.
   Generate with `alembic revision --autogenerate` and verify the migration sets existing NULLs
   to `[]` before applying in production.

#### Risk: Medium
The column DDL change requires a DB migration. The validator change is non-breaking for
well-formed input.

#### Testing
- `POST /api/v1/projects` with `{"technologies": "javascript"}` must return HTTP 422.
- `POST /api/v1/projects` with `{"technologies": [123]}` must return HTTP 422.
- `POST /api/v1/projects` with `{"technologies": null}` must succeed and store `[]`.
- `GET /api/v1/projects` for a row with `technologies = []` must return `"technologies": []`.
- Add `test_project_technologies_validation` to `backend/tests/`.

---

### BE-002: N+1 query risk on company endpoints
**Files:** `backend/app/api/v1/companies.py:33,42`, `backend/app/models/company.py:43`
**Priority:** Low — the relationship exists; async lazy-load failure is a runtime crash waiting
to happen when `projects` is added to `CompanyResponse`

#### Current code

`backend/app/api/v1/companies.py:33`:
```python
result = await db.execute(select(Company).order_by(Company.order_index))
return result.scalars().all()
```

`backend/app/api/v1/companies.py:42`:
```python
result = await db.execute(select(Company).where(Company.id == company_id))
company = result.scalar_one_or_none()
```

`backend/app/models/company.py:43`:
```python
projects = relationship("Project", back_populates="company", cascade="all, delete-orphan")
```

#### Problem

Both company queries execute without an `options()` clause. SQLAlchemy 2.0 async mode disables
implicit lazy loading — accessing `company.projects` outside of the query raises a
`MissingGreenlet` / `greenlet_spawn` error at runtime (not at import time, so tests may not catch
it until the attribute is actually accessed).

Currently `CompanyResponse` does not include `projects`, so the error is latent rather than
active. However:
1. Any developer adding `projects: list[...]` to `CompanyResponse` will trigger the runtime
   crash immediately.
2. `company.to_dict()` does not currently access `projects`, but if updated it will break.
3. The equivalent projects endpoint (`projects.py:35`) already uses
   `selectinload(Project.company)` correctly — companies should mirror this pattern.

Note: this is not a classical N+1 (which requires lazy loading to fire per row), but an
async-greenlet crash on any relationship access without eager loading declared at query time.

#### Web research findings

- SQLAlchemy 2.0 async mode does not support implicit lazy loading. All relationship access must
  be declared at query time via `selectinload`, `joinedload`, or `subqueryload`.
- For one-to-many collections (`Company -> [Project]`), `selectinload` is the recommended async
  strategy. It issues one additional `SELECT ... WHERE company_id IN (id1, id2, ...)` query,
  avoiding the row-duplication issue that `joinedload` produces with collections.
- `joinedload` is preferred for many-to-one scalar relationships. `Project.company` already uses
  `selectinload` (valid for many-to-one in async contexts).
- Per SQLAlchemy 2.0 docs: "selectinload() is most flexible for any kind of originating query"
  for collections and is the standard async-safe choice.

#### Fix

Add `selectinload` import and `.options()` clause to both company queries:

`backend/app/api/v1/companies.py` — add to imports:
```python
from sqlalchemy.orm import selectinload
```

`GET /companies/` — line 33:
```python
# Before
result = await db.execute(select(Company).order_by(Company.order_index))

# After
result = await db.execute(
    select(Company).options(selectinload(Company.projects)).order_by(Company.order_index)
)
```

`GET /companies/{company_id}` — line 42:
```python
# Before
result = await db.execute(select(Company).where(Company.id == company_id))

# After
result = await db.execute(
    select(Company).options(selectinload(Company.projects)).where(Company.id == company_id)
)
```

#### Risk: Low
Adding `selectinload` issues one extra SELECT per request even when `projects` is not in the
response. This is a minor overhead but prevents any future `MissingGreenlet` crash. No schema
or migration changes required.

#### Testing
- `GET /api/v1/companies/` must return HTTP 200 with no `greenlet_spawn` errors in logs.
- `GET /api/v1/companies/{id}` must return HTTP 200.
- Temporarily add `projects: list[str]` to `CompanyResponse` and confirm no `MissingGreenlet`
  exception is raised — then revert if projects is not wanted in the response.
- With SQLAlchemy `echo=True`, confirm exactly 2 queries for the list endpoint (companies SELECT
  + IN-load for projects) vs an error without the fix.

---

### BE-003: CSP `frame-src` allows `https://www.google.com` (overly broad)
**File:** `backend/app/main.py:111,127`
**Priority:** Low — allows any Google-hosted page in iframes, not just Maps embeds

#### Current code

`backend/app/main.py:111` (production) and `:127` (development) — identical in both blocks:
```python
"frame-src 'self' https://www.youtube.com https://www.youtube-nocookie.com https://www.google.com https://maps.google.com",
```

#### Problem

`https://www.google.com` in `frame-src` permits any page under that origin to be framed — not
just `/maps/embed`. An attacker exploiting a reflected XSS or injection vector could embed
`https://www.google.com/search?q=...` or any other Google page. The actual requirement is only
to allow the Maps Embed API (`https://www.google.com/maps/embed?pb=...`).

#### Web research findings

- CSP `frame-src` source expressions support path prefixes. `https://www.google.com/maps` is a
  valid source expression: browsers enforce the path prefix, blocking frames loading
  `https://www.google.com/` or `https://www.google.com/search` while allowing
  `https://www.google.com/maps/embed?pb=...`.
- The Maps Embed API uses URLs of the form `https://www.google.com/maps/embed/v1/...` (API key
  variant) and `https://www.google.com/maps/embed?pb=...` (share embed). Both paths start with
  `/maps`, so `https://www.google.com/maps` as a CSP source covers both.
- `maps.google.com` (already present in the directive) is a separate host used by the classic
  Google Maps interface and some embed variants — it must be retained.
- CSP path matching is a prefix: `https://www.google.com/maps` covers
  `https://www.google.com/maps/embed` and all paths below it, but does NOT cover
  `https://www.google.com/` (root). Per MDN and the CSP spec this is browser-enforced.
- Google's own CSP guidance confirms that path-scoped sources like `https://www.google.com/maps`
  further tighten a policy beyond the full-origin `https://www.google.com/`.

#### Fix

Replace `https://www.google.com` with `https://www.google.com/maps` in both the production
(line 111) and development (line 127) CSP blocks. The `maps.google.com` entry stays unchanged.

```python
# Before (both blocks)
"frame-src 'self' https://www.youtube.com https://www.youtube-nocookie.com https://www.google.com https://maps.google.com",

# After (both blocks)
"frame-src 'self' https://www.youtube.com https://www.youtube-nocookie.com https://www.google.com/maps https://maps.google.com",
```

#### Risk: Low
The only regression risk is an embed URL under `www.google.com` that does NOT begin with `/maps`.
Audit `VideoEmbed.vue` and `MapEmbed.vue` — both already validate that embed URLs match the Maps
domain, so no legitimate embed uses a non-`/maps` path on `www.google.com`.

#### Testing
- Render a company detail page with a Maps embed and confirm the iframe loads cleanly (no CSP
  violation in browser DevTools Console).
- In DevTools console, attempt to create an `<iframe src="https://www.google.com/search?q=test">`
  and confirm the browser blocks it with a CSP violation.
- Search `backend/tests/` for any test asserting on the CSP header value and update the expected
  string.

---

### BE-004: Dev/CI tools bundled in production `requirements.txt`
**Files:** `backend/requirements.txt`, `backend/pyproject.toml:38-46`,
`backend/Dockerfile:13-14`, `.github/workflows/ci-cd.yml:113-115`
**Priority:** Low — increases production Docker image size and attack surface

#### Current code

`backend/requirements.txt` is a single flat file installed by both the Dockerfile and CI. It
includes these dev/CI-only tools alongside the runtime stack:
```
bandit==1.9.4          # static analysis — CI only
coverage==7.13.4       # test coverage — CI only
mypy==1.19.1           # type checking — CI only
pip-audit==2.10.0      # vulnerability scanning — CI only
pre_commit==4.5.1      # git hooks — local dev only
pytest==9.0.2          # test runner — CI only
pytest-asyncio==1.3.0  # test plugin — CI only
pytest-cov==7.0.0      # coverage plugin — CI only
ruff==0.15.5           # linter/formatter — CI only
```

`backend/Dockerfile:13-14`:
```dockerfile
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt
```

`.github/workflows/ci-cd.yml:113-115`:
```yaml
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pytest pytest-cov flake8
```

`backend/pyproject.toml:38-46` already correctly separates dev dependencies:
```toml
[project.optional-dependencies]
dev = [
    "pytest==9.0.2",
    "pytest-asyncio==1.3.0",
    "pytest-cov==7.0.0",
    "aiosqlite==0.22.1",
    "ruff==0.15.5",
    "mypy==1.19.1",
]
```
However, `requirements.txt` is what Docker and CI actually consume, so this separation has no
effect in practice.

#### Problem

1. Production containers install linters and security scanners that never run there, unnecessarily
   expanding the set of packages whose CVEs can affect production.
2. A vulnerability in `pip-audit`, `bandit`, or their transitive deps (`cyclonedx-python-lib`,
   `pip-requirements-parser`, etc.) would affect production even though these tools never execute.
3. CI installs `flake8` explicitly via a separate `pip install` step despite `ruff` already being
   configured in `pyproject.toml` — redundant and inconsistent. `flake8` is not in
   `requirements.txt` or `pyproject.toml`, so it is also unpinned.
4. The `pyproject.toml` `[project.optional-dependencies] dev` block is the correct canonical
   source but is not wired to Docker or CI.

#### Web research findings

- `uv` (already in use — `uv.lock` exists in the repo) supports `uv export --no-dev` to generate
  a production-only `requirements.txt` and `uv export --only-group dev` for a dev file,
  keeping `pyproject.toml` as the single source of truth.
- PEP 735 / `[dependency-groups]` is the 2025 standard for dev-only deps in `pyproject.toml`.
  `uv sync --no-group dev` installs only production deps; `uv sync` (default) includes dev.
- The canonical pip-based pattern is `requirements.txt` (runtime, pinned) +
  `requirements-dev.txt` (CI + local, pinned). Dockerfile uses only `requirements.txt`; CI
  installs both.
- `pip-audit`, `bandit`, `ruff`, `mypy`, and `pre-commit` are explicitly dev/CI-only tools per
  FastAPI production deployment guides. Their presence in a production image creates unnecessary
  advisory surface for supply-chain vulnerabilities.

#### Fix

Step 1 — regenerate the split files from `pyproject.toml` (run from `backend/`):
```bash
# Production requirements only
uv export --no-dev --no-hashes -o requirements.txt

# Dev requirements only
uv export --only-group dev --no-hashes -o requirements-dev.txt
```

Step 2 — `backend/Dockerfile` requires no change (already only installs `requirements.txt`).

Step 3 — update `.github/workflows/ci-cd.yml:113-115`:
```yaml
# Before
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pytest pytest-cov flake8

# After
python -m pip install --upgrade pip
pip install -r requirements.txt -r requirements-dev.txt
```
Remove the separate `pip install pytest pytest-cov flake8` line — these come from
`requirements-dev.txt`. Drop `flake8`; `ruff` (already in `requirements-dev.txt`) replaces it.

Step 4 — update `.github/workflows/ci-cd.yml:109` cache key (see also CI-003):
```yaml
# Before
cache-dependency-path: backend/requirements.txt

# After
cache-dependency-path: backend/requirements*.txt
```

#### Risk: Low
Docker build behavior is unchanged. The CI change is additive. The only risk is if
`uv export --no-dev` omits a package that was in the flat file and is needed at runtime — verify
by running the full test suite against the new split before merging.

#### Testing
- Build the Docker image with the new `requirements.txt` and confirm `/api/v1/health` returns
  HTTP 200.
- Confirm `import bandit`, `import mypy`, `import ruff` raise `ModuleNotFoundError` inside the
  running container (`docker exec ... python -c "import bandit"`).
- Run the full CI pipeline — `pip install -r requirements.txt -r requirements-dev.txt` must
  succeed and all tests must pass.
- `pip list` inside the built container must not include `bandit`, `mypy`, `ruff`, `pip-audit`,
  `pre-commit`, `pytest`, or `coverage`.

---

## DEBT — CSS (Additional)

### CSS-001: Z-index values hardcoded as `9999` instead of using defined tokens
**Files:** `frontend/src/App.vue:43`, `frontend/src/components/LoadingSpinner.vue:57`
**Priority:** Low | **Effort:** 20 minutes
**Risk:** Low — values 1080/1090 are above all other elements (max defined token is 1070)

#### Current code

`frontend/src/App.vue:43`:
```css
.skip-link {
  z-index: 9999;
```

`frontend/src/components/LoadingSpinner.vue:57`:
```css
.loading-container.full-screen {
  z-index: 9999;
```

`frontend/src/styles/variables.css` already defines a complete z-index scale (lines 128–135):
```css
--z-index-dropdown:       1000;
--z-index-sticky:         1020;
--z-index-fixed:          1030;
--z-index-modal-backdrop: 1040;
--z-index-modal:          1050;
--z-index-popover:        1060;
--z-index-tooltip:        1070;
```

No token is defined above `1070`. Both `9999` usages bypass the scale with no documented
relationship to the other layers.

#### Problem

Without named tokens at the top of the scale, any developer who needs a new element above the
loading overlay will guess a higher number (`99999`) — the classic z-index arms race. The scale
becomes meaningless. Additionally, the skip link must sit above the loading overlay (a full-screen
overlay during route change must not hide the accessibility skip link from keyboard users).

#### Web research findings

- Z-index without named tokens is the primary cause of z-index maintenance problems. Every value
  should come from a named token; the question is "which layer is this?" not "what number is
  high enough?". (Smashing Magazine, CSS-Tricks: Systems for z-index)
- Major design systems (US Web Design System, Atlassian, Kickstand) use named tokens like
  `z-index-toast`, `z-index-modal`, `z-index-overlay` with room between values.
- CSS `@layer` manages cascade specificity, not visual stacking — it does not replace z-index
  tokens; both are needed for different concerns.

#### Fix

**Step 1** — Add two tokens to `variables.css` after `--z-index-tooltip` (line 135):
```css
--z-index-tooltip:    1070;
--z-index-overlay:    1080;   /* full-screen loading overlays */
--z-index-skip-link:  1090;   /* accessibility skip link — above everything */
```

**Step 2** — `frontend/src/App.vue:43`:
```css
/* Before */
z-index: 9999;

/* After */
z-index: var(--z-index-skip-link);
```

**Step 3** — `frontend/src/components/LoadingSpinner.vue:57`:
```css
/* Before */
z-index: 9999;

/* After */
z-index: var(--z-index-overlay);
```

Why two separate tokens: the skip link must be above the overlay so keyboard users can still
reach it during route transitions.

#### Testing

1. Tab to skip link on page load — it must appear above the navbar.
2. Trigger a loading spinner (navigate to a route) — it must cover the full viewport including
   the navbar, but the skip link must still be reachable via Tab.
3. `grep -r "z-index:" frontend/src` — all remaining results should use `var(--z-index-*)`.

---

### CSS-002: Hardcoded hex colors in `portfolio.css` gradient should use CSS variables
**File:** `frontend/src/assets/portfolio.css:423-437`
**Priority:** Low | **Effort:** 15 minutes
**Risk:** Low — token values are numerically identical to the hardcoded hex values

#### Current code

`frontend/src/assets/portfolio.css` lines 423–437:
```css
.hero-accent-primary {
  background: linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  color: var(--primary-600); /* Fallback */
}

.hero-accent-secondary {
  background: linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  color: var(--primary-600); /* Fallback */
}
```

`#3b82f6` = `--primary-500`, `#60a5fa` = `--primary-400` (confirmed in `variables.css`). The same
ruleset already uses `var(--primary-600)` as a fallback color — the tokens are known but not used
in the gradient. Also: both classes are identical rulesets — needless duplication.

#### Problem

If the primary blue is ever updated in `variables.css`, the gradient text on the hero stays
hardcoded at the old blue while all other primary-coloured elements update. The inconsistency
is invisible until a design review catches it.

#### Web research findings

- CSS custom properties are fully supported in `linear-gradient()` color stops in all modern
  browsers (Chrome 49+, Firefox 31+, Safari 10+, Edge 16+). There is no reason to hardcode hex
  values instead of tokens. (MDN)
- `stylelint-declaration-use-css-custom-properties` plugin can enforce this rule automatically,
  flagging any declaration where a matching custom property exists.
- Broader audit command to find other instances:
  `grep -n "#3b82f6\|#60a5fa\|#2563eb\|#93c5fd\|#1d4ed8" frontend/src/assets/portfolio.css`

#### Fix

```css
/* Before */
.hero-accent-primary {
  background: linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%);
  ...
}
.hero-accent-secondary {
  background: linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%);
  ...
}

/* After — merged (identical rulesets) + tokenized */
.hero-accent-primary,
.hero-accent-secondary {
  background: linear-gradient(135deg, var(--primary-500) 0%, var(--primary-400) 100%);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  color: var(--primary-600);
}
```

#### Testing

1. Build and confirm hero accent text gradient renders identically.
2. Temporarily set `--primary-500: red` in DevTools — both accent elements must turn red.
3. Run the broader audit grep to find any other primary-hex hardcodes in `portfolio.css`.

---

## EVAL — Architecture Evaluations

### EVAL-001: Evaluate SSG (Static Site Generation) for performance
**Priority:** Medium | **Effort:** 1 day spike to assess feasibility
**Recommendation:** Conditional go — spike `vite-ssg` on public routes only

#### Context

The portfolio is a Vue 3 SPA. Public page load flow: download HTML shell → parse/execute JS bundle
→ fetch API data → render. SSG pre-renders pages at build time so the user receives fully rendered
HTML in the initial response — eliminating the client-side API fetch for first paint.

Current state (`vite.config.ts`): standard Vite + Vue SPA configuration, `vite-plugin-pwa` with
Workbox, Terser, manual chunk splitting. No SSG plugin. No `nuxt.config.ts` anywhere.

Routes that are SSG candidates (`router/index.ts`):
- `/` — static home page
- `/company/:id` — dynamic, API-driven, SSG-able with `includedRoutes` callback
- `/experience/:id` — dynamic, SSG-able with same callback

Routes that must stay SPA (auth-gated):
- `/admin/login`, `/admin`, `/admin/companies`, `/admin/education`, `/admin/projects`

#### Web research findings

- **SPA vs SSG TTFB**: SSG eliminates client-side data fetching for initial render. LCP improves
  significantly — the browser receives painted content in the first HTML document. (Vue.js official
  docs, multiple benchmarks)
- **vite-ssg** (antfu-collective): minimal migration — change build script from `vite build` to
  `vite-ssg build`, change app entry to export `createApp` instead of calling `.mount()`, add
  `includedRoutes` callback for dynamic routes. Last release 2024, compatible with Vite 7 + Vue 3.5.
  Admin routes are excluded from static generation via the `includedRoutes` callback — they remain
  SPA with the existing auth guard. Fully supported use case.
- **Nuxt 3**: complete framework migration. Benefits (ISR, hybrid rendering) are not needed here.
  Migration cost is disproportionate for a small portfolio. **Recommendation: do not use Nuxt 3.**
- **Edge caching**: Vercel already caches the SPA HTML shell at the edge. The real gain from SSG is
  eliminating the client-side API waterfall for first paint, not TTFB of the HTML document.

#### Critical risk item

`ThreeHeroBackground.vue` and all GSAP animations use `window`/`document` globals directly. SSG
pre-renders on Node.js where these don't exist. This causes a build-time crash unless:
1. Three.js is wrapped in `onMounted` (PERF-001 fix, already planned) — this is required before
   attempting SSG
2. GSAP calls are similarly guarded inside `onMounted`/`onBeforeMount`

This is the highest-risk item in the migration. Resolving PERF-001 first is a prerequisite.

#### Migration estimate

| Step | Effort |
|------|--------|
| Install `vite-ssg`, change entry point | 30 min |
| `includedRoutes` callback to enumerate company/experience IDs from API | 45 min |
| Admin route exclusion | 15 min |
| Fix SSR-incompatible `window`/`document` calls (GSAP, Three.js) | 2–4 hrs |
| CI: add rebuild trigger workflow (GitHub Actions webhook on admin save) | 1 hr |
| Testing | 2 hrs |

Total: approximately 1 working day.

#### Action

1. Complete PERF-001 (Three.js dynamic import) first — prerequisite.
2. Spike `vite-ssg` on a branch.
3. Verify build succeeds without SSR globals errors.
4. Measure Lighthouse LCP before and after on the built output.
5. If LCP improvement is ≥0.5s on a simulated slow connection: merge.

---

### EVAL-002: GitHub username hardcoded in `GitHubStats.vue` — move to `config/index.ts`
**File:** `frontend/src/components/GitHubStats.vue` (prop default), `frontend/src/config/index.ts`
**Priority:** Low | **Effort:** 10 minutes
**Risk:** Low — no runtime behavior change

#### Current code

`frontend/src/components/GitHubStats.vue` (lines ~133-137):
```ts
const props = withDefaults(defineProps<Props>(), {
  username: 'Dashtid'
})
```

`frontend/src/config/index.ts` (already contains site-level constants):
```ts
export const config = {
  apiUrl: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  endpoints: { ... },
  app: {
    name: 'Portfolio'
  },
  storageKeys: STORAGE_KEYS
} as const
```

Note: the config file is at `frontend/src/config/index.ts`, not `frontend/src/config.ts` as the
original stub stated.

#### Problem

`'Dashtid'` is a site-identity constant, equivalent to `config.app.name`. It belongs in the config
file next to other site constants. Currently it is invisible to anyone reading `config/index.ts`.
The component also has a local `const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'`
that duplicates `config.apiUrl` — both can be cleaned up in the same pass.

#### Web research findings

- The `config/index.ts` pattern (typed `as const` object) is the Vue 3 standard for public
  constants that do not vary between environments. Use `VITE_*` env vars for per-deployment values;
  use `config.ts` for site-identity constants that are stable across all deployments. (Vite docs,
  Vue School)
- Using `as const` gives TypeScript literal type inference: `config.github.username` is typed as
  `'Dashtid'` not `string`, catching typos at compile time.

#### Fix

**Step 1** — `frontend/src/config/index.ts`:
```ts
export const config = {
  apiUrl: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  endpoints: { ... },
  app: { name: 'Portfolio' },
  github: { username: 'Dashtid' },   // add this
  storageKeys: STORAGE_KEYS
} as const
```

**Step 2** — `frontend/src/components/GitHubStats.vue`:
```ts
/* Remove */
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

/* Replace prop default */
import { config } from '@/config'

const props = withDefaults(defineProps<Props>(), {
  username: config.github.username
})
```

Replace the `API_URL` local constant with `config.apiUrl` throughout the file.

#### Testing

1. `npm run type-check` — passes with no new errors.
2. GitHub stats section renders with repos/language data for the `Dashtid` account.
3. `grep -r "'Dashtid'" frontend/src` — only `config/index.ts` contains the string.

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
