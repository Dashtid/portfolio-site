/**
 * Tests for performance utility (TypeScript)
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// Mock environment variables
vi.stubEnv('VITE_METRICS_ENABLED', 'true')
vi.stubEnv('VITE_API_URL', 'http://localhost:8001')

describe('performance utility', () => {
  let performanceMonitor: any
  let mockFetch: any

  beforeEach(async () => {
    // Mock fetch
    mockFetch = vi.fn().mockResolvedValue({ ok: true })
    global.fetch = mockFetch

    // Mock performance API
    global.performance = {
      mark: vi.fn(),
      measure: vi.fn(),
      getEntriesByName: vi.fn(() => [{ duration: 100 }]),
      getEntriesByType: vi.fn(() => []),
      ...global.performance
    } as any

    // Mock window
    global.window = {
      addEventListener: vi.fn(),
      location: { href: 'http://test.com' },
      ...global.window
    } as any

    global.navigator = {
      userAgent: 'Test Browser'
    } as any

    // Mock PerformanceObserver
    global.PerformanceObserver = vi.fn().mockImplementation((callback) => ({
      observe: vi.fn(),
      disconnect: vi.fn()
    })) as any

    // Reset modules and import fresh
    vi.resetModules()
    const module = await import('@/utils/performance')
    performanceMonitor = module.performanceMonitor
  })

  afterEach(() => {
    vi.unstubAllEnvs()
    vi.clearAllMocks()
  })

  describe('initialization', () => {
    it('initializes performance monitoring when enabled', async () => {
      const consoleLog = vi.spyOn(console, 'log').mockImplementation(() => {})

      await performanceMonitor.init()

      expect(consoleLog).toHaveBeenCalledWith('[Performance] Monitoring initialized')
      consoleLog.mockRestore()
    })

    it('does not initialize when disabled', async () => {
      vi.stubEnv('VITE_METRICS_ENABLED', 'false')
      const consoleLog = vi.spyOn(console, 'log').mockImplementation(() => {})

      vi.resetModules()
      const module = await import('@/utils/performance')
      await module.performanceMonitor.init()

      expect(consoleLog).toHaveBeenCalledWith('[Performance] Monitoring disabled')
      consoleLog.mockRestore()
    })

    it('sets up PerformanceObserver for Core Web Vitals', async () => {
      await performanceMonitor.init()

      // Should create multiple PerformanceObserver instances
      expect(PerformanceObserver).toHaveBeenCalled()
    })
  })

  describe('mark and measure', () => {
    it('creates performance mark', () => {
      performanceMonitor.mark('test-mark')

      expect(performance.mark).toHaveBeenCalledWith('test-mark')
    })

    it('creates performance measure', () => {
      performanceMonitor.measure('test-measure', 'start', 'end')

      expect(performance.measure).toHaveBeenCalledWith('test-measure', 'start', 'end')
      expect(performance.getEntriesByName).toHaveBeenCalledWith('test-measure')
    })

    it('handles mark errors gracefully', () => {
      vi.mocked(performance.mark).mockImplementation(() => {
        throw new Error('Mark failed')
      })
      const consoleWarn = vi.spyOn(console, 'warn').mockImplementation(() => {})

      performanceMonitor.mark('test')

      expect(consoleWarn).toHaveBeenCalled()
      consoleWarn.mockRestore()
    })

    it('handles measure errors gracefully', () => {
      vi.mocked(performance.measure).mockImplementation(() => {
        throw new Error('Measure failed')
      })
      const consoleWarn = vi.spyOn(console, 'warn').mockImplementation(() => {})

      performanceMonitor.measure('test')

      expect(consoleWarn).toHaveBeenCalled()
      consoleWarn.mockRestore()
    })
  })

  describe('getMetrics', () => {
    it('returns empty metrics initially', () => {
      const metrics = performanceMonitor.getMetrics()

      expect(metrics).toEqual({})
    })

    it('returns copy of metrics object', () => {
      const metrics1 = performanceMonitor.getMetrics()
      const metrics2 = performanceMonitor.getMetrics()

      expect(metrics1).not.toBe(metrics2)
      expect(metrics1).toEqual(metrics2)
    })
  })

  describe('Core Web Vitals', () => {
    it('handles PerformanceObserver not supported', async () => {
      global.PerformanceObserver = vi.fn().mockImplementation(() => {
        throw new Error('Not supported')
      }) as any

      const consoleWarn = vi.spyOn(console, 'warn').mockImplementation(() => {})

      await performanceMonitor.init()

      expect(consoleWarn).toHaveBeenCalled()
      consoleWarn.mockRestore()
    })
  })

  describe('navigation timing', () => {
    it('tracks navigation timing on load', async () => {
      const mockNavigation = {
        domainLookupStart: 0,
        domainLookupEnd: 10,
        connectStart: 10,
        connectEnd: 20,
        requestStart: 20,
        responseStart: 30,
        responseEnd: 40,
        domInteractive: 50,
        domComplete: 60,
        loadEventStart: 60,
        loadEventEnd: 70,
        fetchStart: 0
      }

      vi.mocked(performance.getEntriesByType).mockReturnValue([mockNavigation] as any)

      await performanceMonitor.init()

      // Simulate load event
      const loadHandler = vi.mocked(window.addEventListener).mock.calls.find(
        call => call[0] === 'load'
      )?.[1] as Function
      loadHandler?.()

      // Wait for async operations
      await new Promise(resolve => setTimeout(resolve, 10))

      const metrics = performanceMonitor.getMetrics()
      expect(metrics.DNS).toBe(10)
      expect(metrics.TCP).toBe(10)
      expect(metrics.Request).toBe(10)
      expect(metrics.Response).toBe(10)
      expect(metrics.DOM_Processing).toBe(10)
      expect(metrics.Load_Complete).toBe(10)
      expect(metrics.Total_Load_Time).toBe(70)
    })
  })

  describe('resource timing', () => {
    it('categorizes resources by type', async () => {
      const mockResources = [
        { name: 'image.jpg', startTime: 0, responseEnd: 100, transferSize: 1024, initiatorType: 'img' },
        { name: 'script.js', startTime: 0, responseEnd: 50, transferSize: 2048, initiatorType: 'script' },
        { name: 'style.css', startTime: 0, responseEnd: 30, transferSize: 512, initiatorType: 'link' }
      ]

      vi.mocked(performance.getEntriesByType).mockImplementation((type) => {
        if (type === 'resource') return mockResources as any
        return []
      })

      await performanceMonitor.init()

      // Simulate load event
      const loadHandlers = vi.mocked(window.addEventListener).mock.calls.filter(
        call => call[0] === 'load'
      )
      loadHandlers.forEach(([, handler]) => (handler as Function)())

      // Wait for async operations
      await new Promise(resolve => setTimeout(resolve, 10))

      const metrics = performanceMonitor.getMetrics()
      expect(metrics.Avg_Image_Load).toBeDefined()
      expect(metrics.Avg_Script_Load).toBeDefined()
      expect(metrics.Avg_Style_Load).toBeDefined()
    })

    it('handles empty resource arrays', async () => {
      vi.mocked(performance.getEntriesByType).mockReturnValue([])

      await performanceMonitor.init()

      const loadHandlers = vi.mocked(window.addEventListener).mock.calls.filter(
        call => call[0] === 'load'
      )
      loadHandlers.forEach(([, handler]) => (handler as Function)())

      await new Promise(resolve => setTimeout(resolve, 10))

      const metrics = performanceMonitor.getMetrics()
      expect(metrics.Avg_Image_Load).toBe(0)
      expect(metrics.Avg_Script_Load).toBe(0)
      expect(metrics.Avg_Style_Load).toBe(0)
    })
  })

  describe('sendMetrics', () => {
    it('sends metrics to backend on load complete', async () => {
      const mockNavigation = {
        domainLookupStart: 0,
        domainLookupEnd: 10,
        connectStart: 10,
        connectEnd: 20,
        requestStart: 20,
        responseStart: 30,
        responseEnd: 40,
        domInteractive: 50,
        domComplete: 60,
        loadEventStart: 60,
        loadEventEnd: 70,
        fetchStart: 0
      }

      vi.mocked(performance.getEntriesByType).mockReturnValue([mockNavigation] as any)

      await performanceMonitor.init()

      const loadHandler = vi.mocked(window.addEventListener).mock.calls.find(
        call => call[0] === 'load'
      )?.[1] as Function
      loadHandler?.()

      await new Promise(resolve => setTimeout(resolve, 10))

      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8001/api/v1/performance',
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        })
      )
    })

    it('silently fails when backend request fails', async () => {
      mockFetch.mockRejectedValue(new Error('Network error'))
      const consoleWarn = vi.spyOn(console, 'warn').mockImplementation(() => {})

      const mockNavigation = {
        domainLookupStart: 0,
        domainLookupEnd: 10,
        connectStart: 10,
        connectEnd: 20,
        requestStart: 20,
        responseStart: 30,
        responseEnd: 40,
        domInteractive: 50,
        domComplete: 60,
        loadEventStart: 60,
        loadEventEnd: 70,
        fetchStart: 0
      }

      vi.mocked(performance.getEntriesByType).mockReturnValue([mockNavigation] as any)

      await performanceMonitor.init()

      const loadHandler = vi.mocked(window.addEventListener).mock.calls.find(
        call => call[0] === 'load'
      )?.[1] as Function
      loadHandler?.()

      await new Promise(resolve => setTimeout(resolve, 10))

      expect(consoleWarn).toHaveBeenCalled()
      consoleWarn.mockRestore()
    })
  })

  describe('TypeScript types', () => {
    it('exports performanceMonitor instance', () => {
      expect(performanceMonitor).toBeDefined()
      expect(typeof performanceMonitor.init).toBe('function')
      expect(typeof performanceMonitor.mark).toBe('function')
      expect(typeof performanceMonitor.measure).toBe('function')
      expect(typeof performanceMonitor.getMetrics).toBe('function')
    })
  })
})
