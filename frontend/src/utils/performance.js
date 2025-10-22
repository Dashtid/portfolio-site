/**
 * Performance monitoring utility
 *
 * Tracks Core Web Vitals (LCP, FID, CLS) and other performance metrics
 * Uses web-vitals library for accurate measurement
 */

class PerformanceMonitor {
  constructor() {
    this.enabled = import.meta.env.VITE_METRICS_ENABLED === 'true'
    this.apiEndpoint = import.meta.env.VITE_API_URL + '/api/v1/performance' || '/api/v1/performance'
    this.metrics = {}
  }

  /**
   * Initialize performance monitoring
   */
  async init() {
    if (!this.enabled) {
      console.log('[Performance] Monitoring disabled')
      return
    }

    // Track Core Web Vitals
    this.trackCoreWebVitals()

    // Track navigation timing
    this.trackNavigationTiming()

    // Track resource timing
    this.trackResourceTiming()

    console.log('[Performance] Monitoring initialized')
  }

  /**
   * Track Core Web Vitals using Performance Observer API
   */
  trackCoreWebVitals() {
    // Largest Contentful Paint (LCP)
    this.observeMetric('largest-contentful-paint', (entry) => {
      this.recordMetric('LCP', entry.renderTime || entry.loadTime)
    })

    // First Input Delay (FID) - only available with user interaction
    this.observeMetric('first-input', (entry) => {
      this.recordMetric('FID', entry.processingStart - entry.startTime)
    })

    // Cumulative Layout Shift (CLS)
    let clsValue = 0
    this.observeMetric('layout-shift', (entry) => {
      if (!entry.hadRecentInput) {
        clsValue += entry.value
        this.recordMetric('CLS', clsValue)
      }
    })

    // Time to First Byte (TTFB)
    this.observeMetric('navigation', (entry) => {
      this.recordMetric('TTFB', entry.responseStart - entry.requestStart)
    })
  }

  /**
   * Observe performance metrics using PerformanceObserver
   */
  observeMetric(type, callback) {
    try {
      const observer = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          callback(entry)
        }
      })

      observer.observe({ type, buffered: true })
    } catch (err) {
      // PerformanceObserver not supported or metric type not available
      if (import.meta.env.DEV) {
        console.warn(`[Performance] Cannot observe ${type}:`, err.message)
      }
    }
  }

  /**
   * Track Navigation Timing API metrics
   */
  trackNavigationTiming() {
    window.addEventListener('load', () => {
      const navigation = performance.getEntriesByType('navigation')[0]

      if (navigation) {
        this.recordMetric('DNS', navigation.domainLookupEnd - navigation.domainLookupStart)
        this.recordMetric('TCP', navigation.connectEnd - navigation.connectStart)
        this.recordMetric('Request', navigation.responseStart - navigation.requestStart)
        this.recordMetric('Response', navigation.responseEnd - navigation.responseStart)
        this.recordMetric('DOM_Processing', navigation.domComplete - navigation.domInteractive)
        this.recordMetric('Load_Complete', navigation.loadEventEnd - navigation.loadEventStart)
        this.recordMetric('Total_Load_Time', navigation.loadEventEnd - navigation.fetchStart)

        // Send metrics to backend
        this.sendMetrics()
      }
    })
  }

  /**
   * Track Resource Timing (images, scripts, styles)
   */
  trackResourceTiming() {
    window.addEventListener('load', () => {
      const resources = performance.getEntriesByType('resource')

      const resourceStats = {
        images: [],
        scripts: [],
        stylesheets: [],
        other: []
      }

      resources.forEach((resource) => {
        const duration = resource.responseEnd - resource.startTime
        const data = {
          name: resource.name,
          duration: Math.round(duration),
          size: resource.transferSize,
          type: resource.initiatorType
        }

        if (resource.initiatorType === 'img') {
          resourceStats.images.push(data)
        } else if (resource.initiatorType === 'script') {
          resourceStats.scripts.push(data)
        } else if (resource.initiatorType === 'link') {
          resourceStats.stylesheets.push(data)
        } else {
          resourceStats.other.push(data)
        }
      })

      // Calculate averages
      this.recordMetric('Avg_Image_Load', this.calculateAverage(resourceStats.images))
      this.recordMetric('Avg_Script_Load', this.calculateAverage(resourceStats.scripts))
      this.recordMetric('Avg_Style_Load', this.calculateAverage(resourceStats.stylesheets))
    })
  }

  /**
   * Calculate average duration from resource array
   */
  calculateAverage(resources) {
    if (resources.length === 0) return 0
    const sum = resources.reduce((acc, r) => acc + r.duration, 0)
    return Math.round(sum / resources.length)
  }

  /**
   * Record a performance metric
   */
  recordMetric(name, value) {
    const roundedValue = Math.round(value)
    this.metrics[name] = roundedValue

    if (import.meta.env.DEV) {
      console.log(`[Performance] ${name}: ${roundedValue}ms`)
    }
  }

  /**
   * Send metrics to backend
   */
  async sendMetrics() {
    if (!this.enabled) return

    try {
      await fetch(this.apiEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          metrics: this.metrics,
          url: window.location.href,
          userAgent: navigator.userAgent,
          timestamp: new Date().toISOString(),
        }),
      })
    } catch (err) {
      if (import.meta.env.DEV) {
        console.warn('[Performance] Failed to send metrics:', err)
      }
    }
  }

  /**
   * Get current metrics
   */
  getMetrics() {
    return { ...this.metrics }
  }

  /**
   * Manually measure a custom timing
   */
  measure(name, startMark, endMark) {
    try {
      performance.measure(name, startMark, endMark)
      const measure = performance.getEntriesByName(name)[0]
      this.recordMetric(name, measure.duration)
    } catch (err) {
      console.warn(`[Performance] Failed to measure ${name}:`, err)
    }
  }

  /**
   * Mark a performance timestamp
   */
  mark(name) {
    try {
      performance.mark(name)
    } catch (err) {
      console.warn(`[Performance] Failed to mark ${name}:`, err)
    }
  }
}

// Export singleton instance
export const performanceMonitor = new PerformanceMonitor()

export default performanceMonitor
