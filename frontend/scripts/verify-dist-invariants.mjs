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

console.log(
  `[dist-invariants] OK: marked lazy-only (lives in ${markerLivesIn.join(', ')}), ` +
    `${eagerRefs.length} eager chunks clean, Admin excluded + ExperienceDetail present in precache`
)
