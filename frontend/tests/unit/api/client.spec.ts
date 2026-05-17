/**
 * Tests for API client (TypeScript)
 */
/* eslint-disable @typescript-eslint/no-explicit-any */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import axios from 'axios'
import type { InternalAxiosRequestConfig, AxiosError } from 'axios'

vi.mock('axios')

describe('API client', () => {
  let apiClient: any

  beforeEach(async () => {
    vi.resetModules()

    delete (window as any).location
    window.location = { href: '' } as any

    // Mock axios.create to return a mock instance.
    // The instance must be callable (like a function) because apiClient(config) is used.
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

    const module = await import('@/api/client')
    apiClient = module.default
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  describe('initialization', () => {
    it('creates the axios instance with withCredentials so the auth cookies travel automatically', () => {
      expect(axios.create).toHaveBeenCalledWith({
        baseURL: 'http://localhost:8001',
        timeout: 30000,
        withCredentials: true,
        headers: {
          'Content-Type': 'application/json',
          'Cache-Control': 'no-cache',
          Pragma: 'no-cache'
        }
      })
    })

    it('only installs a response interceptor (no request interceptor — cookies handle auth)', () => {
      expect(apiClient.interceptors.response.use).toHaveBeenCalled()
      expect(apiClient.interceptors.request.use).not.toHaveBeenCalled()
    })
  })

  describe('response interceptor', () => {
    it('returns successful responses unchanged', () => {
      const response = { data: { success: true }, status: 200 }
      const responseInterceptor = vi.mocked(apiClient.interceptors.response.use).mock.calls[0][0]

      expect(responseInterceptor(response)).toBe(response)
    })

    it('on 401, calls refresh with an empty body (cookies do the work)', async () => {
      vi.mocked(axios.post).mockResolvedValue({ data: { refreshed: true } })

      const error: Partial<AxiosError> = {
        response: { status: 401 } as any,
        config: { headers: {} as any, url: '/test' } as InternalAxiosRequestConfig
      }

      const errorInterceptor = vi.mocked(apiClient.interceptors.response.use).mock.calls[0][1]
      await errorInterceptor(error)

      expect(axios.post).toHaveBeenCalledWith(
        'http://localhost:8001/api/v1/auth/refresh',
        {},
        { withCredentials: true }
      )
    })

    it('redirects to login when refresh fails', async () => {
      vi.mocked(axios.post).mockRejectedValue(new Error('Refresh failed'))

      const error: Partial<AxiosError> = {
        response: { status: 401 } as any,
        config: { headers: {} as any, url: '/test' } as InternalAxiosRequestConfig
      }

      const errorInterceptor = vi.mocked(apiClient.interceptors.response.use).mock.calls[0][1]

      try {
        await errorInterceptor(error)
      } catch {
        /* expected */
      }

      expect(window.location.href).toBe('/admin/login')
    })

    it('does not retry a request twice (_retry flag short-circuits)', async () => {
      const error: Partial<AxiosError> = {
        response: { status: 401 } as any,
        config: { headers: {} as any, url: '/test', _retry: true } as InternalAxiosRequestConfig & {
          _retry?: boolean
        }
      }

      const errorInterceptor = vi.mocked(apiClient.interceptors.response.use).mock.calls[0][1]
      await expect(errorInterceptor(error)).rejects.toBeDefined()

      expect(axios.post).not.toHaveBeenCalled()
    })

    it('rejects non-401 errors without attempting refresh', async () => {
      const error: Partial<AxiosError> = {
        response: { status: 500 } as any,
        config: {} as InternalAxiosRequestConfig
      }

      const errorInterceptor = vi.mocked(apiClient.interceptors.response.use).mock.calls[0][1]
      await expect(errorInterceptor(error)).rejects.toBeDefined()
      expect(axios.post).not.toHaveBeenCalled()
    })
  })

  describe('concurrent token refresh (race-condition prevention)', () => {
    it('makes only one refresh call when multiple 401s arrive simultaneously', async () => {
      let resolveRefresh: ((value: any) => void) | undefined
      const refreshPromise = new Promise(resolve => {
        resolveRefresh = resolve
      })
      vi.mocked(axios.post).mockReturnValue(refreshPromise as any)

      const createError = (url: string): Partial<AxiosError> => ({
        response: { status: 401 } as any,
        config: { headers: {} as any, url } as InternalAxiosRequestConfig
      })

      const errorInterceptor = vi.mocked(apiClient.interceptors.response.use).mock.calls[0][1]

      const p1 = errorInterceptor(createError('/api/resource1'))
      const p2 = errorInterceptor(createError('/api/resource2'))
      const p3 = errorInterceptor(createError('/api/resource3'))

      resolveRefresh!({ data: { refreshed: true } })
      await Promise.all([p1, p2, p3])

      expect(axios.post).toHaveBeenCalledTimes(1)
      expect(axios.post).toHaveBeenCalledWith(
        'http://localhost:8001/api/v1/auth/refresh',
        {},
        { withCredentials: true }
      )
    })

    it('retries all queued requests after refresh completes', async () => {
      let resolveRefresh: ((value: any) => void) | undefined
      const refreshPromise = new Promise(resolve => {
        resolveRefresh = resolve
      })
      vi.mocked(axios.post).mockReturnValue(refreshPromise as any)

      const createError = (url: string): Partial<AxiosError> => ({
        response: { status: 401 } as any,
        config: { headers: {} as any, url } as InternalAxiosRequestConfig
      })

      const errorInterceptor = vi.mocked(apiClient.interceptors.response.use).mock.calls[0][1]

      const p1 = errorInterceptor(createError('/api/resource1'))
      const p2 = errorInterceptor(createError('/api/resource2'))

      resolveRefresh!({ data: { refreshed: true } })
      await Promise.all([p1, p2])

      // apiClient (the instance) is called for each retry
      expect(apiClient).toHaveBeenCalled()
    })

    it('redirects to login on refresh failure', async () => {
      vi.mocked(axios.post).mockRejectedValue(new Error('Refresh failed'))

      const error: Partial<AxiosError> = {
        response: { status: 401 } as any,
        config: { headers: {} as any, url: '/api/resource' } as InternalAxiosRequestConfig
      }

      const errorInterceptor = vi.mocked(apiClient.interceptors.response.use).mock.calls[0][1]
      await expect(errorInterceptor(error)).rejects.toThrow('Refresh failed')

      expect(window.location.href).toBe('/admin/login')
    })

    it('allows a new refresh after a previous one completes', async () => {
      vi.mocked(axios.post).mockResolvedValue({ data: { refreshed: true } })

      const createError = (): Partial<AxiosError> => ({
        response: { status: 401 } as any,
        config: { headers: {} as any, url: '/test' } as InternalAxiosRequestConfig
      })

      const errorInterceptor = vi.mocked(apiClient.interceptors.response.use).mock.calls[0][1]

      await errorInterceptor(createError())
      vi.mocked(axios.post).mockClear()

      vi.mocked(axios.post).mockResolvedValue({ data: { refreshed: true } })
      await errorInterceptor(createError())

      expect(axios.post).toHaveBeenCalledTimes(1)
    })
  })
})
