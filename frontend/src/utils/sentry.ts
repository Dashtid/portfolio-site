/**
 * Lazily loaded Sentry, with Web Vitals reporting.
 *
 * Three deliberate departures from the stock @sentry/vue setup. The first
 * two were measured against the live site on 2026-09-20 (Lighthouse 12.6,
 * mobile: performance 87, LCP 3.4 s, TBT 160 ms; desktop was already 100):
 *
 * 1. NO session replay. `replayIntegration` was the bulk of the ~150 KB gzip
 *    (454 KB raw) this chunk cost — three times the app's own entry chunk —
 *    and it is the single largest thing on the homepage. What it bought on a
 *    public, static, mostly-four-page portfolio was a `maskAllText` +
 *    `blockAllMedia` replay: a grey wireframe of pages any reader can simply
 *    open. Wrong trade. If replay is ever wanted back, scope it to /admin
 *    (a real app surface with real state) rather than the public routes.
 *
 * 2. The import is scheduled on IDLE rather than fired during mount, so it
 *    stops competing with hydration for both network and main thread.
 *
 * 3. A `beforeSend` that drops errors raised only by code this site never
 *    shipped (browser automation, extensions, userscripts), in its own small
 *    lazy chunk that downloads beside the SDK's and fails open; see
 *    ./sentryForeignCode.ts for the trap it closes. init() never waits for
 *    that chunk: only events raised before it arrives wait, at most
 *    FILTER_WAIT_MS, then go out unfiltered (deferredForeignCodeFilter lists
 *    what that wait can cost). The SDK's callback wrapping is off for the
 *    same reason (see loadSentry).
 *
 * [!] Deferring would normally open a window in which errors are lost, and
 * here that window is not covered by anything else: `VITE_ERROR_TRACKING_ENABLED`
 * is NOT forwarded to the Vercel build (ci-cd.yml and rebake-frontend.yml
 * forward VITE_APP_VERSION and VITE_SENTRY_DSN as the only VITE_* values, plus
 * the SENTRY_AUTH_TOKEN/ORG/PROJECT upload trio), so `utils/errorTracking` is
 * inert in production and Sentry is the ONLY capture there. Hence the buffer
 * below: window `error` and `unhandledrejection` listeners go up synchronously,
 * and everything they catch is replayed into Sentry the moment it initialises.
 * Do not remove the buffer while keeping the deferral.
 */

import type { App } from 'vue'
import type { Router } from 'vue-router'

/**
 * The exports actually used, held individually rather than as the module
 * namespace object.
 *
 * [!] This is load-bearing for bundle size, not style. `SentryModule = await
 * import('@sentry/vue')` followed by `SentryModule.foo()` gives the bundler a
 * namespace object whose property reads it cannot statically resolve, so it
 * must retain every export — and `@sentry/vue`'s entry is
 * `export * from '@sentry/browser'`, which means replay, feedback and
 * profiling all stay in the chunk no matter what the integrations array says.
 * Measured 2026-09-20: dropping replayIntegration from init() while keeping
 * the namespace import changed the emitted chunk by ZERO bytes (454476 raw
 * both ways, identical hash). Destructuring the named exports below is what
 * lets the unused ones actually leave. Keep it destructured, and keep the
 * foreign-code filter's import a statement of its own: folding the two into
 * one Promise.all with array destructuring loses that direct
 * `const { ... } = await import()` form, and the Sentry chunk went from 46 KB
 * to 140 KB gzip when that was tried on 2026-10-11.
 */
interface SentryApi {
  captureException: typeof import('@sentry/vue').captureException
  setMeasurement: typeof import('@sentry/vue').setMeasurement
  setContext: typeof import('@sentry/vue').setContext
}

let sentryInitialized = false
let loadScheduled = false
let sentry: SentryApi | null = null

/**
 * How long to wait for genuine idle before loading anyway. Sentry that never
 * loads on a busy page is worse than Sentry that loads late.
 */
const IDLE_TIMEOUT_MS = 3000

