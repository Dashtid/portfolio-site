/**
 * Tests for useAnalytics composable (TypeScript)
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useAnalytics } from '@/composables/useAnalytics'
import * as analyticsUtils from '@/utils/analytics'

// Mock the analytics utilities
vi.mock('@/utils/analytics', () => ({
  analytics: {
    trackEvent: vi.fn(),
    trackPageView: vi.fn()
  },
  trackEvent: vi.fn(),
  trackPageView: vi.fn(),
  trackOutboundLink: vi.fn(),
  trackDownload: vi.fn()
}))

describe('useAnalytics', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('exports all tracking functions', () => {
    const analytics = useAnalytics()

    expect(analytics.track).toBeDefined()
    expect(analytics.trackNavigation).toBeDefined()
    expect(analytics.trackThemeToggle).toBeDefined()
    expect(analytics.trackButtonClick).toBeDefined()
    expect(analytics.trackExternalLink).toBeDefined()
    expect(analytics.trackContact).toBeDefined()
    expect(analytics.trackProject).toBeDefined()
    expect(analytics.trackScroll).toBeDefined()
    expect(analytics.trackGitHubStats).toBeDefined()
    expect(analytics.trackBackToTop).toBeDefined()
  })

  it('tracks custom events with correct parameters', () => {
    const analytics = useAnalytics()

    analytics.track('Test Event', { test: 'value' })

    expect(analyticsUtils.trackEvent).toHaveBeenCalledWith('Test Event', { test: 'value' })
  })

  it('tracks navigation with section name', () => {
    const analytics = useAnalytics()

    analytics.trackNavigation('About')

    expect(analyticsUtils.trackEvent).toHaveBeenCalledWith('Navigation Click', { section: 'About' })
  })

  it('tracks theme toggle with theme name', () => {
    const analytics = useAnalytics()

    analytics.trackThemeToggle('dark')

    expect(analyticsUtils.trackEvent).toHaveBeenCalledWith('Theme Toggle', { theme: 'dark' })
  })

  it('tracks button clicks with name and location', () => {
    const analytics = useAnalytics()

    analytics.trackButtonClick('Submit', 'Contact Form')

    expect(analyticsUtils.trackEvent).toHaveBeenCalledWith('Button Click', {
      button: 'Submit',
      location: 'Contact Form'
    })
  })

  it('tracks button clicks with default empty location', () => {
    const analytics = useAnalytics()

    analytics.trackButtonClick('Download')

    expect(analyticsUtils.trackEvent).toHaveBeenCalledWith('Button Click', {
      button: 'Download',
      location: ''
    })
  })

  it('tracks external links with URL and label', () => {
    const analytics = useAnalytics()

    analytics.trackExternalLink('https://example.com', 'Example Link')

    expect(analyticsUtils.trackOutboundLink).toHaveBeenCalledWith('https://example.com')
    expect(analyticsUtils.trackEvent).toHaveBeenCalledWith('External Link', {
      url: 'https://example.com',
      label: 'Example Link'
    })
  })

  it('tracks external links without label', () => {
    const analytics = useAnalytics()

    analytics.trackExternalLink('https://example.com')

    expect(analyticsUtils.trackOutboundLink).toHaveBeenCalledWith('https://example.com')
    expect(analyticsUtils.trackEvent).not.toHaveBeenCalledWith(
      expect.stringContaining('External Link'),
      expect.any(Object)
    )
  })

  it('tracks contact method', () => {
    const analytics = useAnalytics()

    analytics.trackContact('email')

    expect(analyticsUtils.trackEvent).toHaveBeenCalledWith('Contact', { method: 'email' })
  })

  it('tracks project interactions', () => {
    const analytics = useAnalytics()

    analytics.trackProject('view', 'Portfolio Site')

    expect(analyticsUtils.trackEvent).toHaveBeenCalledWith('Project Interaction', {
      action: 'view',
      project: 'Portfolio Site'
    })
  })

  it('tracks scroll events', () => {
    const analytics = useAnalytics()

    analytics.trackScroll('Projects')

    expect(analyticsUtils.trackEvent).toHaveBeenCalledWith('Scroll To', { section: 'Projects' })
  })

  it('tracks GitHub stats views', () => {
    const analytics = useAnalytics()

    analytics.trackGitHubStats('testuser')

    expect(analyticsUtils.trackEvent).toHaveBeenCalledWith('GitHub Stats Viewed', {
      username: 'testuser'
    })
  })

  it('tracks back to top button clicks', () => {
    const analytics = useAnalytics()

    analytics.trackBackToTop()

    expect(analyticsUtils.trackEvent).toHaveBeenCalledWith('Back To Top', {})
  })

  it('exposes analytics instance', () => {
    const analytics = useAnalytics()

    expect(analytics.analytics).toBeDefined()
  })

  it('exposes trackPageView function', () => {
    const analytics = useAnalytics()

    expect(analytics.trackPageView).toBeDefined()
  })
})
