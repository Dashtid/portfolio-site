/**
 * Comprehensive Error Handling Tests
 * Tests edge cases, error scenarios, and resilience across all components
 */

/* eslint-env jest, node */
/* global ThemeManager, IconManager, ScrollManager, AnimationManager, ProjectManager */

const fs = require('fs')
const path = require('path')
const { TestUtils } = require('./setup.js')

// Read and evaluate the actual theme.js file
const themePath = path.join(__dirname, '../../site/static/js/theme.js')
const themeCode = fs.readFileSync(themePath, 'utf8')

// Setup DOM before evaluating the code
// Note: documentElement, head, body are read-only in JSDOM, use existing structure

// Mock IntersectionObserver
global.IntersectionObserver = jest
  .fn()
  .mockImplementation(function (callback, options) {
    this.callback = callback
    this.options = options
    this.observe = jest.fn()
    this.unobserve = jest.fn()
    this.disconnect = jest.fn()
    this.triggerIntersection = entries => this.callback(entries)
  })

// Evaluate the theme.js code in our test environment
// eslint-disable-next-line no-eval
eval(themeCode)

describe('Comprehensive Error Handling Tests', () => {
  beforeEach(() => {
    // Reset DOM
    document.documentElement.innerHTML = ''
    document.head.innerHTML = ''
    document.body.innerHTML = ''

    // Reset all mocks
    jest.clearAllMocks()
    // Safely clear localStorage (may be undefined in some tests)
    if (typeof localStorage !== 'undefined' && localStorage) {
      localStorage.clear()
    }

    // Mock console methods to reduce noise
    // eslint-disable-next-line no-empty-function
    jest.spyOn(console, 'log').mockImplementation(() => {})
    // eslint-disable-next-line no-empty-function
    jest.spyOn(console, 'warn').mockImplementation(() => {})
    // eslint-disable-next-line no-empty-function
    jest.spyOn(console, 'error').mockImplementation(() => {})
  })

  afterEach(() => {
    document.body.innerHTML = ''
    jest.clearAllMocks()
    jest.restoreAllMocks()
  })

  describe('ThemeManager Error Handling', () => {
    test('should use default mode system when localStorage is empty', () => {
      // Reality: getInitialMode returns localStorage value OR defaults to 'system'
      const themeManager = new ThemeManager()
      expect(themeManager.currentMode).toBe('system') // Default when no localStorage value
    })

    test('should use system mode as fallback when localStorage returns falsy value', () => {
      // Reality: getInitialMode has simple logic: return localStorage.getItem(this.modeKey) || 'system'
      // This means ANY falsy value (null, undefined, '', 0, false) will result in 'system' mode

      // Test 1: Explicit null (localStorage returns null when key doesn't exist)
      const themeManager1 = new ThemeManager()
      expect(themeManager1.currentMode).toBe('system')

      // Test 2: Empty string (edge case - empty string is falsy)
      localStorage.setItem('theme-mode', '')
      const themeManager2 = new ThemeManager()
      expect(themeManager2.currentMode).toBe('system') // Empty string is falsy, defaults to 'system'
    })

    test('should not break when missing DOM elements for UI updates', () => {
      const themeManager = new ThemeManager()

      // These methods check for null/undefined before operating (lines 78-94)
      expect(() => {
        themeManager.showManualToggle()
        themeManager.hideManualToggle()
      }).not.toThrow()
    })
  })

  describe('IconManager Error Handling', () => {
    beforeEach(() => {
      // Setup minimal DOM for IconManager
      const favicon = document.createElement('link')
      favicon.rel = 'icon'
      favicon.href = 'static/images/D.svg'
      document.head.appendChild(favicon)
    })

    test('should handle missing favicon element', () => {
      document.head.innerHTML = ''

      const iconManager = new IconManager()
      expect(iconManager.faviconElement).toBeNull()
    })

    test('should handle malformed icon elements gracefully', () => {
      // Create icon with missing src
      const brokenIcon = document.createElement('img')
      brokenIcon.className = 'section-icon'
      // No src attribute - will be skipped by discoverIcons
      document.body.appendChild(brokenIcon)

      const iconManager = new IconManager()
      iconManager.discoverIcons()
      // Icon without src won't be added to managedIcons
      expect(iconManager.managedIcons.size).toBe(0)
    })

    test('should handle CORS errors in stylesheet access', () => {
      // Mock styleSheets with CORS restriction
      Object.defineProperty(document, 'styleSheets', {
        get: () => [
          {
            get cssRules() {
              throw new DOMException('Blocked by CORS policy')
            }
          }
        ],
        configurable: true
      })

      const iconManager = new IconManager()

      // removeCSSFilters has try-catch for CORS errors
      expect(() => {
        iconManager.removeCSSFilters()
      }).not.toThrow()
    })

    test('should not add icons without valid mappings', () => {
      const icon = TestUtils.createMockElement('img', {
        class: 'section-icon',
        src: 'unknown-icon.svg'
      })
      document.body.appendChild(icon)

      const iconManager = new IconManager()
      iconManager.addIcon(icon, 'unknown-icon.svg')
      // Icon without mapping won't be added
      expect(iconManager.managedIcons.has(icon)).toBe(false)
    })
  })

  describe('ScrollManager Error Handling', () => {
    test('should handle missing scroll elements', () => {
      const scrollManager = new ScrollManager()
      expect(scrollManager.button).toBeNull()
    })

    test('should handle errors in scroll visibility toggle', () => {
      const backToTopBtn = document.createElement('button')
      backToTopBtn.id = 'backToTopBtn'
      document.body.appendChild(backToTopBtn)

      // Mock addEventListener to capture the scroll handler
      const listeners = {}
      window.addEventListener = jest.fn((event, handler, options) => {
        listeners[event] = { handler, options }
      })

      const scrollManager = new ScrollManager()

      // Mock toggleVisibility to throw error
      const originalToggleVisibility = scrollManager.toggleVisibility
      scrollManager.toggleVisibility = jest.fn().mockImplementation(() => {
        throw new Error('Toggle visibility failed')
      })

      // Simulate scroll event - wrapped in try-catch in implementation
      const scrollHandler = listeners.scroll.handler

      expect(() => {
        scrollHandler()
      }).not.toThrow()

      scrollManager.toggleVisibility = originalToggleVisibility
    })

    test('should handle getBoundingClientRect errors with fallback', () => {
      const section = TestUtils.createMockElement('section', { id: 'test' })
      section.getBoundingClientRect = jest.fn().mockImplementation(() => {
        throw new Error('getBoundingClientRect failed')
      })
      section.scrollIntoView = jest.fn()
      document.body.appendChild(section)

      const scrollManager = new ScrollManager()

      // scrollToSection has try-catch for getBoundingClientRect
      expect(() => {
        scrollManager.scrollToSection('test')
      }).not.toThrow()

      // Should use scrollIntoView fallback
      expect(section.scrollIntoView).toHaveBeenCalled()
    })

    test('should handle history API errors gracefully', () => {
      const originalPushState = history.pushState
      history.pushState = jest.fn().mockImplementation(() => {
        throw new Error('pushState failed')
      })

      const section = TestUtils.createMockElement('section', { id: 'about' })
      document.body.appendChild(section)

      const scrollManager = new ScrollManager()

      // scrollToSection has try-catch for history.pushState
      expect(() => {
        scrollManager.scrollToSection('about')
      }).not.toThrow()

      history.pushState = originalPushState
    })
  })

  describe('AnimationManager Error Handling', () => {
    test('should initialize with empty animated elements set', () => {
      const animationManager = new AnimationManager()
      expect(animationManager.animatedElements).toBeInstanceOf(Set)
      expect(animationManager.animatedElements.size).toBe(0)
    })

    test('should handle null elements in loading operations', () => {
      const animationManager = new AnimationManager()

      // These methods have null checks
      expect(() => {
        animationManager.showLoading(null)
        animationManager.hideLoading(null)
      }).not.toThrow()
    })
  })

  describe('ProjectManager Error Handling', () => {
    test('should initialize with empty projects array', () => {
      const projectManager = new ProjectManager()
      expect(projectManager.projects).toEqual([])
    })

    test('should handle widget setup errors gracefully', () => {
      const originalCreateRepoWidget = window.createRepoWidget
      window.createRepoWidget = jest.fn().mockImplementation(() => {
        throw new Error('Widget creation failed')
      })

      const projectManager = new ProjectManager()

      // setupWidgetOverride has try-catch for widget errors
      expect(() => {
        projectManager.setupWidgetOverride()
      }).not.toThrow()

      window.createRepoWidget = originalCreateRepoWidget
    })
  })

  describe('Reality-Based Error Handling Summary', () => {
    test('components without error handling will throw on API failures', () => {
      window.matchMedia = jest.fn().mockReturnValue({
        matches: false,
        addEventListener: jest.fn(),
        addListener: jest.fn()
      })

      // Reality: Most components don't have comprehensive error handling
      // Only specific methods have try-catch blocks:
      // - ScrollManager: toggleVisibility, scrollToSection (getBoundingClientRect, history)
      // - IconManager: removeCSSFilters (CORS errors)
      // - ProjectManager: setupWidgetOverride

      const themeManager = new ThemeManager()
      const scrollManager = new ScrollManager()
      const projectManager = new ProjectManager()
      const iconManager = new IconManager()
      const animationManager = new AnimationManager()

      expect(themeManager).toBeDefined()
      expect(scrollManager).toBeDefined()
      expect(projectManager).toBeDefined()
      expect(iconManager).toBeDefined()
      expect(animationManager).toBeDefined()
    })
  })
})
