import { ViteSSG } from 'vite-ssg'
import { createPinia } from 'pinia'
import type { ComponentPublicInstance } from 'vue'
import type { RouteLocationNormalized } from 'vue-router'
import { routes, scrollBehavior, DEFAULT_TITLE } from './router'
import { createAdminAuthGuard } from './router/authGuard'
import '@fontsource-variable/geist'
import '@fontsource-variable/geist-mono'
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

// D3-SEC-03: vite-ssg hardcodes its state transport as an EXECUTABLE
// inline script (`<script>window.__INITIAL_STATE__="..."</script>`) whose
// content changes every build — incompatible with a hash-based CSP. The
// onFinished hook in vite.config.ts rewrites that tag into a non-executing
// <script type="application/json"> data block; this shim reads the block
// back into window.__INITIAL_STATE__ before vite-ssg's client bootstrap
// (which runs inside the ViteSSG() call below) looks for it. The block's
// content is the same double-encoded JSON string the executable form
// carried, so deserializeState sees an identical value. No element (dev
// server, tests) means no baked state — exactly as before.
if (!import.meta.env.SSR) {
  const bakedState = document.getElementById('__INITIAL_STATE__')
  if (bakedState?.textContent) {
    ;(window as unknown as { __INITIAL_STATE__?: unknown }).__INITIAL_STATE__ = JSON.parse(
      bakedState.textContent
    )
  }
}

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
      // D3-FE-03: a tab left open across a deploy holds references to old
      // content-hashed chunks that 404 on the new deployment (the SW's
      // skipWaiting/cleanupOutdatedCaches drops them too) — every lazy
      // navigation just died until a manual refresh. Reload once to pick up
      // the fresh manifest; the sessionStorage stamp stops a reload loop if
      // the failure is something else (offline, corporate proxy).
      const RELOAD_STAMP = 'chunk-reload-at'
      const reloadOnStaleChunk = (targetPath?: string): void => {
        const last = Number(sessionStorage.getItem(RELOAD_STAMP) || 0)
        if (Date.now() - last < 60_000) return
        sessionStorage.setItem(RELOAD_STAMP, String(Date.now()))
        window.location.assign(targetPath ?? window.location.pathname)
      }
      window.addEventListener('vite:preloadError', event => {
        event.preventDefault()
        reloadOnStaleChunk()
      })
      router.onError((error, to) => {
        if (
          error instanceof Error &&
          /Failed to fetch dynamically imported module|error loading dynamically imported module|Importing a module script failed/i.test(
            error.message
          )
        ) {
          reloadOnStaleChunk(to.fullPath)
        }
      })

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

      // Update document title and track page views after navigation.
      // NOTE: route-change focus management lives in App.vue's Transition
      // @after-enter hook, NOT here (D3-A11Y-01) — at afterEach+nextTick the
      // out-in transition still shows the OUTGOING view, so focusing
      // #main-content grabbed a node about to be unmounted and focus fell
      // back to <body>, silently breaking screen-reader announcements.
      router.afterEach((to: RouteLocationNormalized) => {
        const title = to.meta.title as string | undefined
        document.title = title || DEFAULT_TITLE

        analyticsService.trackPageView(to.path, to.name as string | undefined)
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
  },
  // `hydration: true` is what makes the prerendered HTML real: without it
  // vite-ssg mounts the client with plain createApp(), which WIPES the
  // container and re-renders everything from scratch on every page load —
  // the SSG output was serving as nothing more than a splash screen, and
  // with an empty __INITIAL_STATE__ the rebuild blocked on the API
  // refetch, blanking the page (the CI-only `h1Count = 0` e2e failure).
  // Hydration requires every route component to keep setup() synchronous —
  // SSR data fetching goes through onServerPrefetch (see
  // HomeView/ExperienceDetail) — and the client render tree to match the
  // server HTML exactly.
  { hydration: true }
)

// Export includedRoutes so vite-ssg can enumerate routes to pre-render.
// Excludes admin paths (auth-gated, must remain SPA).
// Dynamically fetches experience IDs from the API for /experience/:id routes.
export async function includedRoutes(paths: string[]) {
  // Drop admin (auth-gated SPA) and every parameterised template path —
  // including the '/:pathMatch(.*)*' catch-all, which would otherwise be
  // "prerendered" as a literal directory name.
  const publicPaths = paths.filter(p => !p.startsWith('/admin') && !p.includes(':'))

  // D3-FEAT-03: article routes come from the build-time content glob —
  // no network involved, so they prerender even when the API is down.
  const { writingPosts } = await import('./data/writing')
  const articlePaths = writingPosts.map(p => `/writing/${p.slug}`)

  const apiUrl = import.meta.env.VITE_API_URL || 'https://api.dashti.se'

  try {
    const res = await fetch(`${apiUrl}/api/v1/companies/`)
    if (res.ok) {
      const companies: Array<{ id: string }> = await res.json()
      const experiencePaths = companies.map(c => `/experience/${c.id}`)
      return [...publicPaths, ...articlePaths, ...experiencePaths]
    }
  } catch {
    // API not reachable at build time — skip dynamic routes, pre-render static pages only
    if (process.env.NODE_ENV !== 'production') {
      console.warn('[SSG] Could not fetch experience IDs — skipping dynamic routes')
    }
  }

  return [...publicPaths, ...articlePaths]
}
