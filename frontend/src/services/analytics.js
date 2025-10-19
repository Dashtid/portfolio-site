/**
 * Analytics service for tracking page views and user interactions
 */
import axios from 'axios'

const API_URL = 'http://localhost:8001/api/v1/analytics'

class AnalyticsService {
  constructor() {
    this.sessionId = this.getOrCreateSessionId()
    this.isEnabled = true // Can be controlled by user preference
  }

  /**
   * Get or create a session ID for the current visitor
   */
  getOrCreateSessionId() {
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
  async trackPageView(pagePath, pageTitle) {
    if (!this.isEnabled) return

    try {
      const data = {
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
      console.error('Failed to track page view:', error)
    }
  }

  /**
   * Track custom events (e.g., button clicks, form submissions)
   */
  async trackEvent(category, action, label = null, value = null) {
    if (!this.isEnabled) return

    try {
      const data = {
        category,
        action,
        label,
        value,
        session_id: this.sessionId
      }

      // For now, we can track this as a special page view
      await this.trackPageView(
        `/event/${category}/${action}`,
        `Event: ${category} - ${action}`
      )
    } catch (error) {
      console.error('Failed to track event:', error)
    }
  }

  /**
   * Track timing (e.g., page load time)
   */
  trackTiming(category, variable, time, label = null) {
    if (!this.isEnabled) return

    // Store timing data for potential batch sending
    const timingData = {
      category,
      variable,
      time,
      label,
      timestamp: new Date().toISOString()
    }

    // Could be sent to backend or stored locally
    console.log('Timing tracked:', timingData)
  }

  /**
   * Enable or disable analytics tracking
   */
  setEnabled(enabled) {
    this.isEnabled = enabled
    localStorage.setItem('analytics_enabled', enabled ? 'true' : 'false')
  }

  /**
   * Check if analytics is enabled
   */
  isAnalyticsEnabled() {
    const stored = localStorage.getItem('analytics_enabled')
    return stored !== 'false' // Default to true if not set
  }

  /**
   * Get analytics summary (admin only)
   */
  async getAnalyticsSummary(days = 30) {
    try {
      const response = await axios.get(`${API_URL}/stats/summary`, {
        params: { days }
      })
      return response.data
    } catch (error) {
      console.error('Failed to get analytics summary:', error)
      return null
    }
  }

  /**
   * Get visitor statistics (admin only)
   */
  async getVisitorStats(days = 7) {
    try {
      const response = await axios.get(`${API_URL}/stats/visitors`, {
        params: { days }
      })
      return response.data
    } catch (error) {
      console.error('Failed to get visitor stats:', error)
      return null
    }
  }
}

// Export singleton instance
export default new AnalyticsService()