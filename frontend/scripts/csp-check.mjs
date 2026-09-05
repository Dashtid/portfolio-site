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
// exercising the runtime injections the hashes exist to cover.
//
// Run:  node scripts/csp-check.mjs   (after a build; CI runs it in the e2e
// job against the downloaded dist artifact). Non-CSP console noise — e.g.
// CORS failures against the production API from a localhost origin — is
// deliberately ignored; only policy violations and missing styling fail.
import http from 'node:http'
import fs from 'node:fs'
import path from 'node:path'
import { createRequire } from 'node:module'

const require = createRequire(import.meta.url)
const { chromium } = require('playwright')

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

const server = http.createServer((req, res) => {
  const rel = decodeURIComponent(req.url.split('?')[0])
  let file = path.join(DIST, rel)
  if (!fs.existsSync(file) || fs.statSync(file).isDirectory()) {
    const asHtml = path.join(DIST, `${rel}.html`)
    file = fs.existsSync(asHtml) ? asHtml : path.join(DIST, 'index.html')
  }
  const ext = path.extname(file)
  if (ext === '.html') res.setHeader('Content-Security-Policy', CSP)
  res.setHeader('Content-Type', TYPES[ext] ?? 'application/octet-stream')
  fs.createReadStream(file).pipe(res)
})
await new Promise(resolve => server.listen(0, resolve))
const BASE = `http://localhost:${server.address().port}`

// SPA routes: the static pages plus one SSG'd experience page (whichever
// the build produced — no hardcoded UUID).
const routes = ['/', '/colophon', '/writing']
const expDir = path.join(DIST, 'experience')
if (fs.existsSync(expDir)) {
  const first = fs
    .readdirSync(expDir)
    .filter(f => f.endsWith('.html'))
    .sort()[0]
  if (first) routes.push(`/experience/${first.replace(/\.html$/, '')}`)
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
page.on('console', m => {
  if (m.type() === 'error' && /Content Security Policy/i.test(m.text())) {
    failed = true
    console.log(`[-] console CSP error: ${m.text().slice(0, 160)}`)
  }
})

for (const route of routes) {
  await page.goto(`${BASE}${route}`, { waitUntil: 'networkidle' })
  await page.waitForTimeout(500)

  // Flip the theme twice: useDark() injects its transition-guard <style>
  // on every flip, and that injection must stay covered by its pinned
  // hash. A VueUse upgrade that rewords the constant fails HERE (and in
  // cspHashes.spec.ts) instead of silently un-styling production flips.
  const toggle = page.locator('[data-testid="theme-toggle"]')
  if ((await toggle.count()) > 0) {
    await toggle.click()
    await page.waitForTimeout(400)
    await toggle.click()
    await page.waitForTimeout(400)
  }

  const violations = await page.evaluate(() => window.__cspViolations)
  check(
    `${route}: zero CSP violations (incl. two theme flips)`,
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
await page.goto(`${BASE}/`, { waitUntil: 'networkidle' })
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
