/**
 * Unit Tests for ThemeManager Class
 * Tests theme switching, persistence, and event handling
 */

const { TestUtils } = require('./setup.js')

// Mock ThemeManager class for testing
class ThemeManager {
  constructor () {
    this.storageKey = 'theme'
    this.mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    this.currentTheme = this.getInitialTheme()
    this.init()
  }

  getInitialTheme () {
    const saved = localStorage.getItem(this.storageKey)
    return saved || (this.mediaQuery.matches ? 'dark' : 'light')
  }

  setTheme (theme) {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem(this.storageKey, theme)
    this.currentTheme = theme
    window.dispatchEvent(new CustomEvent('themechange', { detail: { theme } }))
  }

  updateButton (button, theme) {
    const isDark = theme === 'dark'
    button.textContent = isDark ? 'Light' : 'Dark'
    button.classList.toggle('btn-outline-light', isDark)
    button.classList.toggle('btn-outline-dark', !isDark)
    button.setAttribute(
      'aria-label',
      `Switch to ${isDark ? 'light' : 'dark'} theme`
    )
  }

  toggleTheme () {
    const nextTheme = this.currentTheme === 'dark' ? 'light' : 'dark'
    this.setTheme(nextTheme)
    return nextTheme
  }

  init () {
    this.setTheme(this.currentTheme)
    const themeButton = document.getElementById('theme-toggle')
    if (themeButton) {
      this.updateButton(themeButton, this.currentTheme)
      themeButton.addEventListener('click', () => {
        const newTheme = this.toggleTheme()
        this.updateButton(themeButton, newTheme)
      })
    }
    this.mediaQuery.addEventListener('change', (e) => {
      if (!localStorage.getItem(this.storageKey)) {
        const systemTheme = e.matches ? 'dark' : 'light'
        this.setTheme(systemTheme)
        if (themeButton) {
          this.updateButton(themeButton, systemTheme)
        }
      }
    })
  }
}

