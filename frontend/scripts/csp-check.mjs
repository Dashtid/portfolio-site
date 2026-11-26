// Enforced-CSP check: serve dist/ with the REAL Content-Security-Policy from
// vercel.json attached to every HTML response, drive the pages in a headless
// browser, and fail on any securitypolicyviolation event.
//
// Why this exists: local servers and `vite preview` never apply vercel.json
// headers, so nothing between "edit the CSP" and "production" runs the pages
// under the actual policy. Static analysis is not enough either — the
// style-src lockdown (e1ee743) shipped only because a run like this caught
// @vueuse/core's useDark() injecting a transient <style> on every theme
// flip, something no grep of the sources or the dist could see. The theme
// is flipped twice on every SPA route below for exactly that reason: keep
// exercising the runtime injections the hashes exist to cover. On the
// experience page every media placeholder is pressed as well, so the
// YouTube and Google Maps frames load under frame-src, and a route whose
// hydration logs a mismatch fails too.
//
// Run:  node scripts/csp-check.mjs   (after a build; CI runs it in the e2e
// job against the downloaded dist artifact). Non-CSP console noise — e.g.
// CORS failures against the production API from a localhost origin — is
// deliberately ignored; only policy violations, hydration mismatches,
// placeholders missing after hydration or loading no frame when pressed,
// and missing styling fail.
import http from 'node:http'
import fs from 'node:fs'
import path from 'node:path'
import { createRequire } from 'node:module'

// @playwright/test is the declared dependency (bare 'playwright' only
// resolves through hoisting) and re-exports the same chromium launcher.
const require = createRequire(import.meta.url)
const { chromium } = require('@playwright/test')

const ROOT = path.resolve(import.meta.dirname, '..')
const DIST = path.join(ROOT, 'dist')

if (!fs.existsSync(path.join(DIST, 'index.html'))) {
  console.error('[-] no dist/index.html — build first (npm run build:ssg)')
  process.exit(1)
}

const vercel = JSON.parse(fs.readFileSync(path.join(ROOT, 'vercel.json'), 'utf-8'))
const CSP = vercel.headers
  .flatMap(h => h.headers)
  .find(h => h.key === 'Content-Security-Policy').value
console.log('[i] enforcing:', CSP.match(/style-src [^;]*/)[0], '| plus full policy')

const TYPES = {
  '.html': 'text/html',
  '.js': 'text/javascript',
  '.css': 'text/css',
  '.json': 'application/json',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.woff2': 'font/woff2',
  '.webmanifest': 'application/manifest+json',
  '.xml': 'application/xml'
}

// Index every servable file up front. The request path is then only ever a
// LOOKUP KEY into this map — no filesystem path is derived from user input
// at all, so a traversal has nothing to traverse (this replaces a
// resolve-and-check guard that was both weaker and opaque to CodeQL's
// js/path-injection model). Unknown routes fall back to index.html, which
// is what the SPA serves for them in production anyway.
const FILES = new Map()
const indexDist = dir => {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name)
    if (entry.isDirectory()) indexDist(full)
    else FILES.set(`/${path.relative(DIST, full).split(path.sep).join('/')}`, full)
  }
}
indexDist(DIST)
const INDEX_HTML = FILES.get('/index.html')

const server = http.createServer((req, res) => {
  let rel
  try {
    rel = decodeURIComponent(req.url.split('?')[0])
  } catch {
    rel = '/'
  }
  const file =
    FILES.get(rel) ??
    FILES.get(`${rel}.html`) ??
    FILES.get(`${rel.replace(/\/+$/, '')}/index.html`) ??
    INDEX_HTML
  const ext = path.extname(file)
  if (ext === '.html') res.setHeader('Content-Security-Policy', CSP)
  res.setHeader('Content-Type', TYPES[ext] ?? 'application/octet-stream')
  fs.createReadStream(file).pipe(res)
})
await new Promise(resolve => server.listen(0, resolve))
const BASE = `http://localhost:${server.address().port}`

// SPA routes: the static pages plus one SSG'd experience page (whichever
// the build produced — no hardcoded UUID).
const routes = ['/', '/colophon', '/privacy', '/writing']
const expDir = path.join(DIST, 'experience')
// Media placeholders in a route's baked HTML, counted the way
// verify-dist-invariants.mjs counts them.
const bakedPlaceholders = new Map()
const placeholdersIn = file =>
  (fs.readFileSync(file, 'utf-8').match(/class="[^"]*\bembed-facade\b/g) ?? []).length
if (fs.existsSync(expDir)) {
  // The first page that bakes a media placeholder, when there is one, so the
  // click step below has something to click.
  const pages = fs
    .readdirSync(expDir)
    .filter(f => f.endsWith('.html'))
    .sort()
  const chosen = pages.find(f => placeholdersIn(path.join(expDir, f)) > 0) ?? pages[0]
  if (chosen) {
    const route = `/experience/${chosen.replace(/\.html$/, '')}`
    routes.push(route)
    bakedPlaceholders.set(route, placeholdersIn(path.join(expDir, chosen)))
  }
}

const browser = await chromium.launch()
const context = await browser.newContext({
  viewport: { width: 1280, height: 900 },
  serviceWorkers: 'block'
})
await context.addInitScript(() => {
  window.__cspViolations = []
  document.addEventListener('securitypolicyviolation', e => {
    window.__cspViolations.push(
      `${e.violatedDirective} @ ${e.sourceFile || '?'}:${e.lineNumber}:${e.columnNumber}`
    )
  })
})

