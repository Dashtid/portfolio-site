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
// [!] Deliberately NOT in this list yet: 'ISMS'. The 2026-09-06 content audit
// found it live in the Hermes entry's CMS copy ("Compliance & ISMS"), where
// the records make ISO 27001 / ISMS site-excluded and ask-before-adding. It
// is a DB edit, not a code edit, so adding the term here today would turn CI
// red and block deploys for a fix only the owner can apply. Add it in the
// same change that lands the CMS correction.
// ---------------------------------------------------------------------------
const BANNED_IN_BAKED_PAGES = [
  // Repos held off the public portfolio (employer-IP / brand). The backend
  // allowlist (services/github_service.py PUBLIC_REPO_ALLOWLIST) is the
  // primary control; this is the backstop that also covers CMS-authored
  // prose mentioning them.
  'dicom-fuzzer',
  'sbom-sentinel',
  'medtech-ai-security',
  'defensive-toolkit',
  'offensive-toolkit',
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

console.log(
  `[dist-invariants] OK: marked lazy-only (lives in ${markerLivesIn.join(', ')}), ` +
    `${eagerRefs.length} eager chunks clean, Admin excluded + ExperienceDetail present in precache, ` +
    'baked HTML free of unhashed styling, ' +
    `${BANNED_IN_BAKED_PAGES.length} banned terms absent from baked content`
)
