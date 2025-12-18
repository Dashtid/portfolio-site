/**
 * Type guard utilities for safer error handling
 * Eliminates verbose type assertions throughout the codebase
 */
import type { AxiosError } from 'axios'

/**
 * Type guard to check if an error is an AxiosError
 * @param error - Unknown error to check
 * @returns True if error is an AxiosError
 */
export function isAxiosError(error: unknown): error is AxiosError {
  return (
    error !== null &&
    typeof error === 'object' &&
    'isAxiosError' in error &&
    (error as AxiosError).isAxiosError === true
  )
}

/**
 * Check if an error has a specific HTTP status code
 * @param error - Unknown error to check
 * @param status - HTTP status code to match
 * @returns True if error is an AxiosError with the specified status
 */
export function hasStatusCode(error: unknown, status: number): boolean {
  return isAxiosError(error) && error.response?.status === status
}

/**
 * Check if error is a 401 Unauthorized error
 * @param error - Unknown error to check
 */
export function isUnauthorizedError(error: unknown): boolean {
  return hasStatusCode(error, 401)
}

/**
 * Check if error is a 403 Forbidden error
 * @param error - Unknown error to check
 */
export function isForbiddenError(error: unknown): boolean {
  return hasStatusCode(error, 403)
}

/**
 * Check if error is a 404 Not Found error
 * @param error - Unknown error to check
 */
export function isNotFoundError(error: unknown): boolean {
  return hasStatusCode(error, 404)
}

/**
 * Check if error is a network error (no response received)
 * @param error - Unknown error to check
 */
export function isNetworkError(error: unknown): boolean {
  return isAxiosError(error) && !error.response && error.code === 'ERR_NETWORK'
}

/**
 * Check if error is a timeout error
 * @param error - Unknown error to check
 */
export function isTimeoutError(error: unknown): boolean {
  return isAxiosError(error) && error.code === 'ECONNABORTED'
}

/**
 * Get HTTP status code from error if available
 * @param error - Unknown error to check
 * @returns HTTP status code or undefined
 */
export function getErrorStatus(error: unknown): number | undefined {
  return isAxiosError(error) ? error.response?.status : undefined
}

/**
 * Get error message from various error types
 * @param error - Unknown error
 * @param fallback - Fallback message if extraction fails
 * @returns Error message string
 */
export function getErrorMessage(error: unknown, fallback = 'An error occurred'): string {
  if (isAxiosError(error)) {
    const data = error.response?.data as { detail?: string } | undefined
    return data?.detail || error.message || fallback
  }
  if (error instanceof Error) {
    return error.message
  }
  if (typeof error === 'string') {
    return error
  }
  return fallback
}
