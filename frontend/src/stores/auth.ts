import { defineStore } from 'pinia'
import apiClient from '../api/client'
import type { LoginResponse } from '@/types'
import { storage, STORAGE_KEYS } from '@/utils/storage'
import { authLogger } from '@/utils/logger'
import { isUnauthorizedError } from '@/utils/typeGuards'
import { config } from '@/config'

interface User {
  id: string
  username: string
  name?: string
  email?: string
  avatar_url?: string
}

interface AuthState {
  user: User | null
  accessToken: string | null
  refreshToken: string | null
  isLoading: boolean
  error: string | null
  isInitialized: boolean
  initializingPromise: Promise<void> | null
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    user: null,
    accessToken: null,
    refreshToken: null,
    isLoading: false,
    error: null,
    isInitialized: false,
    initializingPromise: null
  }),

  getters: {
    // Auth is based on user presence (tokens are in HTTP-only cookies)
    isAuthenticated: (state): boolean => !!state.user || !!state.accessToken,
    currentUser: (state): User | null => state.user
  },

  actions: {
    // Check if we're returning from OAuth callback and fetch user
    // Tokens are now in HTTP-only cookies, not URL params
    async initializeFromCallback(): Promise<boolean> {
      // If we're on /admin and just redirected from OAuth, fetch user
      if (window.location.pathname === '/admin') {
        try {
          await this.fetchUser()
          return !!this.user
        } catch {
          return false
        }
      }
      return false
    },

    // Set tokens for backwards compatibility (localStorage-based auth)
    async setTokens(accessToken: string, refreshToken: string): Promise<void> {
      this.accessToken = accessToken
      this.refreshToken = refreshToken

      // Save to localStorage using storage utility
      storage.setItem(STORAGE_KEYS.ACCESS_TOKEN, accessToken)
      storage.setItem(STORAGE_KEYS.REFRESH_TOKEN, refreshToken)

      // Configure axios default header for backwards compatibility
      if (apiClient.defaults.headers.common) {
        apiClient.defaults.headers.common['Authorization'] = `Bearer ${accessToken}`
      }

      // Fetch user info - await to prevent race condition
      await this.fetchUser()
    },

    // Fetch current user info (uses HTTP-only cookies automatically)
    async fetchUser(): Promise<void> {
      try {
        const response = await apiClient.get<User>('/api/v1/auth/me')
        this.user = response.data
      } catch (error: unknown) {
        // Only clear user on auth errors (401/403), not on network issues
        if (isUnauthorizedError(error)) {
          this.user = null
        } else {
          // Log other errors but don't clear user (could be temporary network issue)
          authLogger.error('Failed to fetch user:', error)
        }
      }
    },

    // Refresh access token
    async refreshAccessToken(): Promise<void> {
      try {
        // Cookies are sent automatically; body is for backwards compatibility
        const response = await apiClient.post<LoginResponse>(
          '/api/v1/auth/refresh',
          this.refreshToken ? { refresh_token: this.refreshToken } : {}
        )

        // Update local state if tokens returned in response
        const newAccessToken = response.data.access_token
        const newRefreshToken = response.data.refresh_token

        if (newAccessToken) {
          this.accessToken = newAccessToken
          storage.setItem(STORAGE_KEYS.ACCESS_TOKEN, newAccessToken)
          if (apiClient.defaults.headers.common) {
            apiClient.defaults.headers.common['Authorization'] = `Bearer ${newAccessToken}`
          }
        }
        if (newRefreshToken) {
          this.refreshToken = newRefreshToken
          storage.setItem(STORAGE_KEYS.REFRESH_TOKEN, newRefreshToken)
        }

        // Fetch updated user info
        await this.fetchUser()
      } catch (error) {
        authLogger.error('Failed to refresh token:', error)
        await this.logout()
      }
    },

    // Login with GitHub
    loginWithGitHub(): void {
      window.location.href = `${config.apiUrl}/api/v1/auth/github`
    },

    // Logout
    async logout(): Promise<void> {
      try {
        await apiClient.post('/api/v1/auth/logout')
      } catch (error) {
        authLogger.error('Logout error:', error)
      } finally {
        // Clear local data
        this.user = null
        this.accessToken = null
        this.refreshToken = null

        // Clear localStorage using storage utility
        storage.removeMultiple([STORAGE_KEYS.ACCESS_TOKEN, STORAGE_KEYS.REFRESH_TOKEN])

        // Clear axios header
        if (apiClient.defaults.headers.common) {
          delete apiClient.defaults.headers.common['Authorization']
        }
      }
    },

    // Check auth status on app start
    async checkAuth(): Promise<void> {
      // With HTTP-only cookies, just try to fetch user
      // Cookies are sent automatically with requests
      await this.fetchUser()

      // Also check localStorage for backwards compatibility
      if (!this.user && this.accessToken) {
        if (apiClient.defaults.headers.common) {
          apiClient.defaults.headers.common['Authorization'] = `Bearer ${this.accessToken}`
        }
        await this.fetchUser()
      }
    },

    // Initialize auth state (called by route guard)
    // Uses Promise-based lock to prevent concurrent initializations
    async initializeAuth(): Promise<void> {
      // Already initialized - return immediately
      if (this.isInitialized) return

      // Another initialization in progress - wait for it
      if (this.initializingPromise) {
        return this.initializingPromise
      }

      // Start initialization with Promise lock
      this.initializingPromise = (async () => {
        // Load tokens from localStorage for backwards compatibility
        const storedAccessToken = storage.getItem(STORAGE_KEYS.ACCESS_TOKEN)
        const storedRefreshToken = storage.getItem(STORAGE_KEYS.REFRESH_TOKEN)

        if (storedAccessToken && storedRefreshToken) {
          this.accessToken = storedAccessToken
          this.refreshToken = storedRefreshToken

          // Set axios header for localStorage-based auth
          if (apiClient.defaults.headers.common) {
            apiClient.defaults.headers.common['Authorization'] = `Bearer ${storedAccessToken}`
          }
        }

        // Try to fetch user (will use cookies or header)
        await this.fetchUser()

        this.isInitialized = true
      })()

      try {
        await this.initializingPromise
      } finally {
        this.initializingPromise = null
      }
    }
  }
})
