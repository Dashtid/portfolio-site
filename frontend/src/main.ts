import { createApp, type ComponentPublicInstance } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import './style.css'
import './assets/portfolio.css'
import App from './App.vue'
import { analytics } from './utils/analytics'
import { errorTracker } from './utils/errorTracking'
import { performanceMonitor } from './utils/performance'

const app = createApp(App)
const pinia = createPinia()

// Initialize analytics (privacy-compliant)
analytics.init()

// Initialize error tracking
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
  errorTracker.handleVueError(error, instance, info)
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
