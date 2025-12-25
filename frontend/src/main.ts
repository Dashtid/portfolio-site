import { createApp, type ComponentPublicInstance } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import './style.css'
import './assets/portfolio.css'
import App from './App.vue'
import { analytics } from './utils/analytics'
import { errorTracker } from './utils/errorTracking'
import { performanceMonitor } from './utils/performance'
import { initSentry, captureException, isSentryInitialized } from './utils/sentry'

const app = createApp(App)
const pinia = createPinia()

// Initialize Sentry lazily (only loads ~100KB bundle if DSN is configured)
initSentry(app, router).catch(error => {
  if (import.meta.env.DEV) {
    console.warn('[Sentry] Lazy init failed:', error)
  }
})

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
  if (import.meta.env.DEV) {
    console.error('Vue Error:', err)
  }
  const error = err instanceof Error ? err : new Error(String(err))

  // Report to custom error tracker
  errorTracker.handleVueError(error, instance, info)

  // Also capture with Sentry if initialized
  if (isSentryInitialized()) {
    captureException(error, {
      componentName: (instance as { $options?: { name?: string } })?.$options?.name,
      errorInfo: info
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
