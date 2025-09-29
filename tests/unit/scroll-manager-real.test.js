/**
 * Unit Tests for Actual ScrollManager Class
 * Tests the real implementation from theme.js with comprehensive scenarios
 */

/* eslint-env jest, node */
/* global ScrollManager */

const fs = require('fs')
const path = require('path')
const { TestUtils } = require('./setup.js')

// Read and evaluate the actual theme.js file
const themePath = path.join(__dirname, '../../site/static/js/theme.js')
const themeCode = fs.readFileSync(themePath, 'utf8')

// Setup DOM before evaluating the code
// Note: documentElement is read-only in JSDOM, so we work with the existing structure

// Mock IntersectionObserver
global.IntersectionObserver = jest
  .fn()
  .mockImplementation(function (callback, options) {
    this.callback = callback
    this.options = options
    this.observe = jest.fn()
    this.unobserve = jest.fn()
    this.disconnect = jest.fn()

    // Simulate entry intersection
    this.triggerIntersection = entries => {
      this.callback(entries)
    }
  })

// Evaluate the theme.js code in our test environment
// eslint-disable-next-line no-eval
eval(themeCode)

describe('ScrollManager (Real Implementation)', () => {
  let scrollManager
  let mockBackToTopBtn
  let mockNavLinks
  let mockSections
  let observer

  beforeEach(() => {
    // Clear mocks FIRST, before creating any mock elements
    jest.clearAllMocks()

    // Reset DOM
    document.documentElement.innerHTML = ''
    document.head.innerHTML = ''
    document.body.innerHTML = ''

    // Create mock DOM elements with Jest spies that ScrollManager expects
    mockBackToTopBtn = TestUtils.createMockElement('button', {
      id: 'backToTopBtn',
      'aria-hidden': 'true'
    })
    mockBackToTopBtn.style.display = 'none'
    document.body.appendChild(mockBackToTopBtn)

    // Create navigation links
    mockNavLinks = [
      TestUtils.createMockElement('a', {
        class: 'internal-nav',
        'data-scroll': 'about'
      }),
      TestUtils.createMockElement('a', {
        class: 'internal-nav',
        'data-scroll': 'skills'
      }),
      TestUtils.createMockElement('a', {
        class: 'internal-nav',
        'data-scroll': 'projects'
      })
    ]

    mockNavLinks.forEach(link => {
      document.body.appendChild(link)
    })

    // Create sections
    mockSections = [
      TestUtils.createMockElement('section', { id: 'about' }),
      TestUtils.createMockElement('section', { id: 'skills' }),
      TestUtils.createMockElement('section', { id: 'projects' })
    ]

    mockSections.forEach(section => {
      document.body.appendChild(section)
    })

    // Mock getBoundingClientRect for sections
    mockSections.forEach((section, index) => {
      section.getBoundingClientRect = jest.fn().mockReturnValue({
        top: 500 + index * 600,
        height: 400,
        bottom: 900 + index * 600,
        left: 0,
        right: 1200,
        width: 1200
      })
    })

    // Mock window properties
    Object.defineProperty(window, 'pageYOffset', {
      writable: true,
      value: 0
    })

    // Mock scroll functions
    window.scrollTo = jest.fn()
    window.requestAnimationFrame = jest.fn(cb => setTimeout(cb, 16))
    window.addEventListener = jest.fn()

    // Mock history API
    window.history = {
      pushState: jest.fn()
    }
  })

  afterEach(() => {
    // Clean up DOM
    document.body.innerHTML = ''
    jest.clearAllMocks()
    jest.useRealTimers()
  })

  describe('Constructor and Initialization', () => {
    test('should initialize with correct default values', () => {
      scrollManager = new ScrollManager()

      expect(scrollManager.threshold).toBe(300)
      expect(scrollManager.isVisible).toBe(false)
      expect(scrollManager.navHeight).toBe(80)
      expect(scrollManager.button).toBe(mockBackToTopBtn)
    })

    test('should handle missing back-to-top button gracefully', () => {
      // Remove the button
      document.body.removeChild(mockBackToTopBtn)
      mockBackToTopBtn = null

      expect(() => {
        scrollManager = new ScrollManager()
      }).not.toThrow()

      expect(scrollManager.button).toBeNull()
    })

    test('should set up scroll event listener with passive option', () => {
      scrollManager = new ScrollManager()

      expect(window.addEventListener).toHaveBeenCalledWith(
        'scroll',
        expect.any(Function),
        { passive: true }
      )
    })

    test('should initialize smooth scrolling for internal nav links', () => {
      scrollManager = new ScrollManager()

      // Check that addEventListener was called for each nav link
      mockNavLinks.forEach(link => {
        expect(link.addEventListener).toHaveBeenCalledWith(
          'click',
          expect.any(Function)
        )
      })
    })

    test('should create intersection observer for navigation highlighting', () => {
      scrollManager = new ScrollManager()

      expect(IntersectionObserver).toHaveBeenCalledWith(
        expect.any(Function),
        expect.objectContaining({
          threshold: expect.any(Array),
          rootMargin: expect.stringContaining('-80px')
        })
      )
    })
  })

  describe('Back-to-Top Visibility Toggle', () => {
    beforeEach(() => {
      scrollManager = new ScrollManager()
    })

    test('should show button when scrolled beyond threshold', () => {
      window.pageYOffset = 400

      scrollManager.toggleVisibility()

      expect(mockBackToTopBtn.style.display).toBe('block')
      expect(mockBackToTopBtn.getAttribute('aria-hidden')).toBe('false')
      expect(scrollManager.isVisible).toBe(true)
    })

    test('should hide button when scrolled below threshold', () => {
      // First show the button
      window.pageYOffset = 400
      scrollManager.toggleVisibility()
      expect(scrollManager.isVisible).toBe(true)

      // Then hide it
      window.pageYOffset = 200
      scrollManager.toggleVisibility()

      expect(mockBackToTopBtn.style.display).toBe('none')
      expect(mockBackToTopBtn.getAttribute('aria-hidden')).toBe('true')
      expect(scrollManager.isVisible).toBe(false)
    })

    test("should not update visibility if state hasn't changed", () => {
      window.pageYOffset = 100
      scrollManager.toggleVisibility()

      const initialDisplay = mockBackToTopBtn.style.display

      // Call again with same scroll position
      scrollManager.toggleVisibility()

      expect(mockBackToTopBtn.style.display).toBe(initialDisplay)
    })

    test('should use requestAnimationFrame for performance', () => {
      scrollManager = new ScrollManager()

      // Simulate scroll event
      const scrollHandler = window.addEventListener.mock.calls.find(
        call => call[0] === 'scroll'
      )[1]

      scrollHandler()

      expect(window.requestAnimationFrame).toHaveBeenCalled()
    })
  })

  describe('Scroll-to-Top Functionality', () => {
    beforeEach(() => {
      scrollManager = new ScrollManager()
      jest.useFakeTimers()
    })

    test('should scroll to top with smooth behavior', () => {
      scrollManager.scrollToTop()

      expect(window.scrollTo).toHaveBeenCalledWith({
        top: 0,
        behavior: 'smooth'
      })
    })

    test('should focus on first heading after scroll delay', () => {
      const mockHeading = document.createElement('h1')
      mockHeading.focus = jest.fn()
      document.body.appendChild(mockHeading)

      scrollManager.scrollToTop()

      // Fast-forward the timeout
      jest.advanceTimersByTime(100)

      expect(mockHeading.focus).toHaveBeenCalled()
    })

    test('should focus on element with tabindex if no heading exists', () => {
      const mockTabElement = document.createElement('div')
      mockTabElement.setAttribute('tabindex', '0')
      mockTabElement.focus = jest.fn()
      document.body.appendChild(mockTabElement)

      scrollManager.scrollToTop()
      jest.advanceTimersByTime(100)

      expect(mockTabElement.focus).toHaveBeenCalled()
    })

    test('should handle missing focusable elements gracefully', () => {
      scrollManager.scrollToTop()

      expect(() => {
        jest.advanceTimersByTime(100)
      }).not.toThrow()
    })

    test('should handle button click events', () => {
      scrollManager = new ScrollManager()

      // Get the click handler
      const clickHandler = mockBackToTopBtn.addEventListener.mock.calls.find(
        call => call[0] === 'click'
      )[1]

      const mockEvent = { preventDefault: jest.fn() }
      clickHandler(mockEvent)

      expect(mockEvent.preventDefault).toHaveBeenCalled()
      expect(window.scrollTo).toHaveBeenCalledWith({
        top: 0,
        behavior: 'smooth'
      })
    })
  })

  describe('Section Scrolling and Navigation', () => {
    beforeEach(() => {
      scrollManager = new ScrollManager()
    })

    test('should scroll to section with navigation offset', () => {
      scrollManager.scrollToSection('about')

      const expectedTop = 500 + 0 - 80 // getBoundingClientRect().top + pageYOffset - navHeight
      expect(window.scrollTo).toHaveBeenCalledWith({
        top: expectedTop,
        behavior: 'smooth'
      })
    })

    test('should update URL hash when scrolling to section', () => {
      scrollManager.scrollToSection('skills')

      expect(window.history.pushState).toHaveBeenCalledWith(
        null,
        null,
        '#skills'
      )
    })

    test('should handle missing target section gracefully', () => {
      expect(() => {
        scrollManager.scrollToSection('nonexistent')
      }).not.toThrow()

      expect(window.scrollTo).not.toHaveBeenCalled()
      expect(window.history.pushState).not.toHaveBeenCalled()
    })

    test('should update active navigation link', () => {
      const activeLink = mockNavLinks[0]

      scrollManager.updateActiveNavLink(activeLink)

      expect(activeLink.classList.add).toHaveBeenCalledWith('active')
      expect(activeLink.setAttribute).toHaveBeenCalledWith(
        'aria-current',
        'page'
      )

      // Check that other links had active state removed
      mockNavLinks.slice(1).forEach(link => {
        expect(link.classList.remove).toHaveBeenCalledWith('active')
        expect(link.removeAttribute).toHaveBeenCalledWith('aria-current')
      })
    })

    test('should handle navigation link clicks', () => {
      const navLink = mockNavLinks[0]

      // Get the click handler
      const clickHandler = navLink.addEventListener.mock.calls.find(
        call => call[0] === 'click'
      )[1]

      const mockEvent = { preventDefault: jest.fn() }
      clickHandler(mockEvent)

      expect(mockEvent.preventDefault).toHaveBeenCalled()
      expect(window.scrollTo).toHaveBeenCalled()
    })

    test('should close mobile navbar when navigating', () => {
      const mockNavbar = document.createElement('div')
      mockNavbar.className = 'navbar-collapse show'
      mockNavbar.classList.remove = jest.fn()
      document.body.appendChild(mockNavbar)

      const navLink = mockNavLinks[0]
      const clickHandler = navLink.addEventListener.mock.calls.find(
        call => call[0] === 'click'
      )[1]

      clickHandler({ preventDefault: jest.fn() })

      expect(mockNavbar.classList.remove).toHaveBeenCalledWith('show')
    })
  })

  describe('Intersection Observer Navigation Highlighting', () => {
    beforeEach(() => {
      scrollManager = new ScrollManager()
      observer = IntersectionObserver.mock.instances[0]
    })

    test('should observe all sections with IDs', () => {
      expect(observer.observe).toHaveBeenCalledTimes(mockSections.length)
      mockSections.forEach(section => {
        expect(observer.observe).toHaveBeenCalledWith(section)
      })
    })

    test('should update active nav link when section intersects', () => {
      // Mock the entry for the 'about' section
      const mockEntry = {
        isIntersecting: true,
        target: mockSections[0], // about section
        intersectionRatio: 0.8,
        boundingClientRect: { top: 100 }
      }

      // Trigger intersection
      observer.triggerIntersection([mockEntry])

      // Should find and update the corresponding nav link
      const correspondingNavLink = mockNavLinks[0] // data-scroll="about"
      expect(correspondingNavLink.classList.add).toHaveBeenCalledWith('active')
    })

    test('should handle multiple intersecting sections by prioritizing highest ratio', () => {
      const entries = [
        {
          isIntersecting: true,
          target: mockSections[0],
          intersectionRatio: 0.3,
          boundingClientRect: { top: 200 }
        },
        {
          isIntersecting: true,
          target: mockSections[1],
          intersectionRatio: 0.7,
          boundingClientRect: { top: 100 }
        }
      ]

      observer.triggerIntersection(entries)

      // Should activate the section with higher intersection ratio
      expect(mockNavLinks[1].classList.add).toHaveBeenCalledWith('active')
    })

    test('should handle sections without corresponding nav links', () => {
      const orphanSection = TestUtils.createMockElement('section', {
        id: 'orphan'
      })
      document.body.appendChild(orphanSection)

      const mockEntry = {
        isIntersecting: true,
        target: orphanSection,
        intersectionRatio: 0.8,
        boundingClientRect: { top: 100 }
      }

      expect(() => {
        observer.triggerIntersection([mockEntry])
      }).not.toThrow()
    })

    test('should not update navigation when no sections are intersecting', () => {
      const entries = [
        {
          isIntersecting: false,
          target: mockSections[0],
          intersectionRatio: 0,
          boundingClientRect: { top: -500 }
        }
      ]

      // Clear previous calls
      jest.clearAllMocks()

      observer.triggerIntersection(entries)

      // No nav links should be updated
      mockNavLinks.forEach(link => {
        expect(link.classList.add).not.toHaveBeenCalled()
      })
    })
  })

  describe('Error Handling and Edge Cases', () => {
    test('should handle missing DOM elements during initialization', () => {
      // Remove all elements
      document.body.innerHTML = ''

      expect(() => {
        scrollManager = new ScrollManager()
      }).not.toThrow()
    })

    test('should handle errors in scroll event handler', () => {
      scrollManager = new ScrollManager()

      // Mock an error in toggleVisibility
      const originalToggleVisibility = scrollManager.toggleVisibility
      scrollManager.toggleVisibility = jest.fn().mockImplementation(() => {
        throw new Error('Test error')
      })

      const scrollHandler = window.addEventListener.mock.calls.find(
        call => call[0] === 'scroll'
      )[1]

      expect(() => {
        scrollHandler()
        // Trigger requestAnimationFrame callback
        window.requestAnimationFrame.mock.calls[0][0]()
      }).not.toThrow()

      scrollManager.toggleVisibility = originalToggleVisibility
    })

    test('should handle errors in intersection observer callback', () => {
      scrollManager = new ScrollManager()
      observer = IntersectionObserver.mock.instances[0]

      // Create malformed entry
      const badEntry = {
        isIntersecting: true,
        target: null,
        intersectionRatio: 0.5,
        boundingClientRect: { top: 100 }
      }

      expect(() => {
        observer.triggerIntersection([badEntry])
      }).not.toThrow()
    })

    test('should handle missing querySelector results', () => {
      // Mock querySelector to return null
      const originalQuerySelector = document.querySelector
      document.querySelector = jest.fn().mockReturnValue(null)

      scrollManager = new ScrollManager()

      expect(() => {
        scrollManager.scrollToTop()
      }).not.toThrow()

      document.querySelector = originalQuerySelector
    })

    test('should handle getBoundingClientRect errors', () => {
      // Ensure fresh ScrollManager instance
      scrollManager = new ScrollManager()

      // Create a fresh mock section to avoid interference
      const testSection = TestUtils.createMockElement('section', {
        id: 'test-error-section'
      })
      testSection.getBoundingClientRect = jest.fn().mockImplementation(() => {
        throw new Error('getBoundingClientRect failed')
      })
      document.body.appendChild(testSection)

      // Test that scrollToSection handles getBoundingClientRect errors gracefully
      expect(() => {
        scrollManager.scrollToSection('test-error-section')
      }).not.toThrow()

      // Clean up
      document.body.removeChild(testSection)
    })
  })

  describe('Performance Optimizations', () => {
    beforeEach(() => {
      scrollManager = new ScrollManager()
    })

    test('should use passive scroll listeners', () => {
      const scrollCall = window.addEventListener.mock.calls.find(
        call => call[0] === 'scroll'
      )

      expect(scrollCall[2]).toEqual({ passive: true })
    })

    test('should throttle scroll events with requestAnimationFrame', () => {
      const scrollHandler = window.addEventListener.mock.calls.find(
        call => call[0] === 'scroll'
      )[1]

      // Trigger multiple scroll events rapidly
      scrollHandler()
      scrollHandler()
      scrollHandler()

      expect(window.requestAnimationFrame).toHaveBeenCalledTimes(3)
    })

    test('should use intersection observer for navigation highlighting instead of scroll events', () => {
      // Verify that IntersectionObserver is used for section highlighting
      expect(IntersectionObserver).toHaveBeenCalled()

      const observerOptions = IntersectionObserver.mock.calls[0][1]
      expect(observerOptions).toHaveProperty('threshold')
      expect(observerOptions).toHaveProperty('rootMargin')
    })
  })

  describe('Accessibility Features', () => {
    beforeEach(() => {
      scrollManager = new ScrollManager()
    })

    test('should manage ARIA attributes for back-to-top button', () => {
      // Test hidden state
      window.pageYOffset = 100
      scrollManager.toggleVisibility()
      expect(mockBackToTopBtn.getAttribute('aria-hidden')).toBe('true')

      // Test visible state
      window.pageYOffset = 400
      scrollManager.toggleVisibility()
      expect(mockBackToTopBtn.getAttribute('aria-hidden')).toBe('false')
    })

    test('should set aria-current on active navigation links', () => {
      const activeLink = mockNavLinks[1]

      scrollManager.updateActiveNavLink(activeLink)

      expect(activeLink.setAttribute).toHaveBeenCalledWith(
        'aria-current',
        'page'
      )
    })

    test('should remove aria-current from inactive navigation links', () => {
      const activeLink = mockNavLinks[1]

      scrollManager.updateActiveNavLink(activeLink)

      // Other links should have aria-current removed
      const inactiveLinks = [mockNavLinks[0], mockNavLinks[2]]
      inactiveLinks.forEach(link => {
        expect(link.removeAttribute).toHaveBeenCalledWith('aria-current')
      })
    })

    test('should focus on heading for keyboard navigation after scroll', () => {
      jest.useFakeTimers()

      const mockHeading = document.createElement('h1')
      mockHeading.focus = jest.fn()
      document.body.appendChild(mockHeading)

      scrollManager.scrollToTop()
      jest.advanceTimersByTime(100)

      expect(mockHeading.focus).toHaveBeenCalled()
    })
  })
})
