import axios, {
  type AxiosInstance,
  type InternalAxiosRequestConfig,
  type AxiosResponse,
  type AxiosError
} from 'axios'
import { config } from '@/config'
import { storage, STORAGE_KEYS } from '@/utils/storage'
import router from '@/router'

/**
 * Axios API Client with Authentication
 *
 * Configured with interceptors for:
 * - Adding auth tokens to requests
 * - Handling 401 errors and token refresh
 * - Automatic logout on refresh failure
 * - Request deduplication for concurrent token refresh
 */

// Token refresh state management to prevent race conditions
// When multiple requests get 401 simultaneously, only one refresh should occur
let isRefreshing = false
let refreshSubscribers: Array<{
  onSuccess: (token: string) => void
  onError: (error: Error) => void
}> = []

// Timeout for refresh subscribers to prevent hanging requests
const REFRESH_TIMEOUT_MS = 10000

/**
 * Notify all subscribers that token refresh completed successfully
 * This retries all queued requests with the new token
 */
function onTokenRefreshed(newToken: string): void {
  refreshSubscribers.forEach(({ onSuccess }) => onSuccess(newToken))
  refreshSubscribers = []
}

/**
 * Notify all subscribers that token refresh failed
 * This rejects all queued requests
 */
function onTokenRefreshFailed(error: Error): void {
  refreshSubscribers.forEach(({ onError }) => onError(error))
  refreshSubscribers = []
}

// Create axios instance with default configuration
const apiClient: AxiosInstance = axios.create({
  baseURL: config.apiUrl,
  timeout: 30000, // 30 second timeout to prevent hanging requests
  withCredentials: true, // Include HTTP-only cookies in requests
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (reqConfig: InternalAxiosRequestConfig): InternalAxiosRequestConfig => {
    const token = storage.getItem(STORAGE_KEYS.ACCESS_TOKEN)
    if (token && reqConfig.headers) {
      reqConfig.headers.Authorization = `Bearer ${token}`
    }
    return reqConfig
  },
  (error: AxiosError) => {
    return Promise.reject(error)
  }
)

// Response interceptor to handle auth errors with request deduplication
apiClient.interceptors.response.use(
  (response: AxiosResponse): AxiosResponse => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      const refreshToken = storage.getItem(STORAGE_KEYS.REFRESH_TOKEN)
      if (refreshToken) {
        // If already refreshing, queue this request to retry after refresh completes
        if (isRefreshing) {
          return new Promise((resolve, reject) => {
            // Create subscriber object to track for cleanup
            const subscriber = {
              onSuccess: (newToken: string) => {
                clearTimeout(timeoutId)
                if (originalRequest.headers) {
                  originalRequest.headers.Authorization = `Bearer ${newToken}`
                }
                resolve(apiClient(originalRequest))
              },
              onError: (refreshError: Error) => {
                clearTimeout(timeoutId)
                reject(refreshError)
              }
            }

            // Set timeout to prevent requests hanging indefinitely
            const timeoutId = setTimeout(() => {
              // Remove subscriber on timeout to prevent memory leak
              const index = refreshSubscribers.indexOf(subscriber)
              if (index > -1) {
                refreshSubscribers.splice(index, 1)
              }
              reject(new Error('Token refresh timeout'))
            }, REFRESH_TIMEOUT_MS)

            refreshSubscribers.push(subscriber)
          })
        }

        // Start refresh process
        isRefreshing = true

        try {
          // Refresh request - cookies will be sent automatically if present
          // Also send refresh token in body for backwards compatibility
          const response = await axios.post<{ access_token: string; refresh_token: string }>(
            `${config.apiUrl}/api/v1/auth/refresh`,
            refreshToken ? { refresh_token: refreshToken } : {},
            { withCredentials: true }
          )

          const newAccessToken = response.data.access_token
          // Store in localStorage for backwards compatibility with header-based auth
          storage.setItem(STORAGE_KEYS.ACCESS_TOKEN, newAccessToken)
          if (response.data.refresh_token) {
            storage.setItem(STORAGE_KEYS.REFRESH_TOKEN, response.data.refresh_token)
          }

          // Clear flag before notifying subscribers to allow new refresh attempts
          isRefreshing = false

          // Notify all queued requests that refresh completed
          onTokenRefreshed(newAccessToken)

          // Retry original request with new token
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${newAccessToken}`
          }
          return apiClient(originalRequest)
        } catch (refreshError) {
          // Clear flag before notifying subscribers to allow new refresh attempts
          isRefreshing = false

          // Refresh failed, logout user
          storage.removeMultiple([STORAGE_KEYS.ACCESS_TOKEN, STORAGE_KEYS.REFRESH_TOKEN])
          // Reject all queued requests with the error
          onTokenRefreshFailed(
            refreshError instanceof Error ? refreshError : new Error('Token refresh failed')
          )
          // Use Vue Router instead of hard redirect to preserve app state
          router.push('/admin/login')
          return Promise.reject(refreshError)
        }
      }
    }

    return Promise.reject(error)
  }
)

export default apiClient
