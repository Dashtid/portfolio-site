/**
 * Tests for analytics utility (TypeScript)
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { analytics, trackEvent, trackPageView, trackOutboundLink, trackDownload } from '@/utils/analytics'

describe('analytics utility', () => {
  beforeEach(() => {
    // Re-import to get fresh instance with test environment variables
    vi.resetModules()

    // Mock window.plausible before importing analytics
    window.plausible = vi.fn()
  })

  afterEach(() => {
    vi.unstubAllEnvs()
    delete window.plausible
    vi.clearAllMocks()
  })

  describe('Analytics class', () => {
    it('initializes with correct provider', () => {
      expect(analytics).toBeDefined()
    })

    it('tracks events with Plausible', () => {
      // Enable analytics for this test
      vi.stubEnv('VITE_ANALYTICS_ENABLED', 'true')

      analytics.trackEvent('Test Event', { test: 'value' })

      expect(window.plausible).toHaveBeenCalledWith('Test Event', {
        props: { test: 'value' }
      })

      vi.unstubAllEnvs()
    })

    it('tracks events with empty props', () => {
      analytics.trackEvent('Test Event')

      expect(window.plausible).toHaveBeenCalledWith('Test Event', { props: {} })
    })

    it('tracks page views', () => {
      const path = '/about'
      analytics.trackPageView(path)

      expect(window.plausible).toHaveBeenCalledWith('pageview', {
        u: expect.stringContaining(path)
      })
    })

    it('tracks outbound link clicks', () => {
      const url = 'https://example.com'
      analytics.trackOutboundLink(url)

      expect(window.plausible).toHaveBeenCalledWith('Outbound Link Click', {
        props: { url }
      })
    })

    it('tracks file downloads', () => {
      const filename = 'test.pdf'
      analytics.trackDownload(filename)

      expect(window.plausible).toHaveBeenCalledWith('File Download', {
        props: { filename }
      })
    })

    it('tracks errors', () => {
      analytics.trackError('Test error', 'TestType')

      expect(window.plausible).toHaveBeenCalledWith('Error', {
        props: {
          message: 'Test error',
          type: 'TestType'
        }
      })
    })

    it('tracks errors with default type', () => {
      analytics.trackError('Test error')

      expect(window.plausible).toHaveBeenCalledWith('Error', {
        props: {
          message: 'Test error',
          type: 'Unknown'
        }
      })
    })

    it('handles tracking when plausible is not available', () => {
      delete window.plausible

      expect(() => {
        analytics.trackEvent('Test Event')
      }).not.toThrow()
    })
  })

  describe('convenience exports', () => {
    it('trackEvent function works', () => {
      trackEvent('Test', { prop: 'value' })

      expect(window.plausible).toHaveBeenCalled()
    })

    it('trackPageView function works', () => {
      trackPageView('/test')

      expect(window.plausible).toHaveBeenCalled()
    })

    it('trackOutboundLink function works', () => {
      trackOutboundLink('https://example.com')

      expect(window.plausible).toHaveBeenCalled()
    })

    it('trackDownload function works', () => {
      trackDownload('file.pdf')

      expect(window.plausible).toHaveBeenCalled()
    })
  })

  describe('TypeScript types', () => {
    it('accepts string tracking props', () => {
      const props = { stringProp: 'value' }
      trackEvent('Test', props)

      expect(window.plausible).toHaveBeenCalledWith('Test', { props })
    })

    it('accepts number tracking props', () => {
      const props = { numberProp: 123 }
      trackEvent('Test', props)

      expect(window.plausible).toHaveBeenCalledWith('Test', { props })
    })

    it('accepts boolean tracking props', () => {
      const props = { boolProp: true }
      trackEvent('Test', props)

      expect(window.plausible).toHaveBeenCalledWith('Test', { props })
    })

    it('accepts mixed type tracking props', () => {
      const props = {
        string: 'value',
        number: 42,
        boolean: true,
        undefined: undefined
      }
      trackEvent('Test', props)

      expect(window.plausible).toHaveBeenCalledWith('Test', { props })
    })
  })
})
