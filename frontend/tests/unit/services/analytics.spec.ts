/**
 * Tests for analytics service (TypeScript)
 *
 * The service was refactored to route all HTTP through apiClient (so it
 * picks up auth interceptors). Tests mock the apiClient module directly.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// Mock apiClient before the service is imported (services/analytics.ts
// imports apiClient at module-eval time as part of the singleton).
vi.mock('@/api/client', () => ({
  default: {
    post: vi.fn(),
    get: vi.fn()
  }
}))

// analyticsLogger is used by the service. The stubs are created once, in
// vi.hoisted (which runs before the hoisted vi.mock calls), so a copy of the
// module loaded again after vi.resetModules() logs to the same stubs.
const loggerStubs = vi.hoisted(() => {
  const stub = () => ({
    error: vi.fn(),
    warn: vi.fn(),
    log: vi.fn(),
    debug: vi.fn(),
    info: vi.fn()
  })
  return {
    analyticsLogger: stub(),
    adminLogger: stub(),
    authLogger: stub(),
    apiLogger: stub(),
    themeLogger: stub(),
    performanceLogger: stub(),
    errorLogger: stub(),
    logger: stub(),
    createLogger: () => stub()
  }
})
vi.mock('@/utils/logger', () => loggerStubs)

import apiClient from '@/api/client'
import analyticsService from '@/services/analytics'

const mockedPost = vi.mocked(apiClient.post)
const mockedGet = vi.mocked(apiClient.get)

/**
 * A stand-in for a Storage object, or for navigator, that records the name
 * of every property read or written on it. Every property reads as a
 * function returning null, so code that calls one runs on and is recorded.
 */
function accessRecorder<T extends object>(touched: string[]): T {
  return new Proxy({} as T, {
    get: (_target, property) => {
      touched.push(String(property))
      return () => null
    },
    set: (_target, property) => {
      touched.push(String(property))
      return true
    },
    has: (_target, property) => {
      touched.push(String(property))
      return false
    }
  })
}

