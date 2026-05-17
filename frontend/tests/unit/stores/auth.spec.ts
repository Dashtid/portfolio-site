/**
 * Tests for Auth Store
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '@/stores/auth'
import apiClient from '@/api/client'

vi.mock('@/api/client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn()
  }
}))

vi.mock('@/utils/logger', () => {
  const noopLogger = {
    error: vi.fn(),
    warn: vi.fn(),
    log: vi.fn(),
    debug: vi.fn(),
    info: vi.fn()
  }
  return {
    authLogger: noopLogger,
    createLogger: vi.fn(() => noopLogger),
    logger: noopLogger
  }
})

describe('Auth Store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()

    Object.defineProperty(window, 'location', {
      value: {
        href: 'http://localhost:3000',
        search: '',
        pathname: '/admin'
      },
      writable: true,
      configurable: true
    })

    window.history.replaceState = vi.fn()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('initial state', () => {
    it('has null user initially', () => {
      const store = useAuthStore()
      expect(store.user).toBeNull()
    })

    it('is not authenticated initially', () => {
      const store = useAuthStore()
      expect(store.isAuthenticated).toBe(false)
    })

    it('has no loading state initially', () => {
      const store = useAuthStore()
      expect(store.isLoading).toBe(false)
    })

    it('has no error initially', () => {
      const store = useAuthStore()
      expect(store.error).toBeNull()
    })
  })

  describe('getters', () => {
    it('isAuthenticated is true when user is set', () => {
      const store = useAuthStore()
      store.user = { id: '1', username: 'testuser' }
      expect(store.isAuthenticated).toBe(true)
    })

    it('isAuthenticated is false when user is null', () => {
      const store = useAuthStore()
      store.user = null
      expect(store.isAuthenticated).toBe(false)
    })

    it('currentUser returns the user object', () => {
      const store = useAuthStore()
      const testUser = { id: '1', username: 'testuser', name: 'Test User' }
      store.user = testUser
      expect(store.currentUser).toEqual(testUser)
    })
  })

  describe('initializeFromCallback', () => {
    it('returns false when not on /admin', async () => {
      window.location.pathname = '/other'
      const store = useAuthStore()
      const result = await store.initializeFromCallback()
      expect(result).toBe(false)
    })

    it('returns true when user is fetched successfully on /admin', async () => {
      window.location.pathname = '/admin'
      const mockUser = { id: '1', username: 'testuser', name: 'Test User' }
      vi.mocked(apiClient.get).mockResolvedValue({ data: mockUser })

      const store = useAuthStore()
      const result = await store.initializeFromCallback()

      expect(result).toBe(true)
      expect(store.user).toEqual(mockUser)
    })

    it('returns false when fetchUser fails on /admin', async () => {
      window.location.pathname = '/admin'
      vi.mocked(apiClient.get).mockRejectedValue(new Error('Not authenticated'))

      const store = useAuthStore()
      const result = await store.initializeFromCallback()

      expect(result).toBe(false)
    })
  })

  describe('fetchUser', () => {
    it('fetches user info via cookies (no body, no header)', async () => {
      const mockUser = { id: '1', username: 'testuser', name: 'Test User' }
      vi.mocked(apiClient.get).mockResolvedValue({ data: mockUser })

      const store = useAuthStore()
      await store.fetchUser()

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/auth/me')
      expect(store.user).toEqual(mockUser)
    })

    it('clears user on 401 unauthorized error', async () => {
      const error = { isAxiosError: true, response: { status: 401 } }
      vi.mocked(apiClient.get).mockRejectedValue(error)

      const store = useAuthStore()
      store.user = { id: '1', username: 'test' }
      await store.fetchUser()

      expect(store.user).toBeNull()
    })

    it('preserves user on network errors', async () => {
      const error = new Error('Network error')
      vi.mocked(apiClient.get).mockRejectedValue(error)

      const store = useAuthStore()
      store.user = { id: '1', username: 'test' }
      await store.fetchUser()

      expect(store.user).toEqual({ id: '1', username: 'test' })
    })
  })

  describe('refreshAccessToken', () => {
    it('calls refresh endpoint with no body and re-fetches user', async () => {
      const mockUser = { id: '1', username: 'test' }
      vi.mocked(apiClient.post).mockResolvedValue({ data: { refreshed: true } })
      vi.mocked(apiClient.get).mockResolvedValue({ data: mockUser })

      const store = useAuthStore()
      await store.refreshAccessToken()

      expect(apiClient.post).toHaveBeenCalledWith('/api/v1/auth/refresh')
      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/auth/me')
      expect(store.user).toEqual(mockUser)
    })

    it('logs out on refresh failure', async () => {
      vi.mocked(apiClient.post).mockRejectedValue(new Error('Refresh failed'))

      const store = useAuthStore()
      store.user = { id: '1', username: 'test' }
      const logoutSpy = vi.spyOn(store, 'logout').mockResolvedValue()

      await store.refreshAccessToken()

      expect(logoutSpy).toHaveBeenCalled()
    })
  })

  describe('loginWithGitHub', () => {
    it('redirects to the GitHub OAuth start URL', () => {
      const store = useAuthStore()

      const hrefSetter = vi.fn()
      Object.defineProperty(window.location, 'href', {
        set: hrefSetter,
        configurable: true
      })

      store.loginWithGitHub()

      expect(hrefSetter).toHaveBeenCalledWith(expect.stringContaining('/api/v1/auth/github'))
    })
  })

  describe('logout', () => {
    it('clears user and calls logout endpoint', async () => {
      vi.mocked(apiClient.post).mockResolvedValue({ data: { message: 'Logged out' } })

      const store = useAuthStore()
      store.user = { id: '1', username: 'test' }

      await store.logout()

      expect(apiClient.post).toHaveBeenCalledWith('/api/v1/auth/logout')
      expect(store.user).toBeNull()
    })

    it('clears user even if logout API fails', async () => {
      vi.mocked(apiClient.post).mockRejectedValue(new Error('Network error'))

      const store = useAuthStore()
      store.user = { id: '1', username: 'test' }

      await store.logout()

      expect(store.user).toBeNull()
    })
  })

  describe('checkAuth', () => {
    it('delegates to fetchUser', async () => {
      const mockUser = { id: '1', username: 'testuser' }
      vi.mocked(apiClient.get).mockResolvedValue({ data: mockUser })

      const store = useAuthStore()
      await store.checkAuth()

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/auth/me')
      expect(store.user).toEqual(mockUser)
    })
  })

  describe('initializeAuth', () => {
    it('runs fetchUser and marks initialized', async () => {
      const mockUser = { id: '1', username: 'testuser' }
      vi.mocked(apiClient.get).mockResolvedValue({ data: mockUser })

      const store = useAuthStore()
      await store.initializeAuth()

      expect(store.isInitialized).toBe(true)
      expect(store.user).toEqual(mockUser)
    })

    it('is a no-op when already initialized', async () => {
      vi.mocked(apiClient.get).mockResolvedValue({ data: { id: '1', username: 'x' } })

      const store = useAuthStore()
      await store.initializeAuth()
      vi.mocked(apiClient.get).mockClear()

      await store.initializeAuth()
      expect(apiClient.get).not.toHaveBeenCalled()
    })

    it('concurrent calls share a single in-flight promise', async () => {
      const mockUser = { id: '1', username: 'testuser' }
      vi.mocked(apiClient.get).mockResolvedValue({ data: mockUser })

      const store = useAuthStore()
      await Promise.all([store.initializeAuth(), store.initializeAuth(), store.initializeAuth()])

      expect(apiClient.get).toHaveBeenCalledTimes(1)
    })
  })
})
