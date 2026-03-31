/**
 * Error handling utilities
 */

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

interface ErrorInfo {
  message?: string
  userMessage?: string
}

/**
 * Create user-friendly error messages from API errors
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
      return error.response.data.detail
        .map(d => (typeof d === 'object' && d !== null && 'msg' in d ? d.msg : String(d)))
        .filter(Boolean)
        .join(', ')
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
