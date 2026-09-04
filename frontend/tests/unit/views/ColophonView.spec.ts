import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { useHead } from '@unhead/vue'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import ColophonView from '@/views/ColophonView.vue'

/**
 * The colophon states security properties of the live site in plain English
 * and invites the reader to check them. That makes it the one page where
 * going stale is not cosmetic — a weakened header would turn published prose
 * into a false claim, on the page a security-minded reader is most likely to
 * verify.
 *
 * So these tests do not just mount the view. They bind each claim to the
 * config that has to remain true for it, and fail when the two diverge in
 * EITHER direction: a policy that gets weaker makes the page a lie, and a
 * policy that gets stronger makes the page's own admission of a gap wrong.
 */

vi.mock('@/components/NavBar.vue', () => ({
  default: { name: 'NavBar', template: '<nav data-testid="navbar" />' }
}))
vi.mock('@/components/FooterSection.vue', () => ({
  default: { name: 'FooterSection', template: '<footer data-testid="footer" />' }
}))

const mockedUseHead = vi.mocked(useHead)

const FRONTEND_ROOT = resolve(__dirname, '../../..')

const directive = (name: string): string => {
  const vercel = JSON.parse(readFileSync(resolve(FRONTEND_ROOT, 'vercel.json'), 'utf-8')) as {
    headers: { headers: { key: string; value: string }[] }[]
  }
  const header = vercel.headers
    .flatMap(h => h.headers)
    .find(h => h.key === 'Content-Security-Policy')
  if (!header) throw new Error('no Content-Security-Policy header in vercel.json')
  const match = header.value.match(new RegExp(`(?:^|; )${name} ([^;]*)`))
  if (!match) throw new Error(`no ${name} directive in the CSP`)
  return match[1]
}

const mountView = async () => {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', component: { template: '<div />' }, name: 'home' },
      { path: '/colophon', component: ColophonView, name: 'colophon' }
    ]
  })
  await router.push('/colophon')
  await router.isReady()
  return mount(ColophonView, { global: { plugins: [router] } })
}

describe('ColophonView', () => {
  it('renders every section the page promises', async () => {
    const wrapper = await mountView()
    const text = wrapper.text()
    expect(text).toContain('Colophon')
    for (const heading of [
      'What it is built with',
      'What the browser is told',
      'The private half',
      'What goes into a build',
      'Backups, and evidence they work',
      'Where it falls short',
      'Reporting something'
    ]) {
      expect(text).toContain(heading)
    }
  })

  it('is indexable and self-canonical', async () => {
    mockedUseHead.mockClear()
    await mountView()

    const headArg = mockedUseHead.mock.calls[0][0] as {
      meta: Array<{ name?: string; property?: string; content: string }>
      link: Array<{ rel: string; href: string }>
    }
    expect(headArg.meta.find(m => m.name === 'robots')?.content).toBe('index, follow')
    expect(headArg.link.find(l => l.rel === 'canonical')?.href).toBe('https://dashti.se/colophon')
    // og:url must match the canonical — a mismatch is the D3-CNT-02 class.
    expect(headArg.meta.find(m => m.property === 'og:url')?.content).toBe(
      'https://dashti.se/colophon'
    )
  })

  it('links out to the security.txt it tells readers to use', async () => {
    const wrapper = await mountView()
    const hrefs = wrapper.findAll('a').map(a => a.attributes('href'))
    expect(hrefs).toContain('/.well-known/security.txt')
  })

  it('carries a verification date, so a stale claim is visibly stale', async () => {
    const wrapper = await mountView()
    expect(wrapper.text()).toMatch(/last verified against the live site on \d{1,2} \w+ \d{4}/i)
  })
})

describe('ColophonView claims still match the shipped CSP', () => {
  it('scripts really do carry no inline exemption', () => {
    // The page: "Scripts may load only from this origin, plus two SHA-256
    // hashes"; and under Where it falls short, that scripts have no exemption.
    const scriptSrc = directive('script-src')
    expect(scriptSrc).not.toContain('unsafe-inline')
    expect(scriptSrc).not.toContain('unsafe-eval')
    expect(scriptSrc).toContain("'self'")
  })

  it('there really are exactly two script hashes', () => {
    // The page says "two SHA-256 hashes". If a third inline script is ever
    // hashed in, the sentence needs rewriting — not just the header.
    const hashes = directive('script-src').match(/'sha256-[^']+'/g) ?? []
    expect(hashes).toHaveLength(2)
  })

  it('the four blanket denials the page names are all still set', () => {
    // "Inline event handlers are refused outright, as are plugins, framing,
    // and any attempt to rewrite the document base or post a form elsewhere."
    expect(directive('script-src-attr')).toBe("'none'")
    expect(directive('object-src')).toBe("'none'")
    expect(directive('frame-ancestors')).toBe("'none'")
    expect(directive('base-uri')).toBe("'self'")
    expect(directive('form-action')).toBe("'self'")
  })

  it('the admitted style-src gap is still real, so the admission is not itself stale', () => {
    // Deliberately asserts the WEAKNESS. If inline styles are ever removed
    // from the policy this fails, which is the prompt to delete the "Where it
    // falls short" section rather than leave the site apologising for a gap
    // it has already closed.
    expect(directive('style-src')).toContain('unsafe-inline')
  })
})
