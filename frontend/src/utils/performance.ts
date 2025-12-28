/**
 * Performance monitoring utility
 *
 * Tracks Core Web Vitals (LCP, FID, CLS) and other performance metrics
 * Uses web-vitals library for accurate measurement
 */

interface PerformanceMetrics {
  [key: string]: number
}

interface MetricEntry {
  renderTime?: number
  loadTime?: number
  processingStart?: number
  startTime?: number
  value?: number
  responseStart?: number
  requestStart?: number
}

interface ResourceData {
  name: string
  duration: number
  size: number
  type: string
}

interface ResourceStats {
  images: ResourceData[]
  scripts: ResourceData[]
  stylesheets: ResourceData[]
  other: ResourceData[]
}

interface LayoutShift extends PerformanceEntry {
  hadRecentInput: boolean
  value: number
}

class PerformanceMonitor {
  private enabled: boolean
  private apiEndpoint: string
  private metrics: PerformanceMetrics
  private initialized: boolean = false
  private observers: PerformanceObserver[] = []
  private loadHandler: (() => void) | null = null

  constructor() {
    this.enabled = import.meta.env.VITE_METRICS_ENABLED === 'true'
    this.apiEndpoint =
      (import.meta.env.VITE_API_URL ?? '') + '/api/v1/performance' || '/api/v1/performance'
    this.metrics = {}
  }

  /**
   * Initialize performance monitoring
   */
  async init(): Promise<void> {
    // Prevent duplicate initialization and listener leaks
    if (this.initialized) {
      if (import.meta.env.DEV) {
        console.log('[Performance] Already initialized, skipping')
      }
      return
    }

    if (!this.enabled) {
      if (import.meta.env.DEV) {
        console.log('[Performance] Monitoring disabled')
      }
      return
    }

    this.initialized = true

    // Track Core Web Vitals
    this.trackCoreWebVitals()

    // Track navigation timing
    this.trackNavigationTiming()

    // Track resource timing
    this.trackResourceTiming()

    if (import.meta.env.DEV) {
      console.log('[Performance] Monitoring initialized')
    }
  }

  /**
   * Cleanup all observers and listeners
   */
  destroy(): void {
    // Disconnect all performance observers
    this.observers.forEach(observer => {
      try {
        observer.disconnect()
      } catch {
        // Ignore errors during cleanup
      }
    })
    this.observers = []

    // Remove load event listener
    if (this.loadHandler) {
      window.removeEventListener('load', this.loadHandler)
      this.loadHandler = null
    }

    this.initialized = false

    if (import.meta.env.DEV) {
      console.log('[Performance] Monitoring destroyed')
    }
  }

  /**
   * Track Core Web Vitals using Performance Observer API
   */
  private trackCoreWebVitals(): void {
    // Largest Contentful Paint (LCP)
    this.observeMetric('largest-contentful-paint', entry => {
      const metricEntry = entry as MetricEntry
      this.recordMetric('LCP', metricEntry.renderTime || metricEntry.loadTime || 0)
    })

    // First Input Delay (FID) - only available with user interaction
    this.observeMetric('first-input', entry => {
      const metricEntry = entry as MetricEntry
      this.recordMetric('FID', (metricEntry.processingStart || 0) - (metricEntry.startTime || 0))
    })

    // Cumulative Layout Shift (CLS)
    let clsValue = 0
    this.observeMetric('layout-shift', entry => {
      const layoutShiftEntry = entry as LayoutShift
      if (!layoutShiftEntry.hadRecentInput) {
        clsValue += layoutShiftEntry.value
        this.recordMetric('CLS', clsValue)
      }
    })

    // Time to First Byte (TTFB)
    this.observeMetric('navigation', entry => {
      const navEntry = entry as PerformanceNavigationTiming
      this.recordMetric('TTFB', navEntry.responseStart - navEntry.requestStart)
    })
  }

  /**
   * Observe performance metrics using PerformanceObserver
   */
  private observeMetric(type: string, callback: (entry: PerformanceEntry) => void): void {
    try {
      const observer = new PerformanceObserver(list => {
        for (const entry of list.getEntries()) {
          callback(entry)
        }
      })

      observer.observe({ type, buffered: true })

      // Store observer reference for cleanup
      this.observers.push(observer)
    } catch (err) {
      // PerformanceObserver not supported or metric type not available
      if (import.meta.env.DEV) {
        const message = err instanceof Error ? err.message : String(err)
        console.warn(`[Performance] Cannot observe ${type}:`, message)
      }
    }
  }

  /**
   * Track Navigation Timing API metrics
   */
  private trackNavigationTiming(): void {
    // Use a single load handler that's stored for cleanup
    this.loadHandler = () => {
      this.collectNavigationMetrics()
      this.collectResourceMetrics()
    }

    window.addEventListener('load', this.loadHandler)
  }

  /**
   * Collect navigation timing metrics
   */
  private collectNavigationMetrics(): void {
    const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming

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
  }

  /**
   * Track Resource Timing (images, scripts, styles)
   * Note: trackResourceTiming is now handled by the single load handler
   */
  private trackResourceTiming(): void {
    // Resource timing is now collected in the single load handler
    // This method is kept for backward compatibility but does nothing
    // The actual collection happens in collectResourceMetrics()
  }

  /**
   * Collect resource timing metrics
   */
  private collectResourceMetrics(): void {
    const resources = performance.getEntriesByType('resource') as PerformanceResourceTiming[]

    const resourceStats: ResourceStats = {
      images: [],
      scripts: [],
      stylesheets: [],
      other: []
    }

    resources.forEach(resource => {
      const duration = resource.responseEnd - resource.startTime
      const data: ResourceData = {
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
  }

  /**
   * Calculate average duration from resource array
   */
  private calculateAverage(resources: ResourceData[]): number {
    if (resources.length === 0) return 0
    const sum = resources.reduce((acc, r) => acc + r.duration, 0)
    return Math.round(sum / resources.length)
  }

  /**
   * Record a performance metric
   */
  private recordMetric(name: string, value: number): void {
    const roundedValue = Math.round(value)
    this.metrics[name] = roundedValue

    if (import.meta.env.DEV) {
      console.log(`[Performance] ${name}: ${roundedValue}ms`)
    }
  }

  /**
   * Send metrics to backend
   */
  private async sendMetrics(): Promise<void> {
    if (!this.enabled) return

    try {
      await fetch(this.apiEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          metrics: this.metrics,
          url: window.location.href,
          userAgent: navigator.userAgent,
          timestamp: new Date().toISOString()
        })
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
  getMetrics(): PerformanceMetrics {
    return { ...this.metrics }
  }

  /**
   * Manually measure a custom timing
   */
  measure(name: string, startMark?: string, endMark?: string): void {
    try {
      performance.measure(name, startMark, endMark)
      const measure = performance.getEntriesByName(name)[0] as PerformanceMeasure
      this.recordMetric(name, measure.duration)
    } catch (err) {
      if (import.meta.env.DEV) {
        console.warn(`[Performance] Failed to measure ${name}:`, err)
      }
    }
  }

  /**
   * Mark a performance timestamp
   */
  mark(name: string): void {
    try {
      performance.mark(name)
    } catch (err) {
      if (import.meta.env.DEV) {
        console.warn(`[Performance] Failed to mark ${name}:`, err)
      }
    }
  }
}

// Export singleton instance
export const performanceMonitor = new PerformanceMonitor()

export default performanceMonitor
