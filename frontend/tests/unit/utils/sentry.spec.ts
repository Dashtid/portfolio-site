/**
 * Guards the two properties that make the lazy-Sentry setup a net win rather
 * than a regression:
 *
 *  - no `replayIntegration` (it was ~60% of a 150 KB gzip chunk on every
 *    public page), and
 *  - no error lost in the idle window the deferral opens, which matters
 *    because `VITE_ERROR_TRACKING_ENABLED` is not forwarded to the Vercel
 *    build, so Sentry is production's ONLY error capture.
 *
 * Both are invisible in a browser: a replay integration that quietly comes
 * back costs bytes nobody measures, and errors dropped before init simply
 * never appear in a dashboard nobody is watching at that second.
 */
import { beforeEach, afterEach, describe, expect, it, vi } from 'vitest'

const init = vi.fn()
const captureExceptionSpy = vi.fn()
const browserTracingIntegration = vi.fn(() => ({ name: 'BrowserTracing' }))
const replayIntegration = vi.fn(() => ({ name: 'Replay' }))
const setMeasurement = vi.fn()
const setContext = vi.fn()

vi.mock('@sentry/vue', () => ({
  init,
  captureException: captureExceptionSpy,
  browserTracingIntegration,
  replayIntegration,
  setMeasurement,
  setContext
}))

vi.mock('web-vitals', () => ({
  onCLS: vi.fn(),
  onINP: vi.fn(),
  onLCP: vi.fn(),
  onFCP: vi.fn(),
  onTTFB: vi.fn()
}))

const DSN = 'https://publickey@o0.ingest.de.sentry.io/1'

const fakeApp = {} as unknown as import('vue').App
const fakeRouter = {} as unknown as import('vue-router').Router

/** Run the callback requestIdleCallback was handed, then let the async load settle. */
async function runIdleAndSettle(idle: ReturnType<typeof vi.fn>): Promise<void> {
  expect(idle).toHaveBeenCalledTimes(1)
  const scheduled = idle.mock.calls[0][0] as () => void
  scheduled()
  // Two ticks: the dynamic import of @sentry/vue, then the web-vitals import.
  await vi.waitFor(() => expect(init).toHaveBeenCalled())
  await Promise.resolve()
}

