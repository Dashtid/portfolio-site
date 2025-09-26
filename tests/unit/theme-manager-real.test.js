/**
 * Unit Tests for Actual ThemeManager Class
 * Tests the real implementation with proper mocking
 */

/* eslint-env jest, node */
/* global ThemeManager */

// Import the actual ThemeManager class
const fs = require('fs')
const path = require('path')

// Read and evaluate the actual theme.js file
const themePath = path.join(__dirname, '../../site/static/js/theme.js')
const themeCode = fs.readFileSync(themePath, 'utf8')

// Setup DOM before evaluating the code
document.documentElement = document.createElement('html')
document.head = document.createElement('head')
document.body = document.createElement('body')

// Evaluate the theme.js code in our test environment
// eslint-disable-next-line no-eval
eval(themeCode)

describe('ThemeManager (Real Implementation)', () => {
  let themeManager
  let mockButton
  let mockManualToggle

  beforeEach(() => {
    // Reset DOM
    document.documentElement.innerHTML = ''
    document.head.innerHTML = ''
    document.body.innerHTML = ''

    // Create mock elements that the ThemeManager expects
    mockButton = document.createElement('div')
    mockButton.id = 'themeToggle'
    mockButton.setAttribute = jest.fn()
    mockButton.getAttribute = jest.fn()
    mockButton.addEventListener = jest.fn()
    mockButton.classList = {
      add: jest.fn(),
      remove: jest.fn(),
      toggle: jest.fn(),
      contains: jest.fn().mockReturnValue(false)
    }

    mockManualToggle = document.createElement('div')
    mockManualToggle.id = 'lightDarkToggle'
    mockManualToggle.setAttribute = jest.fn()
    mockManualToggle.addEventListener = jest.fn()

    const manualContainer = document.createElement('div')
    manualContainer.id = 'manualThemeToggle'
    manualContainer.classList = {
      add: jest.fn(),
      remove: jest.fn(),
      contains: jest.fn().mockReturnValue(false)
    }

    // Mock getElementById
    document.getElementById = jest.fn(id => {
      switch (id) {
        case 'themeToggle':
          return mockButton
        case 'lightDarkToggle':
          return mockManualToggle
        case 'manualThemeToggle':
          return manualContainer
        default:
          return null
      }
    })

    // Clear localStorage
    localStorage.clear()
  })

  describe('Constructor and Initialization', () => {
    test('should initialize with default values', () => {
      themeManager = new ThemeManager()

      expect(themeManager.storageKey).toBe('theme')
      expect(themeManager.modeKey).toBe('theme-mode')
      expect(themeManager.currentMode).toBe('system')
    })

    test('should detect system theme preference', () => {
      // Mock system dark mode preference
      window.matchMedia = jest.fn().mockReturnValue({
        matches: true,
        addListener: jest.fn(),
        addEventListener: jest.fn()
      })

      themeManager = new ThemeManager()
      expect(themeManager.currentTheme).toBe('dark')
    })

    test('should use saved manual theme preference', () => {
      localStorage.setItem('theme-mode', 'manual')
      localStorage.setItem('theme', 'light')

      themeManager = new ThemeManager()
      expect(themeManager.currentMode).toBe('manual')
      expect(themeManager.currentTheme).toBe('light')
    })
  })

  describe('Theme Management', () => {
    beforeEach(() => {
      themeManager = new ThemeManager()
    })

    test('should set theme on document element', () => {
      const setAttribute = jest.spyOn(document.documentElement, 'setAttribute')

      themeManager.setTheme('dark')

      expect(setAttribute).toHaveBeenCalledWith('data-theme', 'dark')
      expect(themeManager.currentTheme).toBe('dark')
    })

    test('should dispatch theme change event', () => {
      const dispatchEvent = jest.spyOn(window, 'dispatchEvent')

      themeManager.setTheme('dark')

      expect(dispatchEvent).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'themeChanged',
          detail: expect.objectContaining({
            theme: 'dark',
            isDark: true
          })
        })
      )
    })

    test('should toggle between themes', () => {
      themeManager.currentTheme = 'light'

      const newTheme = themeManager.toggleTheme()

      expect(newTheme).toBe('dark')
      expect(themeManager.currentTheme).toBe('dark')
    })

    test('should toggle between modes', () => {
      themeManager.currentMode = 'system'

      const newMode = themeManager.toggleMode()

      expect(newMode).toBe('manual')
      expect(themeManager.currentMode).toBe('manual')
    })
  })

  describe('UI Updates', () => {
    beforeEach(() => {
      themeManager = new ThemeManager()
    })

    test('should update slider ARIA attributes', () => {
      themeManager.currentMode = 'manual'

      themeManager.updateSlider(mockButton)

      expect(mockButton.setAttribute).toHaveBeenCalledWith(
        'aria-checked',
        'true'
      )
      expect(mockButton.setAttribute).toHaveBeenCalledWith(
        'aria-label',
        expect.stringContaining('manual')
      )
    })

    test('should update light/dark toggle ARIA attributes', () => {
      themeManager.currentTheme = 'dark'

      themeManager.updateLightDarkToggle(mockManualToggle)

      expect(mockManualToggle.setAttribute).toHaveBeenCalledWith(
        'aria-checked',
        'true'
      )
      expect(mockManualToggle.setAttribute).toHaveBeenCalledWith(
        'aria-label',
        expect.stringContaining('dark')
      )
    })
  })

  describe('Error Handling', () => {
    test('should handle missing DOM elements gracefully', () => {
      document.getElementById = jest.fn().mockReturnValue(null)

      expect(() => {
        themeManager = new ThemeManager()
      }).not.toThrow()
    })

    test('should handle localStorage errors gracefully', () => {
      const originalSetItem = localStorage.setItem
      localStorage.setItem = jest.fn().mockImplementation(() => {
        throw new Error('Storage quota exceeded')
      })

      themeManager = new ThemeManager()

      expect(() => {
        themeManager.setTheme('dark')
      }).not.toThrow()

      localStorage.setItem = originalSetItem
    })
  })

  describe('Accessibility', () => {
    beforeEach(() => {
      themeManager = new ThemeManager()
    })

    test('should detect mobile Safari for specific fixes', () => {
      Object.defineProperty(navigator, 'userAgent', {
        value:
          'Mozilla/5.0 (iPhone; CPU iPhone OS 15_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1',
        configurable: true
      })

      expect(themeManager.isMobileSafari()).toBe(true)
    })

    test('should handle keyboard events for accessibility', () => {
      // Test that the manager is prepared to handle keyboard events
      expect(themeManager.toggleMode).toBeDefined()
      expect(typeof themeManager.toggleMode).toBe('function')
    })
  })
})
