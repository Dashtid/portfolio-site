import { ViteSSG } from 'vite-ssg'
import { createPinia } from 'pinia'
import { nextTick } from 'vue'
import type { ComponentPublicInstance } from 'vue'
import type { RouteLocationNormalized, NavigationGuardNext } from 'vue-router'
import { routes, scrollBehavior, DEFAULT_TITLE } from './router'
import './style.css'
import './assets/portfolio.css'
import App from './App.vue'
import { analytics as umamiAnalytics } from './utils/analytics'
import analyticsService from './services/analytics'
import { errorTracker } from './utils/errorTracking'
import { performanceMonitor } from './utils/performance'
import { initSentry, captureException, isSentryInitialized } from './utils/sentry'

export const createApp = ViteSSG(
  App,
  { routes, base: import.meta.env.BASE_URL, scrollBehavior },
  ({ app, router, isClient }) => {
    const pinia = createPinia()
    app.use(pinia)

    if (isClient) {
      // Navigation guards — client-only (localStorage / window not available during SSG)
      router.beforeEach(
        async (
          to: RouteLocationNormalized,
          _from: RouteLocationNormalized,
          next: NavigationGuardNext
        ) => {
          // Lazy-import auth store inside the guard to avoid SSG tree-shaking issues
          const { useAuthStore } = await import('./stores/auth')
          const authStore = useAuthStore()

          if (!authStore.isInitialized) {
            await authStore.initializeAuth()
          }

          if (to.matched.some(record => record.meta.requiresAuth)) {
            if (!authStore.isAuthenticated) {
              next({ name: 'admin-login' })
            } else {
              next()
            }
          } else if (to.matched.some(record => record.meta.requiresGuest)) {
            if (authStore.isAuthenticated) {
              next({ name: 'admin-dashboard' })
            } else {
              next()
            }
          } else {
            next()
          }
        }
      )

      // Update document title and track page views after navigation
      router.afterEach((to: RouteLocationNormalized) => {
        const title = to.meta.title as string | undefined
        document.title = title || DEFAULT_TITLE

        analyticsService.trackPageView(to.path, to.name as string | undefined)

        // Move focus to main content after route change so screen readers announce new page.
        // tabindex="-1" on each <main id="main-content"> makes it focusable without tab order.
        nextTick(() => {
          const target = document.getElementById('main-content') as HTMLElement | null
          target?.focus({ preventScroll: false })
        })
      })

      // Initialize Sentry lazily (only loads ~100KB bundle if DSN is configured)
      initSentry(app, router).catch(error => {
        if (import.meta.env.DEV) {
          console.warn('[Sentry] Lazy init failed:', error)
        }
      })

      // Initialize analytics (privacy-compliant)
      umamiAnalytics.init()

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

        errorTracker.handleVueError(error, instance, info)

        if (isSentryInitialized()) {
          captureException(error, {
            componentName: (instance as { $options?: { name?: string } })?.$options?.name,
            errorInfo: info
          })
        }
      }

      // Global warning handler (development only)
      if (import.meta.env.DEV) {
        app.config.warnHandler = (
          msg: string,
          _instance: ComponentPublicInstance | null,
          trace: string
        ) => {
          console.warn('Vue Warning:', msg, trace)
        }
      }
    }
  }
)

// Export includedRoutes so vite-ssg can enumerate routes to pre-render.
// Excludes admin paths (auth-gated, must remain SPA).
// Dynamically fetches experience IDs from the API for /experience/:id routes.
export async function includedRoutes(paths: string[]) {
  const publicPaths = paths.filter(p => !p.startsWith('/admin'))

  const apiUrl = import.meta.env.VITE_API_URL || 'https://dashti.se'

  try {
    const res = await fetch(`${apiUrl}/api/v1/companies/`)
    if (res.ok) {
      const companies: Array<{ id: string }> = await res.json()
      const experiencePaths = companies.map(c => `/experience/${c.id}`)
      // Replace the parameterised template paths with real paths
      return [
        ...publicPaths.filter(p => p !== '/experience/:id' && p !== '/company/:id'),
        ...experiencePaths
      ]
    }
  } catch {
    // API not reachable at build time — skip dynamic routes, pre-render static pages only
    if (process.env.NODE_ENV !== 'production') {
      console.warn('[SSG] Could not fetch experience IDs — skipping dynamic routes')
    }
  }

  return publicPaths.filter(p => p !== '/experience/:id' && p !== '/company/:id')
}
