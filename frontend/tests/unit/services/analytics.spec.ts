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
import analyticsService, {
  privacySignalSent,
  setVisitCountingOptOut,
  visitCountingDeclined
} from '@/services/analytics'

const mockedPost = vi.mocked(apiClient.post)
const mockedGet = vi.mocked(apiClient.get)

const OPT_OUT_KEY = 'portfolio-analytics-opt-out'

/** Each signal a browser sends to decline visit counting, set up for one test. */
const SIGNALS: Array<[string, () => void]> = [
  ['Global Privacy Control', () => vi.stubGlobal('navigator', { globalPrivacyControl: true })],
  ['Do Not Track', () => vi.stubGlobal('navigator', { doNotTrack: '1' })]
]

/** Each way a browser declines visit counting, set up for one test. */
const DECLINED_BY: Array<[string, () => void]> = [
  ...SIGNALS,
  ['the stored opt-out', () => setVisitCountingOptOut(true)]
]

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
    it('is not touched when the module is imported, and neither is navigator', async () => {
      const touched: string[] = []
      vi.stubGlobal('localStorage', accessRecorder<Storage>(touched))
      vi.stubGlobal('sessionStorage', accessRecorder<Storage>(touched))
      vi.stubGlobal('navigator', accessRecorder<Navigator>(touched))
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

  describe('visitCountingDeclined', () => {
    it('is false while no signal is set', () => {
      expect(visitCountingDeclined()).toBe(false)
    })

    it.each(DECLINED_BY)('is true under %s', (_name, decline) => {
      decline()
      expect(visitCountingDeclined()).toBe(true)
    })

    it('takes Global Privacy Control only as the boolean true', () => {
      for (const value of [false, 'true', 1, null, undefined]) {
        vi.stubGlobal('navigator', { globalPrivacyControl: value })
        expect(visitCountingDeclined(), String(value)).toBe(false)
      }
    })

    it("takes Do Not Track only as '1'", () => {
      for (const value of ['0', 'unspecified', 'yes', null, 1]) {
        vi.stubGlobal('navigator', { doNotTrack: value })
        expect(visitCountingDeclined(), String(value)).toBe(false)
      }
    })

    it("takes the stored opt-out only as '1'", () => {
      for (const value of ['0', 'true', '']) {
        localStorage.setItem(OPT_OUT_KEY, value)
        expect(visitCountingDeclined(), value).toBe(false)
      }
    })

    it('reads every source again on each call', () => {
      expect(visitCountingDeclined()).toBe(false)
      setVisitCountingOptOut(true)
      expect(visitCountingDeclined()).toBe(true)
      setVisitCountingOptOut(false)
      expect(visitCountingDeclined()).toBe(false)
      vi.stubGlobal('navigator', { doNotTrack: '1' })
      expect(visitCountingDeclined()).toBe(true)
    })

    it('counts a source that throws as not set, and still reads the others', () => {
      vi.stubGlobal('navigator', {
        get globalPrivacyControl(): boolean {
          throw new Error('blocked')
        },
        doNotTrack: '1'
      })
      expect(visitCountingDeclined()).toBe(true)

      vi.stubGlobal('navigator', { doNotTrack: '0' })
      vi.stubGlobal('localStorage', {
        getItem: () => {
          throw new DOMException('The operation is insecure.', 'SecurityError')
        }
      })
      expect(visitCountingDeclined()).toBe(false)
    })

    it('is false where navigator and localStorage do not exist', () => {
      vi.stubGlobal('navigator', undefined)
      vi.stubGlobal('localStorage', undefined)

      expect(visitCountingDeclined()).toBe(false)
      expect(() => setVisitCountingOptOut(true)).not.toThrow()
    })

    it.each(DECLINED_BY)('stops page views and events under %s', async (_name, decline) => {
      mockedPost.mockResolvedValue({ data: {} } as never)
      decline()

      await analyticsService.trackPageView('/test')
      await analyticsService.trackEvent('outbound', 'github', 'footer')

      expect(mockedPost).not.toHaveBeenCalled()
    })
  })

  describe('privacySignalSent', () => {
    it.each(SIGNALS)('is true under %s', (_name, decline) => {
      decline()
      expect(privacySignalSent()).toBe(true)
    })

    it('is false for an opt-out stored without a signal, which still declines', () => {
      setVisitCountingOptOut(true)
      expect(privacySignalSent()).toBe(false)
      expect(visitCountingDeclined()).toBe(true)
    })

    it('reads the values visitCountingDeclined() ignores as no signal', () => {
      for (const stub of [
        { globalPrivacyControl: false },
        { globalPrivacyControl: 'true' },
        { doNotTrack: '0' },
        { doNotTrack: 'unspecified' }
      ]) {
        vi.stubGlobal('navigator', stub)
        expect(privacySignalSent(), JSON.stringify(stub)).toBe(false)
        expect(visitCountingDeclined(), JSON.stringify(stub)).toBe(false)
      }
    })

    it('still reads Do Not Track when reading Global Privacy Control throws', () => {
      vi.stubGlobal('navigator', {
        get globalPrivacyControl(): boolean {
          throw new Error('blocked')
        },
        doNotTrack: '1'
      })
      expect(privacySignalSent()).toBe(true)
    })

    it('is false where navigator is missing or carries neither signal', () => {
      vi.stubGlobal('navigator', undefined)
      expect(privacySignalSent()).toBe(false)
      // A navigator with neither property, such as the one Node defines.
      vi.stubGlobal('navigator', { userAgent: 'Node.js/24' })
      expect(privacySignalSent()).toBe(false)
    })
  })

  describe('setVisitCountingOptOut', () => {
    it("stores '1' when switched on and removes the key when switched off", () => {
      setVisitCountingOptOut(true)
      expect(localStorage.getItem(OPT_OUT_KEY)).toBe('1')

      setVisitCountingOptOut(false)
      expect(localStorage.getItem(OPT_OUT_KEY)).toBeNull()
      expect(localStorage.length).toBe(0)
    })

    it('throws nothing and keeps nothing when storage refuses the write', () => {
      const refuse = (): never => {
        throw new DOMException('The quota has been exceeded.', 'QuotaExceededError')
      }
      vi.stubGlobal('localStorage', { getItem: () => null, setItem: refuse, removeItem: refuse })

      expect(() => setVisitCountingOptOut(true)).not.toThrow()
      expect(() => setVisitCountingOptOut(false)).not.toThrow()
      expect(visitCountingDeclined()).toBe(false)
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
