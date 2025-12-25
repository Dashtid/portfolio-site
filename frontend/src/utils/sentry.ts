/**
 * Lazy-loaded Sentry initialization
 *
 * This module provides lazy loading for Sentry to reduce initial bundle size
 * by ~100KB. Sentry is only loaded when a DSN is configured.
 */

import type { App } from 'vue'
import type { Router } from 'vue-router'

let sentryInitialized = false
let SentryModule: typeof import('@sentry/vue') | null = null

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
