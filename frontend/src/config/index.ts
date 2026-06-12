/**
 * Centralized application configuration.
 */

export const config = {
  /**
   * API base URL — defaults to the production API at api.dashti.se so SSG
   * builds (and any Vercel/CI build without VITE_API_URL set) can fetch
   * real data when pre-rendering. Local dev should set
   * VITE_API_URL=http://localhost:8000.
   */
  apiUrl: import.meta.env.VITE_API_URL || 'https://api.dashti.se',

  /**
   * Site identity constants
   */
  github: {
    username: 'Dashtid'
  }
} as const

export type Config = typeof config
