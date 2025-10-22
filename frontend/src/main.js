import { createApp } from 'vue'
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
app.config.errorHandler = (err, instance, info) => {
  console.error('Vue Error:', err)
  errorTracker.handleVueError(err, instance, info)
}

// Global warning handler for Vue (development)
if (import.meta.env.DEV) {
  app.config.warnHandler = (msg, instance, trace) => {
    console.warn('Vue Warning:', msg, trace)
  }
}

app.use(pinia)
app.use(router)
app.mount('#app')
