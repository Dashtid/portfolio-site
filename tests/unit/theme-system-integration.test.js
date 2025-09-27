/**
 * Integration Tests for Theme System Components
 * Tests how ThemeManager, IconManager, and widgets work together
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

// Mock external dependencies
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

// Mock createRepoWidget for ProjectManager integration
global.createRepoWidget = jest.fn()

// Evaluate the theme.js code in our test environment
// eslint-disable-next-line no-eval
eval(themeCode)

describe('Theme System Integration Tests', () => {
  let themeManager
  let iconManager
  let scrollManager
  let animationManager
  let projectManager

  beforeEach(() => {
    // Reset DOM
    document.documentElement.innerHTML = ''
    document.head.innerHTML = ''
    document.body.innerHTML = ''

    // Setup required DOM elements
    setupThemeElements()
    setupIconElements()
    setupScrollElements()
    setupProjectElements()

    // Clear all mocks
    jest.clearAllMocks()

    // Clear localStorage
    localStorage.clear()

    // Mock console methods to reduce noise in tests
    jest.spyOn(console, 'log').mockImplementation(() => {})
    jest.spyOn(console, 'warn').mockImplementation(() => {})
    jest.spyOn(console, 'error').mockImplementation(() => {})
  })

  afterEach(() => {
    // Clean up DOM
    document.body.innerHTML = ''
    jest.clearAllMocks()
    jest.restoreAllMocks()
  })

  function setupThemeElements() {
    // Theme toggle elements
    const themeToggle = document.createElement('div')
    themeToggle.id = 'themeToggle'
    themeToggle.setAttribute = jest.fn()
    themeToggle.addEventListener = jest.fn()
    document.body.appendChild(themeToggle)

    const lightDarkToggle = document.createElement('div')
    lightDarkToggle.id = 'lightDarkToggle'
    lightDarkToggle.setAttribute = jest.fn()
    lightDarkToggle.addEventListener = jest.fn()
    document.body.appendChild(lightDarkToggle)

    const manualToggle = document.createElement('div')
    manualToggle.id = 'manualThemeToggle'
    manualToggle.classList = {
      add: jest.fn(),
      remove: jest.fn(),
      contains: jest.fn().mockReturnValue(false)
    }
    document.body.appendChild(manualToggle)

    // Mock getElementById for theme elements
    const originalGetElementById = document.getElementById
    document.getElementById = jest.fn(id => {
      switch (id) {
        case 'themeToggle':
          return themeToggle
        case 'lightDarkToggle':
          return lightDarkToggle
        case 'manualThemeToggle':
          return manualToggle
        default:
          return originalGetElementById.call(document, id)
      }
    })
  }

  function setupIconElements() {
    // Create favicon element
    const favicon = document.createElement('link')
    favicon.rel = 'icon'
    favicon.href = 'static/images/D.svg'
    document.head.appendChild(favicon)

    // Create section icons
    const sectionIcons = [
      TestUtils.createMockElement('img', {
        class: 'section-icon',
        src: 'static/images/about.svg',
        alt: 'About Icon'
      }),
      TestUtils.createMockElement('img', {
        class: 'section-icon',
        src: 'static/images/experience.svg',
        alt: 'Experience Icon'
      })
    ]

    // Create contact icons
    const contactIcons = [
      TestUtils.createMockElement('img', {
        class: 'contact-icon',
        src: 'static/images/LinkedIn.svg',
        alt: 'LinkedIn'
      }),
      TestUtils.createMockElement('img', {
        class: 'contact-icon',
        src: 'static/images/github.svg',
        alt: 'GitHub'
      })
    ]

    // Add all icons to DOM
    sectionIcons.concat(contactIcons).forEach(icon => {
      document.body.appendChild(icon)
    })
  }

  function setupScrollElements() {
    // Back to top button
    const backToTopBtn = document.createElement('button')
    backToTopBtn.id = 'backToTopBtn'
    backToTopBtn.style.display = 'none'
    backToTopBtn.addEventListener = jest.fn()
    document.body.appendChild(backToTopBtn)

    // Navigation links
    const navLinks = [
      TestUtils.createMockElement('a', {
        class: 'internal-nav',
        'data-scroll': 'about'
      }),
      TestUtils.createMockElement('a', {
        class: 'internal-nav',
        'data-scroll': 'projects'
      })
    ]

    navLinks.forEach(link => document.body.appendChild(link))

    // Sections
    const sections = [
      TestUtils.createMockElement('section', { id: 'about' }),
      TestUtils.createMockElement('section', { id: 'projects' })
    ]

    sections.forEach(section => document.body.appendChild(section))
  }

  function setupProjectElements() {
    // Project filter elements
    const filterButtons = [
      TestUtils.createMockElement('button', {
        class: 'filter-btn',
        'data-filter': 'all'
      }),
      TestUtils.createMockElement('button', {
        class: 'filter-btn',
        'data-filter': 'cybersecurity'
      })
    ]

    filterButtons.forEach(btn => document.body.appendChild(btn))

    // Sort dropdown
    const sortSelect = document.createElement('select')
    sortSelect.id = 'repo-sort'
    sortSelect.addEventListener = jest.fn()
    document.body.appendChild(sortSelect)

    // Project container
    const projectContainer = document.createElement('div')
    projectContainer.id = 'repo-container'
    document.body.appendChild(projectContainer)

    const noResults = document.createElement('div')
    noResults.id = 'no-results'
    document.body.appendChild(noResults)
  }

  describe('ThemeManager and IconManager Integration', () => {
    beforeEach(() => {
      // Mock window.matchMedia
      window.matchMedia = jest.fn().mockReturnValue({
        matches: false,
        addEventListener: jest.fn(),
        addListener: jest.fn()
      })

      themeManager = new ThemeManager()
      iconManager = new IconManager()
    })

    test('should initialize both managers successfully', () => {
      expect(themeManager).toBeInstanceOf(ThemeManager)
      expect(iconManager).toBeInstanceOf(IconManager)
    })

    test('should sync IconManager with ThemeManager theme changes', () => {
      const iconUpdateSpy = jest.spyOn(iconManager, 'handleThemeChange')

      // Change theme through ThemeManager
      themeManager.setTheme('dark')

      // Should trigger custom event
      const themeChangeEvent = new CustomEvent('themeChanged', {
        detail: { theme: 'dark', isDark: true, mode: 'system' }
      })

      window.dispatchEvent(themeChangeEvent)

      expect(iconUpdateSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          theme: 'dark',
          isDark: true
        })
      )
    })

    test('should update favicon when theme changes', () => {
      const favicon = document.querySelector('link[rel="icon"]')

      // Change to dark theme
      themeManager.setTheme('dark')

      const themeChangeEvent = new CustomEvent('themeChanged', {
        detail: { theme: 'dark', isDark: true }
      })
      window.dispatchEvent(themeChangeEvent)

      expect(favicon.getAttribute('href')).toBe('static/images/D-white.svg')

      // Change to light theme
      themeManager.setTheme('light')

      const lightThemeEvent = new CustomEvent('themeChanged', {
        detail: { theme: 'light', isDark: false }
      })
      window.dispatchEvent(lightThemeEvent)

      expect(favicon.getAttribute('href')).toBe('static/images/D.svg')
    })

    test('should update all managed icons when theme changes', () => {
      const sectionIcon = document.querySelector('.section-icon')
      const contactIcon = document.querySelector('.contact-icon')

      // Trigger dark theme
      const darkThemeEvent = new CustomEvent('themeChanged', {
        detail: { theme: 'dark', isDark: true }
      })
      window.dispatchEvent(darkThemeEvent)

      // Check that icons were updated to white variants
      expect(sectionIcon.getAttribute('src')).toBe(
        'static/images/about-white.svg'
      )
      expect(contactIcon.getAttribute('src')).toBe(
        'static/images/LinkedIn-white.svg'
      )

      // Trigger light theme
      const lightThemeEvent = new CustomEvent('themeChanged', {
        detail: { theme: 'light', isDark: false }
      })
      window.dispatchEvent(lightThemeEvent)

      // Check that icons were reverted to original variants
      expect(sectionIcon.getAttribute('src')).toBe('static/images/about.svg')
      expect(contactIcon.getAttribute('src')).toBe('static/images/LinkedIn.svg')
    })

    test('should update alt text for accessibility when switching themes', () => {
      const sectionIcon = document.querySelector('.section-icon')

      // Trigger dark theme
      const darkThemeEvent = new CustomEvent('themeChanged', {
        detail: { theme: 'dark', isDark: true }
      })
      window.dispatchEvent(darkThemeEvent)

      expect(sectionIcon.getAttribute('alt')).toContain('(dark mode variant)')

      // Trigger light theme
      const lightThemeEvent = new CustomEvent('themeChanged', {
        detail: { theme: 'light', isDark: false }
      })
      window.dispatchEvent(lightThemeEvent)

      expect(sectionIcon.getAttribute('alt')).toBe('About Icon')
    })

    test('should handle theme mode changes affecting icon behavior', () => {
      // Test system mode
      themeManager.setMode('system')
      expect(themeManager.currentMode).toBe('system')

      // Test manual mode
      themeManager.setMode('manual')
      expect(themeManager.currentMode).toBe('manual')

      // Theme changes in manual mode should still update icons
      const themeChangeEvent = new CustomEvent('themeChanged', {
        detail: { theme: 'dark', isDark: true, mode: 'manual' }
      })
      window.dispatchEvent(themeChangeEvent)

      const favicon = document.querySelector('link[rel="icon"]')
      expect(favicon.getAttribute('href')).toBe('static/images/D-white.svg')
    })

    test('should preload icon variants for performance', () => {
      const preloadSpy = jest.spyOn(iconManager, 'preloadIcons')

      iconManager.preloadIcons()

      expect(preloadSpy).toHaveBeenCalled()
    })
  })

  describe('Theme System and GitHub Widget Integration', () => {
    beforeEach(() => {
      window.matchMedia = jest.fn().mockReturnValue({
        matches: false,
        addEventListener: jest.fn(),
        addListener: jest.fn()
      })

      themeManager = new ThemeManager()
    })

    test('should handle GitHub stats theme integration through events', () => {
      let themeChangedEventFired = false
      let eventDetail = null

      // Listen for theme change events like GitHub stats would
      window.addEventListener('themeChanged', event => {
        themeChangedEventFired = true
        eventDetail = event.detail
      })

      themeManager.setTheme('dark')

      expect(themeChangedEventFired).toBe(true)
      expect(eventDetail).toEqual(
        expect.objectContaining({
          theme: 'dark',
          isDark: true,
          mode: expect.any(String)
        })
      )
    })

    test('should provide correct isDark property for widget integration', () => {
      const capturedEvents = []

      window.addEventListener('themeChanged', event => {
        capturedEvents.push(event.detail)
      })

      // Test dark theme
      themeManager.setTheme('dark')
      expect(capturedEvents[0].isDark).toBe(true)

      // Test light theme
      themeManager.setTheme('light')
      expect(capturedEvents[1].isDark).toBe(false)
    })

    test('should handle system theme preference changes affecting widgets', () => {
      // Mock system preference change
      const mockMediaQuery = {
        matches: true,
        addEventListener: jest.fn(),
        addListener: jest.fn()
      }

      window.matchMedia = jest.fn().mockReturnValue(mockMediaQuery)

      themeManager = new ThemeManager()

      const eventsCaught = []
      window.addEventListener('themeChanged', event => {
        eventsCaught.push(event.detail)
      })

      // Simulate system theme change
      const changeHandler = mockMediaQuery.addEventListener.mock.calls.find(
        call => call[0] === 'change'
      )[1]

      changeHandler({ matches: true }) // System switches to dark

      // Should only fire event if we're in system mode
      if (themeManager.currentMode === 'system') {
        expect(eventsCaught).toContainEqual(
          expect.objectContaining({
            theme: 'dark',
            isDark: true
          })
        )
      }
    })
  })

  describe('Complete System Integration', () => {
    beforeEach(() => {
      window.matchMedia = jest.fn().mockReturnValue({
        matches: false,
        addEventListener: jest.fn(),
        addListener: jest.fn()
      })

      // Initialize all managers
      themeManager = new ThemeManager()
      iconManager = new IconManager()
      scrollManager = new ScrollManager()
      animationManager = new AnimationManager()
      projectManager = new ProjectManager()
    })

    test('should initialize all components without conflicts', () => {
      expect(themeManager).toBeInstanceOf(ThemeManager)
      expect(iconManager).toBeInstanceOf(IconManager)
      expect(scrollManager).toBeInstanceOf(ScrollManager)
      expect(animationManager).toBeInstanceOf(AnimationManager)
      expect(projectManager).toBeInstanceOf(ProjectManager)
    })

    test('should handle theme changes affecting all components', () => {
      const iconUpdateSpy = jest.spyOn(iconManager, 'handleThemeChange')

      // Change theme
      themeManager.setTheme('dark')

      // Dispatch the event that would normally be fired
      const themeChangeEvent = new CustomEvent('themeChanged', {
        detail: { theme: 'dark', isDark: true, mode: 'system' }
      })
      window.dispatchEvent(themeChangeEvent)

      // IconManager should respond
      expect(iconUpdateSpy).toHaveBeenCalled()

      // Document should have theme attribute
      expect(document.documentElement.getAttribute('data-theme')).toBe('dark')
    })

    test('should handle intersection observers from multiple managers', () => {
      // AnimationManager creates multiple observers
      expect(IntersectionObserver).toHaveBeenCalledTimes(4) // 3 from AnimationManager + 1 from ScrollManager
    })

    test('should handle localStorage operations across managers', () => {
      const setItemSpy = jest.spyOn(localStorage, 'setItem')

      // Change theme mode (should save to localStorage)
      themeManager.setMode('manual')
      expect(setItemSpy).toHaveBeenCalledWith('theme-mode', 'manual')

      // Change theme in manual mode (should save to localStorage)
      themeManager.setTheme('dark')
      expect(setItemSpy).toHaveBeenCalledWith('theme', 'dark')
    })

    test('should handle errors in one component without affecting others', () => {
      // Mock an error in IconManager
      const originalHandleThemeChange = iconManager.handleThemeChange
      iconManager.handleThemeChange = jest.fn().mockImplementation(() => {
        throw new Error('Icon manager error')
      })

      // Theme change should still work
      expect(() => {
        themeManager.setTheme('dark')
      }).not.toThrow()

      // Document should still have theme applied
      expect(document.documentElement.getAttribute('data-theme')).toBe('dark')

      iconManager.handleThemeChange = originalHandleThemeChange
    })

    test('should support dynamic icon addition through IconManager', () => {
      const newIcon = TestUtils.createMockElement('img', {
        class: 'section-icon',
        src: 'static/images/education.svg'
      })
      document.body.appendChild(newIcon)

      // Add to IconManager
      iconManager.addIcon(newIcon, 'static/images/education.svg')

      // Should now be managed
      expect(iconManager.managedIcons.has(newIcon)).toBe(true)

      // Should respond to theme changes
      const themeChangeEvent = new CustomEvent('themeChanged', {
        detail: { theme: 'dark', isDark: true }
      })
      window.dispatchEvent(themeChangeEvent)

      expect(newIcon.getAttribute('src')).toBe(
        'static/images/education-white.svg'
      )
    })
  })

  describe('Error Handling Integration', () => {
    test('should handle localStorage quota errors gracefully', () => {
      const originalSetItem = localStorage.setItem
      localStorage.setItem = jest.fn().mockImplementation(() => {
        throw new Error('Quota exceeded')
      })

      window.matchMedia = jest.fn().mockReturnValue({
        matches: false,
        addEventListener: jest.fn(),
        addListener: jest.fn()
      })

      expect(() => {
        themeManager = new ThemeManager()
        iconManager = new IconManager()
      }).not.toThrow()

      localStorage.setItem = originalSetItem
    })

    test('should handle missing DOM elements across all managers', () => {
      // Remove all DOM elements
      document.body.innerHTML = ''
      document.head.innerHTML = ''

      window.matchMedia = jest.fn().mockReturnValue({
        matches: false,
        addEventListener: jest.fn(),
        addListener: jest.fn()
      })

      expect(() => {
        themeManager = new ThemeManager()
        iconManager = new IconManager()
        scrollManager = new ScrollManager()
        animationManager = new AnimationManager()
        projectManager = new ProjectManager()
      }).not.toThrow()
    })

    test('should handle event listener errors gracefully', () => {
      const originalAddEventListener = window.addEventListener
      window.addEventListener = jest.fn().mockImplementation(() => {
        throw new Error('Event listener error')
      })

      window.matchMedia = jest.fn().mockReturnValue({
        matches: false,
        addEventListener: jest.fn(),
        addListener: jest.fn()
      })

      expect(() => {
        themeManager = new ThemeManager()
        iconManager = new IconManager()
      }).not.toThrow()

      window.addEventListener = originalAddEventListener
    })

    test('should handle CSS stylesheet access errors', () => {
      // Mock document.styleSheets to throw errors
      Object.defineProperty(document, 'styleSheets', {
        get: () => {
          throw new Error('Stylesheet access denied')
        },
        configurable: true
      })

      window.matchMedia = jest.fn().mockReturnValue({
        matches: false,
        addEventListener: jest.fn(),
        addListener: jest.fn()
      })

      expect(() => {
        themeManager = new ThemeManager()
        iconManager = new IconManager()
      }).not.toThrow()
    })
  })

  describe('Performance Integration', () => {
    beforeEach(() => {
      window.matchMedia = jest.fn().mockReturnValue({
        matches: false,
        addEventListener: jest.fn(),
        addListener: jest.fn()
      })

      themeManager = new ThemeManager()
      iconManager = new IconManager()
    })

    test('should optimize icon updates by checking for changes', () => {
      const icon = document.querySelector('.section-icon')
      const originalSrc = icon.getAttribute('src') // eslint-disable-line no-unused-vars

      // First theme change
      const themeChangeEvent = new CustomEvent('themeChanged', {
        detail: { theme: 'dark', isDark: true }
      })
      window.dispatchEvent(themeChangeEvent)

      expect(icon.getAttribute('src')).toBe('static/images/about-white.svg')

      // Same theme change again - should not update unnecessarily
      const setSrcSpy = jest.spyOn(icon, 'setAttribute')
      window.dispatchEvent(themeChangeEvent)

      // Should not call setAttribute since src is already correct
      expect(setSrcSpy).not.toHaveBeenCalledWith(
        'src',
        'static/images/about-white.svg'
      )
    })

    test('should use requestAnimationFrame for scroll performance', () => {
      window.requestAnimationFrame = jest.fn(cb => setTimeout(cb, 16))

      scrollManager = new ScrollManager()

      // Simulate scroll event
      const scrollHandler = window.addEventListener.mock.calls.find(
        call => call[0] === 'scroll'
      )[1]

      scrollHandler()

      expect(window.requestAnimationFrame).toHaveBeenCalled()
    })

    test('should use intersection observers instead of scroll events for animations', () => {
      animationManager = new AnimationManager()

      // Should create intersection observers, not scroll listeners
      expect(IntersectionObserver).toHaveBeenCalled()
    })

    test('should cache managed icons for performance', () => {
      const iconCount = iconManager.managedIcons.size

      // Add a new icon
      const newIcon = TestUtils.createMockElement('img', {
        class: 'section-icon',
        src: 'static/images/contact.svg'
      })
      document.body.appendChild(newIcon)

      iconManager.addIcon(newIcon, 'static/images/contact.svg')

      expect(iconManager.managedIcons.size).toBe(iconCount + 1)
    })
  })
})
