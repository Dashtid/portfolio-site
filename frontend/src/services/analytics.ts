/**
 * Analytics service for tracking page views and user interactions
 */
import axios, { type AxiosResponse } from 'axios'
import { analyticsLogger } from '../utils/logger'

// Get API URL from environment variables
const BASE_API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
const API_URL = `${BASE_API_URL}/api/v1/analytics`

interface PageViewData {
  page_path: string
  page_title: string
  referrer: string | null
}

interface TimingData {
  category: string
  variable: string
  time: number
  label: string | null
  timestamp: string
}

interface AnalyticsSummary {
  [key: string]: unknown
}

interface VisitorStats {
  [key: string]: unknown
}

class AnalyticsService {
  private isEnabled: boolean

  constructor() {
    // Initialize session ID in storage for potential future use
    this.getOrCreateSessionId()
    this.isEnabled = true // Can be controlled by user preference
  }

  /**
   * Get or create a session ID for the current visitor
   */
  private getOrCreateSessionId(): string {
    let sessionId = sessionStorage.getItem('analytics_session_id')
    if (!sessionId) {
      sessionId = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
      sessionStorage.setItem('analytics_session_id', sessionId)
    }
    return sessionId
  }

  /**
   * Track a page view
   */
  async trackPageView(pagePath?: string, pageTitle?: string): Promise<void> {
    if (!this.isEnabled) return

    try {
      const data: PageViewData = {
        page_path: pagePath || window.location.pathname,
        page_title: pageTitle || document.title,
        referrer: document.referrer || null
      }

      await axios.post(`${API_URL}/track/pageview`, data, {
        headers: {
          'Content-Type': 'application/json'
        }
      })
    } catch (error) {
      analyticsLogger.error('Failed to track page view:', error)
    }
  }

  /**
   * Track custom events (e.g., button clicks, form submissions)
   *
   * Events are tracked as synthetic page views until a dedicated event endpoint
   * is implemented on the backend. The event data format follows GA4 conventions.
   */
  async trackEvent(
    category: string,
    action: string,
    label: string | null = null,
    _value: number | null = null
  ): Promise<void> {
    if (!this.isEnabled) return

    try {
      // Track as a synthetic page view with event path
      await this.trackPageView(
        `/event/${category}/${action}${label ? `/${label}` : ''}`,
        `Event: ${category} - ${action}`
      )
    } catch (error) {
      analyticsLogger.error('Failed to track event:', error)
    }
  }

  /**
   * Track timing (e.g., page load time)
   */
  trackTiming(category: string, variable: string, time: number, label: string | null = null): void {
    if (!this.isEnabled) return

    // Store timing data for potential batch sending
    const timingData: TimingData = {
      category,
      variable,
      time,
      label,
      timestamp: new Date().toISOString()
    }

    // Could be sent to backend or stored locally
    analyticsLogger.debug('Timing tracked:', timingData)
  }

  /**
   * Enable or disable analytics tracking
   */
  setEnabled(enabled: boolean): void {
    this.isEnabled = enabled
    localStorage.setItem('analytics_enabled', enabled ? 'true' : 'false')
  }

  /**
   * Check if analytics is enabled
   */
  isAnalyticsEnabled(): boolean {
    const stored = localStorage.getItem('analytics_enabled')
    return stored !== 'false' // Default to true if not set
  }

  /**
   * Get analytics summary (admin only)
   */
  async getAnalyticsSummary(days: number = 30): Promise<AnalyticsSummary | null> {
    try {
      const response: AxiosResponse<AnalyticsSummary> = await axios.get(
        `${API_URL}/stats/summary`,
        {
          params: { days }
        }
      )
      return response.data
    } catch (error) {
      analyticsLogger.error('Failed to get analytics summary:', error)
      return null
    }
  }

  /**
   * Get visitor statistics (admin only)
   */
  async getVisitorStats(days: number = 7): Promise<VisitorStats | null> {
    try {
      const response: AxiosResponse<VisitorStats> = await axios.get(`${API_URL}/stats/visitors`, {
        params: { days }
      })
      return response.data
    } catch (error) {
      analyticsLogger.error('Failed to get visitor stats:', error)
      return null
    }
  }
}

// Export singleton instance
export default new AnalyticsService()