/** Fallback delay for browsers with no requestIdleCallback. */
const FALLBACK_DELAY_MS = 1200

/** Cap on pre-init errors held in memory. A page throwing more than this is not short of signal. */
const MAX_BUFFERED_ERRORS = 10

/**
 * How long an event may wait for the foreign-code filter's chunk before it is
 * sent unfiltered. Sentry itself never waits for that chunk.
 */
const FILTER_WAIT_MS = 5000

type ForeignCodeFilter = typeof import('./sentryForeignCode').dropForeignCodeErrors
type FilterableEvent = Parameters<ForeignCodeFilter>[0]
type FilterResult = ReturnType<ForeignCodeFilter>

/**
 * The beforeSend handed to init() before the filter's chunk has arrived.
 *
 * [!] init() must not wait for that chunk. It did for one review round, and a
 * filter request only 150 ms slower than the SDK's then lost an early
 * ErrorBoundary error 4 times out of 4 (2026-10-11); a request that never
 * settled kept Sentry off for the whole page view. So each EVENT waits
 * instead: once the chunk has settled the filter runs synchronously, and
 * until then an event waits for it at most FILTER_WAIT_MS and goes out
 * unfiltered if the chunk failed or is still on its way.
 *
 * Never rejects and never throws: a rejected or throwing beforeSend drops the
 * event, which is exactly what a fail-open filter must not do.
 *
 * What the wait costs, only while the chunk is pending. In every natural load
 * measured on 2026-10-11 the 731-byte filter chunk finished before the SDK's,
 * so the window never opened, but when it does: an event held here dies with
 * the page if it is closed, reloaded (the ErrorBoundary's "Try Again"
 * included) or left before the chunk settles or the wait ends, where a build
 * without the filter would have sent it at once; and a burst of held events
 * can overflow the SDK's buffers (64 in the client, then 40 in the fetch
 * transport when they are all released together), so the excess is dropped
 * as queue_overflow. On a bandwidth-limited link the extra request also
 * delays the SDK chunk slightly (+11 ms at 1.6 Mbps, +50 ms at 400 kbps).
 */
function deferredForeignCodeFilter(
  filterLoad: Promise<ForeignCodeFilter | undefined>
): (event: FilterableEvent) => FilterResult | Promise<FilterResult> {
  let settled = false
  let filter: ForeignCodeFilter | undefined
  void filterLoad.then(loaded => {
    filter = loaded
    settled = true
  })
  const apply = (event: FilterableEvent, loaded: ForeignCodeFilter | undefined): FilterResult => {
    try {
      return loaded ? loaded(event) : event
    } catch {
      return event
    }
  }
  return event => {
    if (settled) return apply(event, filter)
    return new Promise<ForeignCodeFilter | undefined>(resolve => {
      const timer = window.setTimeout(() => resolve(undefined), FILTER_WAIT_MS)
      void filterLoad.then(loaded => {
        window.clearTimeout(timer)
        resolve(loaded)
      })
    }).then(
      loaded => apply(event, loaded),
      () => event
    )
  }
}

interface BufferedError {
  error: Error
  context?: Record<string, unknown>
}

let bufferedErrors: BufferedError[] = []
let earlyErrorHandler: ((event: ErrorEvent) => void) | null = null
let earlyRejectionHandler: ((event: PromiseRejectionEvent) => void) | null = null

function bufferError(error: Error, context?: Record<string, unknown>): void {
  if (bufferedErrors.length >= MAX_BUFFERED_ERRORS) return
  bufferedErrors.push({ error, context })
}

/**
 * Catch errors thrown between mount and Sentry being ready. Removed again as
 * soon as the load settles, so Sentry's own globalHandlers integration never
 * double-reports alongside these.
 */
function startEarlyCapture(): void {
  if (earlyErrorHandler) return

  earlyErrorHandler = (event: ErrorEvent): void => {
    const error =
      event.error instanceof Error ? event.error : new Error(event.message || 'Unknown error')
    bufferError(error, { captured_by: 'window.error' })
  }
  earlyRejectionHandler = (event: PromiseRejectionEvent): void => {
    const reason: unknown = event.reason
    const error = reason instanceof Error ? reason : new Error(String(reason))
    bufferError(error, { captured_by: 'unhandledrejection' })
  }

  window.addEventListener('error', earlyErrorHandler)
  window.addEventListener('unhandledrejection', earlyRejectionHandler)
}

