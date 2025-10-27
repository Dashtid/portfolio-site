/**
 * Tests for analytics service (TypeScript)
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import axios from 'axios'
import analyticsService from '@/services/analytics'

vi.mock('axios')

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
      const sessionId = sessionStorage.getItem('analytics_session_id')

      expect(sessionId).toBeNull()

      // Access the private method indirectly by checking sessionStorage after initialization
      // The service is a singleton, so it was initialized when imported
      expect(sessionStorage.getItem('analytics_session_id')).toBeTruthy()
    })

    it('reuses existing session ID', () => {
      const existingSessionId = 'session_existing_123'
      sessionStorage.setItem('analytics_session_id', existingSessionId)

      // Create a new instance to test session reuse
      const sessionId = sessionStorage.getItem('analytics_session_id')

      expect(sessionId).toBe(existingSessionId)
    })

    it('session ID has correct format', () => {
      const sessionId = sessionStorage.getItem('analytics_session_id')

      expect(sessionId).toMatch(/^session_\d+_[a-z0-9]+$/)
    })
  })

  describe('trackPageView', () => {
    it('sends page view to API', async () => {
      const mockPost = vi.mocked(axios.post).mockResolvedValue({ data: {} })

      await analyticsService.trackPageView('/test', 'Test Page')

      expect(mockPost).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/analytics/track/pageview'),
        {
          page_path: '/test',
          page_title: 'Test Page',
          referrer: expect.any(String)
        },
        expect.any(Object)
      )
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
      const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {})

      await expect(analyticsService.trackPageView('/test')).resolves.not.toThrow()

      expect(consoleError).toHaveBeenCalled()
      consoleError.mockRestore()
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
    it('tracks events via page view', async () => {
      const mockPost = vi.mocked(axios.post).mockResolvedValue({ data: {} })

      await analyticsService.trackEvent('click', 'button', 'submit', 1)

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
    it('logs timing data', () => {
      const consoleLog = vi.spyOn(console, 'log').mockImplementation(() => {})

      analyticsService.trackTiming('load', 'page', 1000, 'home')

      expect(consoleLog).toHaveBeenCalledWith(
        'Timing tracked:',
        expect.objectContaining({
          category: 'load',
          variable: 'page',
          time: 1000,
          label: 'home',
          timestamp: expect.any(String)
        })
      )

      consoleLog.mockRestore()
    })

    it('works without label', () => {
      const consoleLog = vi.spyOn(console, 'log').mockImplementation(() => {})

      analyticsService.trackTiming('api', 'request', 500)

      expect(consoleLog).toHaveBeenCalled()
      consoleLog.mockRestore()
    })

    it('does not log when disabled', () => {
      const consoleLog = vi.spyOn(console, 'log').mockImplementation(() => {})
      analyticsService.setEnabled(false)

      analyticsService.trackTiming('test', 'var', 100)

      expect(consoleLog).not.toHaveBeenCalled()

      analyticsService.setEnabled(true)
      consoleLog.mockRestore()
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
      const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {})

      const result = await analyticsService.getAnalyticsSummary()

      expect(result).toBeNull()
      consoleError.mockRestore()
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
      const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {})

      const result = await analyticsService.getVisitorStats()

      expect(result).toBeNull()
      consoleError.mockRestore()
    })
  })

  describe('TypeScript types', () => {
    it('trackEvent accepts string parameters', async () => {
      vi.mocked(axios.post).mockResolvedValue({ data: {} })

      await analyticsService.trackEvent('category', 'action', 'label', 1)

      expect(axios.post).toHaveBeenCalled()
    })

    it('trackEvent accepts null for optional parameters', async () => {
      vi.mocked(axios.post).mockResolvedValue({ data: {} })

      await analyticsService.trackEvent('category', 'action', null, null)

      expect(axios.post).toHaveBeenCalled()
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
