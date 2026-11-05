/**
 * Guards the three properties that make the lazy-Sentry setup a net win rather
 * than a regression:
 *
 *  - no `replayIntegration` (it was ~60% of a 150 KB gzip chunk on every
 *    public page),
 *  - no error lost in the idle window the deferral opens, which matters
 *    because Sentry is the frontend's ONLY error capture, and
 *  - no error from code the site never shipped reaching Sentry: init() wires
 *    the real foreign-code beforeSend (its rule is pinned against the SDK's
 *    real stack parser in sentryForeignCode.spec.ts) and turns off the SDK's
 *    callback wrapping, which would put a frame from this origin under a
 *    bot's own code and make its errors look like ours. The filter's chunk
 *    is requested beside the SDK's and init() never waits for it: events
 *    raised before it arrives wait at most 5 s, and a chunk that fails or
 *    never arrives costs the filter, not Sentry's start-up.
 *
 * All are invisible in a browser: a replay integration that quietly comes
 * back costs bytes nobody measures, errors dropped before init simply never
 * appear in a dashboard nobody is watching at that second, and a filter that
 * is unwired or undermined mails the next bot's error as a new issue.
 *
 * The ignoreErrors entries are pinned here too, one test each, and the
 * service worker one also against the SDK's real inbound filter: its text
 * reaches Sentry as whatever the SDK builds from Chrome's DOMException, and
 * a pattern tested only against strings would test what the author believed
 * that event looks like.
 */
import { beforeEach, afterEach, describe, expect, it, vi } from 'vitest'
import type { ErrorEvent as SentryErrorEvent } from '@sentry/vue'

const init = vi.fn()
const captureExceptionSpy = vi.fn()
const browserTracingIntegration = vi.fn(() => ({ name: 'BrowserTracing' }))
const browserApiErrorsIntegration = vi.fn((options: Record<string, boolean>) => ({
  name: 'BrowserApiErrors',
  options
}))
const replayIntegration = vi.fn(() => ({ name: 'Replay' }))
const setMeasurement = vi.fn()
const setContext = vi.fn()

function sentryVueMock(): Record<string, unknown> {
  return {
    init,
    captureException: captureExceptionSpy,
    browserTracingIntegration,
    browserApiErrorsIntegration,
    replayIntegration,
    setMeasurement,
    setContext
  }
}

vi.mock('@sentry/vue', () => sentryVueMock())

vi.mock('web-vitals', () => ({
  onCLS: vi.fn(),
  onINP: vi.fn(),
  onLCP: vi.fn(),
  onFCP: vi.fn(),
  onTTFB: vi.fn()
}))

const DSN = 'https://publickey@o0.ingest.de.sentry.io/1'

/*
 * Chrome's service worker texts, as Chromium 156 rejected register() and
 * update() with them on 2026-11-05 against a production build (its scope and
 * script URLs swapped for the site's).
 */
const SW = "scope ('https://dashti.se/') with script ('https://dashti.se/sw.js')"
const NEVER_ARRIVED = 'An unknown error occurred when fetching the script.'
/** The 2026-11-05 alert's text. */
const REGISTER_NEVER_ARRIVED = `Failed to register a ServiceWorker for ${SW}: ${NEVER_ARRIVED}`
const UPDATE_NEVER_ARRIVED = `Failed to update a ServiceWorker for ${SW}: ${NEVER_ARRIVED}`
const REGISTER_404 = `Failed to register a ServiceWorker for ${SW}: A bad HTTP response code (404) was received when fetching the script.`

/**
 * Node's own DOMException. happy-dom replaces the global with a plain Error
 * subclass ("[object Error]", no legacy code), from which the SDK builds a
 * different event than from Chrome's, so the platform class is taken from an
 * API that throws one.
 */
const PlatformDOMException = ((): typeof DOMException => {
  try {
    structuredClone(() => {})
  } catch (error) {
    return (error as DOMException).constructor as typeof DOMException
  }
  throw new Error('structuredClone accepted a function')
})()

