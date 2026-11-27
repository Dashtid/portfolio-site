import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createSSRApp } from 'vue'
import { renderToString } from 'vue/server-renderer'
import { createRouter, createMemoryHistory } from 'vue-router'
import { useHead } from '@unhead/vue'
import { readdirSync, readFileSync } from 'node:fs'
import { resolve } from 'node:path'
import PrivacyView from '@/views/PrivacyView.vue'
import { routes } from '@/router'
import { setVisitCountingOptOut, visitCountingDeclined } from '@/services/analytics'

/**
 * The privacy page is static text plus one control, the switch that stores
 * or removes this browser's opt-out through services/analytics.ts. The
 * switch renders only after mount, so the prerendered page carries the
 * sentence for readers without JavaScript and no control, and hydrating it
 * matches the server markup.
 */

// Render functions, not templates: the server renderer cannot compile a
// template string at run time.
vi.mock('@/components/NavBar.vue', async () => {
  const { h } = await import('vue')
  return { default: { name: 'NavBar', render: () => h('nav', { 'data-testid': 'navbar' }) } }
})
vi.mock('@/components/FooterSection.vue', async () => {
  const { h } = await import('vue')
  return {
    default: { name: 'FooterSection', render: () => h('footer', { 'data-testid': 'footer' }) }
  }
})

const mockedUseHead = vi.mocked(useHead)

const REPO_ROOT = resolve(__dirname, '../../../..')
const SRC = resolve(REPO_ROOT, 'frontend/src')
const OPT_OUT_KEY = 'portfolio-analytics-opt-out'
const LINKEDIN = 'https://www.linkedin.com/in/david-dashti/'
const GOOGLE_PRIVACY_POLICY = 'https://policies.google.com/privacy'
const IMY = 'https://www.imy.se/'

const COUNTED = 'Visits from this browser are counted, as described above.'
const DECLINED =
  'Visits from this browser are not counted. The choice is saved in this browser only.'
const SIGNAL =
  'Your browser sends Global Privacy Control or Do Not Track, so this site counts nothing from it.'
const STOP = 'Stop counting my visits'
const RESUME = 'Count my visits again'
const NO_SCRIPT = 'Without JavaScript, the site counts nothing at all.'

/** Every .ts and .vue file under frontend/src, as an absolute path. */
const sourceFiles = (): string[] =>
  readdirSync(SRC, { recursive: true, encoding: 'utf-8' })
    .filter(file => /\.(?:ts|vue)$/.test(file))
    .map(file => resolve(SRC, file))

/** Each browser signal that declines counting, as a navigator stand-in. */
const SIGNALS: Array<[string, object]> = [
  ['Global Privacy Control', { globalPrivacyControl: true }],
  ['Do Not Track', { doNotTrack: '1' }]
]

const routerAtPrivacy = async () => {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', component: { render: () => null } },
      { path: '/privacy', component: PrivacyView }
    ]
  })
  await router.push('/privacy')
  await router.isReady()
  return router
}

const mountView = async (attachTo?: HTMLElement) =>
  mount(PrivacyView, { attachTo, global: { plugins: [await routerAtPrivacy()] } })

/** The page as the server renderer bakes it, with navigator and localStorage stubbed out. */
const renderOnServer = async (): Promise<string> => {
  const app = createSSRApp(PrivacyView)
  app.use(await routerAtPrivacy())
  vi.stubGlobal('navigator', undefined)
  vi.stubGlobal('localStorage', undefined)
  try {
    return await renderToString(app)
  } finally {
    vi.unstubAllGlobals()
  }
}