let failed = false
const check = (label, ok, detail = '') => {
  console.log(`${ok ? '[+]' : '[-]'} ${label}${detail ? ` — ${detail}` : ''}`)
  if (!ok) failed = true
}

const page = await context.newPage()
let current = ''
page.on('console', m => {
  if (m.type() === 'error' && /Content Security Policy/i.test(m.text())) {
    failed = true
    console.log(`[-] console CSP error: ${m.text().slice(0, 160)}`)
  }
  // Every route here is a real prerendered page, so the client's first
  // render must match the baked markup. Vue's production build logs this
  // line once per page when it does not.
  if (m.text().includes('Hydration completed but contains mismatches')) {
    failed = true
    console.log(`[-] ${current}: hydration mismatch: ${m.text().slice(0, 160)}`)
  }
})

for (const route of routes) {
  current = route
  // domcontentloaded + a settle window, NOT networkidle/load: once its
  // media placeholders are clicked, the experience page holds third-party
  // iframes (YouTube, Maps) whose network activity never goes idle on a
  // slow runner — the first CI run of this harness timed out exactly there.
  // CSP violations accumulate in the listener as resources process. The
  // navbar toggle is in the baked HTML, so waiting for it shows that the
  // page has rendered, not that the client has hydrated it; the media step
  // below waits for hydration before it presses anything.
  await page.goto(`${BASE}${route}`, { waitUntil: 'domcontentloaded' })
  await page.waitForSelector('[data-testid="theme-toggle"]', { timeout: 20000 })
  await page.waitForTimeout(800)

  // Flip the theme twice: useDark() injects its transition-guard <style>
  // on every flip, and that injection must stay covered by its pinned
  // hash. A VueUse upgrade that rewords the constant fails HERE (and in
  // cspHashes.spec.ts) instead of silently un-styling production flips.
  const toggle = page.locator('[data-testid="theme-toggle"]')
  await toggle.click()
  await page.waitForTimeout(400)
  await toggle.click()
  await page.waitForTimeout(400)

  // Media placeholders: each button replaces its placeholder with the
  // YouTube or Google Maps iframe, whose navigation frame-src must allow.
  // The buttons are in the baked HTML, so they are on the page before
  // hydration binds their click handlers, and a press before that does
  // nothing. [data-anim] is set in the experience page's onMounted hook,
  // which runs after hydration. Every baked placeholder must still be on
  // the page then: one that is gone was replaced without a click. A
  // pressed placeholder leaves the page, so the first match is always the
  // next one.
  const baked = bakedPlaceholders.get(route) ?? 0
  let placeholders = 0
  if (baked > 0) {
    await page.waitForSelector('[data-anim]', { state: 'attached', timeout: 20000 })
    const facades = page.locator('.embed-facade button')
    placeholders = await facades.count()
    check(
      `${route}: ${baked} baked media placeholder(s) still on the page after hydration`,
      placeholders === baked,
      `${placeholders} found`
    )
    for (let i = 0; i < placeholders; i++) await facades.first().click()
    await page.waitForTimeout(3000)
    const frames = await page.locator('figure iframe').count()
    check(
      `${route}: ${placeholders} media placeholder(s) replaced by their iframes`,
      frames === placeholders,
      `${frames} iframe(s)`
    )
  } else if (route.startsWith('/experience/')) {
    console.log(`[i] ${route}: no media placeholder baked, so none clicked`)
  }

  const exercised = placeholders > 0 ? 'two theme flips and the media clicks' : 'two theme flips'
  const violations = await page.evaluate(() => window.__cspViolations)
  check(
    `${route}: zero CSP violations (incl. ${exercised})`,
    violations.length === 0,
    violations.slice(0, 3).join(' | ')
  )

  const styled = await page.evaluate(
    () => document.styleSheets.length > 0 && getComputedStyle(document.body).fontFamily !== ''
  )
  check(`${route}: stylesheets applied`, styled)
}

// Hero stagger: the nth-of-type CSS that replaced the style attributes
// (e1ee743) must keep producing five distinct animation delays.
current = '/'
await page.goto(`${BASE}/`, { waitUntil: 'domcontentloaded' })
await page.waitForSelector('.trace-nodes .trace-node', { timeout: 20000 })
const delays = await page.$$eval('.trace-nodes .trace-node', els =>
  els.map(el => getComputedStyle(el).animationDelay)
)
check(
  'hero stagger: 5 nodes, 5 distinct delays',
  delays.length === 5 && new Set(delays).size === 5,
  JSON.stringify(delays)
)

// offline.html: its single <style> block is allowed by hash — it must
// actually apply (flex-centred body), not just fail to violate.
current = '/offline.html'
await page.goto(`${BASE}/offline.html`, { waitUntil: 'load' })
await page.waitForTimeout(300)
const offline = await page.evaluate(() => ({
  violations: window.__cspViolations,
  display: getComputedStyle(document.body).display
}))
check(
  'offline.html: zero CSP violations',
  offline.violations.length === 0,
  offline.violations.join(' | ')
)
check(
  'offline.html: hashed style block applied',
  offline.display === 'flex',
  `display=${offline.display}`
)

await browser.close()
server.close()
console.log(failed ? '[-] enforced-CSP check FAILED' : '[+] enforced-CSP check passed')
process.exit(failed ? 1 : 0)
