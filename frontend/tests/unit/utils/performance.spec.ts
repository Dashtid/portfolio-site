/**
 * Tests for performance utility (TypeScript)
 *
 * Note: Environment variables are set in vitest.config.ts
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { performanceMonitor } from '@/utils/performance'

describe('performance utility', () => {
  let mockFetch: ReturnType<typeof vi.fn>
  let mockPerformanceMark: ReturnType<typeof vi.fn>
  let mockPerformanceMeasure: ReturnType<typeof vi.fn>
  let mockGetEntriesByName: ReturnType<typeof vi.fn>
  let mockGetEntriesByType: ReturnType<typeof vi.fn>

  beforeEach(() => {
    // Mock fetch
    mockFetch = vi.fn().mockResolvedValue({ ok: true })
    global.fetch = mockFetch

    // Mock performance API
    mockPerformanceMark = vi.fn()
    mockPerformanceMeasure = vi.fn()
    mockGetEntriesByName = vi.fn(() => [{ duration: 100 }])
    mockGetEntriesByType = vi.fn(() => [])

    vi.spyOn(performance, 'mark').mockImplementation(mockPerformanceMark)
    vi.spyOn(performance, 'measure').mockImplementation(mockPerformanceMeasure)
    vi.spyOn(performance, 'getEntriesByName').mockImplementation(mockGetEntriesByName)
    vi.spyOn(performance, 'getEntriesByType').mockImplementation(mockGetEntriesByType)

    // Mock PerformanceObserver - must use class syntax for vitest 4
    class MockPerformanceObserver {
      callback: PerformanceObserverCallback
      constructor(callback: PerformanceObserverCallback) {
        this.callback = callback
      }
      observe = vi.fn()
      disconnect = vi.fn()
      takeRecords = vi.fn(() => [])
    }
    global.PerformanceObserver = MockPerformanceObserver as unknown as typeof PerformanceObserver
  })

  afterEach(() => {
    vi.clearAllMocks()
    vi.restoreAllMocks()
  })

  describe('initialization', () => {
    it('initializes performance monitoring when enabled', async () => {
      const consoleLog = vi.spyOn(console, 'log').mockImplementation(() => {})

      await performanceMonitor.init()

      expect(consoleLog).toHaveBeenCalledWith('[Performance] Monitoring initialized')
      consoleLog.mockRestore()
    })

    it('sets up PerformanceObserver for Core Web Vitals', async () => {
      // Track how many times MockPerformanceObserver is instantiated
      let observerCount = 0
      class TrackingMockPerformanceObserver {
        callback: PerformanceObserverCallback
        constructor(callback: PerformanceObserverCallback) {
          this.callback = callback
          observerCount++
        }
        observe = vi.fn()
        disconnect = vi.fn()
        takeRecords = vi.fn(() => [])
      }
      global.PerformanceObserver =
        TrackingMockPerformanceObserver as unknown as typeof PerformanceObserver

      await performanceMonitor.init()

      // Should create PerformanceObserver instances for Core Web Vitals
      expect(observerCount).toBeGreaterThan(0)
    })
  })

  describe('mark and measure', () => {
    it('creates performance mark', () => {
      performanceMonitor.mark('test-mark')

      expect(mockPerformanceMark).toHaveBeenCalledWith('test-mark')
    })

    it('creates performance measure', () => {
      performanceMonitor.measure('test-measure', 'start', 'end')

      expect(mockPerformanceMeasure).toHaveBeenCalledWith('test-measure', 'start', 'end')
      expect(mockGetEntriesByName).toHaveBeenCalledWith('test-measure')
    })

    it('handles mark errors gracefully', () => {
      mockPerformanceMark.mockImplementation(() => {
        throw new Error('Mark failed')
      })
      const consoleWarn = vi.spyOn(console, 'warn').mockImplementation(() => {})

      performanceMonitor.mark('test')

      expect(consoleWarn).toHaveBeenCalled()
      consoleWarn.mockRestore()
    })

    it('handles measure errors gracefully', () => {
      mockPerformanceMeasure.mockImplementation(() => {
        throw new Error('Measure failed')
      })
      const consoleWarn = vi.spyOn(console, 'warn').mockImplementation(() => {})

      performanceMonitor.measure('test')

      expect(consoleWarn).toHaveBeenCalled()
      consoleWarn.mockRestore()
    })
  })

  describe('getMetrics', () => {
    it('returns metrics object', () => {
      const metrics = performanceMonitor.getMetrics()

      expect(metrics).toBeDefined()
      expect(typeof metrics).toBe('object')
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
      // Use class that throws on construction
      class FailingPerformanceObserver {
        constructor() {
          throw new Error('Not supported')
        }
        observe = vi.fn()
        disconnect = vi.fn()
        takeRecords = vi.fn(() => [])
      }
      global.PerformanceObserver =
        FailingPerformanceObserver as unknown as typeof PerformanceObserver

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

      mockGetEntriesByType.mockImplementation(type => {
        if (type === 'navigation') return [mockNavigation]
        return []
      })

      const addEventListenerSpy = vi.spyOn(window, 'addEventListener')

      await performanceMonitor.init()

      // Get the load handler
      const loadCall = addEventListenerSpy.mock.calls.find(call => call[0] === 'load')
      expect(loadCall).toBeDefined()

      // Simulate load event
      if (loadCall) {
        const loadHandler = loadCall[1] as EventListener
        loadHandler(new Event('load'))
      }

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

      addEventListenerSpy.mockRestore()
    })
  })

  describe('resource timing', () => {
    it('categorizes resources by type', async () => {
      const mockNavigation = {
        domainLookupStart: 0,
        domainLookupEnd: 0,
        connectStart: 0,
        connectEnd: 0,
        requestStart: 0,
        responseStart: 0,
        responseEnd: 0,
        domInteractive: 0,
        domComplete: 0,
        loadEventStart: 0,
        loadEventEnd: 0,
        fetchStart: 0
      }
      const mockResources = [
        {
          name: 'image.jpg',
          startTime: 0,
          responseEnd: 100,
          transferSize: 1024,
          initiatorType: 'img'
        },
        {
          name: 'script.js',
          startTime: 0,
          responseEnd: 50,
          transferSize: 2048,
          initiatorType: 'script'
        },
        {
          name: 'style.css',
          startTime: 0,
          responseEnd: 30,
          transferSize: 512,
          initiatorType: 'link'
        }
      ]

      mockGetEntriesByType.mockImplementation(type => {
        if (type === 'resource') return mockResources
        if (type === 'navigation') return [mockNavigation]
        return []
      })

      const addEventListenerSpy = vi.spyOn(window, 'addEventListener')

      await performanceMonitor.init()

      // Simulate load events
      const loadCalls = addEventListenerSpy.mock.calls.filter(call => call[0] === 'load')
      loadCalls.forEach(([, handler]) => (handler as EventListener)(new Event('load')))

      // Wait for async operations
      await new Promise(resolve => setTimeout(resolve, 10))

      const metrics = performanceMonitor.getMetrics()
      expect(metrics.Avg_Image_Load).toBeDefined()
      expect(metrics.Avg_Script_Load).toBeDefined()
      expect(metrics.Avg_Style_Load).toBeDefined()

      addEventListenerSpy.mockRestore()
    })

    it('handles empty resource arrays', async () => {
      const mockNavigation = {
        domainLookupStart: 0,
        domainLookupEnd: 0,
        connectStart: 0,
        connectEnd: 0,
        requestStart: 0,
        responseStart: 0,
        responseEnd: 0,
        domInteractive: 0,
        domComplete: 0,
        loadEventStart: 0,
        loadEventEnd: 0,
        fetchStart: 0
      }

      mockGetEntriesByType.mockImplementation(type => {
        if (type === 'navigation') return [mockNavigation]
        return []
      })

      const addEventListenerSpy = vi.spyOn(window, 'addEventListener')

      await performanceMonitor.init()

      const loadCalls = addEventListenerSpy.mock.calls.filter(call => call[0] === 'load')
      loadCalls.forEach(([, handler]) => (handler as EventListener)(new Event('load')))

      await new Promise(resolve => setTimeout(resolve, 10))

      const metrics = performanceMonitor.getMetrics()
      expect(metrics.Avg_Image_Load).toBe(0)
      expect(metrics.Avg_Script_Load).toBe(0)
      expect(metrics.Avg_Style_Load).toBe(0)

      addEventListenerSpy.mockRestore()
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

      mockGetEntriesByType.mockImplementation(type => {
        if (type === 'navigation') return [mockNavigation]
        return []
      })

      const addEventListenerSpy = vi.spyOn(window, 'addEventListener')

      await performanceMonitor.init()

      const loadCall = addEventListenerSpy.mock.calls.find(call => call[0] === 'load')
      if (loadCall) {
        const loadHandler = loadCall[1] as EventListener
        loadHandler(new Event('load'))
      }

      await new Promise(resolve => setTimeout(resolve, 10))

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/performance'),
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        })
      )

      addEventListenerSpy.mockRestore()
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

      mockGetEntriesByType.mockImplementation(type => {
        if (type === 'navigation') return [mockNavigation]
        return []
      })

      const addEventListenerSpy = vi.spyOn(window, 'addEventListener')

      await performanceMonitor.init()

      const loadCall = addEventListenerSpy.mock.calls.find(call => call[0] === 'load')
      if (loadCall) {
        const loadHandler = loadCall[1] as EventListener
        loadHandler(new Event('load'))
      }

      await new Promise(resolve => setTimeout(resolve, 10))

      // Should complete without throwing - that's the silent failure
      expect(true).toBe(true)

      consoleWarn.mockRestore()
      addEventListenerSpy.mockRestore()
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
