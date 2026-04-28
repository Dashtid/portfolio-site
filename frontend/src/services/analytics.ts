/**
 * Analytics service for tracking page views and reading admin stats.
 *
 * All HTTP goes through apiClient so requests pick up auth interceptors,
 * the unified base URL, and the shared error/refresh handling. Types
 * mirror the Pydantic schemas in backend/app/schemas/analytics.py.
 */
import apiClient from '../api/client'
import { analyticsLogger } from '../utils/logger'

const ENDPOINT = '/api/v1/analytics'

interface PageViewData {
  page_path: string
  page_title: string
  referrer: string | null
  visitor_id: string
}

export interface TopPage {
  path: string
  title: string | null
  views: number
}

export interface DailyView {
  date: string
  views: number
}

export interface AnalyticsSummary {
  total_views: number
  unique_visitors: number
  avg_session_duration: number
  top_pages: TopPage[]
  daily_views: DailyView[]
  period_days: number
}

export interface TopCountry {
  country: string
  count: number
}

export interface VisitorStats {
  total_sessions: number
  new_visitors: number
  returning_visitors: number
  avg_session_duration: number | null
  bounce_rate: number | null
  top_countries: TopCountry[]
  period_days: number
}

class AnalyticsService {
  private isEnabled: boolean

  constructor() {
    this.getOrCreateSessionId()
    const stored =
      typeof localStorage !== 'undefined' ? localStorage.getItem('analytics_enabled') : null
    this.isEnabled = stored !== 'false'
  }

  private getOrCreateSessionId(): string {
    if (typeof sessionStorage === 'undefined') return ''
    let sessionId = sessionStorage.getItem('analytics_session_id')
    if (!sessionId) {
      sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
      sessionStorage.setItem('analytics_session_id', sessionId)
    }
    return sessionId
  }

  async trackPageView(pagePath?: string, pageTitle?: string): Promise<void> {
    if (!this.isEnabled) return

    try {
      const data: PageViewData = {
        page_path: pagePath || window.location.pathname,
        page_title: pageTitle || document.title,
        referrer: document.referrer || null,
        visitor_id: this.getOrCreateSessionId()
      }
      await apiClient.post(`${ENDPOINT}/track/pageview`, data)
    } catch (error) {
      analyticsLogger.error('Failed to track page view:', error)
    }
  }

  /**
   * Track a synthetic event as a page view until a dedicated event endpoint
   * exists on the backend. The event path follows GA4-style conventions.
   */
  async trackEvent(
    category: string,
    action: string,
    label: string | null = null,
    _value: number | null = null
  ): Promise<void> {
    if (!this.isEnabled) return

    try {
      await this.trackPageView(
        `/event/${category}/${action}${label ? `/${label}` : ''}`,
        `Event: ${category} - ${action}`
      )
    } catch (error) {
      analyticsLogger.error('Failed to track event:', error)
    }
  }

  trackTiming(category: string, variable: string, time: number, label: string | null = null): void {
    if (!this.isEnabled) return
    analyticsLogger.debug('Timing tracked:', {
      category,
      variable,
      time,
      label,
      timestamp: new Date().toISOString()
    })
  }

  setEnabled(enabled: boolean): void {
    this.isEnabled = enabled
    localStorage.setItem('analytics_enabled', enabled ? 'true' : 'false')
  }

  isAnalyticsEnabled(): boolean {
    return this.isEnabled
  }

  /**
   * Get analytics summary (admin-only endpoint, requires auth cookie).
   * Returns null on failure so consumers can show an empty state.
   */
  async getAnalyticsSummary(days: number = 30): Promise<AnalyticsSummary | null> {
    try {
      const response = await apiClient.get<AnalyticsSummary>(`${ENDPOINT}/stats/summary`, {
        params: { days }
      })
      return response.data
    } catch (error) {
      analyticsLogger.error('Failed to get analytics summary:', error)
      return null
    }
  }

  /**
   * Get visitor statistics (admin-only endpoint, requires auth cookie).
   */
  async getVisitorStats(days: number = 7): Promise<VisitorStats | null> {
    try {
      const response = await apiClient.get<VisitorStats>(`${ENDPOINT}/stats/visitors`, {
        params: { days }
      })
      return response.data
    } catch (error) {
      analyticsLogger.error('Failed to get visitor stats:', error)
      return null
    }
  }
}

export default new AnalyticsService()
