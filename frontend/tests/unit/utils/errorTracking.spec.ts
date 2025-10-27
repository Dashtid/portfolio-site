/**
 * Tests for errorTracking utility (TypeScript)
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// Mock environment variables
vi.stubEnv('VITE_ERROR_TRACKING_ENABLED', 'true')
vi.stubEnv('VITE_API_URL', 'http://localhost:8001')

describe('errorTracking utility', () => {
  let errorTracker: any
  let trackError: any
  let mockFetch: any

  beforeEach(async () => {
    // Mock fetch
    mockFetch = vi.fn().mockResolvedValue({ ok: true })
    global.fetch = mockFetch

    // Mock window and navigator
    global.window = {
      addEventListener: vi.fn(),
      location: { href: 'http://test.com' },
      ...global.window
    } as any

    global.navigator = {
      userAgent: 'Test Browser'
    } as any

    // Reset modules and import fresh
    vi.resetModules()
    const module = await import('@/utils/errorTracking')
    errorTracker = module.errorTracker
    trackError = module.trackError
  })

  afterEach(() => {
    vi.unstubAllEnvs()
    vi.clearAllMocks()
    errorTracker.clearErrors()
  })

  describe('initialization', () => {
    it('initializes with enabled state', () => {
      errorTracker.init()

      expect(window.addEventListener).toHaveBeenCalledWith('error', expect.any(Function))
      expect(window.addEventListener).toHaveBeenCalledWith('unhandledrejection', expect.any(Function))
    })

    it('logs when disabled', async () => {
      vi.stubEnv('VITE_ERROR_TRACKING_ENABLED', 'false')
      const consoleLog = vi.spyOn(console, 'log').mockImplementation(() => {})

      vi.resetModules()
      const module = await import('@/utils/errorTracking')
      module.errorTracker.init()

      expect(consoleLog).toHaveBeenCalledWith('[Error Tracking] Disabled')
      consoleLog.mockRestore()
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
        'http://localhost:8001/api/v1/errors',
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

      // Should not throw
      expect(consoleWarn).toHaveBeenCalled()
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
      expect(errors[0].timestamp).toBeDefined()
      expect(new Date(errors[0].timestamp)).toBeInstanceOf(Date)
    })

    it('includes URL', () => {
      trackError('Test error')

      const errors = errorTracker.getErrors()
      expect(errors[0].url).toBe('http://test.com')
    })

    it('includes user agent', () => {
      trackError('Test error')

      const errors = errorTracker.getErrors()
      expect(errors[0].userAgent).toBe('Test Browser')
    })

    it('includes stack trace when available', () => {
      const error = new Error('Test error')
      trackError(error)

      const errors = errorTracker.getErrors()
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
