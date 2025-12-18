import axios, {
  type AxiosInstance,
  type InternalAxiosRequestConfig,
  type AxiosResponse,
  type AxiosError
} from 'axios'
import { config } from '@/config'

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
let refreshSubscribers: Array<(token: string) => void> = []

/**
 * Subscribe to token refresh completion
 * Queued requests will be retried once refresh completes
 */
function subscribeTokenRefresh(callback: (token: string) => void): void {
  refreshSubscribers.push(callback)
}

/**
 * Notify all subscribers that token refresh completed
 * This retries all queued requests with the new token
 */
function onTokenRefreshed(newToken: string): void {
  refreshSubscribers.forEach(callback => callback(newToken))
  refreshSubscribers = []
}

// Create axios instance with default configuration
const apiClient: AxiosInstance = axios.create({
  baseURL: config.apiUrl,
  timeout: 30000, // 30 second timeout to prevent hanging requests
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor to add auth token
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig): InternalAxiosRequestConfig => {
    const token = localStorage.getItem('accessToken')
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
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

      const refreshToken = localStorage.getItem('refreshToken')
      if (refreshToken) {
        // If already refreshing, queue this request to retry after refresh completes
        if (isRefreshing) {
          return new Promise(resolve => {
            subscribeTokenRefresh((newToken: string) => {
              if (originalRequest.headers) {
                originalRequest.headers.Authorization = `Bearer ${newToken}`
              }
              resolve(apiClient(originalRequest))
            })
          })
        }

        // Start refresh process
        isRefreshing = true

        try {
          const response = await axios.post<{ access_token: string; refresh_token: string }>(
            `${config.apiUrl}/api/v1/auth/refresh`,
            { refresh_token: refreshToken }
          )

          const newAccessToken = response.data.access_token
          localStorage.setItem('accessToken', newAccessToken)
          localStorage.setItem('refreshToken', response.data.refresh_token)

          // Notify all queued requests that refresh completed
          onTokenRefreshed(newAccessToken)

          // Retry original request with new token
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${newAccessToken}`
          }
          return apiClient(originalRequest)
        } catch (refreshError) {
          // Refresh failed, logout user
          localStorage.removeItem('accessToken')
          localStorage.removeItem('refreshToken')
          // Clear any queued requests
          refreshSubscribers = []
          window.location.href = '/admin/login'
          return Promise.reject(refreshError)
        } finally {
          isRefreshing = false
        }
      }
    }

    return Promise.reject(error)
  }
)

export default apiClient
