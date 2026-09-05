import { describe, it, expect } from 'vitest'
import { createHash } from 'node:crypto'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

/**
 * D3-SEC-03 drift tripwire: vercel.json's script-src carries STATIC
 * sha256 hashes for the only two executable inline scripts the site
 * ships — the theme-init IIFE in index.html and offline.html's
 * connection checker. The hashes are whitespace-sensitive: a Prettier
 * reformat, an edited comment, or a new inline script silently breaks
 * the CSP in production while every local test keeps passing (local
 * servers don't apply vercel.json headers). This test recomputes the
 * hashes from source on every run so that drift fails CI instead.
 *
 * If it fails after an intentional edit: recompute with
 *   python -c "import hashlib,base64,re,io;
 *     b=re.search(r'<script>(.*?)</script>', io.open('<file>',
 *     encoding='utf-8', newline='').read(), re.S).group(1);
 *     print('sha256-'+base64.b64encode(hashlib.sha256(
 *     b.encode()).digest()).decode())"
 * and update vercel.json's script-src.
 */

const FRONTEND_ROOT = resolve(__dirname, '../..')

const read = (rel: string): string => readFileSync(resolve(FRONTEND_ROOT, rel), 'utf-8')

// `<script\s*>` rather than `<script>`: HTML treats `<script >` and
// `<SCRIPT>` as the same tag, so the stricter literal would skip a second
// inline script written either way — and this guard exists precisely to stop
// an unhashed inline script slipping past CSP. Attributes still exclude a tag
// from the match (`\s*>` admits whitespace only), which is the intent: scripts
// with src/type are covered by 'self' or are non-executing data blocks.
const BARE_SCRIPT = /<script\s*>([\s\S]*?)<\/script\s*>/i

const firstBareScriptBody = (html: string): string => {
  const match = html.match(BARE_SCRIPT)
  if (!match) throw new Error('no bare inline <script> found')
  return match[1]
}

const cspHash = (scriptBody: string): string =>
  `sha256-${createHash('sha256').update(scriptBody, 'utf-8').digest('base64')}`

const csp = (): string => {
  const vercel = JSON.parse(read('vercel.json')) as {
    headers: { source: string; headers: { key: string; value: string }[] }[]
  }
  const all = vercel.headers.flatMap(h => h.headers)
  const header = all.find(h => h.key === 'Content-Security-Policy')
  if (!header) throw new Error('no Content-Security-Policy header in vercel.json')
  return header.value
}

const directive = (name: string): string => {
  const match = csp().match(new RegExp(`(?:^|; )${name} ([^;]*)`))
  if (!match) throw new Error(`no ${name} directive in the CSP`)
  return match[1]
}

