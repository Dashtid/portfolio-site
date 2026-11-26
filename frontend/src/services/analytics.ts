/**
 * Analytics service for tracking page views and reading admin stats.
 *
 * All HTTP goes through apiClient so requests pick up auth interceptors,
 * the unified base URL, and the shared error/refresh handling. Types
 * mirror the Pydantic schemas in backend/app/schemas/analytics.py.
 *
 * A page view sends two fields, page_path and referrer, and is not sent at
 * all while visitCountingDeclined() is true. The only browser storage the
 * module uses is the opt-out key, read or written inside a call and never
 * when the module loads (the SSG build imports it in Node).
 */
import apiClient from '../api/client'
import { analyticsLogger } from '../utils/logger'

const ENDPOINT = '/api/v1/analytics'

/** localStorage key of this browser's opt-out: '1' while it is set. */
const OPT_OUT_KEY = 'portfolio-analytics-opt-out'

/** What `read` returns, or undefined when it throws (its API missing or blocked). */
function readOrUndefined<T>(read: () => T): T | undefined {
  try {
    return read()
  } catch {
    return undefined
  }
}

/**
 * True while this browser asks not to be counted: Global Privacy Control is
 * on, Do Not Track is '1', or the opt-out is stored. Each source is read
 * again on every call, so a change applies from the next page view on, and
 * a source that is missing (navigator and localStorage in Node) or throws
 * counts as not set.
 */
export function visitCountingDeclined(): boolean {
  return (
    readOrUndefined(
      () => (navigator as Navigator & { globalPrivacyControl?: unknown }).globalPrivacyControl
    ) === true ||
    readOrUndefined(() => navigator.doNotTrack) === '1' ||
    readOrUndefined(() => localStorage.getItem(OPT_OUT_KEY)) === '1'
  )
}

/**
 * Stores this browser's opt-out (true) or removes it (false). Where storage
 * is missing or refuses the change, the call changes nothing and throws
 * nothing; visitCountingDeclined() reads back what holds.
 */
export function setVisitCountingOptOut(on: boolean): void {
  try {
    if (on) localStorage.setItem(OPT_OUT_KEY, '1')
    else localStorage.removeItem(OPT_OUT_KEY)
  } catch {
    // No storage to keep the choice in.
  }
}

interface PageViewData {
  page_path: string
  referrer: string | null
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

export interface OutboundClick {
  destination: string
  count: number
}

export interface AnalyticsSummary {
  total_views: number
  unique_visitors: number
  avg_session_duration: number
  top_pages: TopPage[]
  daily_views: DailyView[]
  period_days: number
  // Optional: older backends omit it. Aggregated outbound-link clicks, kept
  // separate from the page-view metrics above (D3-M-01).
  outbound_clicks?: OutboundClick[]
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
  async trackPageView(pagePath?: string): Promise<void> {
    if (visitCountingDeclined()) return

    try {
      const data: PageViewData = {
        page_path: pagePath || window.location.pathname,
        referrer: document.referrer || null
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
    try {
      await this.trackPageView(`/event/${category}/${action}${label ? `/${label}` : ''}`)
    } catch (error) {
      analyticsLogger.error('Failed to track event:', error)
    }
  }

  trackTiming(category: string, variable: string, time: number, label: string | null = null): void {
    analyticsLogger.debug('Timing tracked:', {
      category,
      variable,
      time,
      label,
      timestamp: new Date().toISOString()
    })
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