describe('utils/sentry', () => {
  let idle: ReturnType<typeof vi.fn>
  let sentry: typeof import('@/utils/sentry')

  beforeEach(async () => {
    vi.clearAllMocks()
    vi.stubEnv('VITE_SENTRY_DSN', DSN)
    idle = vi.fn()
    vi.stubGlobal('requestIdleCallback', idle)
    vi.resetModules()
    sentry = await import('@/utils/sentry')
    sentry.__resetSentryForTests()
  })

  afterEach(() => {
    sentry.__resetSentryForTests()
    vi.unstubAllEnvs()
    vi.unstubAllGlobals()
  })

  it('does not load anything synchronously — the import waits for idle', () => {
    sentry.initSentry(fakeApp, fakeRouter)

    expect(idle).toHaveBeenCalledTimes(1)
    expect(init).not.toHaveBeenCalled()
    expect(sentry.isSentryInitialized()).toBe(false)
  })

  it('passes a timeout so a permanently busy page still gets Sentry', () => {
    sentry.initSentry(fakeApp, fakeRouter)

    expect(idle.mock.calls[0][1]).toEqual({ timeout: 3000 })
  })

  it('initialises WITHOUT session replay', async () => {
    sentry.initSentry(fakeApp, fakeRouter)
    await runIdleAndSettle(idle)

    expect(replayIntegration).not.toHaveBeenCalled()

    const options = init.mock.calls[0][0] as {
      integrations: Array<{ name: string }>
      replaysSessionSampleRate?: number
      replaysOnErrorSampleRate?: number
      dsn: string
    }
    expect(options.dsn).toBe(DSN)
    expect(options.integrations.map(i => i.name)).toEqual(['BrowserTracing'])
    // A replay sample rate left behind would silently re-enable it on a bump
    // that changes the default integration set.
    expect(options.replaysSessionSampleRate).toBeUndefined()
    expect(options.replaysOnErrorSampleRate).toBeUndefined()
    expect(sentry.isSentryInitialized()).toBe(true)
  })

  it('does nothing at all when no DSN is configured', () => {
    vi.stubEnv('VITE_SENTRY_DSN', '')

    sentry.initSentry(fakeApp, fakeRouter)

    expect(idle).not.toHaveBeenCalled()
    expect(init).not.toHaveBeenCalled()
  })

  it('schedules the load only once across repeat calls', () => {
    sentry.initSentry(fakeApp, fakeRouter)
    sentry.initSentry(fakeApp, fakeRouter)

    expect(idle).toHaveBeenCalledTimes(1)
  })

  describe('the idle window', () => {
    it('forwards a captureException raised before Sentry loaded', async () => {
      sentry.initSentry(fakeApp, fakeRouter)
      const early = new Error('thrown while Sentry was still on its way')

      sentry.captureException(early, { componentName: 'HomeView' })
      expect(captureExceptionSpy).not.toHaveBeenCalled()

      await runIdleAndSettle(idle)

      expect(captureExceptionSpy).toHaveBeenCalledTimes(1)
      const [err, opts] = captureExceptionSpy.mock.calls[0] as [
        Error,
        { extra: Record<string, unknown> }
      ]
      expect(err).toBe(early)
      expect(opts.extra.buffered_before_sentry_load).toBe(true)
      expect(opts.extra.componentName).toBe('HomeView')
    })

    it('buffers an uncaught window error and flushes it on load', async () => {
      sentry.initSentry(fakeApp, fakeRouter)
      const boom = new Error('uncaught')

      window.dispatchEvent(new ErrorEvent('error', { error: boom, message: 'uncaught' }))

      await runIdleAndSettle(idle)

      expect(captureExceptionSpy).toHaveBeenCalledTimes(1)
      const [err, opts] = captureExceptionSpy.mock.calls[0] as [
        Error,
        { extra: Record<string, unknown> }
      ]
      expect(err).toBe(boom)
      expect(opts.extra.captured_by).toBe('window.error')
    })

    it('stops its own listeners once Sentry owns capture, so nothing double-reports', async () => {
      sentry.initSentry(fakeApp, fakeRouter)
      await runIdleAndSettle(idle)
      captureExceptionSpy.mockClear()

      window.dispatchEvent(new ErrorEvent('error', { error: new Error('later'), message: 'later' }))
      await Promise.resolve()

      // Sentry's own globalHandlers integration covers this now; our temporary
      // listener must be gone rather than reporting it a second time.
      expect(captureExceptionSpy).not.toHaveBeenCalled()
    })

    it('sends straight through once Sentry is live', async () => {
      sentry.initSentry(fakeApp, fakeRouter)
      await runIdleAndSettle(idle)
      captureExceptionSpy.mockClear()

      const late = new Error('after init')
      sentry.captureException(late)

      expect(captureExceptionSpy).toHaveBeenCalledWith(late, { extra: undefined })
    })

    it('drops a captureException entirely when no DSN is configured', () => {
      vi.stubEnv('VITE_SENTRY_DSN', '')
      sentry.initSentry(fakeApp, fakeRouter)

      sentry.captureException(new Error('nowhere to send this'))

      expect(captureExceptionSpy).not.toHaveBeenCalled()
    })

    it('caps the buffer so a throw-loop cannot grow it without bound', async () => {
      sentry.initSentry(fakeApp, fakeRouter)

      for (let i = 0; i < 25; i++) {
        sentry.captureException(new Error(`spam ${i}`))
      }
      await runIdleAndSettle(idle)

      expect(captureExceptionSpy).toHaveBeenCalledTimes(10)
    })
  })

  it('falls back to setTimeout where requestIdleCallback does not exist', async () => {
    vi.stubGlobal('requestIdleCallback', undefined)
    vi.useFakeTimers()
    try {
      sentry.initSentry(fakeApp, fakeRouter)
      expect(init).not.toHaveBeenCalled()

      vi.advanceTimersByTime(1200)
      await vi.waitFor(() => expect(init).toHaveBeenCalledTimes(1))
    } finally {
      vi.useRealTimers()
    }
  })
})