describe('analytics service', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    sessionStorage.clear()
    localStorage.clear()
  })

  afterEach(() => {
    vi.resetAllMocks()
    vi.unstubAllGlobals()
    vi.restoreAllMocks()
  })

  describe('browser storage', () => {
    it('is not touched when the module is imported', async () => {
      const touched: string[] = []
      vi.stubGlobal('localStorage', accessRecorder<Storage>(touched))
      vi.stubGlobal('sessionStorage', accessRecorder<Storage>(touched))
      vi.resetModules()

      const fresh = await import('@/services/analytics')

      expect(fresh.default).toBeDefined()
      expect(touched).toEqual([])
    })

    it('is not written when a page view or an event is sent', async () => {
      mockedPost.mockResolvedValue({ data: {} } as never)

      await analyticsService.trackPageView('/test')
      await analyticsService.trackEvent('outbound', 'github', 'footer')

      expect(mockedPost).toHaveBeenCalledTimes(2)
      expect(sessionStorage.length).toBe(0)
      expect(localStorage.length).toBe(0)
    })
  })

  describe('trackPageView', () => {
    it('sends the page path and the referrer, and nothing else', async () => {
      mockedPost.mockResolvedValue({ data: {} } as never)
      document.title = 'Test Document Title'
      vi.spyOn(document, 'referrer', 'get').mockReturnValue('https://www.example.com/')

      await analyticsService.trackPageView('/test')

      expect(mockedPost).toHaveBeenCalledTimes(1)
      const [url, payload] = mockedPost.mock.calls[0]
      expect(url).toContain('/api/v1/analytics/track/pageview')
      // Exact equality: any field beyond these two fails here.
      expect(payload).toEqual({ page_path: '/test', referrer: 'https://www.example.com/' })
    })

    it('sends a null referrer when the page has none', async () => {
      mockedPost.mockResolvedValue({ data: {} } as never)
      vi.spyOn(document, 'referrer', 'get').mockReturnValue('')

      await analyticsService.trackPageView('/test')

      expect(mockedPost.mock.calls[0][1]).toEqual({ page_path: '/test', referrer: null })
    })

    it('uses current path when not provided', async () => {
      mockedPost.mockResolvedValue({ data: {} } as never)

      await analyticsService.trackPageView()

      expect(mockedPost).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({ page_path: window.location.pathname })
      )
    })

    it('handles API errors gracefully', async () => {
      mockedPost.mockRejectedValue(new Error('API Error'))
      const { analyticsLogger } = await import('@/utils/logger')

      await expect(analyticsService.trackPageView('/test')).resolves.not.toThrow()
      expect(analyticsLogger.error).toHaveBeenCalled()
    })
  })

  describe('trackEvent', () => {
    it('tracks events via page view with label', async () => {
      mockedPost.mockResolvedValue({ data: {} } as never)

      await analyticsService.trackEvent('click', 'button', 'submit', 1)

      expect(mockedPost).toHaveBeenCalledWith(expect.any(String), {
        page_path: '/event/click/button/submit',
        referrer: null
      })
    })

    it('tracks events via page view without label', async () => {
      mockedPost.mockResolvedValue({ data: {} } as never)

      await analyticsService.trackEvent('click', 'button')

      expect(mockedPost).toHaveBeenCalledWith(expect.any(String), {
        page_path: '/event/click/button',
        referrer: null
      })
    })

    it('tracks events without label and value', async () => {
      mockedPost.mockResolvedValue({ data: {} } as never)
      await analyticsService.trackEvent('pageview', 'home')
      expect(mockedPost).toHaveBeenCalled()
    })
  })

  describe('trackTiming', () => {
    it('logs timing data', async () => {
      const { analyticsLogger } = await import('@/utils/logger')

      analyticsService.trackTiming('load', 'page', 1000, 'home')

      expect(analyticsLogger.debug).toHaveBeenCalledWith(
        'Timing tracked:',
        expect.objectContaining({
          category: 'load',
          variable: 'page',
          time: 1000,
          label: 'home',
          timestamp: expect.any(String)
        })
      )
    })

    it('works without label', async () => {
      const { analyticsLogger } = await import('@/utils/logger')
      analyticsService.trackTiming('api', 'request', 500)
      expect(analyticsLogger.debug).toHaveBeenCalled()
    })
  })

  describe('getAnalyticsSummary', () => {
    it('fetches analytics summary', async () => {
      const mockData = { totalViews: 1000, uniqueVisitors: 500 }
      mockedGet.mockResolvedValue({ data: mockData } as never)

      const result = await analyticsService.getAnalyticsSummary(30)

      expect(result).toEqual(mockData)
      expect(mockedGet).toHaveBeenCalledWith(
        expect.stringContaining('/stats/summary'),
        expect.objectContaining({ params: { days: 30 } })
      )
    })

    it('uses default days parameter', async () => {
      mockedGet.mockResolvedValue({ data: {} } as never)
      await analyticsService.getAnalyticsSummary()
      expect(mockedGet).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({ params: { days: 30 } })
      )
    })

    it('returns null on error', async () => {
      mockedGet.mockRejectedValue(new Error('API Error'))
      const { analyticsLogger } = await import('@/utils/logger')

      const result = await analyticsService.getAnalyticsSummary()

      expect(result).toBeNull()
      expect(analyticsLogger.error).toHaveBeenCalled()
    })
  })

  describe('getVisitorStats', () => {
    it('fetches visitor statistics', async () => {
      const mockData = { visitors: [{ date: '2025-10-27', count: 100 }] }
      mockedGet.mockResolvedValue({ data: mockData } as never)

      const result = await analyticsService.getVisitorStats(7)

      expect(result).toEqual(mockData)
      expect(mockedGet).toHaveBeenCalledWith(
        expect.stringContaining('/stats/visitors'),
        expect.objectContaining({ params: { days: 7 } })
      )
    })

    it('uses default days parameter', async () => {
      mockedGet.mockResolvedValue({ data: {} } as never)
      await analyticsService.getVisitorStats()
      expect(mockedGet).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({ params: { days: 7 } })
      )
    })

    it('returns null on error', async () => {
      mockedGet.mockRejectedValue(new Error('API Error'))
      const { analyticsLogger } = await import('@/utils/logger')

      const result = await analyticsService.getVisitorStats()

      expect(result).toBeNull()
      expect(analyticsLogger.error).toHaveBeenCalled()
    })
  })
})
