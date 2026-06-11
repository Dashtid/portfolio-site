import { describe, it, expect, vi, beforeEach } from 'vitest'
import { defineComponent, h, Suspense, nextTick } from 'vue'
import { mount, flushPromises, type VueWrapper } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import { createRouter, createMemoryHistory } from 'vue-router'
import HomeView from '@/views/HomeView.vue'

// Mock API client to prevent network calls when stubActions: false
vi.mock('@/api/client', () => ({
  default: {
    get: vi.fn().mockResolvedValue({ data: [] }),
    post: vi.fn().mockResolvedValue({ data: {} }),
    put: vi.fn().mockResolvedValue({ data: {} }),
    delete: vi.fn().mockResolvedValue({ data: {} })
  }
}))

// Mock child components
vi.mock('@/components/NavBar.vue', () => ({
  default: {
    name: 'NavBar',
    template: '<nav data-testid="navbar">NavBar</nav>'
  }
}))

vi.mock('@/components/FooterSection.vue', () => ({
  default: {
    name: 'FooterSection',
    template: '<footer data-testid="footer">Footer</footer>'
  }
}))

vi.mock('@/components/GitHubStats.vue', () => ({
  default: {
    name: 'GitHubStats',
    template: '<div data-testid="github-stats">GitHub Stats</div>',
    props: ['username']
  }
}))

vi.mock('@/components/BackToTop.vue', () => ({
  default: {
    name: 'BackToTop',
    template: '<button data-testid="back-to-top">Back to Top</button>'
  }
}))

vi.mock('@/components/DocumentCard.vue', () => ({
  default: {
    name: 'DocumentCard',
    template: '<div data-testid="document-card">Document Card</div>',
    props: ['document']
  }
}))

// Mock service worker
Object.defineProperty(navigator, 'serviceWorker', {
  value: {
    register: vi.fn().mockResolvedValue({})
  },
  writable: true
})

const routes = [
  { path: '/', component: HomeView, name: 'home' },
  { path: '/company/:id', component: { template: '<div />' }, name: 'company-detail' },
  // INFRA-002: the sentinel company in the test fixture renders the
  // v-for block which links to experience-detail. Without this route
  // declared, the router-link setup throws and the suspended page
  // never resolves.
  {
    path: '/experience/:id',
    component: { template: '<div />' },
    name: 'experience-detail'
  }
]

