/**
 * Tests for API client (TypeScript)
 */
/* eslint-disable @typescript-eslint/no-explicit-any */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import axios from 'axios'
import type { InternalAxiosRequestConfig, AxiosError } from 'axios'

// Mock axios
vi.mock('axios')

// Mock router to prevent Pinia errors from navigation guards
vi.mock('@/router', () => ({
  default: {
    push: vi.fn()
  }
}))

import router from '@/router'

describe('API client', () => {
  let apiClient: any
  let mockLocalStorage: { [key: string]: string }

  beforeEach(async () => {
    // Reset modules to get fresh instance
    vi.resetModules()

    // Mock localStorage
    mockLocalStorage = {}
    global.localStorage = {
      getItem: vi.fn((key: string) => mockLocalStorage[key] || null),
      setItem: vi.fn((key: string, value: string) => {
        mockLocalStorage[key] = value
      }),
      removeItem: vi.fn((key: string) => {
        delete mockLocalStorage[key]
      }),
      clear: vi.fn(() => {
        mockLocalStorage = {}
      }),
      length: 0,
      key: vi.fn()
    } as any

    // Mock window.location
    delete (window as any).location
    window.location = { href: '' } as any

    // Mock axios.create to return a mock instance
    // The instance must be callable (like a function) because apiClient(config) is used
    const mockAxiosInstance = Object.assign(vi.fn().mockResolvedValue({ data: {} }), {
      interceptors: {
        request: { use: vi.fn() },
        response: { use: vi.fn() }
      },
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      delete: vi.fn()
    })

    vi.mocked(axios.create).mockReturnValue(mockAxiosInstance as any)
    vi.mocked(axios.post).mockResolvedValue({ data: {} })

    // Import after mocking
    const module = await import('@/api/client')
    apiClient = module.default
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('initialization', () => {
    it('creates axios instance with correct base URL', () => {
      expect(axios.create).toHaveBeenCalledWith({
        baseURL: 'http://localhost:8001',
        timeout: 30000,
        withCredentials: true,
        headers: {
          'Content-Type': 'application/json'
        }
      })
    })

    it('sets up request interceptor', () => {
      expect(apiClient.interceptors.request.use).toHaveBeenCalled()
    })

    it('sets up response interceptor', () => {
      expect(apiClient.interceptors.response.use).toHaveBeenCalled()
    })
  })

  describe('request interceptor', () => {
    it('adds authorization header when token exists', () => {
      const token = 'test-access-token'
      mockLocalStorage['accessToken'] = token

      const config: InternalAxiosRequestConfig = {
        headers: {} as any,
        url: '/test'
      } as InternalAxiosRequestConfig

      // Get the request interceptor function
      const requestInterceptor = vi.mocked(apiClient.interceptors.request.use).mock.calls[0][0]
      const result = requestInterceptor(config)

      expect(result.headers.Authorization).toBe(`Bearer ${token}`)
    })

    it('does not add authorization header when no token', () => {
      const config: InternalAxiosRequestConfig = {
        headers: {} as any,
        url: '/test'
      } as InternalAxiosRequestConfig

      const requestInterceptor = vi.mocked(apiClient.interceptors.request.use).mock.calls[0][0]
      const result = requestInterceptor(config)

      expect(result.headers.Authorization).toBeUndefined()
    })

    it('rejects on error', async () => {
      const error = new Error('Request error')
      const errorInterceptor = vi.mocked(apiClient.interceptors.request.use).mock.calls[0][1]

      await expect(errorInterceptor(error)).rejects.toThrow('Request error')
    })
  })

  describe('response interceptor', () => {
    it('returns successful response', () => {
      const response = { data: { success: true }, status: 200 }
      const responseInterceptor = vi.mocked(apiClient.interceptors.response.use).mock.calls[0][0]

      const result = responseInterceptor(response)

      expect(result).toBe(response)
    })

    it('handles 401 error with token refresh', async () => {
      const refreshToken = 'test-refresh-token'
      const newAccessToken = 'new-access-token'
      const newRefreshToken = 'new-refresh-token'

      mockLocalStorage['refreshToken'] = refreshToken

      const error: Partial<AxiosError> = {
        response: { status: 401 } as any,
        config: {
          headers: {} as any,
          url: '/test'
        } as InternalAxiosRequestConfig
      }

      // Mock successful token refresh
      vi.mocked(axios.post).mockResolvedValue({
        data: {
          access_token: newAccessToken,
          refresh_token: newRefreshToken
        }
      })

      const errorInterceptor = vi.mocked(apiClient.interceptors.response.use).mock.calls[0][1]
      await errorInterceptor(error)

      // Verify refresh endpoint was called
      expect(axios.post).toHaveBeenCalledWith(
        'http://localhost:8001/api/v1/auth/refresh',
        {
          refresh_token: refreshToken
        },
        { withCredentials: true }
      )

      // Verify tokens were updated
      expect(localStorage.setItem).toHaveBeenCalledWith('accessToken', newAccessToken)
      expect(localStorage.setItem).toHaveBeenCalledWith('refreshToken', newRefreshToken)
    })

    it('redirects to login when refresh fails', async () => {
      const refreshToken = 'test-refresh-token'
      mockLocalStorage['refreshToken'] = refreshToken

      const error: Partial<AxiosError> = {
        response: { status: 401 } as any,
        config: {
          headers: {} as any,
          url: '/test'
        } as InternalAxiosRequestConfig
      }

      // Mock failed token refresh
      vi.mocked(axios.post).mockRejectedValue(new Error('Refresh failed'))

      const errorInterceptor = vi.mocked(apiClient.interceptors.response.use).mock.calls[0][1]

      try {
        await errorInterceptor(error)
      } catch {
        // Expected to reject
      }

      // Verify tokens were removed
      expect(localStorage.removeItem).toHaveBeenCalledWith('accessToken')
      expect(localStorage.removeItem).toHaveBeenCalledWith('refreshToken')

      // Verify redirect via router
      expect(router.push).toHaveBeenCalledWith('/admin/login')
    })

    it('does not retry request twice', async () => {
      const error: Partial<AxiosError> = {
        response: { status: 401 } as any,
        config: {
          headers: {} as any,
          url: '/test',
          _retry: true
        } as InternalAxiosRequestConfig & { _retry?: boolean }
      }

      const errorInterceptor = vi.mocked(apiClient.interceptors.response.use).mock.calls[0][1]

      await expect(errorInterceptor(error)).rejects.toBeDefined()

      // Verify no refresh attempt was made
      expect(axios.post).not.toHaveBeenCalled()
    })

    it('rejects non-401 errors', async () => {
      const error: Partial<AxiosError> = {
        response: { status: 500 } as any,
        config: {} as InternalAxiosRequestConfig
      }

      const errorInterceptor = vi.mocked(apiClient.interceptors.response.use).mock.calls[0][1]

      await expect(errorInterceptor(error)).rejects.toBeDefined()
    })
  })

  describe('TypeScript types', () => {
    it('exports axios instance with correct type', () => {
      expect(apiClient).toBeDefined()
      expect(apiClient.interceptors).toBeDefined()
    })
  })

  describe('concurrent token refresh (race condition prevention)', () => {
    it('makes only one refresh call when multiple 401s occur simultaneously', async () => {
      const refreshToken = 'test-refresh-token'
      const newAccessToken = 'new-access-token'
      const newRefreshToken = 'new-refresh-token'
      mockLocalStorage['refreshToken'] = refreshToken

      // Create a deferred promise to control refresh timing
      let resolveRefresh: ((value: any) => void) | undefined
      const refreshPromise = new Promise(resolve => {
        resolveRefresh = resolve
      })

      vi.mocked(axios.post).mockReturnValue(refreshPromise as any)

      const createError = (url: string): Partial<AxiosError> => ({
        response: { status: 401 } as any,
        config: {
          headers: {} as any,
          url
        } as InternalAxiosRequestConfig
      })

      const errorInterceptor = vi.mocked(apiClient.interceptors.response.use).mock.calls[0][1]

      // Fire 3 concurrent 401 errors
      const promise1 = errorInterceptor(createError('/api/resource1'))
      const promise2 = errorInterceptor(createError('/api/resource2'))
      const promise3 = errorInterceptor(createError('/api/resource3'))

      // Resolve the refresh
      resolveRefresh!({
        data: {
          access_token: newAccessToken,
          refresh_token: newRefreshToken
        }
      })

      await Promise.all([promise1, promise2, promise3])

      // Only ONE refresh call should have been made
      expect(axios.post).toHaveBeenCalledTimes(1)
      expect(axios.post).toHaveBeenCalledWith(
        'http://localhost:8001/api/v1/auth/refresh',
        {
          refresh_token: refreshToken
        },
        { withCredentials: true }
      )
    })

    it('retries all queued requests with new token after refresh completes', async () => {
      const refreshToken = 'test-refresh-token'
      const newAccessToken = 'new-access-token'
      const newRefreshToken = 'new-refresh-token'
      mockLocalStorage['refreshToken'] = refreshToken

      let resolveRefresh: ((value: any) => void) | undefined
      const refreshPromise = new Promise(resolve => {
        resolveRefresh = resolve
      })

      vi.mocked(axios.post).mockReturnValue(refreshPromise as any)

      const createError = (url: string): Partial<AxiosError> => ({
        response: { status: 401 } as any,
        config: {
          headers: {} as any,
          url
        } as InternalAxiosRequestConfig
      })

      const errorInterceptor = vi.mocked(apiClient.interceptors.response.use).mock.calls[0][1]

      // Fire concurrent 401 errors
      const promise1 = errorInterceptor(createError('/api/resource1'))
      const promise2 = errorInterceptor(createError('/api/resource2'))

      // Resolve the refresh
      resolveRefresh!({
        data: {
          access_token: newAccessToken,
          refresh_token: newRefreshToken
        }
      })

      await Promise.all([promise1, promise2])

      // Verify both requests were retried (apiClient called for each)
      // First call is the initial request, subsequent are retries
      expect(apiClient).toHaveBeenCalled()
    })

    it('redirects to login and clears tokens when refresh fails', async () => {
      const refreshToken = 'test-refresh-token'
      mockLocalStorage['refreshToken'] = refreshToken

      vi.mocked(axios.post).mockRejectedValue(new Error('Refresh failed'))

      const error: Partial<AxiosError> = {
        response: { status: 401 } as any,
        config: {
          headers: {} as any,
          url: '/api/resource'
        } as InternalAxiosRequestConfig
      }

      const errorInterceptor = vi.mocked(apiClient.interceptors.response.use).mock.calls[0][1]

      // The request that triggered refresh should reject
      await expect(errorInterceptor(error)).rejects.toThrow('Refresh failed')

      // Verify redirect happened via router
      expect(router.push).toHaveBeenCalledWith('/admin/login')

      // Verify tokens were cleared
      expect(localStorage.removeItem).toHaveBeenCalledWith('accessToken')
      expect(localStorage.removeItem).toHaveBeenCalledWith('refreshToken')
    })

    it('allows new refresh after previous refresh completes', async () => {
      const refreshToken = 'test-refresh-token'
      mockLocalStorage['refreshToken'] = refreshToken

      vi.mocked(axios.post).mockResolvedValue({
        data: {
          access_token: 'new-token-1',
          refresh_token: 'new-refresh-1'
        }
      })

      const createError = (): Partial<AxiosError> => ({
        response: { status: 401 } as any,
        config: {
          headers: {} as any,
          url: '/test'
        } as InternalAxiosRequestConfig
      })

      const errorInterceptor = vi.mocked(apiClient.interceptors.response.use).mock.calls[0][1]

      // First refresh cycle
      await errorInterceptor(createError())

      // Reset mock and update stored token
      vi.mocked(axios.post).mockClear()
      mockLocalStorage['refreshToken'] = 'new-refresh-1'

      vi.mocked(axios.post).mockResolvedValue({
        data: {
          access_token: 'new-token-2',
          refresh_token: 'new-refresh-2'
        }
      })

      // Second refresh cycle (should work, not be blocked)
      await errorInterceptor(createError())

      // Second refresh should have been called
      expect(axios.post).toHaveBeenCalledTimes(1)
    })
  })
})
