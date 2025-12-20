/**
 * Tests for analytics utility
 * Comprehensive branch coverage for Plausible and Umami providers
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// We need to test the Analytics class directly to test different configurations
// Re-import for each test scenario

describe('analytics utility', () => {
  let mockPlausible: ReturnType<typeof vi.fn>
  let mockUmamiTrack: ReturnType<typeof vi.fn>

  beforeEach(() => {
    // Mock window.plausible
    mockPlausible = vi.fn()
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    ;(window as any).plausible = mockPlausible

    // Mock window.umami
    mockUmamiTrack = vi.fn()
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    ;(window as any).umami = {
      track: mockUmamiTrack
    }

    // Clear document head for init tests
    document.head.innerHTML = ''
  })

  afterEach(() => {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    delete (window as any).plausible
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    delete (window as any).umami
    vi.clearAllMocks()
    vi.resetModules()
  })

  describe('Analytics class - disabled state', () => {
    it('initializes analytics singleton', async () => {
      const { analytics } = await import('@/utils/analytics')
      expect(analytics).toBeDefined()
    })

    it('has init method', async () => {
      const { analytics } = await import('@/utils/analytics')
      expect(analytics.init).toBeDefined()
      expect(typeof analytics.init).toBe('function')
    })

    it('has trackEvent method', async () => {
      const { analytics } = await import('@/utils/analytics')
      expect(analytics.trackEvent).toBeDefined()
      expect(typeof analytics.trackEvent).toBe('function')
    })

    it('has trackPageView method', async () => {
      const { analytics } = await import('@/utils/analytics')
      expect(analytics.trackPageView).toBeDefined()
      expect(typeof analytics.trackPageView).toBe('function')
    })

    it('has trackOutboundLink method', async () => {
      const { analytics } = await import('@/utils/analytics')
      expect(analytics.trackOutboundLink).toBeDefined()
      expect(typeof analytics.trackOutboundLink).toBe('function')
    })

    it('has trackDownload method', async () => {
      const { analytics } = await import('@/utils/analytics')
      expect(analytics.trackDownload).toBeDefined()
      expect(typeof analytics.trackDownload).toBe('function')
    })

    it('has trackError method', async () => {
      const { analytics } = await import('@/utils/analytics')
      expect(analytics.trackError).toBeDefined()
      expect(typeof analytics.trackError).toBe('function')
    })
  })

  describe('init method', () => {
    it('does not throw when called', async () => {
      const { analytics } = await import('@/utils/analytics')
      expect(() => analytics.init()).not.toThrow()
    })

    it('handles init when analytics is disabled', async () => {
      const { analytics } = await import('@/utils/analytics')
      // Analytics is disabled by default in test env (no VITE_ANALYTICS_ENABLED)
      expect(() => analytics.init()).not.toThrow()
    })
  })

  describe('trackEvent - disabled analytics', () => {
    it('does not throw when tracking events (disabled)', async () => {
      const { analytics } = await import('@/utils/analytics')
      expect(() => analytics.trackEvent('Test Event')).not.toThrow()
    })

    it('does not call plausible when disabled', async () => {
      const { analytics } = await import('@/utils/analytics')
      analytics.trackEvent('Test Event')
      // Should not call because analytics is disabled
      expect(mockPlausible).not.toHaveBeenCalled()
    })

    it('accepts event props', async () => {
      const { analytics } = await import('@/utils/analytics')
      expect(() => analytics.trackEvent('Test Event', { key: 'value' })).not.toThrow()
    })

    it('handles empty props object', async () => {
      const { analytics } = await import('@/utils/analytics')
      expect(() => analytics.trackEvent('Test Event', {})).not.toThrow()
    })
  })

  describe('trackPageView - disabled analytics', () => {
    it('does not throw when tracking page views', async () => {
      const { analytics } = await import('@/utils/analytics')
      expect(() => analytics.trackPageView('/test')).not.toThrow()
    })

    it('does not call plausible when disabled', async () => {
      const { analytics } = await import('@/utils/analytics')
      analytics.trackPageView('/test')
      expect(mockPlausible).not.toHaveBeenCalled()
    })

    it('handles empty path', async () => {
      const { analytics } = await import('@/utils/analytics')
      expect(() => analytics.trackPageView('')).not.toThrow()
    })

    it('handles root path', async () => {
      const { analytics } = await import('@/utils/analytics')
      expect(() => analytics.trackPageView('/')).not.toThrow()
    })
  })

  describe('trackOutboundLink', () => {
    it('tracks outbound link clicks', async () => {
      const { analytics } = await import('@/utils/analytics')
      analytics.trackOutboundLink('https://example.com')
      // Should not throw
      expect(true).toBe(true)
    })

    it('handles various URL formats', async () => {
      const { analytics } = await import('@/utils/analytics')
      expect(() => analytics.trackOutboundLink('https://example.com')).not.toThrow()
      expect(() => analytics.trackOutboundLink('http://example.com')).not.toThrow()
      expect(() => analytics.trackOutboundLink('mailto:test@example.com')).not.toThrow()
    })
  })

  describe('trackDownload', () => {
    it('tracks file downloads', async () => {
      const { analytics } = await import('@/utils/analytics')
      analytics.trackDownload('document.pdf')
      expect(true).toBe(true)
    })

    it('handles various file types', async () => {
      const { analytics } = await import('@/utils/analytics')
      expect(() => analytics.trackDownload('file.pdf')).not.toThrow()
      expect(() => analytics.trackDownload('image.png')).not.toThrow()
      expect(() => analytics.trackDownload('doc.docx')).not.toThrow()
    })
  })

  describe('trackError', () => {
    it('tracks errors with message and type', async () => {
      const { analytics } = await import('@/utils/analytics')
      expect(() => analytics.trackError('Test error', 'TestType')).not.toThrow()
    })

    it('tracks errors with default type', async () => {
      const { analytics } = await import('@/utils/analytics')
      expect(() => analytics.trackError('Test error')).not.toThrow()
    })

    it('handles empty error message', async () => {
      const { analytics } = await import('@/utils/analytics')
      expect(() => analytics.trackError('')).not.toThrow()
    })
  })

  describe('convenience exports', () => {
    it('trackEvent function is exported', async () => {
      const { trackEvent } = await import('@/utils/analytics')
      expect(trackEvent).toBeDefined()
      expect(typeof trackEvent).toBe('function')
    })

    it('trackPageView function is exported', async () => {
      const { trackPageView } = await import('@/utils/analytics')
      expect(trackPageView).toBeDefined()
      expect(typeof trackPageView).toBe('function')
    })

    it('trackOutboundLink function is exported', async () => {
      const { trackOutboundLink } = await import('@/utils/analytics')
      expect(trackOutboundLink).toBeDefined()
      expect(typeof trackOutboundLink).toBe('function')
    })

    it('trackDownload function is exported', async () => {
      const { trackDownload } = await import('@/utils/analytics')
      expect(trackDownload).toBeDefined()
      expect(typeof trackDownload).toBe('function')
    })

    it('trackEvent works correctly', async () => {
      const { trackEvent } = await import('@/utils/analytics')
      expect(() => trackEvent('Test', { prop: 'value' })).not.toThrow()
    })

    it('trackPageView works correctly', async () => {
      const { trackPageView } = await import('@/utils/analytics')
      expect(() => trackPageView('/test')).not.toThrow()
    })

    it('trackOutboundLink works correctly', async () => {
      const { trackOutboundLink } = await import('@/utils/analytics')
      expect(() => trackOutboundLink('https://example.com')).not.toThrow()
    })

    it('trackDownload works correctly', async () => {
      const { trackDownload } = await import('@/utils/analytics')
      expect(() => trackDownload('file.pdf')).not.toThrow()
    })
  })

  describe('TypeScript types', () => {
    it('accepts string tracking props', async () => {
      const { trackEvent } = await import('@/utils/analytics')
      expect(() => trackEvent('Test', { stringProp: 'value' })).not.toThrow()
    })

    it('accepts number tracking props', async () => {
      const { trackEvent } = await import('@/utils/analytics')
      expect(() => trackEvent('Test', { numberProp: 123 })).not.toThrow()
    })

    it('accepts boolean tracking props', async () => {
      const { trackEvent } = await import('@/utils/analytics')
      expect(() => trackEvent('Test', { boolProp: true })).not.toThrow()
    })

    it('accepts undefined tracking props', async () => {
      const { trackEvent } = await import('@/utils/analytics')
      expect(() => trackEvent('Test', { undefinedProp: undefined })).not.toThrow()
    })

    it('accepts mixed type tracking props', async () => {
      const { trackEvent } = await import('@/utils/analytics')
      const props = {
        string: 'value',
        number: 42,
        boolean: true,
        undefined: undefined
      }
      expect(() => trackEvent('Test', props)).not.toThrow()
    })
  })

  describe('error handling', () => {
    it('handles tracking when plausible throws', async () => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      ;(window as any).plausible = vi.fn().mockImplementation(() => {
        throw new Error('Plausible error')
      })

      const { analytics } = await import('@/utils/analytics')
      expect(() => analytics.trackEvent('Test Event')).not.toThrow()
    })

    it('handles tracking when umami throws', async () => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      ;(window as any).umami = {
        track: vi.fn().mockImplementation(() => {
          throw new Error('Umami error')
        })
      }

      const { analytics } = await import('@/utils/analytics')
      expect(() => analytics.trackEvent('Test Event')).not.toThrow()
    })

    it('handles pageview tracking when plausible throws', async () => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      ;(window as any).plausible = vi.fn().mockImplementation(() => {
        throw new Error('Plausible error')
      })

      const { analytics } = await import('@/utils/analytics')
      expect(() => analytics.trackPageView('/test')).not.toThrow()
    })
  })

  describe('default export', () => {
    it('exports analytics as default', async () => {
      const defaultExport = await import('@/utils/analytics')
      expect(defaultExport.default).toBeDefined()
      expect(defaultExport.default.trackEvent).toBeDefined()
    })
  })

  describe('Analytics enabled - Plausible provider', () => {
    beforeEach(() => {
      vi.resetModules()
      // Mock environment variables for enabled Plausible
      vi.stubEnv('VITE_ANALYTICS_ENABLED', 'true')
      vi.stubEnv('VITE_ANALYTICS_PROVIDER', 'plausible')
      vi.stubEnv('VITE_ANALYTICS_SITE_ID', 'test-domain.com')
      vi.stubEnv('VITE_ANALYTICS_URL', 'https://plausible.io/js/script.js')
    })

    afterEach(() => {
      vi.unstubAllEnvs()
    })

    it('calls plausible when tracking events', async () => {
      const { analytics } = await import('@/utils/analytics')
      analytics.trackEvent('Test Event', { key: 'value' })
      expect(mockPlausible).toHaveBeenCalledWith('Test Event', { props: { key: 'value' } })
    })

    it('calls plausible for page views', async () => {
      const { analytics } = await import('@/utils/analytics')
      analytics.trackPageView('/test-page')
      expect(mockPlausible).toHaveBeenCalledWith('pageview', {
        u: expect.stringContaining('/test-page')
      })
    })

    it('initializes Plausible script on init', async () => {
      const { analytics } = await import('@/utils/analytics')
      analytics.init()
      const script = document.querySelector('script[data-domain="test-domain.com"]')
      expect(script).not.toBeNull()
      expect(script?.getAttribute('src')).toBe('https://plausible.io/js/script.js')
    })

    it('uses default Plausible URL when not specified', async () => {
      vi.unstubAllEnvs()
      vi.stubEnv('VITE_ANALYTICS_ENABLED', 'true')
      vi.stubEnv('VITE_ANALYTICS_PROVIDER', 'plausible')
      vi.stubEnv('VITE_ANALYTICS_SITE_ID', 'test-domain.com')
      vi.resetModules()

      const { analytics } = await import('@/utils/analytics')
      analytics.init()
      const script = document.querySelector('script[data-domain="test-domain.com"]')
      expect(script?.getAttribute('src')).toBe('https://plausible.io/js/script.js')
    })

    it('tracks outbound links via trackEvent', async () => {
      const { analytics } = await import('@/utils/analytics')
      analytics.trackOutboundLink('https://external.com')
      expect(mockPlausible).toHaveBeenCalledWith('Outbound Link Click', {
        props: { url: 'https://external.com' }
      })
    })

    it('tracks file downloads via trackEvent', async () => {
      const { analytics } = await import('@/utils/analytics')
      analytics.trackDownload('report.pdf')
      expect(mockPlausible).toHaveBeenCalledWith('File Download', {
        props: { filename: 'report.pdf' }
      })
    })

    it('tracks errors via trackEvent', async () => {
      const { analytics } = await import('@/utils/analytics')
      analytics.trackError('Something went wrong', 'NetworkError')
      expect(mockPlausible).toHaveBeenCalledWith('Error', {
        props: { message: 'Something went wrong', type: 'NetworkError' }
      })
    })

    it('handles missing plausible on window gracefully', async () => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      delete (window as any).plausible
      const { analytics } = await import('@/utils/analytics')
      expect(() => analytics.trackEvent('Test')).not.toThrow()
    })

    it('catches and logs errors when plausible throws', async () => {
      mockPlausible.mockImplementation(() => {
        throw new Error('Tracking failed')
      })
      const { analytics } = await import('@/utils/analytics')
      expect(() => analytics.trackEvent('Test')).not.toThrow()
    })
  })

  describe('Analytics enabled - Umami provider', () => {
    beforeEach(() => {
      vi.resetModules()
      // Mock environment variables for enabled Umami
      vi.stubEnv('VITE_ANALYTICS_ENABLED', 'true')
      vi.stubEnv('VITE_ANALYTICS_PROVIDER', 'umami')
      vi.stubEnv('VITE_ANALYTICS_SITE_ID', 'test-website-id')
      vi.stubEnv('VITE_ANALYTICS_URL', 'https://analytics.umami.is/script.js')
    })

    afterEach(() => {
      vi.unstubAllEnvs()
    })

    it('calls umami.track when tracking events', async () => {
      const { analytics } = await import('@/utils/analytics')
      analytics.trackEvent('Test Event', { key: 'value' })
      expect(mockUmamiTrack).toHaveBeenCalledWith('Test Event', { key: 'value' })
    })

    it('calls umami.track for page views with function callback', async () => {
      const { analytics } = await import('@/utils/analytics')
      analytics.trackPageView('/test-page')
      expect(mockUmamiTrack).toHaveBeenCalledWith(expect.any(Function))
    })

    it('initializes Umami script on init', async () => {
      const { analytics } = await import('@/utils/analytics')
      analytics.init()
      const script = document.querySelector('script[data-website-id="test-website-id"]')
      expect(script).not.toBeNull()
      expect(script?.getAttribute('src')).toBe('https://analytics.umami.is/script.js')
    })

    it('uses default Umami URL when not specified', async () => {
      vi.unstubAllEnvs()
      vi.stubEnv('VITE_ANALYTICS_ENABLED', 'true')
      vi.stubEnv('VITE_ANALYTICS_PROVIDER', 'umami')
      vi.stubEnv('VITE_ANALYTICS_SITE_ID', 'test-website-id')
      vi.resetModules()

      const { analytics } = await import('@/utils/analytics')
      analytics.init()
      const script = document.querySelector('script[data-website-id="test-website-id"]')
      expect(script?.getAttribute('src')).toBe('https://analytics.umami.is/script.js')
    })

    it('handles missing umami on window gracefully', async () => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      delete (window as any).umami
      const { analytics } = await import('@/utils/analytics')
      expect(() => analytics.trackEvent('Test')).not.toThrow()
    })

    it('catches and logs errors when umami throws', async () => {
      mockUmamiTrack.mockImplementation(() => {
        throw new Error('Tracking failed')
      })
      const { analytics } = await import('@/utils/analytics')
      expect(() => analytics.trackEvent('Test')).not.toThrow()
    })
  })

  describe('Analytics init edge cases', () => {
    beforeEach(() => {
      vi.resetModules()
      document.head.innerHTML = ''
    })

    afterEach(() => {
      vi.unstubAllEnvs()
    })

    it('does not init when siteId is missing', async () => {
      vi.stubEnv('VITE_ANALYTICS_ENABLED', 'true')
      vi.stubEnv('VITE_ANALYTICS_PROVIDER', 'plausible')
      // No VITE_ANALYTICS_SITE_ID

      const { analytics } = await import('@/utils/analytics')
      analytics.init()
      const scripts = document.querySelectorAll('script')
      expect(scripts.length).toBe(0)
    })

    it('handles plausible init without siteId', async () => {
      vi.stubEnv('VITE_ANALYTICS_ENABLED', 'true')
      vi.stubEnv('VITE_ANALYTICS_PROVIDER', 'plausible')

      const { analytics } = await import('@/utils/analytics')
      analytics.init()
      // Should not throw and should not add script
      expect(document.querySelectorAll('script').length).toBe(0)
    })

    it('handles umami init without siteId', async () => {
      vi.stubEnv('VITE_ANALYTICS_ENABLED', 'true')
      vi.stubEnv('VITE_ANALYTICS_PROVIDER', 'umami')

      const { analytics } = await import('@/utils/analytics')
      analytics.init()
      // Should not throw and should not add script
      expect(document.querySelectorAll('script').length).toBe(0)
    })
  })
})