describe('CSP script hashes (D3-SEC-03)', () => {
  it('script-src carries the hash of the index.html theme-init script', () => {
    expect(directive('script-src')).toContain(cspHash(firstBareScriptBody(read('index.html'))))
  })

  it('script-src carries the hash of the offline.html connection script', () => {
    expect(directive('script-src')).toContain(
      cspHash(firstBareScriptBody(read('public/offline.html')))
    )
  })

  it('script-src has no unsafe-inline and inline handlers are forbidden', () => {
    expect(directive('script-src')).not.toContain('unsafe-inline')
    expect(directive('script-src-attr')).toBe("'none'")
  })

  // style-src went hash-locked on 2026-09-04 (the /colophon work): the only
  // <style> block the site ships is offline.html's, and the only styled
  // markup (HomeView's --node-i stagger attrs) moved into the stylesheet.
  // These three keep that closed. NOTE for future inline styling: a hash
  // only covers <style> ELEMENTS — a style="" ATTRIBUTE needs
  // 'unsafe-hashes' or a refactor to classes; prefer the refactor.
  it('style-src carries the hash of the offline.html style block', () => {
    const match = read('public/offline.html').match(/<style\s*>([\s\S]*?)<\/style\s*>/i)
    if (!match) throw new Error('no <style> block found in offline.html')
    expect(directive('style-src')).toContain(cspHash(match[1]))
  })

  it('style-src has no unsafe-inline', () => {
    expect(directive('style-src')).not.toContain('unsafe-inline')
  })

  it("style-src carries the hash of VueUse's transition-disable style", () => {
    // useDark() (src/composables/useTheme.ts) injects a transient <style>
    // on every theme change to suppress transitions during the flip. The
    // CSS is a hardcoded constant inside @vueuse/core, so it is hashed
    // rather than allowed wholesale. Read the constant from the INSTALLED
    // package: a VueUse upgrade that rewords it fails here with a clear
    // message instead of silently un-guarding theme flips in production
    // (the failure there is cosmetic and invisible — transitions animate
    // during the flip — which is exactly why CI has to be the one to see it).
    const vueuse = readFileSync(
      resolve(FRONTEND_ROOT, 'node_modules/@vueuse/core/dist/index.js'),
      'utf-8'
    )
    const match = vueuse.match(/\*,\*::before,\*::after\{[^}]*transition:none[^}]*\}/)
    if (!match) {
      throw new Error(
        'transition-disable constant not found in @vueuse/core — ' +
          'if useDark no longer injects styles, drop its hash from style-src'
      )
    }
    expect(directive('style-src')).toContain(cspHash(match[0]))
  })

  it('style-src carries exactly the two hashes with a documented owner', () => {
    // offline.html's block + VueUse's transition guard. A third hash with
    // no test naming its source is how allowances go feral.
    expect(directive('style-src').match(/'sha256-[^']+'/g) ?? []).toHaveLength(2)
  })

  it('the static HTML entry points carry no style attributes or extra style blocks', () => {
    // index.html: zero of both (its styles are all in the built stylesheet).
    // offline.html: exactly the one hashed block above, no attributes.
    expect(read('index.html')).not.toMatch(/<[^>]+\sstyle="/i)
    expect(read('index.html')).not.toMatch(/<style[\s>]/i)
    expect(read('public/offline.html')).not.toMatch(/<[^>]+\sstyle="/i)
    expect(read('public/offline.html').match(/<style[\s>]/gi) ?? []).toHaveLength(1)
  })

  it('index.html has exactly one executable inline script (theme-init)', () => {
    // A second bare <script> would need its own hash — force the author
    // through this file. Scripts with src/type attributes don't count
    // (external scripts are 'self'; JSON-LD is a non-executing data block).
    const bareScripts = read('index.html').match(new RegExp(BARE_SCRIPT, 'gi')) ?? []
    expect(bareScripts).toHaveLength(1)
  })

  it('no inline event handler attributes in the static HTML', () => {
    for (const file of ['index.html', 'public/offline.html']) {
      // script-src-attr 'none' blocks these outright — they must not exist.
      expect(read(file)).not.toMatch(/<[^>]+\son[a-z]+=/i)
    }
  })
})

describe('vercel.json schema hygiene', () => {
  // Vercel validates vercel.json against a CLOSED schema and REJECTS the whole
  // deploy on any unknown key: "Invalid vercel.json - should NOT have additional
  // property X". JSON has no comment syntax, so the tempting `"//key": "why"`
  // convention is a deploy-breaker, not a comment — it cost a deploy on
  // 2026-08-17. Rationale for a setting belongs in the commit message.
  // Every gate here (JSON lint, prettier, build) passes on such a file; only
  // Vercel rejects it, which is why this guard exists.
  it('has no comment-style keys at any depth', () => {
    const offenders: string[] = []
    const walk = (node: unknown, path: string): void => {
      if (Array.isArray(node)) {
        node.forEach((item, i) => walk(item, `${path}[${i}]`))
      } else if (node && typeof node === 'object') {
        for (const [key, value] of Object.entries(node)) {
          if (key.startsWith('//') || key.startsWith('#')) offenders.push(`${path}.${key}`)
          walk(value, `${path}.${key}`)
        }
      }
    }
    walk(JSON.parse(read('vercel.json')), 'vercel.json')
    expect(offenders).toEqual([])
  })
})
