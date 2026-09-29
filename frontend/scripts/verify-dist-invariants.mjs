/**
 * Post-build guard for dist invariants that no unit/e2e/visual test can see
 * (CI runs vitest BEFORE the build; playwright asserts rendering, not chunk
 * membership). Chained into build:ssg, so it runs in CI frontend-quality,
 * the lighthouse rebuild, rebake-frontend, and every Vercel deploy.
 *
 * Invariants:
 * 1. D4-PERF: marked (the markdown renderer) must never enter the eager
 *    homepage graph. Since the vite-8 sprint removed custom chunk grouping
 *    (Rolldown 1.2.1 emits broken module-init code for ANY custom vendor
 *    group — see vite.config.ts), the invariant rests only on module
 *    separation (data/writing.ts is meta-only; data/renderMarkdown.ts is
 *    imported solely by the lazy WritingArticleView route) and Rolldown's
 *    default splitting. Both are silently mutable — this check is the gate.
 * 2. The SW precache must exclude Admin* chunks (single-user bundle; the
 *    admin-table-as-public-surface trap) and MUST include the
 *    ExperienceDetail chunk (offline navigations fall back to the shell,
 *    which needs that chunk to render the retry UI instead of dead-ending
 *    in the stale-chunk reload loop — see the workbox globIgnores comment).
 * 3. No <style> block or style attribute the CSP does not cover.
 * 4. No off-portfolio repo name and no scrubbed credential may appear in the
 *    baked pages. This is the only check that sees CMS/DB CONTENT: the SSG
 *    bake inlines the API payload into __INITIAL_STATE__, so a claim typed
 *    into the admin panel reaches production without passing a single test.
 *    A 2026-09-06 content audit found exactly that class of miss — text that
 *    exists in no source file, only in the database and the baked output.
 * 5. The baked homepage must render project cards: the Projects section once
 *    shipped as a bare heading over an empty client-only widget.
 * 6. Every CSS rule that uses backdrop-filter must ship both the standard and
 *    the -webkit- form: Vite 8's Lightning CSS minifier collapsed the
 *    navbar's pair to the -webkit- form alone, which Chromium and Firefox
 *    ignore.
 */
import fs from 'node:fs'
import path from 'node:path'

const dist = path.resolve(import.meta.dirname, '..', 'dist')
const fail = msg => {
  console.error(`[dist-invariants] FAIL: ${msg}`)
  process.exit(1)
}

// A string minification cannot remove: marked's own error-path URL.
const MARKED_MARKER = 'github.com/markedjs/marked'

const indexHtml = fs.readFileSync(path.join(dist, 'index.html'), 'utf-8')
const eagerRefs = [
  ...new Set([...indexHtml.matchAll(/assets\/js\/[A-Za-z0-9._-]+\.js/g)].map(m => m[0]))
]
if (eagerRefs.length === 0) fail('no script refs found in index.html — parser broken?')

for (const ref of eagerRefs) {
  const src = fs.readFileSync(path.join(dist, ref), 'utf-8')
  if (src.includes(MARKED_MARKER)) {
    fail(`marked found in the eager homepage graph (${ref}) — D4-PERF regression`)
  }
}

// Self-validation: the marker must still exist SOMEWHERE in the build,
// otherwise this check has gone vacuous (marked renamed its URL, or the
// dependency was dropped) and needs updating.
const allChunks = fs.readdirSync(path.join(dist, 'assets', 'js')).filter(f => f.endsWith('.js'))
const markerLivesIn = allChunks.filter(f =>
  fs.readFileSync(path.join(dist, 'assets', 'js', f), 'utf-8').includes(MARKED_MARKER)
)
if (markerLivesIn.length === 0) {
  fail('marked marker string not found in ANY chunk — the check is vacuous, update MARKED_MARKER')
}

const sw = fs.readFileSync(path.join(dist, 'sw.js'), 'utf-8')
const adminInPrecache = [...sw.matchAll(/assets\/js\/(Admin[A-Za-z]*)-[A-Za-z0-9_-]+\.js/g)].map(
  m => m[1]
)
if (adminInPrecache.length > 0) {
  fail(`Admin chunks leaked into the SW precache: ${[...new Set(adminInPrecache)].join(', ')}`)
}
if (!/ExperienceDetail-[A-Za-z0-9_-]+\.js/.test(sw)) {
  fail('ExperienceDetail chunk missing from the SW precache — offline navigations will dead-end')
}