/**
 * A DOMException as Chrome rejects register() with one: Chromium 156 gave the
 * page an AbortError tagged [object DOMException], code 20, with NO stack
 * property, which is why the SDK reports it as "Error: AbortError: ...".
 */
function chromeDomException(message: string, name: string): DOMException {
  const exception = new PlatformDOMException(message, name)
  delete (exception as { stack?: string }).stack
  return exception
}

const fakeApp = {} as unknown as import('vue').App
const fakeRouter = {} as unknown as import('vue-router').Router

type BeforeSend = (event: unknown) => unknown

/** An error event shaped the way the SDK hands it to beforeSend. */
function eventWithFrame(filename: string, lineno: number, colno: number): Record<string, unknown> {
  return {
    exception: {
      values: [
        { type: 'Error', value: 'boom', stacktrace: { frames: [{ filename, lineno, colno }] } }
      ]
    }
  }
}

/** Thrown by this site's own chunk. */
const ownEvent = (): Record<string, unknown> =>
  eventWithFrame(`${window.location.origin}/assets/js/app-x.js`, 2, 200)

/** Thrown by eval'd automation code, like the 2026-10-06 alert. */
const botEvent = (): Record<string, unknown> => eventWithFrame('<anonymous>', 311, 30)

/** Run the callback requestIdleCallback was handed, then let the async load settle. */
async function runIdleAndSettle(idle: ReturnType<typeof vi.fn>): Promise<void> {
  expect(idle).toHaveBeenCalledTimes(1)
  const scheduled = idle.mock.calls[0][0] as () => void
  scheduled()
  // The dynamic imports of the filter and @sentry/vue, then the web-vitals import.
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
    expect(options.integrations.map(i => i.name)).toEqual(['BrowserApiErrors', 'BrowserTracing'])
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

  describe('errors from code the site never shipped', () => {
    it('applies the real foreign-code filter once its chunk is in, and leaves transactions alone', async () => {
      sentry.initSentry(fakeApp, fakeRouter)
      await runIdleAndSettle(idle)

      const options = init.mock.calls[0][0] as {
        beforeSend: BeforeSend
        beforeSendTransaction?: unknown
      }
      expect(options.beforeSendTransaction).toBeUndefined()
      // Once the chunk has settled the filter runs synchronously.
      await vi.waitFor(() => expect(options.beforeSend(botEvent())).toBeNull())
      const own = ownEvent()
      expect(options.beforeSend(own)).toBe(own)
    })

    it("ignores Microsoft's link-scanner rejection and nothing else", async () => {
      sentry.initSentry(fakeApp, fakeRouter)
      await runIdleAndSettle(idle)

      const options = init.mock.calls[0][0] as { ignoreErrors: RegExp[] }
      // Two entries, each pinned by a test of its own: a third needs one too.
      expect(options.ignoreErrors).toHaveLength(2)
      const [scanner] = options.ignoreErrors
      expect(
        scanner.test(
          'Non-Error promise rejection captured with value: Object Not Found Matching Id:3, MethodName:update, ParamCount:4'
        )
      ).toBe(true)
      expect(scanner.test('Object Not Found')).toBe(false)
      expect(scanner.test('TypeError: Failed to fetch')).toBe(false)
    })

    it("turns off all five kinds of the SDK's callback wrapping", async () => {
      sentry.initSentry(fakeApp, fakeRouter)
      await runIdleAndSettle(idle)

      // A wrapped timer or listener puts a frame from this origin under
      // foreign code, so the filter would keep a bot's error as mixed. Exact
      // equality: a sixth option or a missing one fails here.
      expect(browserApiErrorsIntegration).toHaveBeenCalledTimes(1)
      expect(browserApiErrorsIntegration).toHaveBeenCalledWith({
        setTimeout: false,
        setInterval: false,
        requestAnimationFrame: false,
        XMLHttpRequest: false,
        eventTarget: false
      })
      const options = init.mock.calls[0][0] as {
        integrations: Array<{ name: string; options?: Record<string, boolean> }>
      }
      const apiErrors = options.integrations.find(i => i.name === 'BrowserApiErrors')
      expect(apiErrors?.options).toEqual({
        setTimeout: false,
        setInterval: false,
        requestAnimationFrame: false,
        XMLHttpRequest: false,
        eventTarget: false
      })
    })

    describe("the filter's own chunk", () => {
      afterEach(() => {
        vi.doMock('@sentry/vue', () => sentryVueMock())
        vi.doUnmock('@/utils/sentryForeignCode')
      })

      it("is requested beside the SDK's chunk, not a round trip after it", async () => {
        let releaseSdkChunk = (): void => {}
        const sdkChunk = new Promise<void>(resolve => {
          releaseSdkChunk = resolve
        })
        // The SDK's chunk stays on its way until released.
        vi.doMock('@sentry/vue', async () => {
          await sdkChunk
          return sentryVueMock()
        })
        const requested = vi.fn()
        vi.doMock('@/utils/sentryForeignCode', async importOriginal => {
          requested()
          return importOriginal()
        })
        // Vitest 5 applies queued doMocks during the next module load, and a
        // load that starts while they are being applied does not wait for
        // them. loadSentry() asks for both chunks in the same tick, so the
        // SDK import would still get the earlier, ungated mock. Load a fresh
        // copy of the module under test first: that import applies both mocks.
        vi.resetModules()
        sentry = await import('@/utils/sentry')

        sentry.initSentry(fakeApp, fakeRouter)
        ;(idle.mock.calls[0][0] as () => void)()

        // The SDK's chunk is still on its way, and the filter's is already asked for.
        await vi.waitFor(() => expect(requested).toHaveBeenCalledTimes(1))
        expect(init).not.toHaveBeenCalled()

        releaseSdkChunk()
        await vi.waitFor(() => expect(init).toHaveBeenCalledTimes(1))
        const options = init.mock.calls[0][0] as { beforeSend: BeforeSend }
        await vi.waitFor(() => expect(options.beforeSend(botEvent())).toBeNull())
      })

      it('does not hold init() for it; events raised meanwhile wait, then it applies', async () => {
        let releaseFilterChunk = (): void => {}
        const filterChunk = new Promise<void>(resolve => {
          releaseFilterChunk = resolve
        })
        vi.doMock('@/utils/sentryForeignCode', async importOriginal => {
          await filterChunk
          return importOriginal()
        })

        sentry.initSentry(fakeApp, fakeRouter)
        await runIdleAndSettle(idle)

        // Sentry is up although the filter's chunk is still on its way.
        expect(sentry.isSentryInitialized()).toBe(true)
        const options = init.mock.calls[0][0] as { beforeSend: BeforeSend }
        const own = ownEvent()
        const waitingBot = options.beforeSend(botEvent())
        const waitingOwn = options.beforeSend(own)
        expect(waitingBot).toBeInstanceOf(Promise)

        releaseFilterChunk()
        await expect(waitingBot).resolves.toBeNull()
        await expect(waitingOwn).resolves.toBe(own)
      })

      it('starts Sentry when it never arrives, and releases events unfiltered after 5 s', async () => {
        vi.doMock('@/utils/sentryForeignCode', () => new Promise(() => {}))
        sentry.initSentry(fakeApp, fakeRouter)
        const early = new Error('thrown while Sentry was still on its way')
        window.dispatchEvent(new ErrorEvent('error', { error: early, message: early.message }))

        await runIdleAndSettle(idle)

        expect(sentry.isSentryInitialized()).toBe(true)
        // The idle-window buffer is flushed without waiting for the filter.
        expect(captureExceptionSpy).toHaveBeenCalledTimes(1)
        expect(captureExceptionSpy.mock.calls[0][0]).toBe(early)

        vi.useFakeTimers()
        try {
          const options = init.mock.calls[0][0] as { beforeSend: BeforeSend }
          const bot = botEvent()
          let released: unknown = 'still waiting'
          void (options.beforeSend(bot) as Promise<unknown>).then(result => {
            released = result
          })
          await vi.advanceTimersByTimeAsync(4999)
          expect(released).toBe('still waiting')
          await vi.advanceTimersByTimeAsync(1)
          // Unfiltered, never dropped: the filter fails open.
          expect(released).toBe(bot)
        } finally {
          vi.useRealTimers()
        }
      })

      it('fails open: when it cannot load, Sentry starts without the filter', async () => {
        vi.doMock('@/utils/sentryForeignCode', () => {
          throw new TypeError('Failed to fetch dynamically imported module')
        })
        sentry.initSentry(fakeApp, fakeRouter)
        const early = new Error('thrown while Sentry was still on its way')
        window.dispatchEvent(new ErrorEvent('error', { error: early, message: early.message }))

        await runIdleAndSettle(idle)

        const options = init.mock.calls[0][0] as { beforeSend: BeforeSend; dsn: string }
        expect(options.dsn).toBe(DSN)
        // No filter, so even a bot's event goes out unchanged.
        const bot = botEvent()
        await vi.waitFor(() => expect(options.beforeSend(bot)).toBe(bot))
        expect(sentry.isSentryInitialized()).toBe(true)
        // The idle-window buffer is still flushed into the live SDK.
        expect(captureExceptionSpy).toHaveBeenCalledTimes(1)
        expect(captureExceptionSpy.mock.calls[0][0]).toBe(early)
      })

      it('fails open when the chunk arrives but its export cannot be read', async () => {
        // Vitest's mock of a module without the export throws on the read,
        // as reading it from the undefined a preventDefault()-ed Vite preload
        // wrapper resolves to would.
        vi.doMock('@/utils/sentryForeignCode', () => ({}))
        sentry.initSentry(fakeApp, fakeRouter)

        await runIdleAndSettle(idle)

        const options = init.mock.calls[0][0] as { beforeSend: BeforeSend }
        const bot = botEvent()
        await vi.waitFor(() => expect(options.beforeSend(bot)).toBe(bot))
        expect(sentry.isSentryInitialized()).toBe(true)
      })
    })
  })

  describe('service worker scripts the network never delivered', () => {
    it("ignores Chrome's text for them, from register() and update(), and nothing else", async () => {
      sentry.initSentry(fakeApp, fakeRouter)
      await runIdleAndSettle(idle)

      const options = init.mock.calls[0][0] as { ignoreErrors: RegExp[] }
      const neverArrived = options.ignoreErrors[1]
      expect(neverArrived).toBeInstanceOf(RegExp)
      // Every form the SDK tests: the event message, the exception value and
      // its `type: value`.
      for (const text of [
        // The alert: an AbortError (a cancelled request) with no stack, sent
        // as type Error with the name inside the value, and as the message.
        `AbortError: ${REGISTER_NEVER_ARRIVED}`,
        `Error: AbortError: ${REGISTER_NEVER_ARRIVED}`,
        // Offline, a refused, reset or blocked connection, a truncated or
        // undecodable body: a TypeError.
        REGISTER_NEVER_ARRIVED,
        `TypeError: ${REGISTER_NEVER_ARRIVED}`,
        `TypeError: ${UPDATE_NEVER_ARRIVED}`,
        `Error: AbortError: ${UPDATE_NEVER_ARRIVED}`,
        // Any origin: a preview deployment, a local build.
        `TypeError: Failed to register a ServiceWorker for scope ('http://localhost:4173/') with script ('http://localhost:4173/sw.js'): ${NEVER_ARRIVED}`
      ]) {
        expect(neverArrived.test(text), text).toBe(true)
      }
      for (const text of [
        // The site's own failures, each with Chrome's text, still report.
        `TypeError: ${REGISTER_404}`,
        `TypeError: Failed to update a ServiceWorker for ${SW}: A bad HTTP response code (404) was received when fetching the script.`,
        `Error: SecurityError: Failed to register a ServiceWorker for ${SW}: The script has an unsupported MIME type ('text/html').`,
        `Error: SecurityError: Failed to register a ServiceWorker for ${SW}: The script does not have a MIME type.`,
        `Error: SecurityError: Failed to register a ServiceWorker for ${SW}: The script resource is behind a redirect, which is disallowed.`,
        `TypeError: Failed to update a ServiceWorker for ${SW}: The script resource is behind a redirect, which is disallowed.`,
        `TypeError: Failed to register a ServiceWorker for ${SW}: ServiceWorker script evaluation failed`,
        `Error: SecurityError: Failed to register a ServiceWorker for ${SW}: An SSL certificate error occurred when fetching the script.`,
        "Error: SecurityError: Failed to register a ServiceWorker: The origin of the provided scriptURL ('https://other.example') does not match the current origin ('https://dashti.se').",
        "TypeError: Failed to register a ServiceWorker: The URL protocol of the script ('data:text/javascript,1') is not supported.",
        // Nor anything else: the sentence without the call that raised it,
        // the sentence with more after it, a failed fetch.
        NEVER_ARRIVED,
        `${REGISTER_NEVER_ARRIVED} Retrying.`,
        'TypeError: Failed to fetch'
      ]) {
        expect(neverArrived.test(text), text).toBe(false)
      }
    })

    it("drops what the real SDK builds from Chrome's rejection, and keeps a 404's", async () => {
      sentry.initSentry(fakeApp, fakeRouter)
      await runIdleAndSettle(idle)
      const { ignoreErrors } = init.mock.calls[0][0] as { ignoreErrors: RegExp[] }

      // The real SDK, unmocked: its event builder, and its inbound filter
      // (the default integrations carry the same filter under its deprecated
      // name, InboundFilters) fed this init's ignoreErrors.
      const real = await vi.importActual<typeof import('@sentry/vue')>('@sentry/vue')
      let built: SentryErrorEvent | undefined
      let delivered = 0
      const client = new real.BrowserClient({
        dsn: DSN,
        ignoreErrors,
        sendClientReports: false,
        stackParser: real.defaultStackParser,
        integrations: [
          // The event as built, then the filter.
          {
            name: 'Recorder',
            processEvent: event => {
              built = event as SentryErrorEvent
              return event
            }
          },
          real.eventFiltersIntegration()
        ],
        // Whatever gets this far passed the filter. Nothing is sent anywhere.
        beforeSend: () => {
          delivered++
          return null
        },
        transport: () => ({ send: () => Promise.resolve({}), flush: () => Promise.resolve(true) })
      })
      client.init()
      const capture = async (exception: unknown): Promise<SentryErrorEvent | undefined> => {
        built = undefined
        delivered = 0
        client.captureException(exception)
        await client.flush(2000)
        return built
      }

      const alert = chromeDomException(REGISTER_NEVER_ARRIVED, 'AbortError')
      expect([Object.prototype.toString.call(alert), alert.code, 'stack' in alert]).toEqual([
        '[object DOMException]',
        20,
        false
      ])
      const alertEvent = await capture(alert)
      // Exactly the alert's event, and dropped.
      expect(alertEvent?.exception?.values?.[0]).toMatchObject({
        type: 'Error',
        value: `AbortError: ${REGISTER_NEVER_ARRIVED}`
      })
      expect(alertEvent?.tags).toEqual({ 'DOMException.code': '20' })
      expect(delivered).toBe(0)

      // Any other network failure: Chrome's TypeError, with a stack. Dropped.
      expect(
        (await capture(new TypeError(REGISTER_NEVER_ARRIVED)))?.exception?.values?.[0]
      ).toMatchObject({ type: 'TypeError', value: REGISTER_NEVER_ARRIVED })
      expect(delivered).toBe(0)

      // A 404 is the site's own failure, kept as Chrome raises it and in the
      // alert's shape alike: the text decides, not the type.
      expect((await capture(new TypeError(REGISTER_404)))?.exception?.values?.[0]).toMatchObject({
        type: 'TypeError',
        value: REGISTER_404
      })
      expect(delivered).toBe(1)
      await capture(chromeDomException(REGISTER_404, 'AbortError'))
      expect(delivered).toBe(1)
    })
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