describe('PrivacyView', () => {
  it('renders every section the page promises, in order', async () => {
    const wrapper = await mountView()
    expect(wrapper.get('h1').text()).toBe('Privacy')
    expect(wrapper.findAll('h2').map(heading => heading.text())).toEqual([
      'In short',
      'Who is responsible',
      'What is recorded, and why',
      'Who else handles the data',
      'How long it is kept',
      'Your right to object',
      'Your other rights'
    ])
    expect(wrapper.findAll('h3').map(heading => heading.text())).toEqual([
      'Visit statistics',
      'Server logs',
      'Error and performance reports',
      'What is kept in your browser',
      'Videos and maps',
      'Signing in'
    ])
  })

  it('is indexable and self-canonical, with its own title and description', async () => {
    mockedUseHead.mockClear()
    const wrapper = await mountView()

    const head = mockedUseHead.mock.calls[0][0] as {
      title: string
      meta: Array<{ name?: string; property?: string; content: string }>
      link: Array<{ rel: string; href: string }>
    }
    const meta = (key: string) => head.meta.find(m => m.name === key || m.property === key)?.content
    expect(head.title).toBe('Privacy | David Dashti')
    expect(meta('robots')).toBe('index, follow')
    expect(head.link.find(l => l.rel === 'canonical')?.href).toBe('https://dashti.se/privacy')
    expect(meta('og:url')).toBe('https://dashti.se/privacy')
    expect(meta('og:title')).toBe('Privacy | David Dashti')
    expect(meta('twitter:title')).toBe('Privacy | David Dashti')
    const description = meta('description')
    expect(description).toBeTruthy()
    expect(meta('og:description')).toBe(description)
    expect(meta('twitter:description')).toBe(description)
    // The description is the first sentence of the page itself.
    expect(wrapper.text()).toContain(description)
  })

  it('is routed at /privacy, after the colophon and before the catch-all', async () => {
    const paths = routes.map(route => route.path)
    const at = paths.indexOf('/privacy')
    expect(at).toBe(paths.indexOf('/colophon') + 1)
    expect(at).toBeLessThan(paths.indexOf('/:pathMatch(.*)*'))
    const route = routes[at]
    expect(route.name).toBe('privacy')
    expect(route.meta?.title).toBe('Privacy | David Dashti')
    const load = route.component as () => Promise<{ default: unknown }>
    expect((await load()).default).toBe(PrivacyView)
  })

  it('shows the date it was last updated as written, whatever the clock says', async () => {
    vi.useFakeTimers({ toFake: ['Date'] })
    vi.setSystemTime(new Date('2031-03-05T12:00:00Z'))
    try {
      const wrapper = await mountView()
      expect(wrapper.text()).toContain('Last updated: 27 November 2026')
    } finally {
      vi.useRealTimers()
    }
  })

  it("links to LinkedIn, Google's privacy policy and IMY, each in a new tab", async () => {
    const wrapper = await mountView()
    const external = wrapper.findAll('a[target="_blank"]')
    expect(external.map(link => link.attributes('href'))).toEqual([
      LINKEDIN,
      GOOGLE_PRIVACY_POLICY,
      IMY
    ])
    expect(external.map(link => link.text())).toEqual([
      'linkedin.com/in/david-dashti (opens in a new tab)',
      'policies.google.com/privacy (opens in a new tab)',
      'imy.se (opens in a new tab)'
    ])
    for (const link of external) {
      expect(link.attributes('rel')).toBe('noopener noreferrer')
      expect(link.get('.sr-only').text()).toBe('(opens in a new tab)')
    }
    // One of the contact channels that SECURITY.md and security.txt list.
    expect(readFileSync(resolve(REPO_ROOT, 'SECURITY.md'), 'utf-8')).toContain(LINKEDIN)
    expect(
      readFileSync(resolve(REPO_ROOT, 'frontend/public/.well-known/security.txt'), 'utf-8')
    ).toContain(`Contact: ${LINKEDIN}`)
  })

  it('offers no e-mail address and no phone number', async () => {
    const wrapper = await mountView()
    expect(wrapper.html().match(/mailto:|tel:/gi) ?? []).toEqual([])
    expect(wrapper.text().match(/\S+@\S+\.\S+/g) ?? []).toEqual([])
    expect(wrapper.text().match(/\+\d[\d\s-]{7,}/g) ?? []).toEqual([])
  })

  it('sets out how long each record is kept as a table', async () => {
    const wrapper = await mountView()
    const table = wrapper.get('table')
    expect(table.attributes('aria-labelledby')).toBe('retention')
    expect(wrapper.get('h2#retention').text()).toBe('How long it is kept')
    expect(table.findAll('thead th').map(th => [th.text(), th.attributes('scope')])).toEqual([
      ['What', 'col'],
      ['How long', 'col']
    ])
    const rows = table.findAll('tbody tr')
    expect(rows.map(row => row.findAll('th, td').map(cell => cell.text()))).toEqual([
      ['Visit records', '180 days, then deleted automatically'],
      ['Server logs', 'about 7 days, kept by Fly.io'],
      ['Error and performance reports', '30 days, kept by Sentry'],
      [
        'Encrypted database backups',
        "30 days on GitHub, and up to 60 days in Fly.io's disk snapshots, so a deleted record can survive that long in a backup"
      ],
      ["Vercel's request logs", 'a short time, kept by Vercel to run its service'],
      [
        'The daily random value behind the visitor key',
        'until the end of the day (UTC), in memory only'
      ],
      [
        'What your browser keeps',
        'until you clear it, and what is in session storage only until you close the tab'
      ]
    ])
    expect(rows.map(row => row.get('th').attributes('scope'))).toEqual(Array(7).fill('row'))
  })

  it('names the storage of each write the code makes, the reload time included', async () => {
    // The storage area and the key argument of every setItem() call, written
    // with . or ?. and any spaces around them.
    const write = /\b(local|session)Storage\s*\??\.\s*setItem\s*\(\s*([^,]+?)\s*,/g
    const writes = sourceFiles()
      .flatMap(file =>
        [...readFileSync(file, 'utf-8').matchAll(write)].map(([, area, key]) => [area, key])
      )
      .sort()
    // The opt-out in services/analytics.ts and the reload time in main.ts. A
    // new setItem() call anywhere under src fails here: the page's list below
    // must name what it keeps before the call joins this list.
    expect(writes).toEqual([
      ['local', 'OPT_OUT_KEY'],
      ['session', 'RELOAD_STAMP']
    ])
    // A write the pattern cannot read, through an alias of the storage object
    // or setItem in brackets, still names setItem, and fails the count here.
    const mentions = sourceFiles().flatMap(
      file => readFileSync(file, 'utf-8').match(/\bsetItem\b/g) ?? []
    )
    expect(mentions).toHaveLength(writes.length)
    const areas = new Set(writes.map(([area]) => `in ${area} storage`))

    const wrapper = await mountView()
    const items = wrapper.findAll('li').map(item => item.text())
    for (const area of areas) {
      expect(items.filter(item => item.includes(area)).length, area).toBeGreaterThan(0)
    }
    expect(items).toContain(
      'the time of the last automatic reload after a site update, in session storage, so that it cannot repeat in a loop;'
    )
    // Vue Router writes its saved scroll positions to session storage itself
    // (key vue-router:scroll), so the scan above cannot see them;
    // privacy.spec.ts reads the keys a visit leaves in a browser.
    expect(items).toContain(
      'where you had scrolled to on each page, in session storage, so that going back returns you there;'
    )
  })

  it('names the only server log lines that carry a client digest', async () => {
    const wrapper = await mountView()
    // backend/app/middleware/logging.py's request lines carry no client
    // field; rate_limit.py's 429 line carries the digest, and the security
    // events of core/security_events.py the digest and a cut User-Agent.
    expect(wrapper.findAll('p').map(paragraph => paragraph.text())).toContain(
      "The server keeps a technical log of requests to api.dashti.se: the time, what was requested and the result. A request refused by the rate limit is also logged with a keyed digest of your IP address, never the address itself, and each step of a sign-in with that digest and the first 64 characters of your browser's user-agent string. The digest is the same for every request from one address, so that abuse can be traced and blocked. The visit notes described above are logged only when they fail. To limit abuse, the server also counts requests per address for one minute at a time, in memory only. The purpose is to keep the service secure and working; the legal basis is legitimate interest (Article 6(1)(f))."
    )
  })

  it('names what an error report carries, the latest load-time measurement included', async () => {
    const wrapper = await mountView()
    // utils/sentry.ts keeps the latest Web Vital in a context that every
    // later error event carries, except while counting is declined.
    // The SDK's default Breadcrumbs integration, which sentry.ts keeps, also
    // records console messages.
    expect(wrapper.text()).toContain(
      "your browser's language and time zone, the page's latest load-time measurement, and a short trail of what happened on the page before the error (pages opened, buttons clicked, requests made, messages written to the browser console)"
    )
  })
})

describe('PrivacyView opt-out switch', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    vi.restoreAllMocks()
    localStorage.clear()
  })

  it('prerenders the sentence for readers without JavaScript, and no switch', async () => {
    const html = await renderOnServer()
    expect(html).toContain(NO_SCRIPT)
    for (const text of [COUNTED, DECLINED, SIGNAL, STOP, RESUME]) {
      expect(html).not.toContain(text)
    }
    expect(html).not.toContain('<button')
    expect(html).not.toContain('aria-live')
  })

  it('hydrates the prerendered page without a mismatch, then shows the switch', async () => {
    const container = document.createElement('div')
    container.innerHTML = await renderOnServer()
    // A browser whose state differs from the prerender's: had the page read
    // it before mount, the first client render would not match the markup.
    setVisitCountingOptOut(true)
    const warn = vi.spyOn(console, 'warn')
    const error = vi.spyOn(console, 'error')
    const app = createSSRApp(PrivacyView)
    app.use(await routerAtPrivacy())
    app.mount(container)
    await flushPromises()

    const logged = [...warn.mock.calls, ...error.mock.calls].map(args => args.join(' '))
    expect(logged.filter(line => /hydration/i.test(line))).toEqual([])
    expect(container.querySelector('[aria-live="polite"]')?.textContent?.trim()).toBe(DECLINED)
    expect(container.querySelector('button')?.textContent?.trim()).toBe(RESUME)
    expect(container.textContent).toContain(NO_SCRIPT)
    app.unmount()
  })

  it('stores the opt-out on a press and removes it on the next', async () => {
    const wrapper = await mountView()
    const status = wrapper.get('[aria-live="polite"]')
    const button = wrapper.get('button')
    expect(status.text()).toBe(COUNTED)
    expect(button.text()).toBe(STOP)
    expect(button.attributes('type')).toBe('button')
    // The label names the action, so the button carries no pressed state.
    expect(button.attributes('aria-pressed')).toBeUndefined()

    await button.trigger('click')
    expect(localStorage.getItem(OPT_OUT_KEY)).toBe('1')
    expect(visitCountingDeclined()).toBe(true)
    expect(status.text()).toBe(DECLINED)
    expect(button.text()).toBe(RESUME)

    await button.trigger('click')
    expect(localStorage.getItem(OPT_OUT_KEY)).toBeNull()
    expect(visitCountingDeclined()).toBe(false)
    expect(status.text()).toBe(COUNTED)
    expect(button.text()).toBe(STOP)
  })

  it('starts from an opt-out stored earlier', async () => {
    setVisitCountingOptOut(true)
    const wrapper = await mountView()
    expect(wrapper.get('[aria-live="polite"]').text()).toBe(DECLINED)
    expect(wrapper.get('button').text()).toBe(RESUME)
  })

  it('keeps focus on the same button when its label changes', async () => {
    const wrapper = await mountView(document.body)
    const button = wrapper.get('button').element as HTMLButtonElement
    button.focus()
    await wrapper.get('button').trigger('click')
    expect(wrapper.get('button').element).toBe(button)
    expect(document.activeElement).toBe(button)
    wrapper.unmount()
  })

  it.each(SIGNALS)('shows the signal under %s, with no button', async (_name, stub) => {
    vi.stubGlobal('navigator', stub)
    const wrapper = await mountView()
    expect(wrapper.get('[aria-live="polite"]').text()).toBe(SIGNAL)
    expect(wrapper.find('button').exists()).toBe(false)
    // The page view is not sent either.
    expect(visitCountingDeclined()).toBe(true)
  })

  it('shows the signal over an opt-out stored earlier', async () => {
    setVisitCountingOptOut(true)
    vi.stubGlobal('navigator', { globalPrivacyControl: true })
    const wrapper = await mountView()
    expect(wrapper.get('[aria-live="polite"]').text()).toBe(SIGNAL)
    expect(wrapper.find('button').exists()).toBe(false)
  })

  it('reads other values as no signal, as visitCountingDeclined() does', async () => {
    for (const stub of [
      { globalPrivacyControl: false },
      { globalPrivacyControl: 'true' },
      { doNotTrack: '0' },
      { doNotTrack: 'unspecified' }
    ]) {
      vi.stubGlobal('navigator', stub)
      const wrapper = await mountView()
      expect(wrapper.get('[aria-live="polite"]').text(), JSON.stringify(stub)).toBe(COUNTED)
      expect(visitCountingDeclined(), JSON.stringify(stub)).toBe(false)
      wrapper.unmount()
    }
  })

  it('still reads Do Not Track when reading Global Privacy Control throws', async () => {
    vi.stubGlobal('navigator', {
      get globalPrivacyControl(): boolean {
        throw new Error('blocked')
      },
      doNotTrack: '1'
    })
    const wrapper = await mountView()
    expect(wrapper.get('[aria-live="polite"]').text()).toBe(SIGNAL)
    expect(visitCountingDeclined()).toBe(true)
  })

  it('keeps its status where storage refuses the write', async () => {
    const refuse = (): never => {
      throw new DOMException('The quota has been exceeded.', 'QuotaExceededError')
    }
    vi.stubGlobal('localStorage', { getItem: () => null, setItem: refuse, removeItem: refuse })
    const wrapper = await mountView()
    await wrapper.get('button').trigger('click')
    expect(wrapper.get('[aria-live="polite"]').text()).toBe(COUNTED)
    expect(wrapper.get('button').text()).toBe(STOP)
  })
})
