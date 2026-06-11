/**
 * Unit tests for the admin router auth guard (FRONTEND-TESTS-02).
 *
 * The guard is wired onto vue-router's `beforeEach` in `main.ts`. Its
 * job is to redirect unauthenticated users away from `requiresAuth`
 * routes, redirect already-authenticated users away from `requiresGuest`
 * routes (so the login page bounces them back to the dashboard), and
 * crucially to SKIP the `/auth/me` lookup on public routes so anonymous
 * visitors don't generate a spurious 401 on every page load.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import type { RouteLocationNormalized, NavigationGuardNext } from 'vue-router'
import { createAdminAuthGuard, type AuthStoreLike } from '@/router/authGuard'

const route = (overrides: Partial<RouteLocationNormalized> = {}): RouteLocationNormalized => {
  return {
    fullPath: '/',
    path: '/',
    name: undefined,
    params: {},
    query: {},
    hash: '',
    matched: [],
    meta: {},
    redirectedFrom: undefined,
    ...overrides
  } as RouteLocationNormalized
}

// Helper: build a minimal matched record with a meta flag, matching
// the shape that `to.matched.some(r => r.meta.requiresAuth)` checks.
const matchedRecord = (meta: Record<string, unknown>) =>
  ({ meta }) as RouteLocationNormalized['matched'][number]

const makeStore = (overrides: Partial<AuthStoreLike> = {}): AuthStoreLike => ({
  isInitialized: false,
  isAuthenticated: false,
  initializeAuth: vi.fn().mockResolvedValue(undefined),
  ...overrides
})

describe('admin auth guard', () => {
  let next: NavigationGuardNext

  beforeEach(() => {
    next = vi.fn() as unknown as NavigationGuardNext
  })

  describe('public routes', () => {
    it('does NOT resolve the auth store on a public route', async () => {
      const resolver = vi.fn().mockResolvedValue(makeStore())
      const guard = createAdminAuthGuard(resolver)

      await guard(route({ path: '/', matched: [matchedRecord({})] }), route(), next)

      // The whole point of the early-exit: anonymous visitors must not
      // fire /auth/me on every navigation.
      expect(resolver).not.toHaveBeenCalled()
      expect(next).toHaveBeenCalledWith()
    })

    it('skips auth store even when both flags happen to be undefined', async () => {
      const resolver = vi.fn().mockResolvedValue(makeStore())
      const guard = createAdminAuthGuard(resolver)

      await guard(
        route({ path: '/experience/foo', matched: [matchedRecord({ title: 'Experience' })] }),
        route(),
        next
      )

      expect(resolver).not.toHaveBeenCalled()
      expect(next).toHaveBeenCalledWith()
    })
  })

  describe('requiresAuth routes', () => {
    it('redirects unauthenticated users to admin-login', async () => {
      const store = makeStore({ isInitialized: true, isAuthenticated: false })
      const guard = createAdminAuthGuard(() => store)

      await guard(
        route({ path: '/admin', matched: [matchedRecord({ requiresAuth: true })] }),
        route(),
        next
      )

      expect(next).toHaveBeenCalledWith({ name: 'admin-login' })
    })

    it('lets authenticated users through', async () => {
      const store = makeStore({ isInitialized: true, isAuthenticated: true })
      const guard = createAdminAuthGuard(() => store)

      await guard(
        route({ path: '/admin', matched: [matchedRecord({ requiresAuth: true })] }),
        route(),
        next
      )

      expect(next).toHaveBeenCalledWith()
    })

    it('calls initializeAuth when the store is not yet initialised', async () => {
      const store = makeStore({ isInitialized: false, isAuthenticated: false })
      const guard = createAdminAuthGuard(() => store)

      await guard(
        route({ path: '/admin', matched: [matchedRecord({ requiresAuth: true })] }),
        route(),
        next
      )

      expect(store.initializeAuth).toHaveBeenCalledTimes(1)
      expect(next).toHaveBeenCalledWith({ name: 'admin-login' })
    })

    it('does NOT call initializeAuth when the store is already initialised', async () => {
      const store = makeStore({ isInitialized: true, isAuthenticated: true })
      const guard = createAdminAuthGuard(() => store)

      await guard(
        route({ path: '/admin', matched: [matchedRecord({ requiresAuth: true })] }),
        route(),
        next
      )

      expect(store.initializeAuth).not.toHaveBeenCalled()
      expect(next).toHaveBeenCalledWith()
    })

    it('redirects deep-linked unauthenticated users to login (child route inherits parent flag)', async () => {
      const store = makeStore({ isInitialized: true, isAuthenticated: false })
      const guard = createAdminAuthGuard(() => store)

      // /admin/companies inherits requiresAuth via the parent matched record.
      await guard(
        route({
          path: '/admin/companies',
          matched: [matchedRecord({ requiresAuth: true }), matchedRecord({})]
        }),
        route(),
        next
      )

      expect(next).toHaveBeenCalledWith({ name: 'admin-login' })
    })
  })

  describe('requiresGuest routes', () => {
    it('bounces an already-authenticated user away from /admin/login', async () => {
      const store = makeStore({ isInitialized: true, isAuthenticated: true })
      const guard = createAdminAuthGuard(() => store)

      await guard(
        route({ path: '/admin/login', matched: [matchedRecord({ requiresGuest: true })] }),
        route(),
        next
      )

      expect(next).toHaveBeenCalledWith({ name: 'admin-dashboard' })
    })

    it('lets unauthenticated users see the login page', async () => {
      const store = makeStore({ isInitialized: true, isAuthenticated: false })
      const guard = createAdminAuthGuard(() => store)

      await guard(
        route({ path: '/admin/login', matched: [matchedRecord({ requiresGuest: true })] }),
        route(),
        next
      )

      expect(next).toHaveBeenCalledWith()
    })

    it('still initializes auth before deciding (so a logged-in user is detected via cookie)', async () => {
      const store = makeStore({ isInitialized: false, isAuthenticated: false })
      const initWithFlip = vi.fn().mockImplementation(async () => {
        // Simulate the store flipping to authenticated during init
        store.isAuthenticated = true
        store.isInitialized = true
      })
      store.initializeAuth = initWithFlip
      const guard = createAdminAuthGuard(() => store)

      await guard(
        route({ path: '/admin/login', matched: [matchedRecord({ requiresGuest: true })] }),
        route(),
        next
      )

      expect(initWithFlip).toHaveBeenCalledTimes(1)
      expect(next).toHaveBeenCalledWith({ name: 'admin-dashboard' })
    })
  })

  describe('resolver behaviour', () => {
    it('awaits an async resolver before reading the store', async () => {
      let resolved = false
      const store = makeStore({ isInitialized: true, isAuthenticated: true })
      const resolver = () =>
        new Promise<AuthStoreLike>(r => {
          setTimeout(() => {
            resolved = true
            r(store)
          }, 0)
        })
      const guard = createAdminAuthGuard(resolver)

      await guard(
        route({ path: '/admin', matched: [matchedRecord({ requiresAuth: true })] }),
        route(),
        next
      )

      expect(resolved).toBe(true)
      expect(next).toHaveBeenCalledWith()
    })

    it('accepts a synchronous resolver', async () => {
      const store = makeStore({ isInitialized: true, isAuthenticated: true })
      const guard = createAdminAuthGuard(() => store)

      await guard(
        route({ path: '/admin', matched: [matchedRecord({ requiresAuth: true })] }),
        route(),
        next
      )

      expect(next).toHaveBeenCalledWith()
    })
  })
})
