import { createApp, type ComponentPublicInstance } from 'vue'
import { createPinia } from 'pinia'
import * as Sentry from '@sentry/vue'
import router from './router'
import './style.css'
import './assets/portfolio.css'
import App from './App.vue'
import { analytics } from './utils/analytics'
import { errorTracker } from './utils/errorTracking'
import { performanceMonitor } from './utils/performance'

const app = createApp(App)
const pinia = createPinia()

// Initialize Sentry for error tracking and performance monitoring
const sentryDsn = import.meta.env.VITE_SENTRY_DSN
if (sentryDsn) {
  Sentry.init({
    app,
    dsn: sentryDsn,
    environment: import.meta.env.MODE,
    release: `portfolio-frontend@${import.meta.env.VITE_APP_VERSION || '0.0.0'}`,
    integrations: [
      Sentry.browserTracingIntegration({ router }),
      Sentry.replayIntegration({
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
}

// Initialize analytics (privacy-compliant)
analytics.init()

// Initialize error tracking (custom implementation, works alongside Sentry)
errorTracker.init()

// Initialize performance monitoring
performanceMonitor.init()

// Global error handler for Vue
app.config.errorHandler = (
  err: unknown,
  instance: ComponentPublicInstance | null,
  info: string
) => {
  console.error('Vue Error:', err)
  const error = err instanceof Error ? err : new Error(String(err))

  // Report to custom error tracker
  errorTracker.handleVueError(error, instance, info)

  // Also capture with Sentry if initialized
  if (sentryDsn) {
    Sentry.captureException(error, {
      extra: {
        componentName: (instance as { $options?: { name?: string } })?.$options?.name,
        errorInfo: info
      }
    })
  }
}

// Global warning handler for Vue (development)
if (import.meta.env.DEV) {
  app.config.warnHandler = (
    msg: string,
    _instance: ComponentPublicInstance | null,
    trace: string
  ) => {
    console.warn('Vue Warning:', msg, trace)
  }
}

app.use(pinia)
app.use(router)
app.mount('#app')
