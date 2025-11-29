/**
 * Environment-aware logging utility
 *
 * Only logs in development mode to avoid cluttering production console
 * and potential information leakage.
 */

interface LoggerOptions {
  prefix?: string
  enabled?: boolean
}

class Logger {
  private prefix: string
  private enabled: boolean
  private isDev: boolean

  constructor(options: LoggerOptions = {}) {
    this.prefix = options.prefix || ''
    this.enabled = options.enabled ?? true
    this.isDev = import.meta.env.DEV
  }

  private shouldLog(): boolean {
    return this.enabled && this.isDev
  }

  private formatMessage(message: string): string {
    return this.prefix ? `[${this.prefix}] ${message}` : message
  }

  debug(message: string, ...args: unknown[]): void {
    if (this.shouldLog()) {
      console.debug(this.formatMessage(message), ...args)
    }
  }

  log(message: string, ...args: unknown[]): void {
    if (this.shouldLog()) {
      console.log(this.formatMessage(message), ...args)
    }
  }

  info(message: string, ...args: unknown[]): void {
    if (this.shouldLog()) {
      console.info(this.formatMessage(message), ...args)
    }
  }

  warn(message: string, ...args: unknown[]): void {
    if (this.shouldLog()) {
      console.warn(this.formatMessage(message), ...args)
    }
  }

  error(message: string, ...args: unknown[]): void {
    // Errors are always logged, even in production
    // This helps with debugging production issues
    if (this.enabled) {
      console.error(this.formatMessage(message), ...args)
    }
  }

  /**
   * Create a child logger with a specific prefix
   */
  child(prefix: string): Logger {
    const childPrefix = this.prefix ? `${this.prefix}:${prefix}` : prefix
    return new Logger({ prefix: childPrefix, enabled: this.enabled })
  }

  /**
   * Group related logs together (dev only)
   */
  group(label: string, fn: () => void): void {
    if (this.shouldLog()) {
      console.group(this.formatMessage(label))
      fn()
      console.groupEnd()
    }
  }

  /**
   * Log with timing information (dev only)
   */
  time(label: string): void {
    if (this.shouldLog()) {
      console.time(this.formatMessage(label))
    }
  }

  timeEnd(label: string): void {
    if (this.shouldLog()) {
      console.timeEnd(this.formatMessage(label))
    }
  }
}

// Export pre-configured loggers for different modules
export const logger = new Logger()
export const analyticsLogger = new Logger({ prefix: 'Analytics' })
export const authLogger = new Logger({ prefix: 'Auth' })
export const apiLogger = new Logger({ prefix: 'API' })
export const themeLogger = new Logger({ prefix: 'Theme' })
export const performanceLogger = new Logger({ prefix: 'Performance' })
export const errorLogger = new Logger({ prefix: 'Error' })

// Factory function for creating custom loggers
export const createLogger = (prefix: string): Logger => new Logger({ prefix })

export default logger
