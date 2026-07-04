import { ViteSSG } from 'vite-ssg'
import { createPinia } from 'pinia'
import { nextTick } from 'vue'
import type { ComponentPublicInstance } from 'vue'
import type { RouteLocationNormalized } from 'vue-router'
import { routes, scrollBehavior, DEFAULT_TITLE } from './router'
import { createAdminAuthGuard } from './router/authGuard'
import '@fontsource-variable/geist'
// Order matters: tailwind.css MUST come first. style.css's element
// defaults share @layer base with Tailwind preflight, and within a layer
// later source order wins ties — imported the other way round, preflight
// (h1-h6 font-size:inherit, a color:inherit, input background:transparent)
// silently kills every element default in style.css. This order also keeps
// Tailwind's own `properties` layer lowest-priority, as its runtime
// fallback for non-@property browsers requires.
import './styles/tailwind.css'
import './style.css'
import App from './App.vue'
import analyticsService from './services/analytics'
import { errorTracker } from './utils/errorTracking'
import { initSentry, captureException, isSentryInitialized } from './utils/sentry'

export const createApp = ViteSSG(
  App,
  { routes, base: import.meta.env.BASE_URL, scrollBehavior },
  ({ app, router, isClient, initialState }) => {
    const pinia = createPinia()
    app.use(pinia)

    // Transfer Pinia state across the SSR→client boundary. During SSG the
    // rendered store state is written to initialState (vite-ssg serializes it
    // into the page HTML); on the client it's read back so components see
    // SSG-fetched data immediately instead of re-fetching. See
    // stores/experienceDetail.ts for the concrete use.
    if (isClient) {
      pinia.state.value = (initialState.pinia as typeof pinia.state.value) ?? {}
    } else {
      initialState.pinia = pinia.state.value
    }

    if (isClient) {
      // Navigation guards — client-only (localStorage / window not available
      // during SSG). The guard body is extracted to `router/authGuard.ts`
      // so it can be unit-tested without spinning up the full app
      // (FRONTEND-TESTS-02). Lazy-import the auth store inside the
      // resolver to keep SSG tree-shaking able to drop it on builds
      // that don't include /admin routes.
      router.beforeEach(
        createAdminAuthGuard(async () => {
          const { useAuthStore } = await import('./stores/auth')
          return useAuthStore()
        })
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

      // Initialize error tracking (custom implementation, works alongside Sentry)
      errorTracker.init()

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

  const apiUrl = import.meta.env.VITE_API_URL || 'https://api.dashti.se'

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
