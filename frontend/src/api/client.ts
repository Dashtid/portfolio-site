import axios, {
  type AxiosInstance,
  type InternalAxiosRequestConfig,
  type AxiosResponse,
  type AxiosError
} from 'axios'
import { config } from '@/config'

/**
 * Axios API Client
 *
 * Auth lives in HTTP-only cookies (set by /api/v1/auth/* endpoints) and is
 * sent automatically with every request via `withCredentials: true`. On a
 * 401, this client transparently calls /api/v1/auth/refresh once — the
 * backend rotates the cookies and the original request is retried.
 */

// Token refresh state management to prevent race conditions
// When multiple requests get 401 simultaneously, only one refresh should occur
let isRefreshing = false
let refreshSubscribers: Array<{
  onSuccess: () => void
  onError: (error: Error) => void
}> = []

// Timeout for refresh subscribers to prevent hanging requests
const REFRESH_TIMEOUT_MS = 10000

function onTokenRefreshed(): void {
  refreshSubscribers.forEach(({ onSuccess }) => onSuccess())
  refreshSubscribers = []
}

function onTokenRefreshFailed(error: Error): void {
  refreshSubscribers.forEach(({ onError }) => onError(error))
  refreshSubscribers = []
}

const apiClient: AxiosInstance = axios.create({
  baseURL: config.apiUrl,
  timeout: 30000,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
    'Cache-Control': 'no-cache',
    Pragma: 'no-cache'
  }
})

apiClient.interceptors.response.use(
  (response: AxiosResponse): AxiosResponse => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      // If already refreshing, queue this request to retry after refresh completes
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          const subscriber = {
            onSuccess: () => {
              clearTimeout(timeoutId)
              resolve(apiClient(originalRequest))
            },
            onError: (refreshError: Error) => {
              clearTimeout(timeoutId)
              reject(refreshError)
            }
          }

          const timeoutId = setTimeout(() => {
            const index = refreshSubscribers.indexOf(subscriber)
            if (index > -1) {
              refreshSubscribers.splice(index, 1)
            }
            reject(new Error('Token refresh timeout'))
          }, REFRESH_TIMEOUT_MS)

          refreshSubscribers.push(subscriber)
        })
      }

      isRefreshing = true

      try {
        // Cookies are sent automatically; refresh-token cookie is scoped to /api/v1/auth.
        // The timeout mirrors REFRESH_TIMEOUT_MS: without it a hung refresh
        // never resolves, isRefreshing never resets, and every queued request
        // (plus all future 401s) wedges permanently.
        await axios.post(
          `${config.apiUrl}/api/v1/auth/refresh`,
          {},
          { withCredentials: true, timeout: REFRESH_TIMEOUT_MS }
        )

        isRefreshing = false
        onTokenRefreshed()

        return apiClient(originalRequest)
      } catch (refreshError) {
        isRefreshing = false

        onTokenRefreshFailed(
          refreshError instanceof Error ? refreshError : new Error('Token refresh failed')
        )
        // Skip the redirect if we're already on /admin/login: the auth-guard's
        // requiresGuest branch also fires fetchUser on that page, so re-redirecting
        // from /admin/login to /admin/login spins the browser into a reload loop.
        if (window.location.pathname !== '/admin/login') {
          window.location.href = '/admin/login'
        }
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  }
)

export default apiClient
