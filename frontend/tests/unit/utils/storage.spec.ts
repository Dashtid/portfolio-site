import { describe, it, expect, beforeEach, vi } from 'vitest'
import { storage, STORAGE_KEYS } from '@/utils/storage'

// Mock localStorage
const mockLocalStorage = (() => {
  let store: Record<string, string> = {}
  return {
    getItem: vi.fn((key: string) => store[key] || null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value
    }),
    removeItem: vi.fn((key: string) => {
      delete store[key]
    }),
    clear: vi.fn(() => {
      store = {}
    }),
    get length() {
      return Object.keys(store).length
    },
    key: vi.fn((index: number) => Object.keys(store)[index] || null),
  }
})()

Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,
  writable: true,
})

describe('Storage Utility', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockLocalStorage.clear()
  })

  describe('STORAGE_KEYS', () => {
    it('should have all expected keys defined', () => {
      expect(STORAGE_KEYS.ACCESS_TOKEN).toBe('accessToken')
      expect(STORAGE_KEYS.REFRESH_TOKEN).toBe('refreshToken')
      expect(STORAGE_KEYS.THEME).toBe('theme')
      expect(STORAGE_KEYS.USER_PREFERENCES).toBe('userPreferences')
    })
  })

  describe('getItem', () => {
    it('should return null for non-existent key', () => {
      const result = storage.getItem(STORAGE_KEYS.ACCESS_TOKEN)
      expect(result).toBeNull()
    })

    it('should return stored value', () => {
      mockLocalStorage.setItem('accessToken', 'test-token')
      const result = storage.getItem(STORAGE_KEYS.ACCESS_TOKEN)
      expect(result).toBe('test-token')
    })
  })

  describe('setItem', () => {
    it('should store a value', () => {
      const result = storage.setItem(STORAGE_KEYS.ACCESS_TOKEN, 'my-token')
      expect(result).toBe(true)
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith('accessToken', 'my-token')
    })

    it('should return true on success', () => {
      const result = storage.setItem(STORAGE_KEYS.THEME, 'dark')
      expect(result).toBe(true)
    })
  })

  describe('removeItem', () => {
    it('should remove an item', () => {
      mockLocalStorage.setItem('accessToken', 'test')
      const result = storage.removeItem(STORAGE_KEYS.ACCESS_TOKEN)
      expect(result).toBe(true)
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('accessToken')
    })
  })

  describe('getJSON', () => {
    it('should return null for non-existent key', () => {
      const result = storage.getJSON(STORAGE_KEYS.USER_PREFERENCES)
      expect(result).toBeNull()
    })

    it('should parse and return JSON value', () => {
      const data = { theme: 'dark', language: 'en' }
      mockLocalStorage.setItem('userPreferences', JSON.stringify(data))
      const result = storage.getJSON<typeof data>(STORAGE_KEYS.USER_PREFERENCES)
      expect(result).toEqual(data)
    })

    it('should return null for invalid JSON', () => {
      mockLocalStorage.setItem('userPreferences', 'not-json')
      const result = storage.getJSON(STORAGE_KEYS.USER_PREFERENCES)
      expect(result).toBeNull()
    })
  })

  describe('setJSON', () => {
    it('should stringify and store JSON value', () => {
      const data = { theme: 'dark', language: 'en' }
      const result = storage.setJSON(STORAGE_KEYS.USER_PREFERENCES, data)
      expect(result).toBe(true)
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
        'userPreferences',
        JSON.stringify(data)
      )
    })

    it('should handle nested objects', () => {
      const data = {
        preferences: {
          theme: 'dark',
          notifications: { email: true, push: false },
        },
      }
      const result = storage.setJSON(STORAGE_KEYS.USER_PREFERENCES, data)
      expect(result).toBe(true)
    })
  })

  describe('clear', () => {
    it('should clear all storage', () => {
      mockLocalStorage.setItem('accessToken', 'token')
      mockLocalStorage.setItem('refreshToken', 'refresh')
      const result = storage.clear()
      expect(result).toBe(true)
      expect(mockLocalStorage.clear).toHaveBeenCalled()
    })
  })

  describe('getMultiple', () => {
    it('should return multiple values', () => {
      mockLocalStorage.setItem('accessToken', 'access')
      mockLocalStorage.setItem('refreshToken', 'refresh')
      const result = storage.getMultiple([STORAGE_KEYS.ACCESS_TOKEN, STORAGE_KEYS.REFRESH_TOKEN])
      expect(result[STORAGE_KEYS.ACCESS_TOKEN]).toBe('access')
      expect(result[STORAGE_KEYS.REFRESH_TOKEN]).toBe('refresh')
    })

    it('should return null for missing keys', () => {
      mockLocalStorage.setItem('accessToken', 'access')
      const result = storage.getMultiple([STORAGE_KEYS.ACCESS_TOKEN, STORAGE_KEYS.THEME])
      expect(result[STORAGE_KEYS.ACCESS_TOKEN]).toBe('access')
      expect(result[STORAGE_KEYS.THEME]).toBeNull()
    })
  })

  describe('removeMultiple', () => {
    it('should remove multiple items', () => {
      mockLocalStorage.setItem('accessToken', 'access')
      mockLocalStorage.setItem('refreshToken', 'refresh')
      storage.removeMultiple([STORAGE_KEYS.ACCESS_TOKEN, STORAGE_KEYS.REFRESH_TOKEN])
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('accessToken')
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('refreshToken')
    })
  })

  describe('isAvailable', () => {
    it('should be true when localStorage is available', () => {
      expect(storage.isAvailable).toBe(true)
    })
  })
})
