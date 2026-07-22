import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises, type VueWrapper } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import AdminAnalytics from '@/views/admin/AdminAnalytics.vue'
import analyticsService, { type AnalyticsSummary, type VisitorStats } from '@/services/analytics'

// AdminAnalytics talks to the singleton analytics service. Mocking the whole
// module gives the same call-shape as the production code with no real HTTP.
vi.mock('@/services/analytics', () => ({
  default: {
    getAnalyticsSummary: vi.fn(),
    getVisitorStats: vi.fn()
  }
}))

const makeSummary = (overrides: Partial<AnalyticsSummary> = {}): AnalyticsSummary => ({
  total_views: 1234,
  unique_visitors: 456,
  avg_session_duration: 95,
  top_pages: [
    { path: '/', title: 'Home', views: 800 },
    { path: '/about', title: null, views: 200 }
  ],
  daily_views: [
    { date: '2026-06-01', views: 100 },
    { date: '2026-06-02', views: 150 },
    { date: '2026-06-03', views: 175 }
  ],
  period_days: 30,
  outbound_clicks: [
    { destination: 'linkedin/hero', count: 12 },
    { destination: 'github/footer', count: 4 }
  ],
  ...overrides
})

const makeVisitorStats = (overrides: Partial<VisitorStats> = {}): VisitorStats => ({
  total_sessions: 456,
  new_visitors: 380,
  returning_visitors: 76,
  avg_session_duration: 95,
  bounce_rate: 0.42,
  top_countries: [
    { country: 'SE', count: 200 },
    { country: 'US', count: 150 }
  ],
  period_days: 7,
  ...overrides
})

const createWrapper = async (): Promise<VueWrapper> => {
  const wrapper = mount(AdminAnalytics, {
    global: {
      plugins: [createTestingPinia({ createSpy: vi.fn })]
    }
  })
  await flushPromises()
  return wrapper
}

