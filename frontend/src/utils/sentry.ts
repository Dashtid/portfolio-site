/**
 * Lazy-loaded Sentry initialization with Web Vitals reporting
 *
 * This module provides lazy loading for Sentry to reduce initial bundle size
 * by ~100KB. Sentry is only loaded when a DSN is configured.
 *
 * Web Vitals (LCP, CLS, INP, FCP, TTFB) are automatically reported to Sentry
 * for performance monitoring.
 */

import type { App } from 'vue'
import type { Router } from 'vue-router'

let sentryInitialized = false
let SentryModule: typeof import('@sentry/vue') | null = null

/**
 * Initialize Web Vitals reporting to Sentry
 * Reports Core Web Vitals: LCP, CLS, INP (replaces FID), FCP, TTFB
 */
async function initWebVitals(): Promise<void> {
  if (!SentryModule) return

  try {
    const { onCLS, onINP, onLCP, onFCP, onTTFB } = await import('web-vitals')

    const reportVital = (metric: { name: string; value: number; rating: string }): void => {
      if (!SentryModule) return

      // Report as Sentry measurement
      SentryModule.setMeasurement(metric.name, metric.value, 'millisecond')

      // Also set as context for debugging
      SentryModule.setContext('web_vitals', {
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

/**
 * Initialize Sentry lazily
 * Only loads the Sentry bundle if DSN is configured
 */
export async function initSentry(app: App, router: Router): Promise<void> {
  const dsn = import.meta.env.VITE_SENTRY_DSN
  if (!dsn || sentryInitialized) return

  try {
    // Dynamically import Sentry only when needed
    SentryModule = await import('@sentry/vue')

    SentryModule.init({
      app,
      dsn,
      environment: import.meta.env.MODE,
      release: `portfolio-frontend@${import.meta.env.VITE_APP_VERSION || '0.0.0'}`,
      integrations: [
        SentryModule.browserTracingIntegration({ router }),
        SentryModule.replayIntegration({
          maskAllText: true,
          blockAllMedia: true
        })
      ],
      tracesSampleRate: import.meta.env.PROD ? 0.1 : 1.0,
      replaysSessionSampleRate: 0.1,
      replaysOnErrorSampleRate: 1.0,
      tracePropagationTargets: [
        'localhost',
        /^https:\/\/dashti\.se/,
        /^https:\/\/dashti-portfolio-backend\.fly\.dev/
      ]
    })

    sentryInitialized = true

    // Initialize Web Vitals reporting after Sentry is ready
    await initWebVitals()
  } catch (error) {
    // Fail silently - Sentry is optional
    if (import.meta.env.DEV) {
      console.warn('[Sentry] Failed to initialize:', error)
    }
  }
}

/**
 * Capture an exception with Sentry (if initialized)
 */
export function captureException(error: Error, context?: Record<string, unknown>): void {
  if (!sentryInitialized || !SentryModule) return

  SentryModule.captureException(error, {
    extra: context
  })
}

/**
 * Check if Sentry is initialized
 */
export function isSentryInitialized(): boolean {
  return sentryInitialized
}
