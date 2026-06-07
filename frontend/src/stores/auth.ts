import { defineStore } from 'pinia'
import apiClient from '../api/client'
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
  isLoading: boolean
  error: string | null
  isInitialized: boolean
  initializingPromise: Promise<void> | null
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    user: null,
    isLoading: false,
    error: null,
    isInitialized: false,
    initializingPromise: null
  }),

  getters: {
    // Auth state is owned by HTTP-only cookies; the user object is the
    // client-side projection of "are we authenticated".
    isAuthenticated: (state): boolean => !!state.user,
    currentUser: (state): User | null => state.user
  },

  actions: {
    // Check if we're returning from OAuth callback and fetch user
    async initializeFromCallback(): Promise<boolean> {
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
          authLogger.error('Failed to fetch user:', error)
        }
      }
    },

    // Login with GitHub
    loginWithGitHub(): void {
      window.location.href = `${config.apiUrl}/api/v1/auth/github`
    },

    // Logout — backend clears the HTTP-only cookies
    async logout(): Promise<void> {
      try {
        await apiClient.post('/api/v1/auth/logout')
      } catch (error) {
        authLogger.error('Logout error:', error)
      } finally {
        this.user = null
      }
    },

    // Initialize auth state (called by route guard)
    // Uses Promise-based lock to prevent concurrent initializations
    async initializeAuth(): Promise<void> {
      if (this.isInitialized) return

      if (this.initializingPromise) {
        return this.initializingPromise
      }

      this.initializingPromise = (async () => {
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
