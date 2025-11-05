import { defineStore } from 'pinia'
import apiClient from '../api/client'
import type { LoginResponse } from '@/types'

// Get API URL from environment variables
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface User {
  id: string
  username: string
  email?: string
}

interface AuthState {
  user: User | null
  accessToken: string | null
  refreshToken: string | null
  isLoading: boolean
  error: string | null
}

export const useAuthStore = defineStore('auth', {
  state: (): AuthState => ({
    user: null,
    accessToken: localStorage.getItem('accessToken') || null,
    refreshToken: localStorage.getItem('refreshToken') || null,
    isLoading: false,
    error: null
  }),

  getters: {
    isAuthenticated: (state): boolean => !!state.accessToken,
    currentUser: (state): User | null => state.user
  },

  actions: {
    // Initialize auth from URL params (after GitHub OAuth callback)
    initializeFromCallback(): boolean {
      const params = new URLSearchParams(window.location.search)
      const token = params.get('token')
      const refresh = params.get('refresh')

      if (token && refresh) {
        this.setTokens(token, refresh)
        // Clean URL
        window.history.replaceState({}, '', window.location.pathname)
        return true
      }
      return false
    },

    // Set tokens and configure axios
    setTokens(accessToken: string, refreshToken: string): void {
      this.accessToken = accessToken
      this.refreshToken = refreshToken

      // Save to localStorage
      localStorage.setItem('accessToken', accessToken)
      localStorage.setItem('refreshToken', refreshToken)

      // Configure axios default header
      if (apiClient.defaults.headers.common) {
        apiClient.defaults.headers.common['Authorization'] = `Bearer ${accessToken}`
      }

      // Fetch user info
      this.fetchUser()
    },

    // Fetch current user info
    async fetchUser(): Promise<void> {
      if (!this.accessToken) return

      try {
        const response = await apiClient.get<User>('/api/v1/auth/me')
        this.user = response.data
      } catch (error: any) {
        console.error('Failed to fetch user:', error)
        if (error.response?.status === 401) {
          await this.refreshAccessToken()
        }
      }
    },

    // Refresh access token
    async refreshAccessToken(): Promise<void> {
      if (!this.refreshToken) {
        this.logout()
        return
      }

      try {
        const response = await apiClient.post<LoginResponse>('/api/v1/auth/refresh', {
          refresh_token: this.refreshToken
        })

        this.setTokens(response.data.access_token, response.data.access_token)
      } catch (error) {
        console.error('Failed to refresh token:', error)
        this.logout()
      }
    },

    // Login with GitHub
    loginWithGitHub(): void {
      window.location.href = `${API_URL}/api/v1/auth/github`
    },

    // Logout
    async logout(): Promise<void> {
      try {
        await apiClient.post('/api/v1/auth/logout')
      } catch (error) {
        console.error('Logout error:', error)
      } finally {
        // Clear local data
        this.user = null
        this.accessToken = null
        this.refreshToken = null

        // Clear localStorage
        localStorage.removeItem('accessToken')
        localStorage.removeItem('refreshToken')

        // Clear axios header
        if (apiClient.defaults.headers.common) {
          delete apiClient.defaults.headers.common['Authorization']
        }
      }
    },

    // Check auth status on app start
    async checkAuth(): Promise<void> {
      if (this.accessToken) {
        // Set axios header
        if (apiClient.defaults.headers.common) {
          apiClient.defaults.headers.common['Authorization'] = `Bearer ${this.accessToken}`
        }

        // Fetch user info
        await this.fetchUser()
      }
    }
  }
})
