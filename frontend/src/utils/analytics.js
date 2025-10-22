/**
 * Privacy-compliant analytics wrapper
 *
 * Supports Plausible Analytics (recommended) or Umami
 * Both are GDPR-compliant, cookie-less, and privacy-friendly
 */

class Analytics {
  constructor() {
    this.enabled = import.meta.env.VITE_ANALYTICS_ENABLED === 'true'
    this.provider = import.meta.env.VITE_ANALYTICS_PROVIDER || 'plausible' // 'plausible' or 'umami'
    this.siteId = import.meta.env.VITE_ANALYTICS_SITE_ID
    this.scriptUrl = import.meta.env.VITE_ANALYTICS_URL
  }

  /**
   * Initialize analytics
   * Loads the analytics script if enabled
   */
  init() {
    if (!this.enabled || !this.siteId) {
      console.log('[Analytics] Disabled or not configured')
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
  initPlausible() {
    const script = document.createElement('script')
    script.defer = true
    script.setAttribute('data-domain', this.siteId)
    script.src = this.scriptUrl || 'https://plausible.io/js/script.js'

    // Optional: track outbound links
    // script.src = 'https://plausible.io/js/script.outbound-links.js'

    document.head.appendChild(script)

    console.log('[Analytics] Plausible initialized for', this.siteId)
  }

  /**
   * Initialize Umami Analytics
   */
  initUmami() {
    const script = document.createElement('script')
    script.defer = true
    script.setAttribute('data-website-id', this.siteId)
    script.src = this.scriptUrl || 'https://analytics.umami.is/script.js'

    document.head.appendChild(script)

    console.log('[Analytics] Umami initialized for', this.siteId)
  }

  /**
   * Track a custom event
   *
   * @param {string} eventName - Name of the event
   * @param {object} props - Optional event properties
   */
  trackEvent(eventName, props = {}) {
    if (!this.enabled) return

    try {
      if (this.provider === 'plausible' && window.plausible) {
        window.plausible(eventName, { props })
      } else if (this.provider === 'umami' && window.umami) {
        window.umami.track(eventName, props)
      }
    } catch (error) {
      console.warn('[Analytics] Failed to track event:', error)
    }
  }

  /**
   * Track page view (automatic with Plausible/Umami in SPA mode)
   *
   * @param {string} path - Page path
   */
  trackPageView(path) {
    if (!this.enabled) return

    try {
      if (this.provider === 'plausible' && window.plausible) {
        window.plausible('pageview', { u: window.location.origin + path })
      } else if (this.provider === 'umami' && window.umami) {
        window.umami.track(props => ({ ...props, url: path }))
      }
    } catch (error) {
      console.warn('[Analytics] Failed to track pageview:', error)
    }
  }

  /**
   * Track outbound link click
   *
   * @param {string} url - Destination URL
   */
  trackOutboundLink(url) {
    this.trackEvent('Outbound Link Click', { url })
  }

  /**
   * Track file download
   *
   * @param {string} filename - Downloaded file name
   */
  trackDownload(filename) {
    this.trackEvent('File Download', { filename })
  }

  /**
   * Track error (for monitoring purposes)
   *
   * @param {string} errorMessage - Error message
   * @param {string} errorType - Type of error
   */
  trackError(errorMessage, errorType = 'Unknown') {
    this.trackEvent('Error', {
      message: errorMessage,
      type: errorType
    })
  }
}

// Export singleton instance
export const analytics = new Analytics()

// Convenience exports
export const trackEvent = (name, props) => analytics.trackEvent(name, props)
export const trackPageView = (path) => analytics.trackPageView(path)
export const trackOutboundLink = (url) => analytics.trackOutboundLink(url)
export const trackDownload = (filename) => analytics.trackDownload(filename)

export default analytics