function stopEarlyCapture(): void {
  if (earlyErrorHandler) {
    window.removeEventListener('error', earlyErrorHandler)
    earlyErrorHandler = null
  }
  if (earlyRejectionHandler) {
    window.removeEventListener('unhandledrejection', earlyRejectionHandler)
    earlyRejectionHandler = null
  }
}

function flushBufferedErrors(): void {
  if (!sentry) return
  for (const { error, context } of bufferedErrors) {
    sentry.captureException(error, {
      // Flag the delay so a timestamp that predates the Sentry session is not read as clock skew.
      extra: { ...context, buffered_before_sentry_load: true }
    })
  }
}

function whenIdle(run: () => void): void {
  const idle = (
    window as unknown as {
      requestIdleCallback?: (cb: () => void, opts?: { timeout: number }) => number
    }
  ).requestIdleCallback

  if (typeof idle === 'function') {
    idle(run, { timeout: IDLE_TIMEOUT_MS })
  } else {
    window.setTimeout(run, FALLBACK_DELAY_MS)
  }
}

/**
 * Initialize Web Vitals reporting to Sentry.
 * Reports Core Web Vitals: LCP, CLS, INP (replaces FID), FCP, TTFB
 */
async function initWebVitals(): Promise<void> {
  if (!sentry) return

  try {
    const { onCLS, onINP, onLCP, onFCP, onTTFB } = await import('web-vitals')

    const reportVital = (metric: { name: string; value: number; rating: string }): void => {
      if (!sentry) return

      // Report as Sentry measurement
      sentry.setMeasurement(metric.name, metric.value, 'millisecond')

      // Also set as context for debugging
      sentry.setContext('web_vitals', {
        [metric.name]: {
          value: metric.value,
          rating: metric.rating
        }
      })

      if (import.meta.env.DEV) {
        console.log(`[Web Vitals] ${metric.name}: ${metric.value.toFixed(2)} (${metric.rating})`)
      }
    }

    // Core Web Vitals
    onLCP(reportVital) // Largest Contentful Paint
    onCLS(reportVital) // Cumulative Layout Shift
    onINP(reportVital) // Interaction to Next Paint (replaces FID)

    // Additional metrics
    onFCP(reportVital) // First Contentful Paint
    onTTFB(reportVital) // Time to First Byte
  } catch (error) {
    if (import.meta.env.DEV) {
      console.warn('[Sentry] Failed to initialize Web Vitals:', error)
    }
  }
}