// 3. CSP: style-src is hash-locked (no 'unsafe-inline' since 2026-09-04), so
//    the BAKED output must ship zero style attributes and no <style> element
//    beyond offline.html's single hashed block. The unit suite guards the
//    SOURCE files; this guards what a build actually emits — vite-ssg, the
//    admin-shell emitter, or any plugin could inject styling the sources
//    never had, and in production that fails silently as unstyled markup.
const walkHtml = dir =>
  fs.readdirSync(dir, { withFileTypes: true }).flatMap(e => {
    const full = path.join(dir, e.name)
    return e.isDirectory() ? walkHtml(full) : e.name.endsWith('.html') ? [full] : []
  })

for (const file of walkHtml(dist)) {
  const html = fs.readFileSync(file, 'utf-8')
  const rel = path.relative(dist, file)
  if (/<[^>]+\sstyle="/i.test(html)) {
    fail(`style attribute in baked ${rel} — style-src has no 'unsafe-inline' to cover it`)
  }
  const styleBlocks = html.match(/<style[\s>]/gi) ?? []
  const allowed = rel === 'offline.html' ? 1 : 0
  if (styleBlocks.length !== allowed) {
    fail(
      `${styleBlocks.length} <style> block(s) in baked ${rel} (allowed: ${allowed}) — ` +
        'each needs its hash in style-src or it will not apply'
    )
  }
}

// ---------------------------------------------------------------------------
// 4. Banned content in the BAKED pages (visible text + __INITIAL_STATE__).
//
// Everything else in CI reads source files. CMS content never appears in a
// source file: it is typed into the admin panel, stored in Postgres, and
// inlined into these pages at build time. So this is the only gate standing
// between the database and production for the two classes of text that must
// never be published.
//
// [!] Deliberately NOT in this list yet: 'ISMS'. It is site-excluded, like
// ISO 27001 above. The term reaches the pages through CMS
// records rather than through source, so listing it here before those records
// are corrected would turn CI red and block deploys for a fix only the owner
// can apply. Add it in the same change that lands the CMS correction.
// ---------------------------------------------------------------------------
// Repositories held off the public portfolio. The backend allowlist
// (services/github_service.py PUBLIC_REPO_ALLOWLIST) is the primary control;
// this is the backstop that also covers CMS-authored prose mentioning them.
//
// Assembled from fragments, not written out: this repository is public, so the
// backstop that keeps a set of names off the site must not be where those names
// get published. Same approach as the tracked-tree guard in
// frontend/tests/unit/cvPublicScrub.spec.ts.
const OFF_PORTFOLIO_REPOS = [
  ['di', 'com', '-fu', 'zzer'],
  ['sb', 'om-sen', 'tinel'],
  ['med', 'tech-ai-', 'security'],
  ['defen', 'sive-tool', 'kit'],
  ['offen', 'sive-tool', 'kit']
].map(parts => parts.join(''))

const BANNED_IN_BAKED_PAGES = [
  ...OFF_PORTFOLIO_REPOS,
  // Credential claims scrubbed 2026-07-22: never earned, and they had hidden
  // in two places at once. Security+ is the only real certification.
  'AZ-500',
  'Certified Ethical Hacker',
  'ISO 27001 Lead Implementer',
  // The standards claim-gate: ISO 27001 is a LinkedIn-only skill by owner
  // ruling; the site and CV exclude it.
  'ISO 27001',
  'ISO/IEC 27001'
]

for (const file of walkHtml(dist)) {
  const rel = path.relative(dist, file).replace(/\\/g, '/')
  const html = fs.readFileSync(file, 'utf-8')
  for (const term of BANNED_IN_BAKED_PAGES) {
    // Case-insensitive: the point is the claim, not its capitalisation.
    if (new RegExp(term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'i').test(html)) {
      fail(
        `baked page ${rel} contains "${term}" — this text must not be published. ` +
          'If it came from the CMS, fix the record and rebake; if from source, remove it. ' +
          'See the BANNED_IN_BAKED_PAGES comment for why each entry is listed.'
      )
    }
  }
}

