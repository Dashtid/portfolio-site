import { defineStore } from 'pinia'
import apiClient from '../api/client'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    accessToken: localStorage.getItem('accessToken') || null,
    refreshToken: localStorage.getItem('refreshToken') || null,
    isLoading: false,
    error: null
  }),

  getters: {
    isAuthenticated: (state) => !!state.accessToken,
    currentUser: (state) => state.user
  },

  actions: {
    // Initialize auth from URL params (after GitHub OAuth callback)
    initializeFromCallback() {
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
    setTokens(accessToken, refreshToken) {
      this.accessToken = accessToken
      this.refreshToken = refreshToken

      // Save to localStorage
      localStorage.setItem('accessToken', accessToken)
      localStorage.setItem('refreshToken', refreshToken)

      // Configure axios default header
      apiClient.defaults.headers.common['Authorization'] = `Bearer ${accessToken}`

      // Fetch user info
      this.fetchUser()
    },

    // Fetch current user info
    async fetchUser() {
      if (!this.accessToken) return

      try {
        const response = await apiClient.get('/api/v1/auth/me')
        this.user = response.data
      } catch (error) {
        console.error('Failed to fetch user:', error)
        if (error.response?.status === 401) {
          await this.refreshAccessToken()
        }
      }
    },

    // Refresh access token
    async refreshAccessToken() {
      if (!this.refreshToken) {
        this.logout()
        return
      }

      try {
        const response = await apiClient.post('/api/v1/auth/refresh', {
          refresh_token: this.refreshToken
        })

        this.setTokens(response.data.access_token, response.data.refresh_token)
      } catch (error) {
        console.error('Failed to refresh token:', error)
        this.logout()
      }
    },

    // Login with GitHub
    loginWithGitHub() {
      window.location.href = 'http://localhost:8001/api/v1/auth/github'
    },

    // Logout
    async logout() {
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
        delete apiClient.defaults.headers.common['Authorization']
      }
    },

    // Check auth status on app start
    async checkAuth() {
      if (this.accessToken) {
        // Set axios header
        axios.defaults.headers.common['Authorization'] = `Bearer ${this.accessToken}`

        // Fetch user info
        await this.fetchUser()
      }
    }
  }
})