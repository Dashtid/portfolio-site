import type { NavigationGuardNext, RouteLocationNormalized } from 'vue-router'

/**
 * Shape of the auth store the guard depends on. Decoupled from the
 * Pinia store so the guard can be unit-tested without spinning up the
 * full store + axios stack.
 */
export interface AuthStoreLike {
  isInitialized: boolean
  isAuthenticated: boolean
  initializeAuth: () => Promise<void>
}

/**
 * Lazy resolver for the auth store. The production wiring imports the
 * store inside the guard (so SSG tree-shaking can omit it for builds
 * that don't include `/admin` routes); tests substitute a stub.
 */
export type AuthStoreResolver = () => AuthStoreLike | Promise<AuthStoreLike>

/**
 * Admin auth guard for the Vue Router ``beforeEach`` hook.
 *
 * Behaviour:
 *   - Routes flagged ``requiresAuth`` or ``requiresGuest`` trigger an
 *     ``initializeAuth()`` call when the store isn't initialised yet —
 *     so a deep-link to ``/admin/companies`` correctly resolves the
 *     user's session before we decide whether to bounce to login.
 *   - Public routes (no ``requires*`` flag) skip the auth lookup
 *     entirely; unauthenticated visitors don't fire ``/auth/me`` and
 *     don't see a 401 on every page load.
 *   - ``requiresAuth`` + unauthenticated -> bounce to ``admin-login``.
 *   - ``requiresGuest`` + authenticated -> bounce to ``admin-dashboard``
 *     (so an already-logged-in admin can't land on the login page).
 *   - All other combinations -> ``next()``.
 *
 * Extracted from ``main.ts`` for FRONTEND-TESTS-02 so the guard can be
 * exercised in isolation.
 */
export const createAdminAuthGuard = (resolveAuthStore: AuthStoreResolver) => {
  return async (
    to: RouteLocationNormalized,
    _from: RouteLocationNormalized,
    next: NavigationGuardNext
  ): Promise<void> => {
    const needsAuthState = to.matched.some(r => r.meta.requiresAuth || r.meta.requiresGuest)

    if (!needsAuthState) {
      next()
      return
    }

    const authStore = await resolveAuthStore()

    if (!authStore.isInitialized) {
      await authStore.initializeAuth()
    }

    const requiresAuth = to.matched.some(r => r.meta.requiresAuth)
    const requiresGuest = to.matched.some(r => r.meta.requiresGuest)

    if (requiresAuth && !authStore.isAuthenticated) {
      next({ name: 'admin-login' })
      return
    }

    if (requiresGuest && authStore.isAuthenticated) {
      next({ name: 'admin-dashboard' })
      return
    }

    next()
  }
}
