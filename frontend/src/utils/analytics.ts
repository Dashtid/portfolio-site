/**
 * Privacy-compliant analytics wrapper
 *
 * Supports Plausible Analytics (recommended) or Umami
 * Both are GDPR-compliant, cookie-less, and privacy-friendly
 */

import { analyticsLogger } from './logger'

interface TrackingProps {
  [key: string]: string | number | boolean | undefined
}

type AnalyticsProvider = 'plausible' | 'umami'

declare global {
  interface Window {
    plausible?: (eventName: string, options?: { props?: TrackingProps; u?: string }) => void
    umami?: {
      track: (
        eventName: string | ((props: Record<string, unknown>) => Record<string, unknown>),
        props?: TrackingProps
      ) => void
    }
  }
}

class Analytics {
  private enabled: boolean
  private provider: AnalyticsProvider
  private siteId: string | undefined
  private scriptUrl: string | undefined

  constructor() {
    this.enabled = import.meta.env.VITE_ANALYTICS_ENABLED === 'true'
    this.provider = (import.meta.env.VITE_ANALYTICS_PROVIDER || 'plausible') as AnalyticsProvider
    this.siteId = import.meta.env.VITE_ANALYTICS_SITE_ID
    this.scriptUrl = import.meta.env.VITE_ANALYTICS_URL
  }

  /**
   * Initialize analytics
   * Loads the analytics script if enabled
   */
  init(): void {
    if (!this.enabled || !this.siteId) {
      analyticsLogger.log('Disabled or not configured')
      return
    }

    if (this.provider === 'plausible') {
      this.initPlausible()
    } else if (this.provider === 'umami') {
      this.initUmami()
    }
  }

  /**
   * Initialize Plausible Analytics
   */
  private initPlausible(): void {
    const script = document.createElement('script')
    script.defer = true
    script.setAttribute('data-domain', this.siteId!)
    script.src = this.scriptUrl || 'https://plausible.io/js/script.js'

    // Optional: track outbound links
    // script.src = 'https://plausible.io/js/script.outbound-links.js'

    document.head.appendChild(script)

    analyticsLogger.log('Plausible initialized for', this.siteId)
  }

  /**
   * Initialize Umami Analytics
   */
  private initUmami(): void {
    const script = document.createElement('script')
    script.defer = true
    script.setAttribute('data-website-id', this.siteId!)
    script.src = this.scriptUrl || 'https://analytics.umami.is/script.js'

    document.head.appendChild(script)

    analyticsLogger.log('Umami initialized for', this.siteId)
  }

  /**
   * Track a custom event
   *
   * @param eventName - Name of the event
   * @param props - Optional event properties
   */
  trackEvent(eventName: string, props: TrackingProps = {}): void {
    if (!this.enabled) return

    try {
      if (this.provider === 'plausible' && window.plausible) {
        window.plausible(eventName, { props })
      } else if (this.provider === 'umami' && window.umami) {
        window.umami.track(eventName, props)
      }
    } catch (error) {
      analyticsLogger.warn('Failed to track event:', error)
    }
  }

  /**
   * Track page view (automatic with Plausible/Umami in SPA mode)
   *
   * @param path - Page path
   */
  trackPageView(path: string): void {
    if (!this.enabled) return

    try {
      if (this.provider === 'plausible' && window.plausible) {
        window.plausible('pageview', { u: window.location.origin + path })
      } else if (this.provider === 'umami' && window.umami) {
        window.umami.track(props => ({ ...props, url: path }))
      }
    } catch (error) {
      analyticsLogger.warn('Failed to track pageview:', error)
    }
  }

  /**
   * Track outbound link click
   *
   * @param url - Destination URL
   */
  trackOutboundLink(url: string): void {
    this.trackEvent('Outbound Link Click', { url })
  }

  /**
   * Track file download
   *
   * @param filename - Downloaded file name
   */
  trackDownload(filename: string): void {
    this.trackEvent('File Download', { filename })
  }

  /**
   * Track error (for monitoring purposes)
   *
   * @param errorMessage - Error message
   * @param errorType - Type of error
   */
  trackError(errorMessage: string, errorType: string = 'Unknown'): void {
    this.trackEvent('Error', {
      message: errorMessage,
      type: errorType
    })
  }
}

// Export singleton instance
export const analytics = new Analytics()

// Convenience exports
export const trackEvent = (name: string, props?: TrackingProps): void =>
  analytics.trackEvent(name, props)
export const trackPageView = (path: string): void => analytics.trackPageView(path)
export const trackOutboundLink = (url: string): void => analytics.trackOutboundLink(url)
export const trackDownload = (filename: string): void => analytics.trackDownload(filename)

export default analytics
