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
    localStorage.clear()

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
    test('should handle localStorage access errors during initialization', () => {
      // Mock localStorage to throw errors
      const originalGetItem = localStorage.getItem
      localStorage.getItem = jest.fn().mockImplementation(() => {
        throw new Error('localStorage access denied')
      })

      window.matchMedia = jest.fn().mockReturnValue({
        matches: false,
        addEventListener: jest.fn(),
        addListener: jest.fn()
      })

      expect(() => {
        const themeManager = new ThemeManager()
        expect(themeManager.currentMode).toBe('system') // Should fall back to default
      }).not.toThrow()

      localStorage.getItem = originalGetItem
    })

    test('should handle localStorage write errors gracefully', () => {
      const originalSetItem = localStorage.setItem
      localStorage.setItem = jest.fn().mockImplementation(() => {
        throw new Error('Storage quota exceeded')
      })

      window.matchMedia = jest.fn().mockReturnValue({
        matches: false,
        addEventListener: jest.fn(),
        addListener: jest.fn()
      })

      const themeManager = new ThemeManager()

      expect(() => {
        themeManager.setTheme('dark')
        themeManager.setMode('manual')
      }).not.toThrow()

      localStorage.setItem = originalSetItem
    })

    test('should handle missing matchMedia API', () => {
      delete window.matchMedia

      expect(() => {
        const themeManager = new ThemeManager()
        expect(themeManager.currentTheme).toBeDefined()
      }).not.toThrow()

      // Restore matchMedia
      window.matchMedia = jest.fn().mockReturnValue({
        matches: false,
        addEventListener: jest.fn(),
        addListener: jest.fn()
      })
    })

    test('should handle errors in event dispatching', () => {
      const originalDispatchEvent = window.dispatchEvent
      window.dispatchEvent = jest.fn().mockImplementation(() => {
        throw new Error('Event dispatch failed')
      })

      window.matchMedia = jest.fn().mockReturnValue({
        matches: false,
        addEventListener: jest.fn(),
        addListener: jest.fn()
      })

      const themeManager = new ThemeManager()

      expect(() => {
        themeManager.setTheme('dark')
      }).not.toThrow()

      window.dispatchEvent = originalDispatchEvent
    })

    test('should handle malformed theme values', () => {
      localStorage.setItem('theme', 'invalid-theme')
      localStorage.setItem('theme-mode', 'invalid-mode')

      window.matchMedia = jest.fn().mockReturnValue({
        matches: false,
        addEventListener: jest.fn(),
        addListener: jest.fn()
      })

      expect(() => {
        const themeManager = new ThemeManager()
        expect(['light', 'dark']).toContain(themeManager.currentTheme)
        expect(['system', 'manual']).toContain(themeManager.currentMode)
      }).not.toThrow()
    })

    test('should handle DOM manipulation errors', () => {
      const originalSetAttribute = document.documentElement.setAttribute
      document.documentElement.setAttribute = jest
        .fn()
        .mockImplementation(() => {
          throw new Error('setAttribute failed')
        })

      window.matchMedia = jest.fn().mockReturnValue({
        matches: false,
        addEventListener: jest.fn(),
        addListener: jest.fn()
      })

      const themeManager = new ThemeManager()

      expect(() => {
        themeManager.setTheme('dark')
      }).not.toThrow()

      document.documentElement.setAttribute = originalSetAttribute
    })

    test('should handle missing DOM elements for UI updates', () => {
      window.matchMedia = jest.fn().mockReturnValue({
        matches: false,
        addEventListener: jest.fn(),
        addListener: jest.fn()
      })

      const themeManager = new ThemeManager()

      // Test with null elements
      expect(() => {
        themeManager.updateSlider(null)
        themeManager.updateLightDarkToggle(null)
        themeManager.showManualToggle()
        themeManager.hideManualToggle()
      }).not.toThrow()
    })

    test('should handle corrupted localStorage data', () => {
      // Simulate corrupted data
      const originalGetItem = localStorage.getItem
      localStorage.getItem = jest.fn().mockImplementation(key => {
        if (key === 'theme') return '{"corrupted": json}'
        if (key === 'theme-mode') return 'null'
        return null
      })

      window.matchMedia = jest.fn().mockReturnValue({
        matches: false,
        addEventListener: jest.fn(),
        addListener: jest.fn()
      })

      expect(() => {
        const themeManager = new ThemeManager()
        expect(themeManager.currentMode).toBe('system')
      }).not.toThrow()

      localStorage.getItem = originalGetItem
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

      expect(() => {
        const iconManager = new IconManager() // eslint-disable-line no-unused-vars
        expect(iconManager.faviconElement).toBeNull()
      }).not.toThrow()
    })

    test('should handle errors in icon discovery', () => {
      const originalQuerySelectorAll = document.querySelectorAll
      document.querySelectorAll = jest.fn().mockImplementation(() => {
        throw new Error('querySelector failed')
      })

      expect(() => {
        const iconManager = new IconManager() // eslint-disable-line no-unused-vars
        expect(iconManager.managedIcons.size).toBe(0)
      }).not.toThrow()

      document.querySelectorAll = originalQuerySelectorAll
    })

    test('should handle malformed icon elements', () => {
      // Create icon with missing src
      const brokenIcon = document.createElement('img')
      brokenIcon.className = 'section-icon'
      // No src attribute
      document.body.appendChild(brokenIcon)

      expect(() => {
        const iconManager = new IconManager() // eslint-disable-line no-unused-vars
        iconManager.discoverIcons()
      }).not.toThrow()
    })

    test('should handle errors in stylesheet manipulation', () => {
      // Mock styleSheets to throw errors
      Object.defineProperty(document, 'styleSheets', {
        get: () => {
          throw new Error('Stylesheet access denied')
        },
        configurable: true
      })

      const iconManager = new IconManager()

      expect(() => {
        iconManager.removeCSSFilters()
      }).not.toThrow()
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

      expect(() => {
        iconManager.removeCSSFilters()
      }).not.toThrow()
    })

    test('should handle theme change event errors', () => {
      const iconManager = new IconManager()

      // Mock updateIcons to throw error
      const originalUpdateIcons = iconManager.updateIcons
      iconManager.updateIcons = jest.fn().mockImplementation(() => {
        throw new Error('Icon update failed')
      })

      expect(() => {
        iconManager.handleThemeChange({ theme: 'dark', isDark: true })
      }).not.toThrow()

      iconManager.updateIcons = originalUpdateIcons
    })

    test('should handle errors in icon attribute manipulation', () => {
      const brokenIcon = {
        getAttribute: jest.fn().mockImplementation(() => {
          throw new Error('getAttribute failed')
        }),
        setAttribute: jest.fn().mockImplementation(() => {
          throw new Error('setAttribute failed')
        })
      }

      const iconManager = new IconManager()
      iconManager.managedIcons.set(brokenIcon, {
        originalSrc: 'test.svg',
        whiteSrc: 'test-white.svg',
        element: brokenIcon
      })

      expect(() => {
        iconManager.updateIcons(true)
      }).not.toThrow()
    })

    test('should handle missing icon mappings', () => {
      const icon = TestUtils.createMockElement('img', {
        class: 'section-icon',
        src: 'unknown-icon.svg'
      })
      document.body.appendChild(icon)

      expect(() => {
        const iconManager = new IconManager() // eslint-disable-line no-unused-vars
        iconManager.addIcon(icon, 'unknown-icon.svg')
        expect(iconManager.managedIcons.has(icon)).toBe(false)
      }).not.toThrow()
    })

    test('should handle errors in image preloading', () => {
      // Mock Image constructor to throw errors
      const originalImage = window.Image
      window.Image = jest.fn().mockImplementation(() => {
        throw new Error('Image creation failed')
      })

      const iconManager = new IconManager()

      expect(() => {
        iconManager.preloadIcons()
      }).not.toThrow()

      window.Image = originalImage
    })
  })

  describe('ScrollManager Error Handling', () => {
    test('should handle missing scroll elements', () => {
      expect(() => {
        const scrollManager = new ScrollManager()
        expect(scrollManager.button).toBeNull()
      }).not.toThrow()
    })

    test('should handle errors in scroll event handlers', () => {
      const backToTopBtn = document.createElement('button')
      backToTopBtn.id = 'backToTopBtn'
      backToTopBtn.addEventListener = jest.fn()
      document.body.appendChild(backToTopBtn)

      const scrollManager = new ScrollManager()

      // Mock toggleVisibility to throw error
      const originalToggleVisibility = scrollManager.toggleVisibility
      scrollManager.toggleVisibility = jest.fn().mockImplementation(() => {
        throw new Error('Toggle visibility failed')
      })

      // Simulate scroll event
      const scrollHandler = window.addEventListener.mock.calls.find(
        call => call[0] === 'scroll'
      )[1]

      expect(() => {
        scrollHandler()
      }).not.toThrow()

      scrollManager.toggleVisibility = originalToggleVisibility
    })

    test('should handle errors in scrollTo API', () => {
      const originalScrollTo = window.scrollTo
      window.scrollTo = jest.fn().mockImplementation(() => {
        throw new Error('scrollTo failed')
      })

      const scrollManager = new ScrollManager()

      expect(() => {
        scrollManager.scrollToTop()
        scrollManager.scrollToSection('about')
      }).not.toThrow()

      window.scrollTo = originalScrollTo
    })

    test('should handle errors in history API', () => {
      const originalPushState = history.pushState
      history.pushState = jest.fn().mockImplementation(() => {
        throw new Error('pushState failed')
      })

      const scrollManager = new ScrollManager()

      expect(() => {
        scrollManager.scrollToSection('about')
      }).not.toThrow()

      history.pushState = originalPushState
    })

    test('should handle getBoundingClientRect errors', () => {
      const section = TestUtils.createMockElement('section', { id: 'test' })
      section.getBoundingClientRect = jest.fn().mockImplementation(() => {
        throw new Error('getBoundingClientRect failed')
      })
      document.body.appendChild(section)

      const scrollManager = new ScrollManager()

      expect(() => {
        scrollManager.scrollToSection('test')
      }).not.toThrow()
    })

    test('should handle intersection observer errors', () => {
      const brokenObserver = jest.fn().mockImplementation(function (callback) {
        this.callback = callback
        this.observe = jest.fn().mockImplementation(() => {
          throw new Error('Observe failed')
        })
        this.disconnect = jest.fn()
      })

      const originalIntersectionObserver = global.IntersectionObserver
      global.IntersectionObserver = brokenObserver

      expect(() => {
        const scrollManager = new ScrollManager()
        expect(scrollManager).toBeDefined()
      }).not.toThrow()

      global.IntersectionObserver = originalIntersectionObserver
    })

    test('should handle focus errors', () => {
      const heading = document.createElement('h1')
      heading.focus = jest.fn().mockImplementation(() => {
        throw new Error('Focus failed')
      })
      document.body.appendChild(heading)

      const scrollManager = new ScrollManager()

      expect(() => {
        scrollManager.scrollToTop()
      }).not.toThrow()
    })

    test('should handle malformed navigation links', () => {
      const brokenLink = document.createElement('a')
      brokenLink.className = 'internal-nav'
      // Missing data-scroll attribute
      brokenLink.addEventListener = jest.fn()
      document.body.appendChild(brokenLink)

      expect(() => {
        const scrollManager = new ScrollManager()
        expect(scrollManager).toBeDefined()
      }).not.toThrow()
    })
  })

  describe('AnimationManager Error Handling', () => {
    test('should handle missing animation elements', () => {
      expect(() => {
        const animationManager = new AnimationManager()
        expect(animationManager.animatedElements).toBeInstanceOf(Set)
      }).not.toThrow()
    })

    test('should handle errors in intersection observer callbacks', () => {
      const animationManager = new AnimationManager() // eslint-disable-line no-unused-vars

      // Create broken entries
      const brokenEntries = [
        { isIntersecting: true, target: null },
        { isIntersecting: true, target: undefined },
        { target: document.createElement('div') } // Missing isIntersecting
      ]

      // Get the first observer (sections)
      const sectionObserver = IntersectionObserver.mock.instances[0]

      expect(() => {
        sectionObserver.triggerIntersection(brokenEntries)
      }).not.toThrow()
    })

    test('should handle errors in style manipulation', () => {
      const brokenElement = {
        style: null,
        getAttribute: jest.fn().mockReturnValue('85'),
        classList: {
          add: jest.fn().mockImplementation(() => {
            throw new Error('classList.add failed')
          })
        }
      }

      const progressBarObserver = IntersectionObserver.mock.instances[1]

      expect(() => {
        progressBarObserver.triggerIntersection([
          {
            isIntersecting: true,
            target: brokenElement
          }
        ])
      }).not.toThrow()
    })

    test('should handle setTimeout errors', () => {
      const originalSetTimeout = window.setTimeout
      window.setTimeout = jest.fn().mockImplementation(() => {
        throw new Error('setTimeout failed')
      })

      const animationManager = new AnimationManager()

      expect(() => {
        animationManager.revealContent(document.createElement('div'), 'content')
      }).not.toThrow()

      window.setTimeout = originalSetTimeout
    })

    test('should handle skills section animation errors', () => {
      const skillsSection = TestUtils.createMockElement('section', {
        id: 'skills'
      })
      document.body.appendChild(skillsSection)

      const brokenProgressBar = {
        style: {
          get width() {
            throw new Error('Style access failed')
          },
          set width(value) {
            throw new Error('Style write failed')
          }
        }
      }

      // Mock querySelectorAll to return broken element
      const originalQuerySelectorAll = document.querySelectorAll
      document.querySelectorAll = jest.fn().mockImplementation(selector => {
        if (selector.includes('#skills .progress-bar')) {
          return [brokenProgressBar]
        }
        return originalQuerySelectorAll.call(document, selector)
      })

      const animationManager = new AnimationManager()

      expect(() => {
        animationManager.animateSkillsBars()
      }).not.toThrow()

      document.querySelectorAll = originalQuerySelectorAll
    })

    test('should handle DOM query errors', () => {
      const originalQuerySelectorAll = document.querySelectorAll
      document.querySelectorAll = jest.fn().mockImplementation(() => {
        throw new Error('querySelectorAll failed')
      })

      expect(() => {
        const animationManager = new AnimationManager()
        expect(animationManager).toBeDefined()
      }).not.toThrow()

      document.querySelectorAll = originalQuerySelectorAll
    })

    test('should handle loading/hiding operations on null elements', () => {
      const animationManager = new AnimationManager()

      expect(() => {
        animationManager.showLoading(null)
        animationManager.hideLoading(null)
        animationManager.revealContent(null, 'content')
      }).not.toThrow()
    })

    test('should handle errors in element content manipulation', () => {
      const brokenElement = {
        get innerHTML() {
          throw new Error('innerHTML read failed')
        },
        set innerHTML(value) {
          throw new Error('innerHTML write failed')
        },
        querySelector: jest.fn().mockImplementation(() => {
          throw new Error('querySelector failed')
        })
      }

      const animationManager = new AnimationManager()

      expect(() => {
        animationManager.showLoading(brokenElement)
        animationManager.hideLoading(brokenElement)
        animationManager.revealContent(brokenElement, 'content')
      }).not.toThrow()
    })
  })

  describe('ProjectManager Error Handling', () => {
    test('should handle missing project elements', () => {
      expect(() => {
        const projectManager = new ProjectManager()
        expect(projectManager.projects).toEqual([])
      }).not.toThrow()
    })

    test('should handle errors in event listener setup', () => {
      const brokenButton = {
        addEventListener: jest.fn().mockImplementation(() => {
          throw new Error('addEventListener failed')
        })
      }

      const originalQuerySelectorAll = document.querySelectorAll
      document.querySelectorAll = jest.fn().mockImplementation(selector => {
        if (selector === '.filter-btn') {
          return [brokenButton]
        }
        return []
      })

      expect(() => {
        const projectManager = new ProjectManager()
        expect(projectManager).toBeDefined()
      }).not.toThrow()

      document.querySelectorAll = originalQuerySelectorAll
    })

    test('should handle malformed project data', () => {
      const projectManager = new ProjectManager()
      projectManager.projects = [
        null,
        undefined,
        {},
        { name: null },
        { description: undefined },
        { name: 'test', stargazers_count: 'invalid' }
      ]

      expect(() => {
        projectManager.filterProjects()
        projectManager.sortProjects(projectManager.projects)
        projectManager.renderProjects(projectManager.projects)
      }).not.toThrow()
    })

    test('should handle DOM manipulation errors during rendering', () => {
      const brokenContainer = {
        style: {},
        get innerHTML() {
          throw new Error('innerHTML read failed')
        },
        set innerHTML(value) {
          throw new Error('innerHTML write failed')
        },
        querySelector: jest.fn().mockReturnValue({
          appendChild: jest.fn().mockImplementation(() => {
            throw new Error('appendChild failed')
          })
        })
      }

      document.getElementById = jest.fn().mockImplementation(id => {
        if (id === 'repo-container') return brokenContainer
        if (id === 'no-results') return { style: {} }
        return null
      })

      const projectManager = new ProjectManager()

      expect(() => {
        projectManager.renderProjects([{ name: 'test', description: 'test' }])
      }).not.toThrow()
    })

    test('should handle errors in project categorization', () => {
      const projectManager = new ProjectManager()

      // Test with malformed projects
      const brokenProjects = [
        { name: null, description: null },
        {
          get name() {
            throw new Error('name access failed')
          }
        },
        {
          name: 'test',
          get description() {
            throw new Error('description access failed')
          }
        }
      ]

      expect(() => {
        brokenProjects.forEach(project => {
          projectManager.categorizeProject(project)
        })
      }).not.toThrow()
    })

    test('should handle widget setup errors', () => {
      const originalCreateRepoWidget = window.createRepoWidget
      window.createRepoWidget = jest.fn().mockImplementation(() => {
        throw new Error('Widget creation failed')
      })

      const projectManager = new ProjectManager()

      expect(() => {
        projectManager.setupWidgetOverride()
      }).not.toThrow()

      window.createRepoWidget = originalCreateRepoWidget
    })
  })

  describe('Cross-Component Error Resilience', () => {
    test('should handle multiple component failures without breaking others', () => {
      // Mock various APIs to fail
      const originalQuerySelectorAll = document.querySelectorAll
      const originalGetElementById = document.getElementById
      const originalSetTimeout = window.setTimeout

      document.querySelectorAll = jest.fn().mockImplementation(() => {
        throw new Error('querySelectorAll failed')
      })

      document.getElementById = jest.fn().mockImplementation(() => {
        throw new Error('getElementById failed')
      })

      window.setTimeout = jest.fn().mockImplementation(() => {
        throw new Error('setTimeout failed')
      })

      window.matchMedia = jest.fn().mockReturnValue({
        matches: false,
        addEventListener: jest.fn(),
        addListener: jest.fn()
      })

      // All components should still initialize
      expect(() => {
        const themeManager = new ThemeManager()
        const iconManager = new IconManager() // eslint-disable-line no-unused-vars
        const scrollManager = new ScrollManager()
        const animationManager = new AnimationManager()
        const projectManager = new ProjectManager()

        expect(themeManager).toBeDefined()
        expect(iconManager).toBeDefined()
        expect(scrollManager).toBeDefined()
        expect(animationManager).toBeDefined()
        expect(projectManager).toBeDefined()
      }).not.toThrow()

      // Restore APIs
      document.querySelectorAll = originalQuerySelectorAll
      document.getElementById = originalGetElementById
      window.setTimeout = originalSetTimeout
    })

    test('should handle event system failures gracefully', () => {
      const originalAddEventListener = window.addEventListener
      const originalDispatchEvent = window.dispatchEvent

      window.addEventListener = jest.fn().mockImplementation(() => {
        throw new Error('addEventListener failed')
      })

      window.dispatchEvent = jest.fn().mockImplementation(() => {
        throw new Error('dispatchEvent failed')
      })

      window.matchMedia = jest.fn().mockReturnValue({
        matches: false,
        addEventListener: jest.fn(),
        addListener: jest.fn()
      })

      expect(() => {
        const themeManager = new ThemeManager()
        const iconManager = new IconManager() // eslint-disable-line no-unused-vars

        themeManager.setTheme('dark')
        // Should not break even if events fail
      }).not.toThrow()

      window.addEventListener = originalAddEventListener
      window.dispatchEvent = originalDispatchEvent
    })

    test.skip('should handle memory and resource constraints', () => {
      // Skipped: Mocking window.Set breaks Jest's internal dependencies
      // This scenario (Set constructor failing) is extremely rare and unrealistic
      // Real memory constraints would manifest differently in production
    })

    test('should handle browser compatibility issues', () => {
      // Remove modern APIs
      const originalRequestAnimationFrame = window.requestAnimationFrame
      const originalIntersectionObserver = global.IntersectionObserver
      const originalMatchMedia = window.matchMedia

      delete window.requestAnimationFrame
      delete global.IntersectionObserver
      delete window.matchMedia

      expect(() => {
        const themeManager = new ThemeManager()
        const scrollManager = new ScrollManager()
        const animationManager = new AnimationManager()

        expect(themeManager).toBeDefined()
        expect(scrollManager).toBeDefined()
        expect(animationManager).toBeDefined()
      }).not.toThrow()

      // Restore APIs
      window.requestAnimationFrame = originalRequestAnimationFrame
      global.IntersectionObserver = originalIntersectionObserver
      window.matchMedia = originalMatchMedia
    })
  })

  describe('Recovery and Fallback Mechanisms', () => {
    test('should provide fallback behavior when localStorage is unavailable', () => {
      const originalLocalStorage = window.localStorage
      delete window.localStorage

      window.matchMedia = jest.fn().mockReturnValue({
        matches: false,
        addEventListener: jest.fn(),
        addListener: jest.fn()
      })

      expect(() => {
        const themeManager = new ThemeManager()
        expect(themeManager.currentMode).toBe('system')
        expect(['light', 'dark']).toContain(themeManager.currentTheme)
      }).not.toThrow()

      window.localStorage = originalLocalStorage
    })

    test('should gracefully degrade when intersection observer is unavailable', () => {
      const originalIntersectionObserver = global.IntersectionObserver
      delete global.IntersectionObserver

      expect(() => {
        const scrollManager = new ScrollManager()
        const animationManager = new AnimationManager()

        expect(scrollManager).toBeDefined()
        expect(animationManager).toBeDefined()
      }).not.toThrow()

      global.IntersectionObserver = originalIntersectionObserver
    })

    test('should handle CSS not loading or being blocked', () => {
      // Mock getComputedStyle to return empty values
      const originalGetComputedStyle = window.getComputedStyle
      window.getComputedStyle = jest.fn().mockReturnValue({
        getPropertyValue: jest.fn().mockReturnValue(''),
        display: 'none'
      })

      window.matchMedia = jest.fn().mockReturnValue({
        matches: false,
        addEventListener: jest.fn(),
        addListener: jest.fn()
      })

      expect(() => {
        const themeManager = new ThemeManager()
        const iconManager = new IconManager() // eslint-disable-line no-unused-vars

        themeManager.setTheme('dark')
        // Should still work even without CSS
      }).not.toThrow()

      window.getComputedStyle = originalGetComputedStyle
    })

    test('should recover from temporary network failures', () => {
      // Simulate network-related errors
      const networkError = new Error('Network request failed')
      networkError.name = 'NetworkError'

      const originalFetch = global.fetch
      global.fetch = jest.fn().mockRejectedValue(networkError)

      // Components should not break due to network failures
      expect(() => {
        const projectManager = new ProjectManager()
        expect(projectManager).toBeDefined()
      }).not.toThrow()

      global.fetch = originalFetch
    })
  })
})
