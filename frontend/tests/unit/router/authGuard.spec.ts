/**
 * Unit tests for the admin router auth guard (FRONTEND-TESTS-02).
 *
 * The guard is wired onto vue-router's `beforeEach` in `main.ts`. It is
 * a RETURN-style guard (vue-router 5 deprecates the next() callback):
 * `true` continues, a route location redirects. Its job is to redirect
 * unauthenticated users away from `requiresAuth` routes, redirect
 * already-authenticated users away from `requiresGuest` routes (so the
 * login page bounces them back to the dashboard), and crucially to SKIP
 * the `/auth/me` lookup on public routes so anonymous visitors don't
 * generate a spurious 401 on every page load.
 */
import { describe, it, expect, vi } from 'vitest'
import type { RouteLocationNormalized } from 'vue-router'
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
  describe('public routes', () => {
    it('does NOT resolve the auth store on a public route', async () => {
      const resolver = vi.fn().mockResolvedValue(makeStore())
      const guard = createAdminAuthGuard(resolver)

      const result = await guard(route({ path: '/', matched: [matchedRecord({})] }))

      // The whole point of the early-exit: anonymous visitors must not
      // fire /auth/me on every navigation.
      expect(resolver).not.toHaveBeenCalled()
      expect(result).toBe(true)
    })

    it('skips auth store even when both flags happen to be undefined', async () => {
      const resolver = vi.fn().mockResolvedValue(makeStore())
      const guard = createAdminAuthGuard(resolver)

      const result = await guard(
        route({ path: '/experience/foo', matched: [matchedRecord({ title: 'Experience' })] })
      )

      expect(resolver).not.toHaveBeenCalled()
      expect(result).toBe(true)
    })
  })

  describe('requiresAuth routes', () => {
    it('redirects unauthenticated users to admin-login', async () => {
      const store = makeStore({ isInitialized: true, isAuthenticated: false })
      const guard = createAdminAuthGuard(() => store)

      const result = await guard(
        route({ path: '/admin', matched: [matchedRecord({ requiresAuth: true })] })
      )

      expect(result).toEqual({ name: 'admin-login' })
    })

    it('lets authenticated users through', async () => {
      const store = makeStore({ isInitialized: true, isAuthenticated: true })
      const guard = createAdminAuthGuard(() => store)

      const result = await guard(
        route({ path: '/admin', matched: [matchedRecord({ requiresAuth: true })] })
      )

      expect(result).toBe(true)
    })

    it('calls initializeAuth when the store is not yet initialised', async () => {
      const store = makeStore({ isInitialized: false, isAuthenticated: false })
      const guard = createAdminAuthGuard(() => store)

      const result = await guard(
        route({ path: '/admin', matched: [matchedRecord({ requiresAuth: true })] })
      )

      expect(store.initializeAuth).toHaveBeenCalledTimes(1)
      expect(result).toEqual({ name: 'admin-login' })
    })

    it('does NOT call initializeAuth when the store is already initialised', async () => {
      const store = makeStore({ isInitialized: true, isAuthenticated: true })
      const guard = createAdminAuthGuard(() => store)

      const result = await guard(
        route({ path: '/admin', matched: [matchedRecord({ requiresAuth: true })] })
      )

      expect(store.initializeAuth).not.toHaveBeenCalled()
      expect(result).toBe(true)
    })

    it('redirects deep-linked unauthenticated users to login (child route inherits parent flag)', async () => {
      const store = makeStore({ isInitialized: true, isAuthenticated: false })
      const guard = createAdminAuthGuard(() => store)

      // /admin/companies inherits requiresAuth via the parent matched record.
      const result = await guard(
        route({
          path: '/admin/companies',
          matched: [matchedRecord({ requiresAuth: true }), matchedRecord({})]
        })
      )

      expect(result).toEqual({ name: 'admin-login' })
    })
  })

  describe('requiresGuest routes', () => {
    it('bounces an already-authenticated user away from /admin/login', async () => {
      const store = makeStore({ isInitialized: true, isAuthenticated: true })
      const guard = createAdminAuthGuard(() => store)

      const result = await guard(
        route({ path: '/admin/login', matched: [matchedRecord({ requiresGuest: true })] })
      )

      expect(result).toEqual({ name: 'admin-dashboard' })
    })

    it('lets unauthenticated users see the login page', async () => {
      const store = makeStore({ isInitialized: true, isAuthenticated: false })
      const guard = createAdminAuthGuard(() => store)

      const result = await guard(
        route({ path: '/admin/login', matched: [matchedRecord({ requiresGuest: true })] })
      )

      expect(result).toBe(true)
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

      const result = await guard(
        route({ path: '/admin/login', matched: [matchedRecord({ requiresGuest: true })] })
      )

      expect(initWithFlip).toHaveBeenCalledTimes(1)
      expect(result).toEqual({ name: 'admin-dashboard' })
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

      const result = await guard(
        route({ path: '/admin', matched: [matchedRecord({ requiresAuth: true })] })
      )

      expect(resolved).toBe(true)
      expect(result).toBe(true)
    })

    it('accepts a synchronous resolver', async () => {
      const store = makeStore({ isInitialized: true, isAuthenticated: true })
      const guard = createAdminAuthGuard(() => store)

      const result = await guard(
        route({ path: '/admin', matched: [matchedRecord({ requiresAuth: true })] })
      )

      expect(result).toBe(true)
    })
  })
})
