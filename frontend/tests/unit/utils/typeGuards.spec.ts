/**
 * Tests for typeGuards utility
 * Comprehensive tests for error type checking functions
 */
import { describe, it, expect } from 'vitest'
import {
  isAxiosError,
  hasStatusCode,
  isUnauthorizedError,
  isForbiddenError,
  isNotFoundError,
  isNetworkError,
  isTimeoutError,
  getErrorStatus,
  getErrorMessage
} from '@/utils/typeGuards'

describe('typeGuards', () => {
  describe('isAxiosError', () => {
    it('returns true for valid AxiosError with isAxiosError flag', () => {
      const axiosError = {
        isAxiosError: true,
        message: 'Request failed',
        response: { status: 500 }
      }
      expect(isAxiosError(axiosError)).toBe(true)
    })

    it('returns false when isAxiosError flag is false', () => {
      const error = {
        isAxiosError: false,
        message: 'Request failed'
      }
      expect(isAxiosError(error)).toBe(false)
    })

    it('returns false for null', () => {
      expect(isAxiosError(null)).toBe(false)
    })

    it('returns false for undefined', () => {
      expect(isAxiosError(undefined)).toBe(false)
    })

    it('returns false for primitive string', () => {
      expect(isAxiosError('error')).toBe(false)
    })

    it('returns false for primitive number', () => {
      expect(isAxiosError(404)).toBe(false)
    })

    it('returns false for regular Error', () => {
      expect(isAxiosError(new Error('test'))).toBe(false)
    })

    it('returns false for object without isAxiosError property', () => {
      const error = { message: 'error', response: { status: 500 } }
      expect(isAxiosError(error)).toBe(false)
    })

    it('returns false for empty object', () => {
      expect(isAxiosError({})).toBe(false)
    })
  })

  describe('hasStatusCode', () => {
    it('returns true when AxiosError has matching status code', () => {
      const error = {
        isAxiosError: true,
        response: { status: 404 }
      }
      expect(hasStatusCode(error, 404)).toBe(true)
    })

    it('returns false when status code does not match', () => {
      const error = {
        isAxiosError: true,
        response: { status: 500 }
      }
      expect(hasStatusCode(error, 404)).toBe(false)
    })

    it('returns false when response is undefined', () => {
      const error = {
        isAxiosError: true
      }
      expect(hasStatusCode(error, 404)).toBe(false)
    })

    it('returns false for non-AxiosError', () => {
      expect(hasStatusCode(new Error('test'), 404)).toBe(false)
    })

    it('returns false for null', () => {
      expect(hasStatusCode(null, 404)).toBe(false)
    })
  })

  describe('isUnauthorizedError', () => {
    it('returns true for 401 status', () => {
      const error = {
        isAxiosError: true,
        response: { status: 401 }
      }
      expect(isUnauthorizedError(error)).toBe(true)
    })

    it('returns false for 403 status', () => {
      const error = {
        isAxiosError: true,
        response: { status: 403 }
      }
      expect(isUnauthorizedError(error)).toBe(false)
    })

    it('returns false for non-AxiosError', () => {
      expect(isUnauthorizedError(new Error('unauthorized'))).toBe(false)
    })
  })

  describe('isForbiddenError', () => {
    it('returns true for 403 status', () => {
      const error = {
        isAxiosError: true,
        response: { status: 403 }
      }
      expect(isForbiddenError(error)).toBe(true)
    })

    it('returns false for 401 status', () => {
      const error = {
        isAxiosError: true,
        response: { status: 401 }
      }
      expect(isForbiddenError(error)).toBe(false)
    })

    it('returns false for non-AxiosError', () => {
      expect(isForbiddenError(new Error('forbidden'))).toBe(false)
    })
  })

  describe('isNotFoundError', () => {
    it('returns true for 404 status', () => {
      const error = {
        isAxiosError: true,
        response: { status: 404 }
      }
      expect(isNotFoundError(error)).toBe(true)
    })

    it('returns false for 500 status', () => {
      const error = {
        isAxiosError: true,
        response: { status: 500 }
      }
      expect(isNotFoundError(error)).toBe(false)
    })

    it('returns false for non-AxiosError', () => {
      expect(isNotFoundError(new Error('not found'))).toBe(false)
    })
  })

  describe('isNetworkError', () => {
    it('returns true for network error with ERR_NETWORK code', () => {
      const error = {
        isAxiosError: true,
        code: 'ERR_NETWORK',
        response: undefined
      }
      expect(isNetworkError(error)).toBe(true)
    })

    it('returns false when response exists', () => {
      const error = {
        isAxiosError: true,
        code: 'ERR_NETWORK',
        response: { status: 500 }
      }
      expect(isNetworkError(error)).toBe(false)
    })

    it('returns false for different error code', () => {
      const error = {
        isAxiosError: true,
        code: 'ECONNABORTED',
        response: undefined
      }
      expect(isNetworkError(error)).toBe(false)
    })

    it('returns false for non-AxiosError', () => {
      expect(isNetworkError(new Error('network error'))).toBe(false)
    })
  })

  describe('isTimeoutError', () => {
    it('returns true for timeout error with ECONNABORTED code', () => {
      const error = {
        isAxiosError: true,
        code: 'ECONNABORTED'
      }
      expect(isTimeoutError(error)).toBe(true)
    })

    it('returns false for different error code', () => {
      const error = {
        isAxiosError: true,
        code: 'ERR_NETWORK'
      }
      expect(isTimeoutError(error)).toBe(false)
    })

    it('returns false for non-AxiosError', () => {
      expect(isTimeoutError(new Error('timeout'))).toBe(false)
    })

    it('returns false when code is undefined', () => {
      const error = {
        isAxiosError: true
      }
      expect(isTimeoutError(error)).toBe(false)
    })
  })

  describe('getErrorStatus', () => {
    it('returns status code from AxiosError response', () => {
      const error = {
        isAxiosError: true,
        response: { status: 404 }
      }
      expect(getErrorStatus(error)).toBe(404)
    })

    it('returns undefined when response is missing', () => {
      const error = {
        isAxiosError: true
      }
      expect(getErrorStatus(error)).toBeUndefined()
    })

    it('returns undefined for non-AxiosError', () => {
      expect(getErrorStatus(new Error('test'))).toBeUndefined()
    })

    it('returns undefined for null', () => {
      expect(getErrorStatus(null)).toBeUndefined()
    })

    it('returns undefined for string', () => {
      expect(getErrorStatus('error')).toBeUndefined()
    })
  })

  describe('getErrorMessage', () => {
    it('returns detail from AxiosError response data', () => {
      const error = {
        isAxiosError: true,
        message: 'Request failed',
        response: {
          status: 400,
          data: { detail: 'Validation failed' }
        }
      }
      expect(getErrorMessage(error)).toBe('Validation failed')
    })

    it('returns error.message when response.data.detail is missing', () => {
      const error = {
        isAxiosError: true,
        message: 'Network Error',
        response: {
          status: 500,
          data: {}
        }
      }
      expect(getErrorMessage(error)).toBe('Network Error')
    })

    it('returns fallback when AxiosError has no message', () => {
      const error = {
        isAxiosError: true,
        response: {
          status: 500,
          data: {}
        }
      }
      expect(getErrorMessage(error, 'Custom fallback')).toBe('Custom fallback')
    })

    it('returns message from regular Error', () => {
      const error = new Error('Something went wrong')
      expect(getErrorMessage(error)).toBe('Something went wrong')
    })

    it('returns string error directly', () => {
      expect(getErrorMessage('Direct error message')).toBe('Direct error message')
    })

    it('returns default fallback for unknown error type', () => {
      expect(getErrorMessage(12345)).toBe('An error occurred')
    })

    it('returns custom fallback for unknown error type', () => {
      expect(getErrorMessage({ unknown: true }, 'Unknown error')).toBe('Unknown error')
    })

    it('returns fallback for null', () => {
      expect(getErrorMessage(null)).toBe('An error occurred')
    })

    it('returns fallback for undefined', () => {
      expect(getErrorMessage(undefined)).toBe('An error occurred')
    })

    it('handles AxiosError without response', () => {
      const error = {
        isAxiosError: true,
        message: 'No response received'
      }
      expect(getErrorMessage(error)).toBe('No response received')
    })

    it('handles AxiosError with null data', () => {
      const error = {
        isAxiosError: true,
        message: 'Failed',
        response: {
          status: 500,
          data: null
        }
      }
      expect(getErrorMessage(error)).toBe('Failed')
    })
  })
})