async function loadSentry(app: App, router: Router, dsn: string): Promise<void> {
  try {
    // The foreign-code filter, in its own small lazy chunk. Requested first,
    // so it downloads beside the SDK's chunk, and never awaited before init()
    // (see deferredForeignCodeFilter). Fail-open: a chunk that cannot load
    // costs the filter, and Sentry still starts on time; what events raised
    // while it is pending risk is listed there.
    // [!] The failure handler is the second argument of THIS .then, not a
    // .catch: the build moves this .then inside Vite's preload wrapper, so a
    // failed load is settled before the wrapper sees it. A rejection that
    // reached the wrapper would fire vite:preloadError, and main.ts answers
    // that with a page reload. The trailing .catch is for a bundler that
    // leaves the .then outside: the wrapper then resolves to undefined once
    // main.ts has called preventDefault(), and reading the export throws.
    const foreignCodeFilter = import('./sentryForeignCode')
      .then(
        module => module.dropForeignCodeErrors,
        () => undefined
      )
      .catch(() => undefined)
    const beforeSend = deferredForeignCodeFilter(foreignCodeFilter)
    // Named destructuring, never the namespace object — see SentryApi above.
    const {
      init,
      browserTracingIntegration,
      browserApiErrorsIntegration,
      captureException,
      setMeasurement,
      setContext
    } = await import('@sentry/vue')

    init({
      app,
      dsn,
      environment: import.meta.env.MODE,
      release: `portfolio-frontend@${import.meta.env.VITE_APP_VERSION || '0.0.0'}`,
      integrations: [
        // [!] By default the SDK wraps every callback handed to setTimeout,
        // setInterval, requestAnimationFrame, XMLHttpRequest and
        // addEventListener in a function of its own. Minified, that wrapper
        // has a short name the SDK's /sentryWrapped/ frame strip never
        // matches, and it wraps foreign callbacks too: automation that binds
        // the timers after Sentry has loaded gets a frame from THIS origin
        // under its own code, and the foreign-code filter would then keep its
        // errors as ours. Errors in the site's own callbacks still reach the
        // globalHandlers integration (window error and unhandledrejection)
        // and Vue's errorHandler, their own frames intact. What they lose is
        // the wrapper's own detail: its frame, the mechanism data (handler,
        // target) and the callback arguments it attached as extra.arguments.
        // The SDK's fetch, XHR and History instrumentation is separate and
        // stays on; sentryForeignCode.ts lists what that still lets through.
        browserApiErrorsIntegration({
          setTimeout: false,
          setInterval: false,
          requestAnimationFrame: false,
          XMLHttpRequest: false,
          eventTarget: false
        }),
        // Tracing. Replay is deliberately absent; see the file header.
        browserTracingIntegration({ router })
      ],
      tracesSampleRate: import.meta.env.PROD ? 0.1 : 1.0,
      tracePropagationTargets: ['localhost', /^https:\/\/dashti\.se/, /^https:\/\/api\.dashti\.se/],
      // CefSharp-based hosts, such as the link scanner behind Outlook Safe
      // Links, reject with this exact text when they open a mailed link. The
      // site never produces it.
      ignoreErrors: [/Object Not Found Matching Id:\d+, MethodName:\w+, ParamCount:\d+/],
      // Errors raised only by code the site never shipped stop here.
      beforeSend
    })

    sentry = { captureException, setMeasurement, setContext }
    sentryInitialized = true
    flushBufferedErrors()

    await initWebVitals()
  } catch (error) {
    // Fail silently - Sentry is optional
    if (import.meta.env.DEV) {
      console.warn('[Sentry] Failed to initialize:', error)
    }
  } finally {
    // Either Sentry owns error capture now, or it never will. Both cases want
    // these listeners gone rather than shadowing Sentry's own or leaking.
    stopEarlyCapture()
    bufferedErrors = []
  }
}

/**
 * Schedule Sentry. Returns immediately; the bundle loads when the main thread
 * next goes idle (or after IDLE_TIMEOUT_MS, whichever comes first). No-op when
 * no DSN is configured, which is every local build and every test run.
 */
export function initSentry(app: App, router: Router): void {
  const dsn = import.meta.env.VITE_SENTRY_DSN
  if (!dsn || sentryInitialized || loadScheduled) return

  loadScheduled = true
  startEarlyCapture()
  whenIdle(() => {
    void loadSentry(app, router, dsn)
  })
}

/**
 * Capture an exception. Safe to call before Sentry has finished loading: while
 * a load is pending the error is buffered and sent once Sentry is up. Dropped
 * only when no DSN is configured at all.
 */
export function captureException(error: Error, context?: Record<string, unknown>): void {
  if (sentryInitialized && sentry) {
    sentry.captureException(error, { extra: context })
    return
  }
  if (loadScheduled) {
    bufferError(error, context)
  }
}

/**
 * True once Sentry is live. Note this is FALSE during the idle window, so do
 * not gate captureException() on it — that call handles the window itself.
 */
export function isSentryInitialized(): boolean {
  return sentryInitialized
}

/** Test seam: reset module state between specs. */
export function __resetSentryForTests(): void {
  sentryInitialized = false
  loadScheduled = false
  sentry = null
  bufferedErrors = []
  stopEarlyCapture()
}
