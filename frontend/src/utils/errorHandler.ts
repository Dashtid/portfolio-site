/**
 * Global error handling utilities
 */

import { ref, type Ref, type App } from 'vue'

/**
 * Error types
 */
export const ErrorTypes = {
  NETWORK: 'network',
  AUTH: 'auth',
  VALIDATION: 'validation',
  SERVER: 'server',
  CLIENT: 'client',
  UNKNOWN: 'unknown'
} as const

export type ErrorType = typeof ErrorTypes[keyof typeof ErrorTypes]

/**
 * Error severity levels
 */
export const ErrorSeverity = {
  LOW: 'low',
  MEDIUM: 'medium',
  HIGH: 'high',
  CRITICAL: 'critical'
} as const

export type ErrorSeverityLevel = typeof ErrorSeverity[keyof typeof ErrorSeverity]

interface ErrorInfo {
  message: string
  type: ErrorType
  severity: ErrorSeverityLevel
  timestamp: string
  context: Record<string, unknown>
  stack?: string
  userMessage?: string
}

interface ErrorResponse {
  status?: number
  data?: {
    message?: string
    detail?: string | Array<{ msg: string }>
  }
}

interface ErrorWithResponse extends Error {
  code?: string
  response?: ErrorResponse
}

// Global error state
export const globalError: Ref<ErrorInfo | null> = ref(null)
export const errorQueue: Ref<ErrorInfo[]> = ref([])

declare global {
  interface Window {
    analytics?: {
      trackEvent: (name: string, type: string, message: string) => void
    }
  }
}

/**
 * Handle different types of errors
 */
export function handleError(error: ErrorWithResponse, context: Record<string, unknown> = {}): ErrorInfo {
  const errorInfo: ErrorInfo = {
    message: error.message || 'An unexpected error occurred',
    type: ErrorTypes.UNKNOWN,
    severity: ErrorSeverity.MEDIUM,
    timestamp: new Date().toISOString(),
    context,
    stack: error.stack,
    ...classifyError(error)
  }

  // Add to error queue
  errorQueue.value.push(errorInfo)

  // Log to console in development
  if (import.meta.env.DEV) {
    console.error('Error handled:', errorInfo)
  }

  // Send to analytics if available
  if (window.analytics) {
    window.analytics.trackEvent('Error', errorInfo.type, errorInfo.message)
  }

  // Set global error for critical errors
  if (errorInfo.severity === ErrorSeverity.CRITICAL) {
    globalError.value = errorInfo
  }

  return errorInfo
}

/**
 * Classify error type and severity
 */
function classifyError(error: ErrorWithResponse): Partial<ErrorInfo> {
  // Network errors
  if (error.code === 'ECONNREFUSED' || error.message?.includes('Network')) {
    return {
      type: ErrorTypes.NETWORK,
      severity: ErrorSeverity.HIGH,
      userMessage: 'Connection error. Please check your internet connection.'
    }
  }

  // Auth errors
  if (error.response?.status === 401 || error.response?.status === 403) {
    return {
      type: ErrorTypes.AUTH,
      severity: ErrorSeverity.MEDIUM,
      userMessage: 'Authentication required. Please log in.'
    }
  }

  // Validation errors
  if (error.response?.status === 422 || error.response?.status === 400) {
    return {
      type: ErrorTypes.VALIDATION,
      severity: ErrorSeverity.LOW,
      userMessage: 'Please check your input and try again.'
    }
  }

  // Server errors
  if (error.response?.status >= 500) {
    return {
      type: ErrorTypes.SERVER,
      severity: ErrorSeverity.HIGH,
      userMessage: 'Server error. Please try again later.'
    }
  }

  // Client errors
  if (error.response?.status >= 400) {
    return {
      type: ErrorTypes.CLIENT,
      severity: ErrorSeverity.MEDIUM,
      userMessage: 'Request error. Please try again.'
    }
  }

  // Default
  return {
    type: ErrorTypes.UNKNOWN,
    severity: ErrorSeverity.MEDIUM,
    userMessage: 'Something went wrong. Please try again.'
  }
}

