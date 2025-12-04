/**
 * Storage utility for type-safe localStorage operations
 *
 * Provides a centralized, type-safe abstraction over localStorage
 * with support for JSON serialization and error handling.
 */

import { createLogger } from './logger'

const logger = createLogger('Storage')

/**
 * Storage keys used throughout the application
 */
export const STORAGE_KEYS = {
  ACCESS_TOKEN: 'accessToken',
  REFRESH_TOKEN: 'refreshToken',
  THEME: 'theme',
  USER_PREFERENCES: 'userPreferences'
} as const

export type StorageKey = (typeof STORAGE_KEYS)[keyof typeof STORAGE_KEYS]

/**
 * Check if localStorage is available
 */
function isStorageAvailable(): boolean {
  try {
    const testKey = '__storage_test__'
    localStorage.setItem(testKey, testKey)
    localStorage.removeItem(testKey)
    return true
  } catch {
    return false
  }
}

/**
 * Storage manager for type-safe localStorage operations
 */
export const storage = {
  /**
   * Check if storage is available
   */
  isAvailable: isStorageAvailable(),

  /**
   * Get a string value from storage
   */
  getItem(key: StorageKey): string | null {
    if (!this.isAvailable) {
      logger.warn('localStorage not available')
      return null
    }

    try {
      return localStorage.getItem(key)
    } catch (error) {
      logger.error(`Failed to get item "${key}"`, error)
      return null
    }
  },

  /**
   * Set a string value in storage
   */
  setItem(key: StorageKey, value: string): boolean {
    if (!this.isAvailable) {
      logger.warn('localStorage not available')
      return false
    }

    try {
      localStorage.setItem(key, value)
      return true
    } catch (error) {
      logger.error(`Failed to set item "${key}"`, error)
      return false
    }
  },

  /**
   * Remove an item from storage
   */
  removeItem(key: StorageKey): boolean {
    if (!this.isAvailable) {
      logger.warn('localStorage not available')
      return false
    }

    try {
      localStorage.removeItem(key)
      return true
    } catch (error) {
      logger.error(`Failed to remove item "${key}"`, error)
      return false
    }
  },

  /**
   * Get a JSON-parsed value from storage
   */
  getJSON<T>(key: StorageKey): T | null {
    const value = this.getItem(key)
    if (value === null) return null

    try {
      return JSON.parse(value) as T
    } catch (error) {
      logger.error(`Failed to parse JSON for key "${key}"`, error)
      return null
    }
  },

  /**
   * Set a JSON-stringified value in storage
   */
  setJSON<T>(key: StorageKey, value: T): boolean {
    try {
      const stringValue = JSON.stringify(value)
      return this.setItem(key, stringValue)
    } catch (error) {
      logger.error(`Failed to stringify JSON for key "${key}"`, error)
      return false
    }
  },

  /**
   * Clear all storage (use with caution)
   */
  clear(): boolean {
    if (!this.isAvailable) {
      logger.warn('localStorage not available')
      return false
    }

    try {
      localStorage.clear()
      return true
    } catch (error) {
      logger.error('Failed to clear storage', error)
      return false
    }
  },

  /**
   * Get multiple items at once
   */
  getMultiple(keys: StorageKey[]): Record<StorageKey, string | null> {
    const result = {} as Record<StorageKey, string | null>
    for (const key of keys) {
      result[key] = this.getItem(key)
    }
    return result
  },

  /**
   * Remove multiple items at once
   */
  removeMultiple(keys: StorageKey[]): void {
    for (const key of keys) {
      this.removeItem(key)
    }
  }
}

export default storage
