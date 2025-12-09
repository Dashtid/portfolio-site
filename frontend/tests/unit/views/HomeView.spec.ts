import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import { createRouter, createMemoryHistory } from 'vue-router'
import HomeView from '@/views/HomeView.vue'

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

// Mock composables
vi.mock('@/composables/useScrollAnimations', () => ({
  useBatchAnimation: vi.fn()
}))

// Mock API services
vi.mock('@/api/services', () => ({
  getDocuments: vi.fn().mockResolvedValue([])
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
  { path: '/company/:id', component: { template: '<div />' }, name: 'company-detail' }
]

describe('HomeView', () => {
  const createWrapper = (options = {}) => {
    const router = createRouter({
      history: createMemoryHistory(),
      routes
    })

    return mount(HomeView, {
      global: {
        plugins: [
          createTestingPinia({
            createSpy: vi.fn,
            initialState: {
              portfolio: {
                companies: [],
                projects: [],
                education: [],
                skills: []
              }
            }
          }),
          router
        ],
        stubs: {
          NavBar: true,
          FooterSection: true,
          GitHubStats: true,
          BackToTop: true,
          DocumentCard: true
        }
      },
      ...options
    })
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Rendering', () => {
    it('should render the portfolio home container', async () => {
      const wrapper = createWrapper()
      await flushPromises()

      expect(wrapper.find('.portfolio-home').exists()).toBe(true)
    })

    it('should render the hero section', async () => {
      const wrapper = createWrapper()
      await flushPromises()

      expect(wrapper.find('#hero').exists()).toBe(true)
      expect(wrapper.find('.hero-section').exists()).toBe(true)
    })

    it('should render the experience section', async () => {
      const wrapper = createWrapper()
      await flushPromises()

      expect(wrapper.find('#experience').exists()).toBe(true)
      expect(wrapper.find('.experience-list').exists()).toBe(true)
    })

    it('should render the education section', async () => {
      const wrapper = createWrapper()
      await flushPromises()

      expect(wrapper.find('#education').exists()).toBe(true)
      expect(wrapper.find('.education-grid').exists()).toBe(true)
    })

    it('should render the publications section', async () => {
      const wrapper = createWrapper()
      await flushPromises()

      expect(wrapper.find('#publications').exists()).toBe(true)
    })

    it('should render the projects section', async () => {
      const wrapper = createWrapper()
      await flushPromises()

      expect(wrapper.find('#projects').exists()).toBe(true)
      expect(wrapper.find('.projects-grid').exists()).toBe(true)
    })

    it('should render the about section', async () => {
      const wrapper = createWrapper()
      await flushPromises()

      expect(wrapper.find('#about').exists()).toBe(true)
      expect(wrapper.find('.about-layout').exists()).toBe(true)
    })
  })

  describe('Hero Section Content', () => {
    it('should display the hero title', async () => {
      const wrapper = createWrapper()
      await flushPromises()

      const title = wrapper.find('.custom-hero-title')
      expect(title.exists()).toBe(true)
      expect(title.text()).toContain('Cybersecurity')
      expect(title.text()).toContain('Artificial Intelligence')
    })

    it('should display the hero lead text', async () => {
      const wrapper = createWrapper()
      await flushPromises()

      const lead = wrapper.find('.custom-hero-lead')
      expect(lead.exists()).toBe(true)
      expect(lead.text()).toContain('Biomedical Engineer')
      expect(lead.text()).toContain('Stockholm, Sweden')
    })
  })

  describe('Static Fallback Content', () => {
    it('should show static fallback when no companies from API', async () => {
      const wrapper = createWrapper()
      await flushPromises()

      // When companies array is empty, should show static fallback
      expect(wrapper.find('.experience-card').exists()).toBe(true)
      expect(wrapper.text()).toContain('Hermes Medical Solutions')
    })

    it('should show static projects when no projects from API', async () => {
      const wrapper = createWrapper()
      await flushPromises()

      // Static projects should be displayed
      expect(wrapper.find('.project-card').exists()).toBe(true)
      expect(wrapper.text()).toContain('Portfolio Website')
    })
  })

  describe('Section Icons', () => {
    it('should have section icons for all main sections', async () => {
      const wrapper = createWrapper()
      await flushPromises()

      const sectionIcons = wrapper.findAll('.section-icon')
      expect(sectionIcons.length).toBeGreaterThanOrEqual(5)
    })

    it('should have lazy loading on section icons', async () => {
      const wrapper = createWrapper()
      await flushPromises()

      const sectionIcons = wrapper.findAll('.section-icon')
      sectionIcons.forEach(icon => {
        expect(icon.attributes('loading')).toBe('lazy')
      })
    })
  })
})
