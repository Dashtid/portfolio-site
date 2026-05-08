import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import axios from 'axios'
import { useHead } from '@unhead/vue'
import { defineComponent, h, Suspense, type ComputedRef } from 'vue'
import ExperienceDetail from '@/views/experience/ExperienceDetail.vue'
import type { Company } from '@/types'

vi.mock('axios')
vi.mock('gsap', () => ({
  gsap: {
    context: vi.fn((cb: () => void) => {
      cb()
      return { revert: vi.fn() }
    }),
    from: vi.fn()
  }
}))
vi.mock('@/utils/logger', async importOriginal => {
  const actual = await importOriginal<typeof import('@/utils/logger')>()
  return {
    ...actual,
    apiLogger: { error: vi.fn(), warn: vi.fn(), info: vi.fn(), debug: vi.fn() }
  }
})
vi.mock('@/components/NavBar.vue', () => ({
  default: { name: 'NavBar', template: '<nav data-testid="navbar" />' }
}))
vi.mock('@/components/VideoEmbed.vue', () => ({
  default: {
    name: 'VideoEmbed',
    template: '<div data-testid="video-embed" />',
    props: ['url', 'heading', 'title']
  }
}))
vi.mock('@/components/MapEmbed.vue', () => ({
  default: {
    name: 'MapEmbed',
    template: '<div data-testid="map-embed" />',
    props: ['url', 'heading', 'title']
  }
}))

const mockedAxios = vi.mocked(axios, true)
const mockedUseHead = vi.mocked(useHead)

type AxiosCallArgs = [string, { signal?: AbortSignal } | undefined]

const getCallSignal = (callIndex: number): AbortSignal => {
  const call = mockedAxios.get.mock.calls[callIndex] as unknown as AxiosCallArgs
  const config = call[1]
  if (!config?.signal) throw new Error('expected axios.get to receive a signal')
  return config.signal
}

const baseCompany: Company = {
  id: 'co-1',
  name: 'Acme Corp',
  title: 'Senior Engineer',
  description: 'Built things.',
  start_date: '2020-01-01',
  end_date: '2022-12-31',
  location: 'Stockholm',
  technologies: ['Vue', 'Python'],
  responsibilities: ['Did stuff', 'Built things'],
  detailed_description: null,
  logo_url: null,
  website: null,
  video_url: null,
  video_title: null,
  map_url: null,
  map_title: null,
  order_index: 1
}

// ExperienceDetail uses a top-level await inside `if (import.meta.env.SSR)`,
// which makes its setup async. Vue requires async-setup components to be
// wrapped in <Suspense> or they render nothing. We provide that boundary here.
const SuspenseHost = defineComponent({
  name: 'SuspenseHost',
  setup() {
    return () => h(Suspense, null, { default: () => h(ExperienceDetail) })
  }
})

const createWrapper = async (id = 'co-1') => {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/experience/:id', component: SuspenseHost, name: 'experience-detail' },
      { path: '/', component: { template: '<div />' }, name: 'home' }
    ]
  })

  await router.push(`/experience/${id}`)
  await router.isReady()

  const wrapper = mount(SuspenseHost, {
    global: {
      plugins: [router]
    }
  })

  await flushPromises()
  return { wrapper, router }
}

