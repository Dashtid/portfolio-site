import { describe, it, expect } from 'vitest'
import { readdirSync, readFileSync } from 'node:fs'
import { join, relative, resolve, sep } from 'node:path'
import { safeUrl } from '@/utils/safeUrl'

// Built from char codes so the control characters stay visible in review.
const TAB = String.fromCharCode(9)
const NEWLINE = String.fromCharCode(10)
const CONTROL = String.fromCharCode(1)

describe('safeUrl', () => {
  it.each([
    'https://hermesmedical.com',
    'http://example.com/page',
    'mailto:someone@example.com',
    '/images/hermes.png',
    'media/thesis.pdf',
    ''
  ])('keeps %j unchanged', url => {
    expect(safeUrl(url)).toBe(url)
  })

  it.each([
    'javascript:alert(1)',
    'JavaScript:alert(1)',
    ' javascript:alert(1)',
    `java${TAB}script:alert(1)`,
    `java${NEWLINE}script:alert(1)`,
    `${CONTROL}javascript:alert(1)`,
    'data:text/html,<script>alert(1)</script>',
    'vbscript:msgbox(1)',
    'file:///etc/passwd',
    'http://[::1'
  ])('drops %j', url => {
    expect(safeUrl(url)).toBeUndefined()
  })

  it('drops a missing value', () => {
    expect(safeUrl(null)).toBeUndefined()
    expect(safeUrl(undefined)).toBeUndefined()
  })
})

const SRC = resolve(__dirname, '../../../src')

// Bindings that may skip safeUrl: each takes no API or CMS value, or another
// check already pins its scheme. Adding a binding here is a deliberate act.
const EXEMPT: Record<string, string[]> = {
  // Static navigation and the build stamp.
  'components/NavBar.vue': ['`#${item.href}`'],
  'components/FooterSection.vue': [
    'link.href',
    '`https://github.com/Dashtid/portfolio-site/commit/${buildCommit}`'
  ],
  // useEmbedValidator admits https URLs on the embed hosts only.
  'components/VideoEmbed.vue': ['safeUrl'],
  'components/MapEmbed.vue': ['localizedUrl'],
  // The CV photo: a data:image URI (PhotoDataUri in the backend schema) in an
  // img, which never runs a URL as script.
  'components/cv/CvDocument.vue': ['resume.basics.image'],
  'views/admin/AdminCv.vue': ['profile.photo']
}

const vueFiles = (dir: string): string[] =>
  readdirSync(dir, { withFileTypes: true }).flatMap(entry => {
    const full = join(dir, entry.name)
    if (entry.isDirectory()) return vueFiles(full)
    return entry.name.endsWith('.vue') ? [full] : []
  })

const boundUrls = (): Array<{ file: string; expr: string }> =>
  vueFiles(SRC).flatMap(full => {
    const file = relative(SRC, full).split(sep).join('/')
    const source = readFileSync(full, 'utf-8')
    return [...source.matchAll(/\s(?::|v-bind:)(?:href|src)="([^"]*)"/g)].map(m => ({
      file,
      expr: m[1]
    }))
  })

describe('URL bindings in templates', () => {
  it('pass every bound href and src through safeUrl unless exempt', () => {
    const unguarded = boundUrls()
      .filter(({ file, expr }) => !expr.startsWith('safeUrl(') && !EXEMPT[file]?.includes(expr))
      .map(({ file, expr }) => `${file}: ${expr}`)
    expect(unguarded).toEqual([])
  })

  it('lists only exemptions that still exist', () => {
    const bound = new Set(boundUrls().map(({ file, expr }) => `${file}: ${expr}`))
    const stale = Object.entries(EXEMPT)
      .flatMap(([file, exprs]) => exprs.map(expr => `${file}: ${expr}`))
      .filter(entry => !bound.has(entry))
    expect(stale).toEqual([])
  })
})
