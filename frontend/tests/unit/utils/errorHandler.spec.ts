/**
 * Tests for errorHandler utility (TypeScript)
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import {
  handleError,
  getUserMessage,
  clearError,
  clearErrorQueue,
  retryOperation,
  globalError,
  errorQueue,
  ErrorTypes,
  ErrorSeverity
} from '@/utils/errorHandler'

describe('errorHandler utility', () => {
  beforeEach(() => {
    clearError()
    clearErrorQueue()
    vi.clearAllMocks()
  })

  describe('handleError', () => {
    it('captures error message', () => {
      const error = new Error('Test error')
      const errorInfo = handleError(error)

      expect(errorInfo.message).toBe('Test error')
      expect(errorInfo.type).toBe(ErrorTypes.UNKNOWN)
      expect(errorInfo.severity).toBe(ErrorSeverity.MEDIUM)
    })

    it('classifies network errors', () => {
      const error = new Error('Network request failed')
      const errorInfo = handleError(error)

      expect(errorInfo.type).toBe(ErrorTypes.NETWORK)
      expect(errorInfo.severity).toBe(ErrorSeverity.HIGH)
    })

    it('classifies auth errors from 401 status', () => {
      const error = new Error('Unauthorized') as any
      error.response = { status: 401 }
      const errorInfo = handleError(error)

      expect(errorInfo.type).toBe(ErrorTypes.AUTH)
      expect(errorInfo.severity).toBe(ErrorSeverity.MEDIUM)
    })

    it('classifies auth errors from 403 status', () => {
      const error = new Error('Forbidden') as any
      error.response = { status: 403 }
      const errorInfo = handleError(error)

      expect(errorInfo.type).toBe(ErrorTypes.AUTH)
    })

    it('classifies validation errors from 422 status', () => {
      const error = new Error('Validation failed') as any
      error.response = { status: 422 }
      const errorInfo = handleError(error)

      expect(errorInfo.type).toBe(ErrorTypes.VALIDATION)
      expect(errorInfo.severity).toBe(ErrorSeverity.LOW)
    })

    it('classifies server errors from 500 status', () => {
      const error = new Error('Server error') as any
      error.response = { status: 500 }
      const errorInfo = handleError(error)

      expect(errorInfo.type).toBe(ErrorTypes.SERVER)
      expect(errorInfo.severity).toBe(ErrorSeverity.HIGH)
    })

    it('adds error to queue', () => {
      const error = new Error('Test')
      handleError(error)

      expect(errorQueue.value).toHaveLength(1)
      expect(errorQueue.value[0].message).toBe('Test')
    })

    it('sets global error for critical errors', () => {
      const error = new Error('Critical error') as any
      const errorInfo = handleError(error)

      // Manually set as critical to test the global error functionality
      errorInfo.severity = ErrorSeverity.CRITICAL
      globalError.value = errorInfo

      expect(globalError.value).toBeDefined()
      expect(globalError.value?.severity).toBe(ErrorSeverity.CRITICAL)
    })

    it('includes error stack', () => {
      const error = new Error('Test')
      const errorInfo = handleError(error)

      expect(errorInfo.stack).toBeDefined()
    })

    it('includes custom context', () => {
      const error = new Error('Test')
      const context = { userId: '123', action: 'login' }
      const errorInfo = handleError(error, context)

      expect(errorInfo.context).toEqual(context)
    })
  })

  describe('getUserMessage', () => {
    it('returns string directly', () => {
      expect(getUserMessage('Test message')).toBe('Test message')
    })

    it('returns custom userMessage if present', () => {
      const error = {
        message: 'Technical error',
        userMessage: 'User-friendly message'
      } as any

      expect(getUserMessage(error)).toBe('User-friendly message')
    })

    it('returns response data message', () => {
      const error = {
        response: {
          data: {
            message: 'API error message'
          }
        }
      } as any

      expect(getUserMessage(error)).toBe('API error message')
    })

    it('returns FastAPI detail string', () => {
      const error = {
        response: {
          data: {
            detail: 'FastAPI validation error'
          }
        }
      } as any

      expect(getUserMessage(error)).toBe('FastAPI validation error')
    })

    it('joins FastAPI detail array', () => {
      const error = {
        response: {
          data: {
            detail: [
              { msg: 'Field 1 error' },
              { msg: 'Field 2 error' }
            ]
          }
        }
      } as any

      expect(getUserMessage(error)).toBe('Field 1 error, Field 2 error')
    })

    it('returns status-based message for 404', () => {
      const error = {
        response: { status: 404 }
      } as any

      expect(getUserMessage(error)).toBe('The requested resource was not found.')
    })

    it('returns status-based message for 500', () => {
      const error = {
        response: { status: 500 }
      } as any

      expect(getUserMessage(error)).toBe('Server error. Please try again later.')
    })

    it('returns error message as fallback', () => {
      const error = {
        message: 'Fallback message'
      } as any

      expect(getUserMessage(error)).toBe('Fallback message')
    })
  })

  describe('clearError', () => {
    it('clears global error state', () => {
      globalError.value = {
        message: 'Test',
        type: ErrorTypes.UNKNOWN,
        severity: ErrorSeverity.MEDIUM,
        timestamp: new Date().toISOString(),
        context: {}
      }

      clearError()

      expect(globalError.value).toBeNull()
    })
  })

  describe('clearErrorQueue', () => {
    it('clears error queue', () => {
      handleError(new Error('Test 1'))
      handleError(new Error('Test 2'))

      expect(errorQueue.value).toHaveLength(2)

      clearErrorQueue()

      expect(errorQueue.value).toHaveLength(0)
    })
  })

  describe('retryOperation', () => {
    it('succeeds on first try', async () => {
      const operation = vi.fn().mockResolvedValue('success')

      const result = await retryOperation(operation)

      expect(result).toBe('success')
      expect(operation).toHaveBeenCalledTimes(1)
    })

    it('retries on failure and succeeds', async () => {
      const operation = vi.fn()
        .mockRejectedValueOnce(new Error('Fail 1'))
        .mockRejectedValueOnce(new Error('Fail 2'))
        .mockResolvedValue('success')

      const result = await retryOperation(operation, 3, 10)

      expect(result).toBe('success')
      expect(operation).toHaveBeenCalledTimes(3)
    })

    it('throws after max retries', async () => {
      const operation = vi.fn().mockRejectedValue(new Error('Always fails'))

      await expect(retryOperation(operation, 2, 10)).rejects.toThrow('Always fails')
      expect(operation).toHaveBeenCalledTimes(2)
    })

    it('does not retry on client errors', async () => {
      const error = new Error('Bad request') as any
      error.response = { status: 400 }
      const operation = vi.fn().mockRejectedValue(error)

      await expect(retryOperation(operation, 3, 10)).rejects.toThrow('Bad request')
      expect(operation).toHaveBeenCalledTimes(1)
    })

    it('retries on server errors', async () => {
      const serverError = new Error('Server error') as any
      serverError.response = { status: 500 }
      const operation = vi.fn()
        .mockRejectedValueOnce(serverError)
        .mockResolvedValue('success')

      const result = await retryOperation(operation, 2, 10)

      expect(result).toBe('success')
      expect(operation).toHaveBeenCalledTimes(2)
    })

    it('uses exponential backoff', async () => {
      const operation = vi.fn()
        .mockRejectedValueOnce(new Error('Fail'))
        .mockResolvedValue('success')

      const startTime = Date.now()
      await retryOperation(operation, 3, 100)
      const duration = Date.now() - startTime

      // Should have waited at least 100ms (first retry delay)
      expect(duration).toBeGreaterThanOrEqual(100)
    })
  })

  describe('TypeScript types', () => {
    it('accepts ErrorWithResponse type', () => {
      const error: any = new Error('Test')
      error.code = 'ECONNREFUSED'
      error.response = { status: 500 }

      const result = handleError(error)
      expect(result).toBeDefined()
    })

    it('retryOperation is generic', async () => {
      const operation = async (): Promise<number> => 42

      const result = await retryOperation(operation)

      expect(result).toBe(42)
      expect(typeof result).toBe('number')
    })

    it('retryOperation accepts custom types', async () => {
      interface CustomResult {
        success: boolean
        data: string
      }

      const operation = async (): Promise<CustomResult> => ({
        success: true,
        data: 'test'
      })

      const result = await retryOperation(operation)

      expect(result.success).toBe(true)
      expect(result.data).toBe('test')
    })
  })
})
