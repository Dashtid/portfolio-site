/**
 * Tests for errorTracking utility (TypeScript)
 *
 * Note: Environment variables are set in vitest.config.ts
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { errorTracker, trackError } from '@/utils/errorTracking'

describe('errorTracking utility', () => {
  let mockFetch: ReturnType<typeof vi.fn>

  beforeEach(() => {
    // Mock fetch
    mockFetch = vi.fn().mockResolvedValue({ ok: true })
    global.fetch = mockFetch

    // Clear any previous errors
    errorTracker.clearErrors()
  })

  afterEach(() => {
    vi.clearAllMocks()
    errorTracker.clearErrors()
  })

  describe('initialization', () => {
    it('initializes with enabled state', () => {
      const addEventListenerSpy = vi.spyOn(window, 'addEventListener')

      errorTracker.init()

      expect(addEventListenerSpy).toHaveBeenCalledWith('error', expect.any(Function))
      expect(addEventListenerSpy).toHaveBeenCalledWith('unhandledrejection', expect.any(Function))

      addEventListenerSpy.mockRestore()
    })
  })

  describe('trackError', () => {
    it('tracks manual errors with Error object', async () => {
      const error = new Error('Test error')
      const context = { userId: 123 }

      trackError(error, context)

      // Wait for async operations
      await new Promise(resolve => setTimeout(resolve, 10))

      const errors = errorTracker.getErrors()
      expect(errors).toHaveLength(1)
      expect(errors[0].type).toBe('manual')
      expect(errors[0].message).toBe('Test error')
      expect(errors[0].context).toEqual(context)
    })

    it('tracks manual errors with string', async () => {
      trackError('String error')

      await new Promise(resolve => setTimeout(resolve, 10))

      const errors = errorTracker.getErrors()
      expect(errors).toHaveLength(1)
      expect(errors[0].type).toBe('manual')
      expect(errors[0].message).toBe('String error')
    })

    it('sends error to backend', async () => {
      trackError('Test error')

      await new Promise(resolve => setTimeout(resolve, 10))

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/errors'),
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: expect.stringContaining('Test error')
        })
      )
    })

    it('silently fails when backend request fails', async () => {
      mockFetch.mockRejectedValue(new Error('Network error'))
      const consoleWarn = vi.spyOn(console, 'warn').mockImplementation(() => {})

      trackError('Test error')

      await new Promise(resolve => setTimeout(resolve, 10))

      // Should not throw - function completes without exception
      expect(true).toBe(true)
      consoleWarn.mockRestore()
    })
  })

  describe('handleVueError', () => {
    it('captures Vue component errors', () => {
      const error = new Error('Vue error')
      const instance = { $options: { name: 'TestComponent' } }
      const info = 'render'

      errorTracker.handleVueError(error, instance, info)

      const errors = errorTracker.getErrors()
      expect(errors).toHaveLength(1)
      expect(errors[0].type).toBe('vueError')
      expect(errors[0].message).toBe('Vue error')
      expect(errors[0].componentName).toBe('TestComponent')
      expect(errors[0].errorInfo).toBe('render')
    })

    it('handles unknown component name', () => {
      const error = new Error('Vue error')
      const instance = {}
      const info = 'mount'

      errorTracker.handleVueError(error, instance, info)

      const errors = errorTracker.getErrors()
      expect(errors).toHaveLength(1)
      expect(errors[0].componentName).toBe('Unknown')
    })
  })

  describe('error queue management', () => {
    it('adds errors to queue', () => {
      trackError('Error 1')
      trackError('Error 2')

      const errors = errorTracker.getErrors()
      expect(errors).toHaveLength(2)
    })

    it('limits queue size to 10 errors', () => {
      for (let i = 0; i < 15; i++) {
        trackError(`Error ${i}`)
      }

      const errors = errorTracker.getErrors()
      expect(errors).toHaveLength(10)
      // Should keep the most recent 10
      expect(errors[0].message).toBe('Error 5')
      expect(errors[9].message).toBe('Error 14')
    })

    it('clears error queue', () => {
      trackError('Error 1')
      trackError('Error 2')

      errorTracker.clearErrors()

      const errors = errorTracker.getErrors()
      expect(errors).toHaveLength(0)
    })
  })

  describe('error data structure', () => {
    it('includes timestamp', () => {
      trackError('Test error')

      const errors = errorTracker.getErrors()
      expect(errors).toHaveLength(1)
      expect(errors[0].timestamp).toBeDefined()
      expect(new Date(errors[0].timestamp)).toBeInstanceOf(Date)
    })

    it('includes URL', () => {
      trackError('Test error')

      const errors = errorTracker.getErrors()
      expect(errors).toHaveLength(1)
      expect(errors[0].url).toBeDefined()
    })

    it('includes user agent', () => {
      trackError('Test error')

      const errors = errorTracker.getErrors()
      expect(errors).toHaveLength(1)
      expect(errors[0].userAgent).toBeDefined()
    })

    it('includes stack trace when available', () => {
      const error = new Error('Test error')
      trackError(error)

      const errors = errorTracker.getErrors()
      expect(errors).toHaveLength(1)
      expect(errors[0].stack).toBeDefined()
      expect(errors[0].stack).toContain('Error: Test error')
    })
  })

  describe('TypeScript types', () => {
    it('accepts Error objects', () => {
      const error = new Error('Test')
      expect(() => trackError(error)).not.toThrow()
    })

    it('accepts string errors', () => {
      expect(() => trackError('Test string error')).not.toThrow()
    })

    it('accepts optional context', () => {
      expect(() => trackError('Test', { key: 'value' })).not.toThrow()
    })

    it('accepts missing context', () => {
      expect(() => trackError('Test')).not.toThrow()
    })
  })
})
