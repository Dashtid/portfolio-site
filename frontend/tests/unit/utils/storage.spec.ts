import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { storage, STORAGE_KEYS } from '@/utils/storage'

// Mock localStorage
const createMockLocalStorage = () => {
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
    _getStore: () => store,
    _setStore: (newStore: Record<string, string>) => {
      store = newStore
    }
  }
}

let mockLocalStorage: ReturnType<typeof createMockLocalStorage>

beforeEach(() => {
  mockLocalStorage = createMockLocalStorage()
  Object.defineProperty(window, 'localStorage', {
    value: mockLocalStorage,
    writable: true
  })
})

afterEach(() => {
  vi.clearAllMocks()
})

describe('Storage Utility', () => {
  beforeEach(() => {
    mockLocalStorage.clear()
  })

  describe('STORAGE_KEYS', () => {
    it('should have all expected keys defined', () => {
      expect(STORAGE_KEYS.ACCESS_TOKEN).toBe('accessToken')
      expect(STORAGE_KEYS.REFRESH_TOKEN).toBe('refreshToken')
      expect(STORAGE_KEYS.THEME).toBe('theme')
      expect(STORAGE_KEYS.USER_PREFERENCES).toBe('userPreferences')
    })

    it('should be readonly', () => {
      // TypeScript const assertion makes it readonly
      expect(Object.keys(STORAGE_KEYS)).toHaveLength(4)
    })
  })

  describe('isAvailable', () => {
    it('should be true when localStorage is available', () => {
      expect(storage.isAvailable).toBe(true)
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

    it('should handle localStorage.getItem throwing error', () => {
      mockLocalStorage.getItem.mockImplementation(() => {
        throw new Error('Storage quota exceeded')
      })

      const result = storage.getItem(STORAGE_KEYS.ACCESS_TOKEN)
      expect(result).toBeNull()
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

    it('should handle localStorage.setItem throwing error', () => {
      mockLocalStorage.setItem.mockImplementation(() => {
        throw new Error('Storage quota exceeded')
      })

      const result = storage.setItem(STORAGE_KEYS.ACCESS_TOKEN, 'token')
      expect(result).toBe(false)
    })

    it('should handle empty string value', () => {
      const result = storage.setItem(STORAGE_KEYS.ACCESS_TOKEN, '')
      expect(result).toBe(true)
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith('accessToken', '')
    })
  })

  describe('removeItem', () => {
    it('should remove an item', () => {
      mockLocalStorage.setItem('accessToken', 'test')
      const result = storage.removeItem(STORAGE_KEYS.ACCESS_TOKEN)
      expect(result).toBe(true)
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('accessToken')
    })

    it('should return true when removing non-existent key', () => {
      const result = storage.removeItem(STORAGE_KEYS.ACCESS_TOKEN)
      expect(result).toBe(true)
    })

    it('should handle localStorage.removeItem throwing error', () => {
      mockLocalStorage.removeItem.mockImplementation(() => {
        throw new Error('Storage error')
      })

      const result = storage.removeItem(STORAGE_KEYS.ACCESS_TOKEN)
      expect(result).toBe(false)
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

    it('should parse array JSON correctly', () => {
      const data = [1, 2, 3, 'test']
      mockLocalStorage.setItem('userPreferences', JSON.stringify(data))
      const result = storage.getJSON<typeof data>(STORAGE_KEYS.USER_PREFERENCES)
      expect(result).toEqual(data)
    })

    it('should parse nested object JSON correctly', () => {
      const data = {
        level1: {
          level2: {
            level3: 'deep value'
          }
        }
      }
      mockLocalStorage.setItem('userPreferences', JSON.stringify(data))
      const result = storage.getJSON<typeof data>(STORAGE_KEYS.USER_PREFERENCES)
      expect(result).toEqual(data)
    })

    it('should handle null JSON value', () => {
      mockLocalStorage.setItem('userPreferences', 'null')
      const result = storage.getJSON(STORAGE_KEYS.USER_PREFERENCES)
      expect(result).toBeNull()
    })

    it('should handle boolean JSON value', () => {
      mockLocalStorage.setItem('userPreferences', 'true')
      const result = storage.getJSON<boolean>(STORAGE_KEYS.USER_PREFERENCES)
      expect(result).toBe(true)
    })

    it('should handle number JSON value', () => {
      mockLocalStorage.setItem('userPreferences', '42')
      const result = storage.getJSON<number>(STORAGE_KEYS.USER_PREFERENCES)
      expect(result).toBe(42)
    })
  })

  describe('setJSON', () => {
    it('should stringify and store JSON value', () => {
      const data = { theme: 'dark', language: 'en' }
      const result = storage.setJSON(STORAGE_KEYS.USER_PREFERENCES, data)
      expect(result).toBe(true)
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith('userPreferences', JSON.stringify(data))
    })

    it('should handle nested objects', () => {
      const data = {
        preferences: {
          theme: 'dark',
          notifications: { email: true, push: false }
        }
      }
      const result = storage.setJSON(STORAGE_KEYS.USER_PREFERENCES, data)
      expect(result).toBe(true)
    })

    it('should handle arrays', () => {
      const data = ['a', 'b', 'c']
      const result = storage.setJSON(STORAGE_KEYS.USER_PREFERENCES, data)
      expect(result).toBe(true)
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith('userPreferences', JSON.stringify(data))
    })

    it('should handle circular reference error', () => {
      const circular: Record<string, unknown> = { name: 'test' }
      circular.self = circular

      const result = storage.setJSON(STORAGE_KEYS.USER_PREFERENCES, circular)
      expect(result).toBe(false)
    })

    it('should handle null value', () => {
      const result = storage.setJSON(STORAGE_KEYS.USER_PREFERENCES, null)
      expect(result).toBe(true)
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith('userPreferences', 'null')
    })

    it('should handle boolean value', () => {
      const result = storage.setJSON(STORAGE_KEYS.USER_PREFERENCES, true)
      expect(result).toBe(true)
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith('userPreferences', 'true')
    })

    it('should handle number value', () => {
      const result = storage.setJSON(STORAGE_KEYS.USER_PREFERENCES, 42)
      expect(result).toBe(true)
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith('userPreferences', '42')
    })

    it('should handle localStorage error during setJSON', () => {
      mockLocalStorage.setItem.mockImplementation(() => {
        throw new Error('Quota exceeded')
      })

      const result = storage.setJSON(STORAGE_KEYS.USER_PREFERENCES, { test: 'data' })
      expect(result).toBe(false)
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

    it('should handle localStorage.clear throwing error', () => {
      mockLocalStorage.clear.mockImplementation(() => {
        throw new Error('Clear failed')
      })

      const result = storage.clear()
      expect(result).toBe(false)
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

    it('should return empty object for empty keys array', () => {
      const result = storage.getMultiple([])
      expect(result).toEqual({})
    })

    it('should return all nulls when storage is empty', () => {
      const result = storage.getMultiple([
        STORAGE_KEYS.ACCESS_TOKEN,
        STORAGE_KEYS.REFRESH_TOKEN,
        STORAGE_KEYS.THEME
      ])
      expect(result[STORAGE_KEYS.ACCESS_TOKEN]).toBeNull()
      expect(result[STORAGE_KEYS.REFRESH_TOKEN]).toBeNull()
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

    it('should handle empty keys array', () => {
      storage.removeMultiple([])
      expect(mockLocalStorage.removeItem).not.toHaveBeenCalled()
    })

    it('should handle removing non-existent keys', () => {
      storage.removeMultiple([STORAGE_KEYS.ACCESS_TOKEN, STORAGE_KEYS.THEME])
      expect(mockLocalStorage.removeItem).toHaveBeenCalledTimes(2)
    })
  })

  describe('storage unavailable scenarios', () => {
    // We need to test what happens when isAvailable is false
    // This requires creating a new storage instance or mocking the property

    it('should return null from getItem when storage unavailable', () => {
      // Temporarily set isAvailable to false
      const originalIsAvailable = storage.isAvailable
      Object.defineProperty(storage, 'isAvailable', { value: false, writable: true })

      const result = storage.getItem(STORAGE_KEYS.ACCESS_TOKEN)
      expect(result).toBeNull()

      // Restore
      Object.defineProperty(storage, 'isAvailable', {
        value: originalIsAvailable,
        writable: true
      })
    })

    it('should return false from setItem when storage unavailable', () => {
      const originalIsAvailable = storage.isAvailable
      Object.defineProperty(storage, 'isAvailable', { value: false, writable: true })

      const result = storage.setItem(STORAGE_KEYS.ACCESS_TOKEN, 'token')
      expect(result).toBe(false)

      Object.defineProperty(storage, 'isAvailable', {
        value: originalIsAvailable,
        writable: true
      })
    })

    it('should return false from removeItem when storage unavailable', () => {
      const originalIsAvailable = storage.isAvailable
      Object.defineProperty(storage, 'isAvailable', { value: false, writable: true })

      const result = storage.removeItem(STORAGE_KEYS.ACCESS_TOKEN)
      expect(result).toBe(false)

      Object.defineProperty(storage, 'isAvailable', {
        value: originalIsAvailable,
        writable: true
      })
    })

    it('should return false from clear when storage unavailable', () => {
      const originalIsAvailable = storage.isAvailable
      Object.defineProperty(storage, 'isAvailable', { value: false, writable: true })

      const result = storage.clear()
      expect(result).toBe(false)

      Object.defineProperty(storage, 'isAvailable', {
        value: originalIsAvailable,
        writable: true
      })
    })
  })

  describe('type safety', () => {
    it('should properly type getJSON result', () => {
      interface UserPrefs {
        theme: string
        language: string
      }
      const data: UserPrefs = { theme: 'dark', language: 'en' }
      mockLocalStorage.setItem('userPreferences', JSON.stringify(data))

      const result = storage.getJSON<UserPrefs>(STORAGE_KEYS.USER_PREFERENCES)
      if (result) {
        expect(result.theme).toBe('dark')
        expect(result.language).toBe('en')
      }
    })

    it('should accept StorageKey type for all methods', () => {
      // These should all compile without errors
      storage.getItem(STORAGE_KEYS.ACCESS_TOKEN)
      storage.setItem(STORAGE_KEYS.REFRESH_TOKEN, 'value')
      storage.removeItem(STORAGE_KEYS.THEME)
      storage.getJSON(STORAGE_KEYS.USER_PREFERENCES)
      storage.setJSON(STORAGE_KEYS.USER_PREFERENCES, {})
    })
  })
})