describe('ExperienceDetail', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockedAxios.isCancel.mockReturnValue(false)
  })

  describe('Render branches', () => {
    it('shows loading spinner before fetch resolves', async () => {
      mockedAxios.get.mockReturnValue(new Promise(() => {}) as never)
      const { wrapper } = await createWrapper('co-1')

      expect(wrapper.find('.spinner-border').exists()).toBe(true)
      expect(wrapper.text()).toContain('Loading experience details')
    })

    it('renders company details on successful fetch', async () => {
      mockedAxios.get.mockResolvedValue({ data: baseCompany })
      const { wrapper } = await createWrapper()

      expect(wrapper.text()).toContain('Senior Engineer')
      expect(wrapper.text()).toContain('Acme Corp')
      expect(wrapper.text()).toContain('Stockholm')
      expect(wrapper.find('.spinner-border').exists()).toBe(false)
      expect(wrapper.find('.alert-danger').exists()).toBe(false)
    })

    it('renders 404-specific error when API returns 404', async () => {
      mockedAxios.get.mockRejectedValue({ response: { status: 404 } })
      const { wrapper } = await createWrapper()

      expect(wrapper.find('.alert-danger').exists()).toBe(true)
      expect(wrapper.text()).toContain('Company not found')
    })

    it('renders generic error message on non-404 failure', async () => {
      mockedAxios.get.mockRejectedValue({ response: { status: 500 } })
      const { wrapper } = await createWrapper()

      expect(wrapper.text()).toContain('Failed to load company details')
    })

    it('does not surface error when axios.isCancel returns true', async () => {
      mockedAxios.get.mockRejectedValue(new Error('cancelled'))
      mockedAxios.isCancel.mockReturnValue(true)

      const { wrapper } = await createWrapper()

      expect(wrapper.find('.alert-danger').exists()).toBe(false)
    })

    it('renders technologies as badges', async () => {
      mockedAxios.get.mockResolvedValue({
        data: { ...baseCompany, technologies: ['Rust', 'WASM'] }
      })
      const { wrapper } = await createWrapper()

      const badges = wrapper.findAll('.badge')
      const labels = badges.map(b => b.text())
      expect(labels).toContain('Rust')
      expect(labels).toContain('WASM')
    })

    it('renders responsibilities as a list', async () => {
      mockedAxios.get.mockResolvedValue({
        data: { ...baseCompany, responsibilities: ['Wrote code', 'Reviewed PRs'] }
      })
      const { wrapper } = await createWrapper()

      const items = wrapper.findAll('.list-group-item')
      expect(items.length).toBe(2)
      expect(items[0].text()).toContain('Wrote code')
      expect(items[1].text()).toContain('Reviewed PRs')
    })
  })

  describe('Lifecycle / fetch', () => {
    it('fetches the company on mount with the route id', async () => {
      mockedAxios.get.mockResolvedValue({ data: baseCompany })
      await createWrapper('co-42')

      expect(mockedAxios.get).toHaveBeenCalledTimes(1)
      const url = mockedAxios.get.mock.calls[0][0] as string
      expect(url).toContain('/api/v1/companies/co-42')
      expect(getCallSignal(0)).toBeInstanceOf(AbortSignal)
    })

    it('refetches with a fresh AbortController on route param change and aborts the prior request', async () => {
      mockedAxios.get.mockResolvedValue({ data: baseCompany })
      const { router } = await createWrapper('co-1')
      const firstSignal = getCallSignal(0)

      await router.push('/experience/co-2')
      await flushPromises()

      expect(mockedAxios.get).toHaveBeenCalledTimes(2)
      const secondUrl = mockedAxios.get.mock.calls[1][0] as string
      expect(secondUrl).toContain('/api/v1/companies/co-2')

      expect(firstSignal.aborted).toBe(true)
      const secondSignal = getCallSignal(1)
      expect(secondSignal).not.toBe(firstSignal)
      expect(secondSignal.aborted).toBe(false)
    })

    it('aborts the in-flight request on unmount', async () => {
      mockedAxios.get.mockReturnValue(new Promise(() => {}) as never)
      const { wrapper } = await createWrapper()
      const signal = getCallSignal(0)

      expect(signal.aborted).toBe(false)
      wrapper.unmount()
      expect(signal.aborted).toBe(true)
    })
  })

  describe('useHead', () => {
    it('passes reactive title/description/canonical that resolve once company loads', async () => {
      mockedAxios.get.mockResolvedValue({
        data: { ...baseCompany, name: 'Initech', description: 'Made widgets.' }
      })
      await createWrapper('co-99')

      const headArg = mockedUseHead.mock.calls[0][0] as {
        title: ComputedRef<string>
        meta: Array<{ name: string; content: ComputedRef<string> }>
        link: Array<{ rel: string; href: ComputedRef<string> }>
      }

      expect(headArg.title.value).toContain('Initech')
      expect(headArg.title.value).toContain('Experience | David Dashti')

      const desc = headArg.meta.find(m => m.name === 'description')
      expect(desc?.content.value).toBe('Made widgets.')

      const canonical = headArg.link.find(l => l.rel === 'canonical')
      expect(canonical?.href.value).toBe('https://dashti.se/experience/co-99')
    })

    it('falls back to a generic title before the company resolves', async () => {
      mockedAxios.get.mockReturnValue(new Promise(() => {}) as never)
      await createWrapper('co-1')

      const headArg = mockedUseHead.mock.calls[0][0] as {
        title: ComputedRef<string>
        meta: Array<{ name: string; content: ComputedRef<string> }>
      }

      expect(headArg.title.value).toBe('Experience | David Dashti')
      const desc = headArg.meta.find(m => m.name === 'description')
      expect(desc?.content.value).toBe('Experience details')
    })
  })

  describe('Description rendering', () => {
    it('splits paragraphs on blank lines into separate <p> tags', async () => {
      mockedAxios.get.mockResolvedValue({
        data: { ...baseCompany, description: 'First para.\n\nSecond para.\n\nThird.' }
      })
      const { wrapper } = await createWrapper()

      const html = wrapper.html()
      expect(html).toContain('<p>First para.</p>')
      expect(html).toContain('<p>Second para.</p>')
      expect(html).toContain('<p>Third.</p>')
    })

    it('renders **bold** as <strong>', async () => {
      mockedAxios.get.mockResolvedValue({
        data: { ...baseCompany, description: 'I am **strong**.' }
      })
      const { wrapper } = await createWrapper()

      expect(wrapper.html()).toContain('<strong>strong</strong>')
    })

    it('renders *italic* as <em>', async () => {
      mockedAxios.get.mockResolvedValue({
        data: { ...baseCompany, description: 'Not *that* one.' }
      })
      const { wrapper } = await createWrapper()

      expect(wrapper.html()).toContain('<em>that</em>')
    })

    it('does not mangle **bold** into <em>bold</em> (regex ordering)', async () => {
      mockedAxios.get.mockResolvedValue({
        data: { ...baseCompany, description: '**title**' }
      })
      const { wrapper } = await createWrapper()

      const html = wrapper.html()
      expect(html).toContain('<strong>title</strong>')
      expect(html).not.toMatch(/<em>title<\/em>/)
    })

    it('escapes raw HTML so script tags cannot reach the DOM as markup', async () => {
      mockedAxios.get.mockResolvedValue({
        data: {
          ...baseCompany,
          description: '<script>alert(1)</script> & "quotes"'
        }
      })
      const { wrapper } = await createWrapper()

      // Re-serialised HTML: the characters that MUST be escaped in text content
      // (<, >, &) come back as entities. Quotes/apostrophes round-trip as raw
      // text since they aren't dangerous outside attribute context — that's
      // happy-dom doing what every browser serializer does, not a leak.
      const html = wrapper.html()
      expect(html).not.toMatch(/<script[^>]*>alert/i)
      expect(html).toContain('&lt;script&gt;')
      expect(html).toContain('&amp;')

      // Confirm no real <script> element was created in the live DOM, even
      // though the raw text reads "<script>" as plain characters.
      const scripts = wrapper.element.querySelectorAll('script')
      expect(scripts.length).toBe(0)
    })

    it('renders detailed_description in a separate Role & Responsibilities block', async () => {
      mockedAxios.get.mockResolvedValue({
        data: { ...baseCompany, detailed_description: 'Led the **secure** rollout.' }
      })
      const { wrapper } = await createWrapper()

      expect(wrapper.text()).toContain('Role & Responsibilities')
      expect(wrapper.html()).toContain('<strong>secure</strong>')
    })

    it('treats null/undefined detailed_description as absent (no Role section)', async () => {
      mockedAxios.get.mockResolvedValue({
        data: { ...baseCompany, detailed_description: null }
      })
      const { wrapper } = await createWrapper()

      expect(wrapper.text()).not.toContain('Role & Responsibilities')
    })
  })

  describe('Logo error fallback', () => {
    it('hides the logo image after the @error handler fires', async () => {
      mockedAxios.get.mockResolvedValue({
        data: { ...baseCompany, logo_url: 'https://example.com/logo.png' }
      })
      const { wrapper } = await createWrapper()

      const img = wrapper.find('img[alt$="logo"]')
      expect(img.exists()).toBe(true)

      await img.trigger('error')

      expect(wrapper.find('img[alt$="logo"]').exists()).toBe(false)
    })
  })
})