// ---------------------------------------------------------------------------
// 5. The Projects section must ship with actual projects in it.
//
// It shipped as a bare heading over a client-only, IntersectionObserver-gated
// widget: crawlers, no-JS readers and anyone who did not scroll got a section
// title and nothing else, while the curated projects sat in the page's baked
// JSON state, rendered by no component (2026-09-06 content audit). Nothing
// failed loudly — the section simply had no content, which is exactly the
// kind of regression that survives review. The bake is a pure function of the
// API response, so an empty grid here means either the fetch degraded or the
// rendering was dropped; both should stop the build.
// ---------------------------------------------------------------------------
const homeCards = (indexHtml.match(/class="[^"]*\bproject-card\b/g) ?? []).length
if (homeCards === 0) {
  fail(
    'baked index.html renders no project cards — the Projects section would ship ' +
      'as a heading over an empty client-only widget. Check that the projects API ' +
      'responded during the bake and that HomeView still renders featuredProjects.'
  )
}

// ---------------------------------------------------------------------------
// 6. backdrop-filter must ship in BOTH forms, in every rule that uses it.
//
// Lightning CSS, Vite 8's minifier under build.cssMinify, treats
// backdrop-filter and -webkit-backdrop-filter as ONE property: a second
// declaration replaces the first, and only an unprefixed one is expanded to
// the prefixes the targets need. NavBar.vue declared the standard form, then
// the -webkit- form, so from the vite-8 sprint on the build shipped
// -webkit-backdrop-filter alone. Chromium and Firefox ignore that form, and
// the glass navbar lost its blur everywhere but Safari. The visual suite
// could not see it: its per-pixel colour threshold absorbs a blur that soft.
// Upstream treats declaration order as the author's job
// (parcel-bundler/lightningcss #785, #1327), so the output is what gets
// checked, in both directions:
//   - -webkit- without the standard form: Chromium and Firefox get no blur.
//   - the standard form without -webkit-: Safari before 18 gets none. The CSS
//     targets reach Safari 16.4 (build.target es2022, which Vite maps to its
//     minify targets). If that floor is ever raised past Safari 17, the
//     prefix rightly disappears and this half of the check goes with it.
// ---------------------------------------------------------------------------
const cssDir = path.join(dist, 'assets', 'css')
let backdropRules = 0
let navbarGlass = false
for (const file of fs.readdirSync(cssDir).filter(f => f.endsWith('.css'))) {
  const css = fs.readFileSync(path.join(cssDir, file), 'utf-8')
  // Every declaration block is `prelude{body}` with no brace inside; blocks
  // nested in @media/@layer match on their own, without the wrapper.
  for (const [, prelude, body] of css.matchAll(/([^{}]*)\{([^{}]*)\}/g)) {
    const props = new Set(
      body.split(';').map(decl => {
        const colon = decl.indexOf(':')
        return colon === -1 ? '' : decl.slice(0, colon).trim().toLowerCase()
      })
    )
    const standard = props.has('backdrop-filter')
    const webkit = props.has('-webkit-backdrop-filter')
    if (!standard && !webkit) continue
    backdropRules++
    const where = `${file}: ${prelude.trim().slice(0, 80)}`
    if (!standard) {
      fail(
        `${where} ships -webkit-backdrop-filter without backdrop-filter, so Chromium and ` +
          'Firefox render no blur. Declare only the standard property and let the build ' +
          'add the prefix (see invariant 6).'
      )
    }
    if (!webkit) {
      fail(
        `${where} ships backdrop-filter without -webkit-backdrop-filter, so Safari before 18 ` +
          'renders no blur. Check the CSS targets (see invariant 6).'
      )
    }
    if (/\.navbar-custom(?![\w-])/.test(prelude)) navbarGlass = true
  }
}
if (!navbarGlass) {
  fail(
    'no .navbar-custom rule with backdrop-filter in dist CSS, so invariant 6 has gone ' +
      'vacuous (NavBar.vue renamed the class or dropped the glass): update the check'
  )
}

console.log(
  `[dist-invariants] OK: marked lazy-only (lives in ${markerLivesIn.join(', ')}), ` +
    `${eagerRefs.length} eager chunks clean, Admin excluded + ExperienceDetail present in precache, ` +
    'baked HTML free of unhashed styling, ' +
    `${BANNED_IN_BAKED_PAGES.length} banned terms absent from baked content, ` +
    `${homeCards} project cards prerendered, ` +
    `${backdropRules} backdrop-filter rules carry both forms`
)
