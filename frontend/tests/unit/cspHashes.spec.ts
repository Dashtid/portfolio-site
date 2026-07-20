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

const firstBareScriptBody = (html: string): string => {
  const match = html.match(/<script>([\s\S]*?)<\/script>/)
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

  it('index.html has exactly one executable inline script (theme-init)', () => {
    // A second bare <script> would need its own hash — force the author
    // through this file. Scripts with src/type attributes don't count
    // (external scripts are 'self'; JSON-LD is a non-executing data block).
    const bareScripts = read('index.html').match(/<script>[\s\S]*?<\/script>/g) ?? []
    expect(bareScripts).toHaveLength(1)
  })

  it('no inline event handler attributes in the static HTML', () => {
    for (const file of ['index.html', 'public/offline.html']) {
      // script-src-attr 'none' blocks these outright — they must not exist.
      expect(read(file)).not.toMatch(/<[^>]+\son[a-z]+=/i)
    }
  })
})
