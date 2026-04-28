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

// Logger mock must be complete: storage.ts (transitively imported via
// apiClient) calls createLogger, and analyticsLogger is used by the service.
// Factory must be inlined inside vi.mock — the call is hoisted above any
// outer-scope declarations.
vi.mock('@/utils/logger', () => {
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

import apiClient from '@/api/client'
import analyticsService from '@/services/analytics'

const mockedPost = vi.mocked(apiClient.post)
const mockedGet = vi.mocked(apiClient.get)

describe('analytics service', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    sessionStorage.clear()
    localStorage.clear()
    analyticsService.setEnabled(true)
  })

  afterEach(() => {
    vi.resetAllMocks()
  })

  describe('session management', () => {
    it('reuses existing session ID', () => {
      const existingSessionId = 'session_existing_123'
      sessionStorage.setItem('analytics_session_id', existingSessionId)
      const sessionId = sessionStorage.getItem('analytics_session_id')
      expect(sessionId).toBe(existingSessionId)
    })

    it('session ID has correct format', () => {
      const sessionId = `session_${Date.now()}_abcdef123`
      sessionStorage.setItem('analytics_session_id', sessionId)
      const retrievedId = sessionStorage.getItem('analytics_session_id')
      expect(retrievedId).not.toBeNull()
      expect(String(retrievedId)).toMatch(/^session_\d+_[a-z0-9]+$/)
    })
  })

  describe('trackPageView', () => {
    it('sends page view to API', async () => {
      mockedPost.mockResolvedValue({ data: {} } as never)

      await analyticsService.trackPageView('/test', 'Test Page')

      expect(mockedPost).toHaveBeenCalled()
      const call = mockedPost.mock.calls[0]
      expect(call[0]).toContain('/api/v1/analytics/track/pageview')
      expect(call[1]).toMatchObject({
        page_path: '/test',
        page_title: 'Test Page'
      })
    })

    it('uses current path when not provided', async () => {
      mockedPost.mockResolvedValue({ data: {} } as never)

      await analyticsService.trackPageView()

      expect(mockedPost).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({ page_path: expect.any(String) })
      )
    })

    it('uses document title when not provided', async () => {
      mockedPost.mockResolvedValue({ data: {} } as never)
      document.title = 'Test Document Title'

      await analyticsService.trackPageView('/test')

      expect(mockedPost).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({ page_title: 'Test Document Title' })
      )
    })

    it('handles API errors gracefully', async () => {
      mockedPost.mockRejectedValue(new Error('API Error'))
      const { analyticsLogger } = await import('@/utils/logger')

      await expect(analyticsService.trackPageView('/test')).resolves.not.toThrow()
      expect(analyticsLogger.error).toHaveBeenCalled()
    })

    it('does not track when disabled', async () => {
      analyticsService.setEnabled(false)
      await analyticsService.trackPageView('/test')
      expect(mockedPost).not.toHaveBeenCalled()
    })
  })

  describe('trackEvent', () => {
    it('tracks events via page view with label', async () => {
      mockedPost.mockResolvedValue({ data: {} } as never)

      await analyticsService.trackEvent('click', 'button', 'submit', 1)

      expect(mockedPost).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          page_path: '/event/click/button/submit',
          page_title: 'Event: click - button'
        })
      )
    })

    it('tracks events via page view without label', async () => {
      mockedPost.mockResolvedValue({ data: {} } as never)

      await analyticsService.trackEvent('click', 'button')

      expect(mockedPost).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          page_path: '/event/click/button',
          page_title: 'Event: click - button'
        })
      )
    })

    it('tracks events without label and value', async () => {
      mockedPost.mockResolvedValue({ data: {} } as never)
      await analyticsService.trackEvent('pageview', 'home')
      expect(mockedPost).toHaveBeenCalled()
    })

    it('does not track when disabled', async () => {
      analyticsService.setEnabled(false)
      await analyticsService.trackEvent('test', 'action')
      expect(mockedPost).not.toHaveBeenCalled()
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

    it('does not log when disabled', async () => {
      const { analyticsLogger } = await import('@/utils/logger')
      vi.mocked(analyticsLogger.debug).mockClear()
      analyticsService.setEnabled(false)
      analyticsService.trackTiming('test', 'var', 100)
      expect(analyticsLogger.debug).not.toHaveBeenCalled()
    })
  })

  describe('setEnabled / isAnalyticsEnabled', () => {
    it('persists disabled state to localStorage', () => {
      analyticsService.setEnabled(false)
      expect(localStorage.getItem('analytics_enabled')).toBe('false')
      expect(analyticsService.isAnalyticsEnabled()).toBe(false)
    })

    it('persists enabled state to localStorage', () => {
      analyticsService.setEnabled(true)
      expect(localStorage.getItem('analytics_enabled')).toBe('true')
      expect(analyticsService.isAnalyticsEnabled()).toBe(true)
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