describe('HomeView', () => {
  // INFRA-002 moved portfolio data fetch from onMounted to top-level await
  // in setup() so vite-ssg's __INITIAL_STATE__ captures populated state.
  // Async setup needs a <Suspense> boundary in tests; we pre-populate the
  // store with a sentinel company so the setup-level guard short-circuits
  // and the suspended boundary resolves on the first flush.
  const createWrapper = async (
    options: {
      global?: Record<string, unknown>
      initialPortfolio?: Record<string, unknown>
    } = {}
  ): Promise<VueWrapper> => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes
    })

    const SuspenseHarness = defineComponent({
      name: 'SuspenseHarness',
      components: { HomeView },
      setup() {
        return () => h(Suspense, null, { default: () => h(HomeView) })
      }
    })

    const { global: globalOverrides, initialPortfolio, ...rest } = options
    const wrapper = mount(SuspenseHarness, {
      global: {
        plugins: [
          createTestingPinia({
            createSpy: vi.fn,
            stubActions: true,
            initialState: {
              portfolio: {
                companies: [{ id: 'sentinel', name: 'Sentinel', start_date: '2020-01-01' }],
                projects: [],
                education: [],
                skills: [],
                ...(initialPortfolio ?? {})
              }
            }
          }),
          router
        ],
        stubs: {
          NavBar: true,
          FooterSection: true,
          GitHubStats: {
            template: '<div data-testid="github-stats">GitHub Stats</div>'
          },
          BackToTop: true,
          DocumentCard: true,
          // ThreeHeroBackground is a defineAsyncComponent; without a stub
          // the dynamic import fails under happy-dom and the surrounding
          // tree renders partially. Stub it to a placeholder so the hero
          // section's siblings render reliably.
          ThreeHeroBackground: true
        },
        ...(globalOverrides ?? {})
      },
      ...rest
    })
    // Drain Suspense + setup + onMounted across multiple ticks. The async
    // setup resolves on a microtask, Suspense promotes the resolved tree
    // on the next tick, onMounted fires after patch, and the documents
    // fetch chains further microtasks.
    for (let i = 0; i < 5; i++) {
      await flushPromises()
      await nextTick()
    }
    return wrapper
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Rendering', () => {
    it('should render the portfolio home container', async () => {
      const wrapper = await createWrapper()

      expect(wrapper.find('.portfolio-home').exists()).toBe(true)
    })

    it('should render the hero section', async () => {
      const wrapper = await createWrapper()

      expect(wrapper.find('#hero').exists()).toBe(true)
      expect(wrapper.find('.hero-section').exists()).toBe(true)
    })

    it('should render the experience section', async () => {
      const wrapper = await createWrapper()

      expect(wrapper.find('#experience').exists()).toBe(true)
      expect(wrapper.find('.experience-list').exists()).toBe(true)
    })

    it('should render the education section', async () => {
      const wrapper = await createWrapper()

      expect(wrapper.find('#education').exists()).toBe(true)
      expect(wrapper.find('.education-grid').exists()).toBe(true)
    })

    it('should render the publications section', async () => {
      const wrapper = await createWrapper()

      expect(wrapper.find('#publications').exists()).toBe(true)
    })

    it('should render the projects section', async () => {
      const wrapper = await createWrapper()

      expect(wrapper.find('#projects').exists()).toBe(true)
      // Projects are now rendered via GitHubStats component with featured_repos
      expect(wrapper.find('[data-testid="github-stats"]').exists()).toBe(true)
    })

    it('should render the about section', async () => {
      const wrapper = await createWrapper()

      expect(wrapper.find('#about').exists()).toBe(true)
      expect(wrapper.find('.about-layout').exists()).toBe(true)
    })
  })

  describe('Hero Section Content', () => {
    it('should display the hero title', async () => {
      const wrapper = await createWrapper()

      const title = wrapper.find('.custom-hero-title')
      expect(title.exists()).toBe(true)
      expect(title.text()).toContain('Cybersecurity')
      expect(title.text()).toContain('Artificial Intelligence')
    })

    it('should display the hero lead text', async () => {
      const wrapper = await createWrapper()

      const lead = wrapper.find('.custom-hero-lead')
      expect(lead.exists()).toBe(true)
      expect(lead.text()).toContain('Biomedical Engineer')
      expect(lead.text()).toContain('Stockholm, Sweden')
    })
  })

  describe('Static Fallback Content', () => {
    it('should show static fallback when no companies from API', async () => {
      // Force the empty-store path so the v-if template falls through to
      // the CONTENT-001 static fallback block (Hermes/Philips/Karolinska).
      const wrapper = await createWrapper({ initialPortfolio: { companies: [] } })

      // When companies array is empty, should show static fallback
      expect(wrapper.find('.experience-card').exists()).toBe(true)
      expect(wrapper.text()).toContain('Hermes Medical Solutions')
    })

    it('should show GitHub stats component for projects', async () => {
      const wrapper = await createWrapper()

      // Projects are now displayed via GitHubStats component with featured repos
      expect(wrapper.find('[data-testid="github-stats"]').exists()).toBe(true)
    })
  })

  describe('Section Icons', () => {
    it('should have section icons for all main sections', async () => {
      const wrapper = await createWrapper()

      const sectionIcons = wrapper.findAll('.section-icon')
      expect(sectionIcons.length).toBeGreaterThanOrEqual(5)
    })

    it('should have lazy loading on section icons', async () => {
      const wrapper = await createWrapper()

      const sectionIcons = wrapper.findAll('.section-icon')
      sectionIcons.forEach(icon => {
        expect(icon.attributes('loading')).toBe('lazy')
      })
    })
  })
})
