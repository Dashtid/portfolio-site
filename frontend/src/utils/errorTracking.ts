/**
 * Frontend error tracking utility
 *
 * Captures and reports JavaScript errors, unhandled promise rejections,
 * and Vue component errors
 */

interface ErrorData {
  type: string
  message: string
  filename?: string
  lineno?: number
  colno?: number
  stack?: string
  componentName?: string
  errorInfo?: string
  timestamp: string
  url: string
  userAgent: string
  context?: Record<string, unknown>
}

class ErrorTracker {
  private enabled: boolean
  private apiEndpoint: string
  private errorQueue: ErrorData[]
  private maxQueueSize: number

  constructor() {
    this.enabled = import.meta.env.VITE_ERROR_TRACKING_ENABLED === 'true'
    this.apiEndpoint = import.meta.env.VITE_API_URL + '/api/v1/errors' || '/api/v1/errors'
    this.errorQueue = []
    this.maxQueueSize = 10
  }

  /**
   * Initialize error tracking
   */
  init(): void {
    if (!this.enabled) {
      console.log('[Error Tracking] Disabled')
      return
    }

    // Capture uncaught errors
    window.addEventListener('error', this.handleError.bind(this))

    // Capture unhandled promise rejections
    window.addEventListener('unhandledrejection', this.handleRejection.bind(this))

    console.log('[Error Tracking] Initialized')
  }

  /**
   * Handle global errors
   */
  private handleError(event: ErrorEvent): void {
    const errorData: ErrorData = {
      type: 'error',
      message: event.message,
      filename: event.filename,
      lineno: event.lineno,
      colno: event.colno,
      stack: event.error?.stack,
      timestamp: new Date().toISOString(),
      url: window.location.href,
      userAgent: navigator.userAgent
    }

    this.captureError(errorData)
  }

  /**
   * Handle unhandled promise rejections
   */
  private handleRejection(event: PromiseRejectionEvent): void {
    const errorData: ErrorData = {
      type: 'unhandledRejection',
      message: event.reason?.message || String(event.reason),
      stack: event.reason?.stack,
      timestamp: new Date().toISOString(),
      url: window.location.href,
      userAgent: navigator.userAgent
    }

    this.captureError(errorData)
  }

  /**
   * Capture Vue component errors
   */
  handleVueError(err: Error, instance: unknown, info: string): void {
    const componentName =
      (instance as { $options?: { name?: string } })?.$options?.name || 'Unknown'
    const errorData: ErrorData = {
      type: 'vueError',
      message: err.message,
      stack: err.stack,
      componentName,
      errorInfo: info,
      timestamp: new Date().toISOString(),
      url: window.location.href,
      userAgent: navigator.userAgent
    }

    this.captureError(errorData)
  }

  /**
   * Manually capture an error
   */
  private captureError(errorData: ErrorData): void {
    if (!this.enabled) return

    // Add to queue
    this.errorQueue.push(errorData)

    // Limit queue size
    if (this.errorQueue.length > this.maxQueueSize) {
      this.errorQueue.shift()
    }

    // Log to console in development
    if (import.meta.env.DEV) {
      console.error('[Error Tracked]', errorData)
    }

    // Send to backend
    this.sendError(errorData)
  }

  /**
   * Send error to backend
   */
  private async sendError(errorData: ErrorData): Promise<void> {
    try {
      await fetch(this.apiEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(errorData)
      })
    } catch (err) {
      // Silently fail - don't want error tracking to cause more errors
      if (import.meta.env.DEV) {
        console.warn('[Error Tracking] Failed to send error:', err)
      }
    }
  }

  /**
   * Manually track an error with context
   */
  trackError(error: Error | string, context: Record<string, unknown> = {}): void {
    const errorObj = typeof error === 'string' ? new Error(error) : error
    const errorData: ErrorData = {
      type: 'manual',
      message: errorObj.message || String(error),
      stack: errorObj.stack,
      context,
      timestamp: new Date().toISOString(),
      url: window.location.href,
      userAgent: navigator.userAgent
    }

    this.captureError(errorData)
  }

  /**
   * Get error queue (for debugging)
   */
  getErrors(): ErrorData[] {
    return this.errorQueue
  }

  /**
   * Clear error queue
   */
  clearErrors(): void {
    this.errorQueue = []
  }
}

// Export singleton instance
export const errorTracker = new ErrorTracker()

// Convenience export
export const trackError = (error: Error | string, context?: Record<string, unknown>): void =>
  errorTracker.trackError(error, context)

export default errorTracker