/**
 * Create user-friendly error messages
 */
export function getUserMessage(error: ErrorWithResponse | ErrorInfo | string): string {
  if (typeof error === 'string') return error

  // Check for custom user message
  if ('userMessage' in error && error.userMessage) return error.userMessage

  // Check for response data message
  if ('response' in error && error.response?.data?.message) return error.response.data.message

  // Check for response data detail (FastAPI)
  if ('response' in error && error.response?.data?.detail) {
    if (typeof error.response.data.detail === 'string') {
      return error.response.data.detail
    }
    if (Array.isArray(error.response.data.detail)) {
      return error.response.data.detail.map(d => d.msg).join(', ')
    }
  }

  // Default messages by status code
  const statusMessages: Record<number, string> = {
    400: 'Invalid request. Please check your input.',
    401: 'Please log in to continue.',
    403: 'You do not have permission to perform this action.',
    404: 'The requested resource was not found.',
    408: 'Request timeout. Please try again.',
    422: 'Validation error. Please check your input.',
    429: 'Too many requests. Please slow down.',
    500: 'Server error. Please try again later.',
    502: 'Bad gateway. Please try again later.',
    503: 'Service unavailable. Please try again later.',
    504: 'Gateway timeout. Please try again later.'
  }

  if ('response' in error && error.response?.status && statusMessages[error.response.status]) {
    return statusMessages[error.response.status]
  }

  // Fallback
  return ('message' in error && error.message) || 'An unexpected error occurred'
}

/**
 * Clear error state
 */
export function clearError(): void {
  globalError.value = null
}

/**
 * Clear error queue
 */
export function clearErrorQueue(): void {
  errorQueue.value = []
}

/**
 * Retry failed operation
 */
export async function retryOperation<T>(
  operation: () => Promise<T>,
  maxRetries: number = 3,
  delay: number = 1000
): Promise<T> {
  let lastError: ErrorWithResponse | undefined

  for (let i = 0; i < maxRetries; i++) {
    try {
      return await operation()
    } catch (error) {
      lastError = error as ErrorWithResponse

      // Don't retry on client errors
      if (lastError.response?.status && lastError.response.status >= 400 && lastError.response.status < 500) {
        throw error
      }

      // Wait before retrying
      if (i < maxRetries - 1) {
        await new Promise(resolve => setTimeout(resolve, delay * Math.pow(2, i)))
      }
    }
  }

  throw lastError
}

/**
 * Setup global error handlers
 */
export function setupGlobalErrorHandlers(app: App): void {
  // Vue error handler
  app.config.errorHandler = (err, instance, info) => {
    handleError(err as ErrorWithResponse, {
      component: instance?.$options.name,
      info
    })
  }

  // Unhandled promise rejection
  window.addEventListener('unhandledrejection', event => {
    handleError(new Error(event.reason as string) as ErrorWithResponse, { type: 'unhandledRejection' })
    event.preventDefault()
  })

  // Global error
  window.addEventListener('error', event => {
    handleError((event.error || new Error(event.message)) as ErrorWithResponse, { type: 'globalError' })
  })
}

interface ErrorNotificationOptions {
  showAlert?: boolean
  [key: string]: unknown
}

/**
 * Create error toast/notification
 */
export function showErrorNotification(message: string, options: ErrorNotificationOptions = {}): void {
  // This would integrate with your notification system
  console.error('Error notification:', message, options)

  // For now, we'll just use alert in development
  if (import.meta.env.DEV && options.showAlert) {
    alert(`Error: ${message}`)
  }
}

// Export a composable for Vue components
export function useErrorHandler() {
  return {
    globalError,
    errorQueue,
    handleError,
    getUserMessage,
    clearError,
    clearErrorQueue,
    retryOperation,
    showErrorNotification
  }
}