describe('AdminAnalytics', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(analyticsService.getAnalyticsSummary).mockResolvedValue(makeSummary())
    vi.mocked(analyticsService.getVisitorStats).mockResolvedValue(makeVisitorStats())
  })

  describe('Rendering', () => {
    it('renders the page header and range tabs', async () => {
      const wrapper = await createWrapper()
      expect(wrapper.find('.admin-analytics').exists()).toBe(true)
      expect(wrapper.find('h2').text()).toBe('Analytics')
      expect(wrapper.findAll('.range-tab')).toHaveLength(4)
    })

    it('renders the four summary cards once data has loaded', async () => {
      const wrapper = await createWrapper()
      expect(wrapper.findAll('.stat-card')).toHaveLength(4)
      // toLocaleString uses the CI runner's locale (sv-SE on this box) and
      // varies in thousands-separator: comma, regular space, or narrow
      // no-break space U+202F. Strip the separator before asserting.
      const normalized = wrapper.text().replace(/[\s,]/g, '')
      expect(normalized).toContain('1234')
      expect(normalized).toContain('456')
    })

    it('formats the average session duration as `Xm Ys`', async () => {
      const wrapper = await createWrapper()
      // 95s → 1m 35s
      expect(wrapper.text()).toContain('1m 35s')
    })

    it('renders an em dash when avg_session_duration is zero', async () => {
      vi.mocked(analyticsService.getAnalyticsSummary).mockResolvedValue(
        makeSummary({ avg_session_duration: 0 })
      )
      const wrapper = await createWrapper()
      const sessionCard = wrapper.findAll('.stat-card')[2]
      expect(sessionCard.text()).toContain('—')
    })

    it('formats the bounce rate as a rounded percentage', async () => {
      const wrapper = await createWrapper()
      // 0.42 → 42%
      expect(wrapper.text()).toContain('42%')
    })

    it('renders the daily-views SVG chart and axis labels', async () => {
      const wrapper = await createWrapper()
      expect(wrapper.find('svg.chart').exists()).toBe(true)
      // One <circle> per data point.
      expect(wrapper.findAll('svg.chart circle')).toHaveLength(3)
      // formatDate() uses toLocaleDateString(undefined, ...) which renders
      // differently per locale (Jun 1 in en-US, 1 juni in sv-SE). Assert on
      // the locale-independent label container instead, plus the bare numbers.
      const axisText = wrapper.find('.chart-axis-labels').text()
      expect(axisText).toMatch(/1/)
      expect(axisText).toMatch(/3/)
    })

    it('renders top pages and top countries with counts', async () => {
      const wrapper = await createWrapper()
      const text = wrapper.text()
      const normalized = text.replace(/[\s,]/g, '')
      expect(text).toContain('Home')
      expect(text).toContain('/about')
      expect(text).toContain('SE')
      expect(text).toContain('US')
      expect(normalized).toContain('200')
    })

    it('renders the outbound-clicks card, separate from page views', async () => {
      const wrapper = await createWrapper()
      const text = wrapper.text()
      expect(text).toContain('Outbound clicks')
      expect(text).toContain('linkedin/hero')
      expect(text).toContain('github/footer')
    })

    it('shows an empty state when there are no outbound clicks', async () => {
      vi.mocked(analyticsService.getAnalyticsSummary).mockResolvedValue(
        makeSummary({ outbound_clicks: [] })
      )
      const wrapper = await createWrapper()
      expect(wrapper.text()).toContain('No outbound clicks tracked yet.')
    })
  })

  describe('Range selection', () => {
    it('defaults to the 30-day tab', async () => {
      const wrapper = await createWrapper()
      const active = wrapper.find('.range-tab.active')
      expect(active.text()).toBe('30d')
    })

    it('refetches with the new window when a different tab is clicked', async () => {
      const wrapper = await createWrapper()
      vi.clearAllMocks()
      vi.mocked(analyticsService.getAnalyticsSummary).mockResolvedValue(
        makeSummary({ period_days: 90 })
      )
      vi.mocked(analyticsService.getVisitorStats).mockResolvedValue(makeVisitorStats())

      const tabs = wrapper.findAll('.range-tab')
      const ninetyDay = tabs.find(t => t.text() === '90d')
      expect(ninetyDay).toBeDefined()
      await ninetyDay!.trigger('click')
      await flushPromises()

      expect(analyticsService.getAnalyticsSummary).toHaveBeenCalledWith(90)
      // visitor-stats window is capped at 90 in the view.
      expect(analyticsService.getVisitorStats).toHaveBeenCalledWith(90)
    })

    it('does NOT refetch when the already-active tab is clicked', async () => {
      const wrapper = await createWrapper()
      vi.clearAllMocks()
      const active = wrapper.find('.range-tab.active')
      await active.trigger('click')
      await flushPromises()
      expect(analyticsService.getAnalyticsSummary).not.toHaveBeenCalled()
    })

    it('clamps the visitor-stats range at 90 days for the 1-year tab', async () => {
      const wrapper = await createWrapper()
      vi.clearAllMocks()
      vi.mocked(analyticsService.getAnalyticsSummary).mockResolvedValue(
        makeSummary({ period_days: 365 })
      )
      vi.mocked(analyticsService.getVisitorStats).mockResolvedValue(makeVisitorStats())

      const yearTab = wrapper.findAll('.range-tab').find(t => t.text() === '1y')
      await yearTab!.trigger('click')
      await flushPromises()

      expect(analyticsService.getAnalyticsSummary).toHaveBeenCalledWith(365)
      // Visitor stats argument should be min(365, 90) = 90.
      expect(analyticsService.getVisitorStats).toHaveBeenCalledWith(90)
    })
  })

  describe('Empty / error / loading states', () => {
    it('shows the loading state on initial mount', () => {
      vi.mocked(analyticsService.getAnalyticsSummary).mockImplementation(
        () => new Promise(() => undefined)
      )
      const wrapper = mount(AdminAnalytics, {
        global: { plugins: [createTestingPinia({ createSpy: vi.fn })] }
      })
      expect(wrapper.text()).toContain('Loading analytics')
    })

    it('shows an error alert when the summary fetch rejects', async () => {
      vi.mocked(analyticsService.getAnalyticsSummary).mockRejectedValue(new Error('boom'))
      const wrapper = await createWrapper()
      expect(wrapper.find('.error-alert').exists()).toBe(true)
      expect(wrapper.text()).toContain('Failed to load analytics')
    })

    it('shows an error alert when the service returns null', async () => {
      vi.mocked(analyticsService.getAnalyticsSummary).mockResolvedValue(null)
      const wrapper = await createWrapper()
      expect(wrapper.text()).toContain('Could not load analytics summary')
    })

    it('clicking Retry refires the load', async () => {
      vi.mocked(analyticsService.getAnalyticsSummary).mockRejectedValue(new Error('boom'))
      const wrapper = await createWrapper()
      vi.mocked(analyticsService.getAnalyticsSummary).mockResolvedValue(makeSummary())
      vi.mocked(analyticsService.getVisitorStats).mockResolvedValue(makeVisitorStats())

      await wrapper.find('.retry-button').trigger('click')
      await flushPromises()

      expect(wrapper.find('.error-alert').exists()).toBe(false)
      const normalized = wrapper.text().replace(/[\s,]/g, '')
      expect(normalized).toContain('1234')
    })

    it('renders an empty-state when there are no daily views', async () => {
      vi.mocked(analyticsService.getAnalyticsSummary).mockResolvedValue(
        makeSummary({ daily_views: [] })
      )
      const wrapper = await createWrapper()
      expect(wrapper.text()).toContain('No traffic in this range yet.')
    })

    it('renders an empty-state for top pages and countries when arrays are empty', async () => {
      vi.mocked(analyticsService.getAnalyticsSummary).mockResolvedValue(
        makeSummary({ top_pages: [] })
      )
      vi.mocked(analyticsService.getVisitorStats).mockResolvedValue(
        makeVisitorStats({ top_countries: [] })
      )
      const wrapper = await createWrapper()
      expect(wrapper.text()).toContain('No pages tracked yet.')
      expect(wrapper.text()).toContain('No country data')
    })
  })

  describe('Lifecycle', () => {
    it('fires both service calls on mount with the default range', async () => {
      await createWrapper()
      expect(analyticsService.getAnalyticsSummary).toHaveBeenCalledTimes(1)
      expect(analyticsService.getAnalyticsSummary).toHaveBeenCalledWith(30)
      expect(analyticsService.getVisitorStats).toHaveBeenCalledTimes(1)
      // Default range (30) is below the 90 clamp, so passed through.
      expect(analyticsService.getVisitorStats).toHaveBeenCalledWith(30)
    })
  })
})
