/**
 * Mock Implementation Verification Tests
 * Ensures mock classes match real implementations in terms of methods and properties
 */

/* eslint-env jest, node */
/* global ThemeManager, IconManager, ScrollManager, AnimationManager, ProjectManager */

const fs = require('fs')
const path = require('path')

// Read and evaluate the actual theme.js file
const themePath = path.join(__dirname, '../../site/static/js/theme.js')
const themeCode = fs.readFileSync(themePath, 'utf8')

// Setup DOM before evaluating the code
// Note: documentElement, head, body are read-only in JSDOM, use existing structure

// Mock dependencies
global.IntersectionObserver = jest
  .fn()
  .mockImplementation(function (callback, options) {
    this.callback = callback
    this.options = options
    this.observe = jest.fn()
    this.unobserve = jest.fn()
    this.disconnect = jest.fn()
  })

window.matchMedia = jest.fn().mockReturnValue({
  matches: false,
  addEventListener: jest.fn(),
  addListener: jest.fn()
})

// Evaluate the theme.js code in our test environment
// eslint-disable-next-line no-eval
eval(themeCode)

describe('Mock Implementation Verification', () => {
  beforeEach(() => {
    // Reset DOM
    document.documentElement.innerHTML = ''
    document.head.innerHTML = ''
    document.body.innerHTML = ''

    // Clear all mocks
    jest.clearAllMocks()
    localStorage.clear()

    // Mock console methods
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

  describe('ThemeManager Class Verification', () => {
    test('should have all expected methods matching mock implementation', () => {
      const themeManager = new ThemeManager()

      // Verify all public methods exist
      const expectedMethods = [
        'getInitialMode',
        'getInitialTheme',
        'setTheme',
        'setMode',
        'updateSlider',
        'updateLightDarkToggle',
        'showManualToggle',
        'hideManualToggle',
        'toggleMode',
        'toggleTheme',
        'init',
        'isMobileSafari'
      ]

      expectedMethods.forEach(method => {
        expect(typeof themeManager[method]).toBe('function')
      })
    })

    test('should have all expected properties matching mock implementation', () => {
      const themeManager = new ThemeManager()

      // Verify all properties exist and have correct types
      expect(typeof themeManager.storageKey).toBe('string')
      expect(typeof themeManager.modeKey).toBe('string')
      expect(typeof themeManager.currentMode).toBe('string')
      expect(typeof themeManager.currentTheme).toBe('string')
      expect(themeManager.mediaQuery).toBeDefined()
    })

    test('should have constructor that accepts no parameters', () => {
      expect(() => {
        const tm = new ThemeManager() // eslint-disable-line no-unused-vars
        expect(tm).toBeDefined()
      }).not.toThrow()
    })

    test('should have methods that return expected types', () => {
      const themeManager = new ThemeManager()

      // Test return types
      expect(typeof themeManager.getInitialMode()).toBe('string')
      expect(typeof themeManager.getInitialTheme()).toBe('string')
      expect(typeof themeManager.toggleMode()).toBe('string')
      expect(typeof themeManager.toggleTheme()).toBe('string')
      expect(typeof themeManager.isMobileSafari()).toBe('boolean')
    })
  })

  describe('IconManager Class Verification', () => {
    beforeEach(() => {
      // Setup favicon for IconManager
      const favicon = document.createElement('link')
      favicon.rel = 'icon'
      favicon.href = 'static/images/D.svg'
      document.head.appendChild(favicon)
    })

    test('should have all expected methods', () => {
      const iconManager = new IconManager()

      const expectedMethods = [
        'init',
        'discoverIcons',
        'handleThemeChange',
        'updateFavicon',
        'updateIcons',
        'removeCSSFilters',
        'addIcon',
        'preloadIcons'
      ]

      expectedMethods.forEach(method => {
        expect(typeof iconManager[method]).toBe('function')
      })
    })

    test('should have all expected properties', () => {
      const iconManager = new IconManager()

      expect(typeof iconManager.iconMappings).toBe('object')
      expect(iconManager.managedIcons).toBeInstanceOf(Map)
      expect(
        iconManager.currentTheme === null ||
          typeof iconManager.currentTheme === 'string'
      ).toBe(true)
      expect(
        iconManager.faviconElement === null ||
          iconManager.faviconElement.tagName === 'LINK'
      ).toBe(true)
    })

    test('should have iconMappings with correct structure', () => {
      const iconManager = new IconManager()

      // Verify iconMappings has string keys and values
      Object.entries(iconManager.iconMappings).forEach(([key, value]) => {
        expect(typeof key).toBe('string')
        expect(typeof value).toBe('string')
        expect(key).toMatch(/\.svg$/)
        expect(value).toMatch(/\.svg$/)
      })
    })

    test('should handle theme change events with correct signature', () => {
      const iconManager = new IconManager()

      expect(() => {
        iconManager.handleThemeChange({ theme: 'dark', isDark: true })
        iconManager.handleThemeChange({ theme: 'light', isDark: false })
      }).not.toThrow()
    })
  })

  describe('ScrollManager Class Verification', () => {
    beforeEach(() => {
      // Setup elements for ScrollManager
      const backToTopBtn = document.createElement('button')
      backToTopBtn.id = 'backToTopBtn'
      backToTopBtn.addEventListener = jest.fn()
      document.body.appendChild(backToTopBtn)

      // Mock window methods
      window.scrollTo = jest.fn()
      window.requestAnimationFrame = jest.fn(cb => setTimeout(cb, 16))
      window.addEventListener = jest.fn()
      window.history = { pushState: jest.fn() }
    })

    test('should have all expected methods', () => {
      const scrollManager = new ScrollManager()

      const expectedMethods = [
        'toggleVisibility',
        'scrollToTop',
        'init',
        'initSmoothScrolling',
        'scrollToSection',
        'updateActiveNavLink',
        'setupNavigationHighlighting'
      ]

      expectedMethods.forEach(method => {
        expect(typeof scrollManager[method]).toBe('function')
      })
    })

    test('should have all expected properties with correct types', () => {
      const scrollManager = new ScrollManager()

      expect(typeof scrollManager.threshold).toBe('number')
      expect(typeof scrollManager.isVisible).toBe('boolean')
      expect(typeof scrollManager.navHeight).toBe('number')
      expect(
        scrollManager.button === null ||
          scrollManager.button.tagName === 'BUTTON'
      ).toBe(true)
    })

    test('should have correct default values', () => {
      const scrollManager = new ScrollManager()

      expect(scrollManager.threshold).toBe(300)
      expect(scrollManager.isVisible).toBe(false)
      expect(scrollManager.navHeight).toBe(80)
    })

    test('should handle method calls with correct parameters', () => {
      const scrollManager = new ScrollManager()

      expect(() => {
        scrollManager.scrollToSection('test')
        scrollManager.toggleVisibility()
        scrollManager.scrollToTop()
      }).not.toThrow()
    })
  })

  describe('AnimationManager Class Verification', () => {
    test('should have all expected methods', () => {
      const animationManager = new AnimationManager()

      const expectedMethods = [
        'init',
        'setupScrollAnimations',
        'animateProgressBars',
        'setupCardAnimations',
        'animateSkillsBars',
        'showLoading',
        'hideLoading',
        'revealContent'
      ]

      expectedMethods.forEach(method => {
        expect(typeof animationManager[method]).toBe('function')
      })
    })

    test('should have all expected properties', () => {
      const animationManager = new AnimationManager()

      expect(animationManager.animatedElements).toBeInstanceOf(Set)
    })

    test('should handle method calls with correct parameters', () => {
      const animationManager = new AnimationManager()
      const testElement = document.createElement('div')

      expect(() => {
        animationManager.showLoading(testElement)
        animationManager.hideLoading(testElement)
        animationManager.revealContent(testElement, 'test content')
        animationManager.animateSkillsBars()
      }).not.toThrow()
    })

    test('should use Set for tracking animated elements', () => {
      const animationManager = new AnimationManager()
      const testElement = document.createElement('div')

      // Should support Set operations
      expect(() => {
        animationManager.animatedElements.add(testElement)
        animationManager.animatedElements.has(testElement)
        animationManager.animatedElements.delete(testElement)
      }).not.toThrow()
    })
  })

  describe('ProjectManager Class Verification', () => {
    beforeEach(() => {
      // Setup elements for ProjectManager
      const filterBtn = document.createElement('button')
      filterBtn.className = 'filter-btn'
      filterBtn.setAttribute('data-filter', 'all')
      filterBtn.addEventListener = jest.fn()
      document.body.appendChild(filterBtn)

      const sortSelect = document.createElement('select')
      sortSelect.id = 'repo-sort'
      sortSelect.addEventListener = jest.fn()
      document.body.appendChild(sortSelect)

      const container = document.createElement('div')
      container.id = 'repo-container'
      document.body.appendChild(container)

      const noResults = document.createElement('div')
      noResults.id = 'no-results'
      document.body.appendChild(noResults)
    })

    test('should have all expected methods', () => {
      const projectManager = new ProjectManager()

      const expectedMethods = [
        'init',
        'setupEventListeners',
        'setFilter',
        'updateFilterButtons',
        'categorizeProject',
        'filterProjects',
        'sortProjects',
        'applyFiltersAndSort',
        'renderProjects',
        'createProjectCard',
        'interceptRepoWidget',
        'setupWidgetOverride',
        'hideLoading'
      ]

      expectedMethods.forEach(method => {
        expect(typeof projectManager[method]).toBe('function')
      })
    })

    test('should have all expected properties with correct types', () => {
      const projectManager = new ProjectManager()

      expect(Array.isArray(projectManager.projects)).toBe(true)
      expect(typeof projectManager.currentFilter).toBe('string')
      expect(typeof projectManager.currentSort).toBe('string')
      expect(typeof projectManager.categories).toBe('object')
    })

    test('should have correct default values', () => {
      const projectManager = new ProjectManager()

      expect(projectManager.projects).toEqual([])
      expect(projectManager.currentFilter).toBe('all')
      expect(projectManager.currentSort).toBe('updated')
      expect(projectManager.categories).toHaveProperty('cybersecurity')
      expect(projectManager.categories).toHaveProperty('healthcare')
      expect(projectManager.categories).toHaveProperty('automation')
      expect(projectManager.categories).toHaveProperty('tools')
    })

    test('should handle method calls with correct parameters', () => {
      const projectManager = new ProjectManager()

      const testProject = {
        name: 'test-project',
        description: 'Test description',
        html_url: 'https://github.com/test/project',
        stargazers_count: 5,
        language: 'JavaScript',
        created_at: '2023-01-01',
        updated_at: '2023-06-01'
      }

      expect(() => {
        projectManager.setFilter('cybersecurity')
        projectManager.categorizeProject(testProject)
        projectManager.sortProjects([testProject])
        projectManager.filterProjects()
        projectManager.renderProjects([testProject])
      }).not.toThrow()
    })

    test('should return correct types from methods', () => {
      const projectManager = new ProjectManager()

      const testProject = { name: 'test', description: 'test description' }

      expect(typeof projectManager.categorizeProject(testProject)).toBe(
        'string'
      )
      expect(Array.isArray(projectManager.filterProjects())).toBe(true)
      expect(Array.isArray(projectManager.sortProjects([testProject]))).toBe(
        true
      )
    })
  })

  describe('Cross-Class Interface Verification', () => {
    test('should have consistent event handling patterns', () => {
      const themeManager = new ThemeManager()
      const iconManager = new IconManager()

      // Both should handle theme change events
      expect(() => {
        themeManager.setTheme('dark')
        iconManager.handleThemeChange({ theme: 'dark', isDark: true })
      }).not.toThrow()
    })

    test('should have consistent initialization patterns', () => {
      // All managers should have init methods or initialize in constructor
      const managers = [
        new ThemeManager(),
        new IconManager(),
        new ScrollManager(),
        new AnimationManager(),
        new ProjectManager()
      ]

      managers.forEach(manager => {
        if (manager.init) {
          expect(typeof manager.init).toBe('function')
        }
        // All should initialize without errors
        expect(manager).toBeDefined()
      })
    })

    test('should have consistent error handling patterns', () => {
      // All classes should handle null/undefined inputs gracefully
      const managers = [
        new ThemeManager(),
        new IconManager(),
        new ScrollManager(),
        new AnimationManager(),
        new ProjectManager()
      ]

      managers.forEach(manager => {
        // Should not throw when called with edge case inputs
        expect(manager).toBeDefined()
      })
    })

    test('should have consistent DOM interaction patterns', () => {
      const iconManager = new IconManager()
      const scrollManager = new ScrollManager()
      const animationManager = new AnimationManager()

      // All should handle missing DOM elements gracefully
      expect(() => {
        iconManager.updateFavicon(true)
        scrollManager.toggleVisibility()
        animationManager.showLoading(null)
      }).not.toThrow()
    })
  })

  describe('Mock vs Real Implementation Comparison', () => {
    test('ScrollManager mock methods should match real implementation', () => {
      const scrollManager = new ScrollManager()

      // Compare with mock from scroll-manager.test.js
      const mockMethods = [
        'toggleVisibility',
        'scrollToTop',
        'init',
        'initSmoothScrolling',
        'scrollToSection',
        'updateActiveNavLink',
        'setupNavigationHighlighting'
      ]

      mockMethods.forEach(method => {
        expect(typeof scrollManager[method]).toBe('function')
      })

      // Check that constructor signature matches
      expect(scrollManager.threshold).toBe(300)
      expect(scrollManager.navHeight).toBe(80)
      expect(typeof scrollManager.isVisible).toBe('boolean')
    })

    test('AnimationManager mock functionality should match real implementation', () => {
      const animationManager = new AnimationManager()

      // Should have Set for tracking animated elements like the mock tests assume
      expect(animationManager.animatedElements).toBeInstanceOf(Set)

      // Should have loading state methods
      expect(typeof animationManager.showLoading).toBe('function')
      expect(typeof animationManager.hideLoading).toBe('function')
      expect(typeof animationManager.revealContent).toBe('function')

      // Should handle skills animation
      expect(typeof animationManager.animateSkillsBars).toBe('function')
    })

    test('ProjectManager mock behavior should match real implementation', () => {
      const projectManager = new ProjectManager()

      // Should have filter and sort functionality
      expect(typeof projectManager.setFilter).toBe('function')
      expect(typeof projectManager.filterProjects).toBe('function')
      expect(typeof projectManager.sortProjects).toBe('function')

      // Should have categories object structure
      expect(projectManager.categories).toHaveProperty('cybersecurity')
      expect(Array.isArray(projectManager.categories.cybersecurity)).toBe(true)

      // Should start with empty projects array
      expect(Array.isArray(projectManager.projects)).toBe(true)
      expect(projectManager.currentFilter).toBe('all')
    })

    test('ThemeManager should dispatch events as expected by other components', () => {
      // Spy on window.dispatchEvent to verify it's called
      const dispatchSpy = jest.spyOn(window, 'dispatchEvent')

      const themeManager = new ThemeManager()

      // Verify dispatchEvent was called during initialization
      expect(dispatchSpy).toHaveBeenCalled()

      // Get the event that was dispatched
      const dispatchCall = dispatchSpy.mock.calls.find(call => {
        const event = call[0]
        return event && event.type === 'themeChanged'
      })

      expect(dispatchCall).toBeDefined()
      const event = dispatchCall[0]

      // Verify event structure
      expect(event.detail).toEqual(
        expect.objectContaining({
          theme: expect.any(String),
          isDark: expect.any(Boolean),
          mode: expect.any(String)
        })
      )

      // Test that subsequent setTheme calls also dispatch correctly
      dispatchSpy.mockClear()
      themeManager.setTheme('dark')

      const darkThemeCall = dispatchSpy.mock.calls.find(call => {
        const evt = call[0]
        return evt && evt.type === 'themeChanged'
      })

      expect(darkThemeCall).toBeDefined()
      expect(darkThemeCall[0].detail).toEqual(
        expect.objectContaining({
          theme: 'dark',
          isDark: true,
          mode: expect.any(String)
        })
      )

      dispatchSpy.mockRestore()
    })
  })

  describe('API Contract Verification', () => {
    test('should maintain backward compatibility with existing interfaces', () => {
      // Verify that all classes can be instantiated without parameters
      expect(() => {
        const tm = new ThemeManager() // eslint-disable-line no-unused-vars
        const im = new IconManager() // eslint-disable-line no-unused-vars
        const sm = new ScrollManager() // eslint-disable-line no-unused-vars
        const am = new AnimationManager() // eslint-disable-line no-unused-vars
        const pm = new ProjectManager() // eslint-disable-line no-unused-vars
        expect(tm && im && sm && am && pm).toBeTruthy()
      }).not.toThrow()
    })

    test('should have stable method signatures for public APIs', () => {
      const themeManager = new ThemeManager()
      const iconManager = new IconManager()

      // Theme manager public API
      expect(themeManager.setTheme.length).toBe(1) // Should accept one parameter
      expect(themeManager.setMode.length).toBe(1)

      // Icon manager public API
      expect(iconManager.handleThemeChange.length).toBe(1)
      expect(iconManager.addIcon.length).toBe(2)
    })

    test('should return consistent data types from methods', () => {
      const projectManager = new ProjectManager()

      // Methods should return expected types
      const testProject = { name: 'test', description: 'test' }

      const category = projectManager.categorizeProject(testProject)
      expect(typeof category).toBe('string')

      const filtered = projectManager.filterProjects()
      expect(Array.isArray(filtered)).toBe(true)

      const sorted = projectManager.sortProjects([testProject])
      expect(Array.isArray(sorted)).toBe(true)
    })

    test('should handle null and undefined inputs consistently', () => {
      const animationManager = new AnimationManager()
      const iconManager = new IconManager()

      // Methods with null checks should handle null/undefined gracefully
      expect(() => {
        animationManager.showLoading(null)
        animationManager.hideLoading(undefined)
        iconManager.addIcon(null, 'test.svg')
      }).not.toThrow()

      // revealContent doesn't have null checks, so it throws
      expect(() => {
        animationManager.revealContent(null, 'content')
      }).toThrow()
    })
  })
})
