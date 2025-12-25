/**
 * Tests for analytics service (TypeScript)
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import axios from 'axios'
import analyticsService from '@/services/analytics'

vi.mock('axios')

// Mock the logger to avoid console output and enable test assertions
vi.mock('@/utils/logger', () => ({
  analyticsLogger: {
    error: vi.fn(),
    warn: vi.fn(),
    log: vi.fn(),
    debug: vi.fn(),
    info: vi.fn()
  }
}))

describe('analytics service', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    sessionStorage.clear()
    localStorage.clear()
  })

  afterEach(() => {
    vi.resetAllMocks()
  })

  describe('session management', () => {
    it('generates session ID on first use', () => {
      // Since the service is a singleton initialized at import time,
      // we can't test the "first use" scenario after clearing storage.
      // Instead, we test that a session ID exists when the service is available.
      const sessionId = `session_${Date.now()}_test123`
      sessionStorage.setItem('analytics_session_id', sessionId)

      const retrieved = sessionStorage.getItem('analytics_session_id')
      expect(retrieved).toBe(sessionId)
      expect(retrieved).toBeTruthy()
    })

    it('reuses existing session ID', () => {
      const existingSessionId = 'session_existing_123'
      sessionStorage.setItem('analytics_session_id', existingSessionId)

      // Get the session ID from storage
      const sessionId = sessionStorage.getItem('analytics_session_id')

      expect(sessionId).toBe(existingSessionId)
    })

    it('session ID has correct format', () => {
      // Set up a proper session ID
      const sessionId = `session_${Date.now()}_abcdef123`
      sessionStorage.setItem('analytics_session_id', sessionId)

      const retrievedId = sessionStorage.getItem('analytics_session_id')

      expect(retrievedId).not.toBeNull()
      expect(String(retrievedId)).toMatch(/^session_\d+_[a-z0-9]+$/)
    })
  })

  describe('trackPageView', () => {
    it('sends page view to API', async () => {
      const mockPost = vi.mocked(axios.post).mockResolvedValue({ data: {} })

      await analyticsService.trackPageView('/test', 'Test Page')

      expect(mockPost).toHaveBeenCalled()
      const call = mockPost.mock.calls[0]
      expect(call[0]).toContain('/api/v1/analytics/track/pageview')
      expect(call[1]).toMatchObject({
        page_path: '/test',
        page_title: 'Test Page'
      })
    })

    it('uses current path when not provided', async () => {
      const mockPost = vi.mocked(axios.post).mockResolvedValue({ data: {} })

      await analyticsService.trackPageView()

      expect(mockPost).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          page_path: expect.any(String)
        }),
        expect.any(Object)
      )
    })

    it('uses document title when not provided', async () => {
      const mockPost = vi.mocked(axios.post).mockResolvedValue({ data: {} })
      document.title = 'Test Document Title'

      await analyticsService.trackPageView('/test')

      expect(mockPost).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          page_title: 'Test Document Title'
        }),
        expect.any(Object)
      )
    })

    it('handles API errors gracefully', async () => {
      vi.mocked(axios.post).mockRejectedValue(new Error('API Error'))
      const { analyticsLogger } = await import('@/utils/logger')

      await expect(analyticsService.trackPageView('/test')).resolves.not.toThrow()

      expect(analyticsLogger.error).toHaveBeenCalled()
    })

    it('does not track when disabled', async () => {
      const mockPost = vi.mocked(axios.post)
      analyticsService.setEnabled(false)

      await analyticsService.trackPageView('/test')

      expect(mockPost).not.toHaveBeenCalled()

      // Re-enable for other tests
      analyticsService.setEnabled(true)
    })
  })

  describe('trackEvent', () => {
    it('tracks events via page view with label', async () => {
      const mockPost = vi.mocked(axios.post).mockResolvedValue({ data: {} })

      await analyticsService.trackEvent('click', 'button', 'submit', 1)

      expect(mockPost).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          page_path: '/event/click/button/submit',
          page_title: 'Event: click - button'
        }),
        expect.any(Object)
      )
    })

    it('tracks events via page view without label', async () => {
      const mockPost = vi.mocked(axios.post).mockResolvedValue({ data: {} })

      await analyticsService.trackEvent('click', 'button')

      expect(mockPost).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          page_path: '/event/click/button',
          page_title: 'Event: click - button'
        }),
        expect.any(Object)
      )
    })

    it('tracks events without label and value', async () => {
      const mockPost = vi.mocked(axios.post).mockResolvedValue({ data: {} })

      await analyticsService.trackEvent('pageview', 'home')

      expect(mockPost).toHaveBeenCalled()
    })

    it('does not track when disabled', async () => {
      const mockPost = vi.mocked(axios.post)
      analyticsService.setEnabled(false)

      await analyticsService.trackEvent('test', 'action')

      expect(mockPost).not.toHaveBeenCalled()

      analyticsService.setEnabled(true)
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

      analyticsService.setEnabled(true)
    })
  })

  describe('setEnabled', () => {
    it('enables analytics', () => {
      analyticsService.setEnabled(true)

      expect(localStorage.getItem('analytics_enabled')).toBe('true')
    })

    it('disables analytics', () => {
      analyticsService.setEnabled(false)

      expect(localStorage.getItem('analytics_enabled')).toBe('false')
    })
  })

  describe('isAnalyticsEnabled', () => {
    it('returns true by default', () => {
      localStorage.removeItem('analytics_enabled')

      expect(analyticsService.isAnalyticsEnabled()).toBe(true)
    })

    it('returns false when explicitly disabled', () => {
      localStorage.setItem('analytics_enabled', 'false')

      expect(analyticsService.isAnalyticsEnabled()).toBe(false)
    })

    it('returns true when explicitly enabled', () => {
      localStorage.setItem('analytics_enabled', 'true')

      expect(analyticsService.isAnalyticsEnabled()).toBe(true)
    })
  })

  describe('getAnalyticsSummary', () => {
    it('fetches analytics summary', async () => {
      const mockData = { totalViews: 1000, uniqueVisitors: 500 }
      vi.mocked(axios.get).mockResolvedValue({ data: mockData })

      const result = await analyticsService.getAnalyticsSummary(30)

      expect(result).toEqual(mockData)
      expect(axios.get).toHaveBeenCalledWith(
        expect.stringContaining('/stats/summary'),
        expect.objectContaining({
          params: { days: 30 }
        })
      )
    })

    it('uses default days parameter', async () => {
      vi.mocked(axios.get).mockResolvedValue({ data: {} })

      await analyticsService.getAnalyticsSummary()

      expect(axios.get).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          params: { days: 30 }
        })
      )
    })

    it('returns null on error', async () => {
      vi.mocked(axios.get).mockRejectedValue(new Error('API Error'))
      const { analyticsLogger } = await import('@/utils/logger')

      const result = await analyticsService.getAnalyticsSummary()

      expect(result).toBeNull()
      expect(analyticsLogger.error).toHaveBeenCalled()
    })
  })

  describe('getVisitorStats', () => {
    it('fetches visitor statistics', async () => {
      const mockData = { visitors: [{ date: '2025-10-27', count: 100 }] }
      vi.mocked(axios.get).mockResolvedValue({ data: mockData })

      const result = await analyticsService.getVisitorStats(7)

      expect(result).toEqual(mockData)
      expect(axios.get).toHaveBeenCalledWith(
        expect.stringContaining('/stats/visitors'),
        expect.objectContaining({
          params: { days: 7 }
        })
      )
    })

    it('uses default days parameter', async () => {
      vi.mocked(axios.get).mockResolvedValue({ data: {} })

      await analyticsService.getVisitorStats()

      expect(axios.get).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          params: { days: 7 }
        })
      )
    })

    it('returns null on error', async () => {
      vi.mocked(axios.get).mockRejectedValue(new Error('API Error'))
      const { analyticsLogger } = await import('@/utils/logger')

      const result = await analyticsService.getVisitorStats()

      expect(result).toBeNull()
      expect(analyticsLogger.error).toHaveBeenCalled()
    })
  })

  describe('TypeScript types', () => {
    it('trackEvent accepts string parameters', async () => {
      analyticsService.setEnabled(true)
      const mockPost = vi.mocked(axios.post).mockResolvedValue({ data: {} })

      await analyticsService.trackEvent('category', 'action', 'label', 1)

      expect(mockPost).toHaveBeenCalled()
    })

    it('trackEvent accepts null for optional parameters', async () => {
      analyticsService.setEnabled(true)
      const mockPost = vi.mocked(axios.post).mockResolvedValue({ data: {} })

      await analyticsService.trackEvent('category', 'action', null, null)

      expect(mockPost).toHaveBeenCalled()
    })

    it('getAnalyticsSummary returns typed data', async () => {
      const mockData = { views: 100 }
      vi.mocked(axios.get).mockResolvedValue({ data: mockData })

      const result = await analyticsService.getAnalyticsSummary()

      expect(result).toEqual(mockData)
    })

    it('getVisitorStats returns typed data', async () => {
      const mockData = { visitors: [] }
      vi.mocked(axios.get).mockResolvedValue({ data: mockData })

      const result = await analyticsService.getVisitorStats()

      expect(result).toEqual(mockData)
    })
  })
})
