/**
 * Lazily loaded Sentry, with Web Vitals reporting.
 *
 * Two deliberate departures from the stock @sentry/vue setup, both measured
 * against the live site on 2026-09-20 (Lighthouse 12.6, mobile: performance
 * 87, LCP 3.4 s, TBT 160 ms; desktop was already 100):
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
 * [!] Deferring would normally open a window in which errors are lost, and
 * here that window is not covered by anything else: `VITE_ERROR_TRACKING_ENABLED`
 * is NOT forwarded to the Vercel build (ci-cd.yml passes only VITE_APP_VERSION
 * and VITE_SENTRY_DSN), so `utils/errorTracking` is inert in production and
 * Sentry is the ONLY capture there. Hence the buffer below: window `error` and
 * `unhandledrejection` listeners go up synchronously, and everything they catch
 * is replayed into Sentry the moment it initialises. Do not remove the buffer
 * while keeping the deferral.
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
 * lets the unused ones actually leave. Keep it destructured.
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
    // Named destructuring, never the namespace object — see SentryApi above.
    const { init, browserTracingIntegration, captureException, setMeasurement, setContext } =
      await import('@sentry/vue')

    init({
      app,
      dsn,
      environment: import.meta.env.MODE,
      release: `portfolio-frontend@${import.meta.env.VITE_APP_VERSION || '0.0.0'}`,
      // Tracing only. Replay is deliberately absent — see the file header.
      integrations: [browserTracingIntegration({ router })],
      tracesSampleRate: import.meta.env.PROD ? 0.1 : 1.0,
      tracePropagationTargets: ['localhost', /^https:\/\/dashti\.se/, /^https:\/\/api\.dashti\.se/]
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