describe('ThemeManager', () => {
  let themeManager
  let mockButton

  beforeEach(() => {
    document.documentElement.removeAttribute('data-theme')

    mockButton = TestUtils.createMockElement('button', {
      id: 'theme-toggle',
      'aria-label': 'Switch to dark theme'
    })
    document.body.appendChild(mockButton)

    localStorage.clear()

    window.matchMedia = jest.fn().mockReturnValue({
      matches: false,
      addEventListener: jest.fn(),
      removeEventListener: jest.fn()
    })
  })

  afterEach(() => {
    if (mockButton.parentNode) {
      document.body.removeChild(mockButton)
    }
    jest.clearAllMocks()
  })

  describe('Constructor', () => {
    test('should initialize with correct default values', () => {
      themeManager = new ThemeManager()

      expect(themeManager.storageKey).toBe('theme')
      expect(themeManager.currentTheme).toBe('light')
    })

    test('should respect saved theme preference', () => {
      localStorage.getItem.mockReturnValue('dark')

      themeManager = new ThemeManager()

      expect(themeManager.currentTheme).toBe('dark')
    })

    test('should respect system dark mode preference when no saved preference', () => {
      window.matchMedia = jest.fn().mockReturnValue({
        matches: true,
        addEventListener: jest.fn(),
        removeEventListener: jest.fn()
      })

      themeManager = new ThemeManager()

      expect(themeManager.currentTheme).toBe('dark')
    })
  })

  describe('Theme Detection and Initial Setup', () => {
    test('should detect light theme as default when no preference set', () => {
      themeManager = new ThemeManager()

      const initialTheme = themeManager.getInitialTheme()
      expect(initialTheme).toBe('light')
    })

    test('should detect saved theme preference', () => {
      localStorage.getItem.mockReturnValue('dark')
      themeManager = new ThemeManager()

      const initialTheme = themeManager.getInitialTheme()
      expect(initialTheme).toBe('dark')
    })

    test('should detect system theme preference when no saved preference', () => {
      window.matchMedia = jest.fn().mockReturnValue({
        matches: true,
        addEventListener: jest.fn(),
        removeEventListener: jest.fn()
      })

      themeManager = new ThemeManager()

      const initialTheme = themeManager.getInitialTheme()
      expect(initialTheme).toBe('dark')
    })
  })

  describe('Theme Setting and Persistence', () => {
    beforeEach(() => {
      themeManager = new ThemeManager()
    })

    test('should set theme attribute on document element', () => {
      themeManager.setTheme('dark')

      expect(document.documentElement.getAttribute('data-theme')).toBe('dark')
      expect(themeManager.currentTheme).toBe('dark')
    })

    test('should save theme preference to localStorage', () => {
      themeManager.setTheme('dark')

      expect(localStorage.setItem).toHaveBeenCalledWith('theme', 'dark')
    })

    test('should dispatch custom theme change event', () => {
      const eventSpy = jest.spyOn(window, 'dispatchEvent')

      themeManager.setTheme('dark')

      expect(eventSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          type: 'themechange',
          detail: { theme: 'dark' }
        })
      )
    })
  })

  describe('Theme Toggle Functionality', () => {
    beforeEach(() => {
      themeManager = new ThemeManager()
    })

    test('should toggle from light to dark', () => {
      themeManager.currentTheme = 'light'

      const result = themeManager.toggleTheme()

      expect(result).toBe('dark')
      expect(themeManager.currentTheme).toBe('dark')
    })

    test('should toggle from dark to light', () => {
      themeManager.currentTheme = 'dark'

      const result = themeManager.toggleTheme()

      expect(result).toBe('light')
      expect(themeManager.currentTheme).toBe('light')
    })
  })

  describe('Button Update Functionality', () => {
    beforeEach(() => {
      themeManager = new ThemeManager()
    })

    test('should update button for dark theme', () => {
      themeManager.updateButton(mockButton, 'dark')

      expect(mockButton.textContent).toBe('Light')
      expect(mockButton.classList.contains('btn-outline-light')).toBe(true)
      expect(mockButton.classList.contains('btn-outline-dark')).toBe(false)
      expect(mockButton.getAttribute('aria-label')).toBe(
        'Switch to light theme'
      )
    })

    test('should update button for light theme', () => {
      themeManager.updateButton(mockButton, 'light')

      expect(mockButton.textContent).toBe('Dark')
      expect(mockButton.classList.contains('btn-outline-light')).toBe(false)
      expect(mockButton.classList.contains('btn-outline-dark')).toBe(true)
      expect(mockButton.getAttribute('aria-label')).toBe('Switch to dark theme')
    })
  })

  describe('Event Handling', () => {
    beforeEach(() => {
      themeManager = new ThemeManager()
    })

    test('should handle button click to toggle theme', () => {
      const initialTheme = themeManager.currentTheme

      TestUtils.simulateClick(mockButton)

      expect(themeManager.currentTheme).not.toBe(initialTheme)
    })

    test('should listen for system theme changes', () => {
      const mockMediaQuery = {
        matches: false,
        addEventListener: jest.fn(),
        removeEventListener: jest.fn()
      }

      window.matchMedia = jest.fn().mockReturnValue(mockMediaQuery)

      themeManager = new ThemeManager()

      expect(mockMediaQuery.addEventListener).toHaveBeenCalledWith(
        'change',
        expect.any(Function)
      )
    })

    test('should respond to system theme changes when no user preference saved', () => {
      localStorage.clear()

      const mockMediaQuery = {
        matches: false,
        addEventListener: jest.fn(),
        removeEventListener: jest.fn()
      }

      window.matchMedia = jest.fn().mockReturnValue(mockMediaQuery)
      themeManager = new ThemeManager()

      const changeHandler = mockMediaQuery.addEventListener.mock.calls[0][1]
      changeHandler({ matches: true })

      expect(document.documentElement.getAttribute('data-theme')).toBe('dark')
    })
  })

  describe('Accessibility Features', () => {
    beforeEach(() => {
      themeManager = new ThemeManager()
    })

    test('should maintain proper ARIA labels', () => {
      themeManager.updateButton(mockButton, 'light')
      expect(mockButton.getAttribute('aria-label')).toContain(
        'Switch to dark theme'
      )

      themeManager.updateButton(mockButton, 'dark')
      expect(mockButton.getAttribute('aria-label')).toContain(
        'Switch to light theme'
      )
    })

    test('should handle missing theme toggle button gracefully', () => {
      document.body.removeChild(mockButton)

      expect(() => {
        themeManager = new ThemeManager()
      }).not.toThrow()
    })
  })

  describe('Custom Event Integration', () => {
    beforeEach(() => {
      themeManager = new ThemeManager()
    })

    test('should allow other components to listen for theme changes', () => {
      const mockListener = jest.fn()
      window.addEventListener('themechange', mockListener)

      themeManager.setTheme('dark')

      expect(mockListener).toHaveBeenCalledWith(
        expect.objectContaining({
          detail: { theme: 'dark' }
        })
      )
    })
  })
})
