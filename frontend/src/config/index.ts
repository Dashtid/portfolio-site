/**
 * Centralized application configuration
 * Eliminates duplicate env variable access across the codebase
 */

import { STORAGE_KEYS } from '@/utils/storage'

export const config = {
  /**
   * API base URL - defaults to localhost for development
   */
  apiUrl: import.meta.env.VITE_API_URL || 'http://localhost:8000',

  /**
   * API endpoints
   */
  endpoints: {
    companies: '/api/v1/companies',
    skills: '/api/v1/skills',
    projects: '/api/v1/projects',
    education: '/api/v1/education',
    auth: {
      login: '/api/v1/auth/login',
      refresh: '/api/v1/auth/refresh',
      logout: '/api/v1/auth/logout'
    }
  },

  /**
   * Application settings
   */
  app: {
    name: 'Portfolio'
  },

  /**
   * Re-export storage keys for convenience (single source of truth)
   */
  storageKeys: STORAGE_KEYS
} as const

export type Config = typeof config
