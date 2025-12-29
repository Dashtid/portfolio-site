/**
 * Tests for Auth Store
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '@/stores/auth'
import apiClient from '@/api/client'

// Mock the api client
vi.mock('@/api/client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    defaults: {
      headers: {
        common: {}
      }
    }
  }
}))

// Mock the logger to avoid console output during tests
vi.mock('@/utils/logger', () => ({
  authLogger: {
    error: vi.fn(),
    warn: vi.fn(),
    log: vi.fn(),
    debug: vi.fn(),
    info: vi.fn()
  }
}))

// Mock storage utility
vi.mock('@/utils/storage', () => ({
  storage: {
    getItem: vi.fn(() => null),
    setItem: vi.fn(),
    removeItem: vi.fn(),
    removeMultiple: vi.fn()
  },
  STORAGE_KEYS: {
    ACCESS_TOKEN: 'accessToken',
    REFRESH_TOKEN: 'refreshToken'
  }
}))

describe('Auth Store', () => {
  beforeEach(() => {
    // Create a fresh pinia instance for each test
    setActivePinia(createPinia())

    // Reset all mocks
    vi.clearAllMocks()

    // Mock window.location
    Object.defineProperty(window, 'location', {
      value: {
        href: 'http://localhost:3000',
        search: '',
        pathname: '/admin'
      },
      writable: true,
      configurable: true
    })

    // Mock window.history
    window.history.replaceState = vi.fn()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('initial state', () => {
    it('should have null user initially', () => {
      const store = useAuthStore()
      expect(store.user).toBeNull()
    })

    it('should have null tokens initially when storage is empty', () => {
      const store = useAuthStore()
      expect(store.accessToken).toBeNull()
      expect(store.refreshToken).toBeNull()
    })

    it('should not be authenticated initially', () => {
      const store = useAuthStore()
      expect(store.isAuthenticated).toBe(false)
    })

    it('should have no loading state initially', () => {
      const store = useAuthStore()
      expect(store.isLoading).toBe(false)
    })

    it('should have no error initially', () => {
      const store = useAuthStore()
      expect(store.error).toBeNull()
    })
  })

  describe('getters', () => {
    it('isAuthenticated returns true when accessToken exists', () => {
      const store = useAuthStore()
      store.accessToken = 'valid-token'
      expect(store.isAuthenticated).toBe(true)
    })

    it('isAuthenticated returns false when accessToken is null', () => {
      const store = useAuthStore()
      store.accessToken = null
      expect(store.isAuthenticated).toBe(false)
    })

    it('currentUser returns the user object', () => {
      const store = useAuthStore()
      const testUser = { id: '1', username: 'testuser', name: 'Test User' }
      store.user = testUser
      expect(store.currentUser).toEqual(testUser)
    })

    it('currentUser returns null when no user', () => {
      const store = useAuthStore()
      expect(store.currentUser).toBeNull()
    })
  })

  describe('initializeFromCallback', () => {
    it('should return false when not on /admin', async () => {
      window.location.pathname = '/other'
      const store = useAuthStore()
      const result = await store.initializeFromCallback()
      expect(result).toBe(false)
    })

    it('should return true when user is fetched successfully on /admin', async () => {
      window.location.pathname = '/admin'
      const mockUser = { id: '1', username: 'testuser', name: 'Test User' }
      vi.mocked(apiClient.get).mockResolvedValue({ data: mockUser })

      const store = useAuthStore()
      const result = await store.initializeFromCallback()

      expect(result).toBe(true)
      expect(store.user).toEqual(mockUser)
    })

    it('should return false when fetchUser fails on /admin', async () => {
      window.location.pathname = '/admin'
      vi.mocked(apiClient.get).mockRejectedValue(new Error('Not authenticated'))

      const store = useAuthStore()
      const result = await store.initializeFromCallback()

      expect(result).toBe(false)
    })
  })

  describe('setTokens', () => {
    it('should set accessToken and refreshToken', async () => {
      vi.mocked(apiClient.get).mockResolvedValue({ data: { id: '1', username: 'test' } })
      const store = useAuthStore()
      await store.setTokens('access-token', 'refresh-token')

      expect(store.accessToken).toBe('access-token')
      expect(store.refreshToken).toBe('refresh-token')
    })

    it('should set Authorization header on apiClient', async () => {
      vi.mocked(apiClient.get).mockResolvedValue({ data: { id: '1', username: 'test' } })
      const store = useAuthStore()
      await store.setTokens('access-token', 'refresh-token')

      expect(apiClient.defaults.headers.common['Authorization']).toBe('Bearer access-token')
    })
  })

  describe('fetchUser', () => {
    it('should fetch user info via HTTP-only cookies', async () => {
      const mockUser = { id: '1', username: 'testuser', name: 'Test User' }
      vi.mocked(apiClient.get).mockResolvedValue({ data: mockUser })

      const store = useAuthStore()

      await store.fetchUser()

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/auth/me')
      expect(store.user).toEqual(mockUser)
    })

    it('should clear user on 401 unauthorized error', async () => {
      // Mock AxiosError with isAxiosError flag for type guard compatibility
      const error = { isAxiosError: true, response: { status: 401 } }
      vi.mocked(apiClient.get).mockRejectedValue(error)

      const store = useAuthStore()
      store.user = { id: '1', username: 'test' }

      await store.fetchUser()

      expect(store.user).toBeNull()
    })

    it('should not clear user on network errors', async () => {
      // Network error (not a 401)
      const error = new Error('Network error')
      vi.mocked(apiClient.get).mockRejectedValue(error)

      const store = useAuthStore()
      store.user = { id: '1', username: 'test' }

      await store.fetchUser()

      // User should NOT be cleared on network errors
      expect(store.user).toEqual({ id: '1', username: 'test' })
    })
  })

  describe('refreshAccessToken', () => {
    it('should logout if no refresh token', async () => {
      const store = useAuthStore()
      store.refreshToken = null
      store.accessToken = 'some-token'
      store.logout = vi.fn()

      await store.refreshAccessToken()

      expect(store.logout).toHaveBeenCalled()
    })

    it('should refresh token and update tokens', async () => {
      const mockResponse = {
        data: {
          access_token: 'new-access-token',
          refresh_token: 'new-refresh-token'
        }
      }
      vi.mocked(apiClient.post).mockResolvedValue(mockResponse)

      const store = useAuthStore()
      store.refreshToken = 'old-refresh-token'
      store.accessToken = 'old-access-token'

      await store.refreshAccessToken()

      expect(apiClient.post).toHaveBeenCalledWith('/api/v1/auth/refresh', {
        refresh_token: 'old-refresh-token'
      })
      expect(store.accessToken).toBe('new-access-token')
      expect(store.refreshToken).toBe('new-refresh-token')
    })

    it('should use existing refresh token if not returned by server', async () => {
      const mockResponse = {
        data: {
          access_token: 'new-access-token'
          // No refresh_token in response
        }
      }
      vi.mocked(apiClient.post).mockResolvedValue(mockResponse)

      const store = useAuthStore()
      store.refreshToken = 'existing-refresh-token'
      store.accessToken = 'old-access-token'

      await store.refreshAccessToken()

      expect(store.refreshToken).toBe('existing-refresh-token')
    })

    it('should logout on refresh failure', async () => {
      vi.mocked(apiClient.post).mockRejectedValue(new Error('Refresh failed'))

      const store = useAuthStore()
      store.refreshToken = 'old-refresh-token'
      store.accessToken = 'old-access-token'
      store.logout = vi.fn()

      await store.refreshAccessToken()

      expect(store.logout).toHaveBeenCalled()
    })
  })

  describe('loginWithGitHub', () => {
    it('should redirect to GitHub OAuth URL', () => {
      const store = useAuthStore()

      // Mock window.location.href setter
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
    it('should clear user and tokens', async () => {
      vi.mocked(apiClient.post).mockResolvedValue({ data: { message: 'Logged out' } })

      const store = useAuthStore()
      store.user = { id: '1', username: 'test' }
      store.accessToken = 'token'
      store.refreshToken = 'refresh'

      await store.logout()

      expect(store.user).toBeNull()
      expect(store.accessToken).toBeNull()
      expect(store.refreshToken).toBeNull()
    })

    it('should call logout endpoint', async () => {
      vi.mocked(apiClient.post).mockResolvedValue({ data: { message: 'Logged out' } })

      const store = useAuthStore()

      await store.logout()

      expect(apiClient.post).toHaveBeenCalledWith('/api/v1/auth/logout')
    })

    it('should clear Authorization header', async () => {
      vi.mocked(apiClient.post).mockResolvedValue({ data: { message: 'Logged out' } })

      const store = useAuthStore()
      apiClient.defaults.headers.common['Authorization'] = 'Bearer token'

      await store.logout()

      expect(apiClient.defaults.headers.common['Authorization']).toBeUndefined()
    })

    it('should still clear local state even if logout API fails', async () => {
      vi.mocked(apiClient.post).mockRejectedValue(new Error('Network error'))

      const store = useAuthStore()
      store.user = { id: '1', username: 'test' }
      store.accessToken = 'token'

      await store.logout()

      expect(store.user).toBeNull()
      expect(store.accessToken).toBeNull()
    })
  })

  describe('checkAuth', () => {
    it('should fetch user using HTTP-only cookies first', async () => {
      const mockUser = { id: '1', username: 'testuser' }
      vi.mocked(apiClient.get).mockResolvedValue({ data: mockUser })

      const store = useAuthStore()

      await store.checkAuth()

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/auth/me')
      expect(store.user).toEqual(mockUser)
    })

    it('should fallback to localStorage token if cookies fail', async () => {
      const mockUser = { id: '1', username: 'testuser' }
      // First call fails (no cookies), second call with header succeeds
      vi.mocked(apiClient.get)
        .mockRejectedValueOnce(new Error('No session'))
        .mockResolvedValueOnce({ data: mockUser })

      const store = useAuthStore()
      store.accessToken = 'existing-token'

      await store.checkAuth()

      expect(apiClient.defaults.headers.common['Authorization']).toBe('Bearer existing-token')
      expect(apiClient.get).toHaveBeenCalledTimes(2)
    })
  })

  describe('security: HTTP-only cookies', () => {
    it('should use withCredentials for cookie-based auth', async () => {
      const mockUser = { id: '1', username: 'testuser' }
      vi.mocked(apiClient.get).mockResolvedValue({ data: mockUser })

      const store = useAuthStore()
      await store.fetchUser()

      // API client should send cookies automatically (configured in client.ts)
      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/auth/me')
    })

    it('should clear local state on logout even if API fails', async () => {
      vi.mocked(apiClient.post).mockRejectedValue(new Error('Network error'))

      const store = useAuthStore()
      store.user = { id: '1', username: 'test' }
      store.accessToken = 'token'
      store.refreshToken = 'refresh'

      await store.logout()

      expect(store.user).toBeNull()
      expect(store.accessToken).toBeNull()
      expect(store.refreshToken).toBeNull()
    })
  })
})
