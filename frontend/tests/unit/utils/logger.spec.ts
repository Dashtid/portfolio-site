/**
 * Tests for logger utility (TypeScript)
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'

// We need to test the Logger class directly, so we import after setting up mocks
describe('logger utility', () => {
  let consoleDebugSpy: ReturnType<typeof vi.spyOn>
  let consoleLogSpy: ReturnType<typeof vi.spyOn>
  let consoleInfoSpy: ReturnType<typeof vi.spyOn>
  let consoleWarnSpy: ReturnType<typeof vi.spyOn>
  let consoleErrorSpy: ReturnType<typeof vi.spyOn>
  let consoleGroupSpy: ReturnType<typeof vi.spyOn>
  let consoleGroupEndSpy: ReturnType<typeof vi.spyOn>
  let consoleTimeSpy: ReturnType<typeof vi.spyOn>
  let consoleTimeEndSpy: ReturnType<typeof vi.spyOn>

  beforeEach(() => {
    consoleDebugSpy = vi.spyOn(console, 'debug').mockImplementation(() => {})
    consoleLogSpy = vi.spyOn(console, 'log').mockImplementation(() => {})
    consoleInfoSpy = vi.spyOn(console, 'info').mockImplementation(() => {})
    consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})
    consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    consoleGroupSpy = vi.spyOn(console, 'group').mockImplementation(() => {})
    consoleGroupEndSpy = vi.spyOn(console, 'groupEnd').mockImplementation(() => {})
    consoleTimeSpy = vi.spyOn(console, 'time').mockImplementation(() => {})
    consoleTimeEndSpy = vi.spyOn(console, 'timeEnd').mockImplementation(() => {})
  })

  afterEach(() => {
    vi.clearAllMocks()
    vi.restoreAllMocks()
  })

  describe('Logger class', () => {
    it('exports default logger instance', async () => {
      const { default: logger } = await import('@/utils/logger')
      expect(logger).toBeDefined()
    })

    it('exports pre-configured loggers', async () => {
      const {
        logger,
        analyticsLogger,
        authLogger,
        apiLogger,
        themeLogger,
        performanceLogger,
        errorLogger
      } = await import('@/utils/logger')

      expect(logger).toBeDefined()
      expect(analyticsLogger).toBeDefined()
      expect(authLogger).toBeDefined()
      expect(apiLogger).toBeDefined()
      expect(themeLogger).toBeDefined()
      expect(performanceLogger).toBeDefined()
      expect(errorLogger).toBeDefined()
    })

    it('exports createLogger factory function', async () => {
      const { createLogger } = await import('@/utils/logger')
      expect(createLogger).toBeDefined()
      expect(typeof createLogger).toBe('function')
    })

    it('createLogger creates new logger with prefix', async () => {
      const { createLogger } = await import('@/utils/logger')
      const customLogger = createLogger('Custom')
      expect(customLogger).toBeDefined()
    })
  })

  describe('logging methods in dev mode', () => {
    // Note: import.meta.env.DEV is true in test environment

    it('debug logs message with prefix', async () => {
      const { createLogger } = await import('@/utils/logger')
      const testLogger = createLogger('Test')

      testLogger.debug('debug message', { extra: 'data' })

      expect(consoleDebugSpy).toHaveBeenCalledWith('[Test] debug message', { extra: 'data' })
    })

    it('log logs message with prefix', async () => {
      const { createLogger } = await import('@/utils/logger')
      const testLogger = createLogger('Test')

      testLogger.log('log message')

      expect(consoleLogSpy).toHaveBeenCalledWith('[Test] log message')
    })

    it('info logs message with prefix', async () => {
      const { createLogger } = await import('@/utils/logger')
      const testLogger = createLogger('Test')

      testLogger.info('info message', 123)

      expect(consoleInfoSpy).toHaveBeenCalledWith('[Test] info message', 123)
    })

    it('warn logs message with prefix', async () => {
      const { createLogger } = await import('@/utils/logger')
      const testLogger = createLogger('Test')

      testLogger.warn('warn message')

      expect(consoleWarnSpy).toHaveBeenCalledWith('[Test] warn message')
    })

    it('error always logs even when enabled', async () => {
      const { createLogger } = await import('@/utils/logger')
      const testLogger = createLogger('Test')

      testLogger.error('error message', new Error('test'))

      expect(consoleErrorSpy).toHaveBeenCalledWith('[Test] error message', expect.any(Error))
    })

    it('logs without prefix when prefix is empty', async () => {
      const { logger } = await import('@/utils/logger')

      logger.log('no prefix message')

      expect(consoleLogSpy).toHaveBeenCalledWith('no prefix message')
    })
  })

  describe('child logger', () => {
    it('creates child logger with combined prefix', async () => {
      const { createLogger } = await import('@/utils/logger')
      const parentLogger = createLogger('Parent')
      const childLogger = parentLogger.child('Child')

      childLogger.log('child message')

      expect(consoleLogSpy).toHaveBeenCalledWith('[Parent:Child] child message')
    })

    it('creates child logger from logger without prefix', async () => {
      const { logger } = await import('@/utils/logger')
      const childLogger = logger.child('Child')

      childLogger.log('message')

      expect(consoleLogSpy).toHaveBeenCalledWith('[Child] message')
    })
  })

  describe('group method', () => {
    it('groups logs together', async () => {
      const { createLogger } = await import('@/utils/logger')
      const testLogger = createLogger('Test')
      const groupFn = vi.fn()

      testLogger.group('Group Label', groupFn)

      expect(consoleGroupSpy).toHaveBeenCalledWith('[Test] Group Label')
      expect(groupFn).toHaveBeenCalled()
      expect(consoleGroupEndSpy).toHaveBeenCalled()
    })

    it('executes group function', async () => {
      const { createLogger } = await import('@/utils/logger')
      const testLogger = createLogger('Test')
      let executed = false

      testLogger.group('Label', () => {
        executed = true
      })

      expect(executed).toBe(true)
    })
  })

  describe('time methods', () => {
    it('time starts console timer', async () => {
      const { createLogger } = await import('@/utils/logger')
      const testLogger = createLogger('Test')

      testLogger.time('Timer')

      expect(consoleTimeSpy).toHaveBeenCalledWith('[Test] Timer')
    })

    it('timeEnd stops console timer', async () => {
      const { createLogger } = await import('@/utils/logger')
      const testLogger = createLogger('Test')

      testLogger.timeEnd('Timer')

      expect(consoleTimeEndSpy).toHaveBeenCalledWith('[Test] Timer')
    })
  })

  describe('multiple arguments', () => {
    it('passes multiple arguments to console methods', async () => {
      const { createLogger } = await import('@/utils/logger')
      const testLogger = createLogger('Test')

      testLogger.log('message', 1, 2, 3, { obj: true })

      expect(consoleLogSpy).toHaveBeenCalledWith('[Test] message', 1, 2, 3, { obj: true })
    })

    it('debug accepts multiple arguments', async () => {
      const { createLogger } = await import('@/utils/logger')
      const testLogger = createLogger('Test')

      testLogger.debug('debug', 'arg1', 'arg2')

      expect(consoleDebugSpy).toHaveBeenCalledWith('[Test] debug', 'arg1', 'arg2')
    })

    it('info accepts multiple arguments', async () => {
      const { createLogger } = await import('@/utils/logger')
      const testLogger = createLogger('Test')

      testLogger.info('info', [1, 2, 3])

      expect(consoleInfoSpy).toHaveBeenCalledWith('[Test] info', [1, 2, 3])
    })

    it('warn accepts multiple arguments', async () => {
      const { createLogger } = await import('@/utils/logger')
      const testLogger = createLogger('Test')

      testLogger.warn('warning', { detail: 'info' })

      expect(consoleWarnSpy).toHaveBeenCalledWith('[Test] warning', { detail: 'info' })
    })

    it('error accepts multiple arguments', async () => {
      const { createLogger } = await import('@/utils/logger')
      const testLogger = createLogger('Test')

      testLogger.error('error', 'context', { stack: 'trace' })

      expect(consoleErrorSpy).toHaveBeenCalledWith('[Test] error', 'context', { stack: 'trace' })
    })
  })

  describe('pre-configured loggers', () => {
    it('analyticsLogger has Analytics prefix', async () => {
      const { analyticsLogger } = await import('@/utils/logger')

      analyticsLogger.log('test')

      expect(consoleLogSpy).toHaveBeenCalledWith('[Analytics] test')
    })

    it('authLogger has Auth prefix', async () => {
      const { authLogger } = await import('@/utils/logger')

      authLogger.log('test')

      expect(consoleLogSpy).toHaveBeenCalledWith('[Auth] test')
    })

    it('apiLogger has API prefix', async () => {
      const { apiLogger } = await import('@/utils/logger')

      apiLogger.log('test')

      expect(consoleLogSpy).toHaveBeenCalledWith('[API] test')
    })

    it('themeLogger has Theme prefix', async () => {
      const { themeLogger } = await import('@/utils/logger')

      themeLogger.log('test')

      expect(consoleLogSpy).toHaveBeenCalledWith('[Theme] test')
    })

    it('performanceLogger has Performance prefix', async () => {
      const { performanceLogger } = await import('@/utils/logger')

      performanceLogger.log('test')

      expect(consoleLogSpy).toHaveBeenCalledWith('[Performance] test')
    })

    it('errorLogger has Error prefix', async () => {
      const { errorLogger } = await import('@/utils/logger')

      errorLogger.log('test')

      expect(consoleLogSpy).toHaveBeenCalledWith('[Error] test')
    })
  })
})
