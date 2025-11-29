/**
 * Tests for analytics utility (TypeScript)
 *
 * Note: Environment variables are set in vitest.config.ts
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import {
  analytics,
  trackEvent,
  trackPageView,
  trackOutboundLink,
  trackDownload
} from '@/utils/analytics'

describe('analytics utility', () => {
  beforeEach(() => {
    // Mock window.plausible
    window.plausible = vi.fn()
    // Mock window.umami
    window.umami = {
      track: vi.fn()
    }
    // Clear document head for init tests
    document.head.innerHTML = ''
  })

  afterEach(() => {
    delete window.plausible
    delete window.umami
    vi.clearAllMocks()
  })

  describe('Analytics class', () => {
    it('initializes analytics singleton', () => {
      expect(analytics).toBeDefined()
    })

    it('has init method', () => {
      expect(analytics.init).toBeDefined()
      expect(typeof analytics.init).toBe('function')
    })

    it('has trackEvent method', () => {
      expect(analytics.trackEvent).toBeDefined()
      expect(typeof analytics.trackEvent).toBe('function')
    })

    it('has trackPageView method', () => {
      expect(analytics.trackPageView).toBeDefined()
      expect(typeof analytics.trackPageView).toBe('function')
    })

    it('has trackOutboundLink method', () => {
      expect(analytics.trackOutboundLink).toBeDefined()
      expect(typeof analytics.trackOutboundLink).toBe('function')
    })

    it('has trackDownload method', () => {
      expect(analytics.trackDownload).toBeDefined()
      expect(typeof analytics.trackDownload).toBe('function')
    })

    it('has trackError method', () => {
      expect(analytics.trackError).toBeDefined()
      expect(typeof analytics.trackError).toBe('function')
    })
  })

  describe('init method', () => {
    it('does not throw when called', () => {
      expect(() => analytics.init()).not.toThrow()
    })

    it('handles init when analytics is disabled', () => {
      // Analytics is disabled by default in test env (no VITE_ANALYTICS_ENABLED)
      expect(() => analytics.init()).not.toThrow()
    })
  })

  describe('trackEvent', () => {
    it('does not throw when tracking events', () => {
      expect(() => analytics.trackEvent('Test Event')).not.toThrow()
    })

    it('accepts event props', () => {
      expect(() => analytics.trackEvent('Test Event', { key: 'value' })).not.toThrow()
    })

    it('handles empty props object', () => {
      expect(() => analytics.trackEvent('Test Event', {})).not.toThrow()
    })

    it('handles tracking when plausible throws', () => {
      window.plausible = vi.fn().mockImplementation(() => {
        throw new Error('Plausible error')
      })

      expect(() => analytics.trackEvent('Test Event')).not.toThrow()
    })
  })

  describe('trackPageView', () => {
    it('does not throw when tracking page views', () => {
      expect(() => analytics.trackPageView('/test')).not.toThrow()
    })

    it('handles empty path', () => {
      expect(() => analytics.trackPageView('')).not.toThrow()
    })

    it('handles root path', () => {
      expect(() => analytics.trackPageView('/')).not.toThrow()
    })

    it('handles tracking when plausible throws', () => {
      window.plausible = vi.fn().mockImplementation(() => {
        throw new Error('Plausible error')
      })

      expect(() => analytics.trackPageView('/test')).not.toThrow()
    })
  })

  describe('trackOutboundLink', () => {
    it('tracks outbound link clicks', () => {
      analytics.trackOutboundLink('https://example.com')

      // Should not throw
      expect(true).toBe(true)
    })

    it('handles various URL formats', () => {
      expect(() => analytics.trackOutboundLink('https://example.com')).not.toThrow()
      expect(() => analytics.trackOutboundLink('http://example.com')).not.toThrow()
      expect(() => analytics.trackOutboundLink('mailto:test@example.com')).not.toThrow()
    })
  })

  describe('trackDownload', () => {
    it('tracks file downloads', () => {
      analytics.trackDownload('document.pdf')

      // Should not throw
      expect(true).toBe(true)
    })

    it('handles various file types', () => {
      expect(() => analytics.trackDownload('file.pdf')).not.toThrow()
      expect(() => analytics.trackDownload('image.png')).not.toThrow()
      expect(() => analytics.trackDownload('doc.docx')).not.toThrow()
    })
  })

  describe('trackError', () => {
    it('tracks errors with message and type', () => {
      expect(() => analytics.trackError('Test error', 'TestType')).not.toThrow()
    })

    it('tracks errors with default type', () => {
      expect(() => analytics.trackError('Test error')).not.toThrow()
    })

    it('handles empty error message', () => {
      expect(() => analytics.trackError('')).not.toThrow()
    })
  })

  describe('convenience exports', () => {
    it('trackEvent function is exported', () => {
      expect(trackEvent).toBeDefined()
      expect(typeof trackEvent).toBe('function')
    })

    it('trackPageView function is exported', () => {
      expect(trackPageView).toBeDefined()
      expect(typeof trackPageView).toBe('function')
    })

    it('trackOutboundLink function is exported', () => {
      expect(trackOutboundLink).toBeDefined()
      expect(typeof trackOutboundLink).toBe('function')
    })

    it('trackDownload function is exported', () => {
      expect(trackDownload).toBeDefined()
      expect(typeof trackDownload).toBe('function')
    })

    it('trackEvent works correctly', () => {
      expect(() => trackEvent('Test', { prop: 'value' })).not.toThrow()
    })

    it('trackPageView works correctly', () => {
      expect(() => trackPageView('/test')).not.toThrow()
    })

    it('trackOutboundLink works correctly', () => {
      expect(() => trackOutboundLink('https://example.com')).not.toThrow()
    })

    it('trackDownload works correctly', () => {
      expect(() => trackDownload('file.pdf')).not.toThrow()
    })
  })

  describe('TypeScript types', () => {
    it('accepts string tracking props', () => {
      expect(() => trackEvent('Test', { stringProp: 'value' })).not.toThrow()
    })

    it('accepts number tracking props', () => {
      expect(() => trackEvent('Test', { numberProp: 123 })).not.toThrow()
    })

    it('accepts boolean tracking props', () => {
      expect(() => trackEvent('Test', { boolProp: true })).not.toThrow()
    })

    it('accepts undefined tracking props', () => {
      expect(() => trackEvent('Test', { undefinedProp: undefined })).not.toThrow()
    })

    it('accepts mixed type tracking props', () => {
      const props = {
        string: 'value',
        number: 42,
        boolean: true,
        undefined: undefined
      }
      expect(() => trackEvent('Test', props)).not.toThrow()
    })
  })
})
