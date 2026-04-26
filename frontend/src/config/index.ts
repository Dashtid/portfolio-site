/**
 * Centralized application configuration
 * Eliminates duplicate env variable access across the codebase
 */

import { STORAGE_KEYS } from '@/utils/storage'

export const config = {
  /**
   * API base URL — defaults to the production API so SSG builds (and any
   * Vercel/CI build without VITE_API_URL set) can fetch real data when
   * pre-rendering. Local dev should set VITE_API_URL=http://localhost:8000.
   */
  apiUrl: import.meta.env.VITE_API_URL || 'https://dashti.se',

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
   * Site identity constants
   */
  github: {
    username: 'Dashtid'
  },

  /**
   * Re-export storage keys for convenience (single source of truth)
   */
  storageKeys: STORAGE_KEYS
} as const

export type Config = typeof config
