/**
 * Unit Tests for ScrollManager Class
 * Tests scroll-to-top functionality and smooth scrolling navigation
 */

/* eslint-env jest, node */

const { TestUtils } = require('./setup.js')

// Mock ScrollManager class
class ScrollManager {
  constructor() {
    this.threshold = 300
    this.isVisible = false
    this.button = document.getElementById('backToTopBtn')
    this.navHeight = 80

    if (this.button) {
      this.init()
    }
    this.initSmoothScrolling()
  }

  toggleVisibility() {
    const shouldShow = window.pageYOffset > this.threshold

    if (shouldShow !== this.isVisible) {
      this.isVisible = shouldShow
      this.button.style.display = shouldShow ? 'block' : 'none'
      this.button.setAttribute('aria-hidden', !shouldShow)
    }
  }

  scrollToTop() {
    window.scrollTo({
      top: 0,
      behavior: 'smooth'
    })

    setTimeout(() => {
      document.querySelector('h1, [tabindex="0"]')?.focus()
    }, 100)
  }

  init() {
    window.addEventListener(
      'scroll',
      () => {
        requestAnimationFrame(() => this.toggleVisibility())
      },
      { passive: true }
    )

    this.button.addEventListener('click', e => {
      e.preventDefault()
      this.scrollToTop()
    })

    this.toggleVisibility()
  }

  initSmoothScrolling() {
    const internalNavLinks = document.querySelectorAll(
      '.internal-nav[data-scroll]'
    )

    internalNavLinks.forEach(link => {
      link.addEventListener('click', e => {
        e.preventDefault()
        const targetId = link.getAttribute('data-scroll')
        this.scrollToSection(targetId)
        this.updateActiveNavLink(link)

        const navbar = document.querySelector('.navbar-collapse')
        if (navbar && navbar.classList.contains('show')) {
          navbar.classList.remove('show')
        }
      })
    })

    this.setupNavigationHighlighting()
  }

  scrollToSection(targetId) {
    const target = document.getElementById(targetId)
    if (!target) return

    const targetPosition =
      target.getBoundingClientRect().top + window.pageYOffset - this.navHeight

    window.scrollTo({
      top: targetPosition,
      behavior: 'smooth'
    })

    history.pushState(null, null, `#${targetId}`)
  }

  updateActiveNavLink(activeLink) {
    document.querySelectorAll('.internal-nav').forEach(link => {
      link.classList.remove('active')
      link.removeAttribute('aria-current')
    })

    activeLink.classList.add('active')
    activeLink.setAttribute('aria-current', 'page')
  }

  setupNavigationHighlighting() {
    const sections = document.querySelectorAll('section[id]')
    const observer = new IntersectionObserver(
      entries => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            const currentNavLink = document.querySelector(
              `[data-scroll="${entry.target.id}"]`
            )
            if (currentNavLink) {
              this.updateActiveNavLink(currentNavLink)
            }
          }
        })
      },
      {
        threshold: 0.3,
        rootMargin: `-${this.navHeight}px 0px -50% 0px`
      }
    )

    sections.forEach(section => observer.observe(section))
  }
}

describe('ScrollManager', () => {
  let scrollManager
  let mockBackToTopBtn
  let mockNavLinks
  let mockSections

  beforeEach(() => {
    mockBackToTopBtn = TestUtils.createMockElement('button', {
      id: 'backToTopBtn',
      style: 'display: none;'
    })
    document.body.appendChild(mockBackToTopBtn)

    mockNavLinks = [
      TestUtils.createMockElement('a', {
        class: 'internal-nav',
        'data-scroll': 'about'
      }),
      TestUtils.createMockElement('a', {
        class: 'internal-nav',
        'data-scroll': 'skills'
      })
    ]
    mockNavLinks.forEach(link => document.body.appendChild(link))

    // Mock document.querySelectorAll to return our mock nav links
    document.querySelectorAll = jest.fn().mockImplementation(selector => {
      if (selector === '.internal-nav') {
        return mockNavLinks
      }
      return []
    })

    mockSections = [
      TestUtils.createMockElement('section', { id: 'about' }),
      TestUtils.createMockElement('section', { id: 'skills' })
    ]
    mockSections.forEach(section => document.body.appendChild(section))

    mockSections.forEach((section, index) => {
      section.getBoundingClientRect = jest.fn().mockReturnValue({
        top: 500 + index * 600,
        height: 400
      })
    })

    Object.defineProperty(window, 'pageYOffset', {
      writable: true,
      value: 0
    })

    window.scrollTo = jest.fn()
    window.requestAnimationFrame = jest.fn(cb => setTimeout(cb, 16))
  })

  afterEach(() => {
    [mockBackToTopBtn, ...mockNavLinks, ...mockSections].forEach(el => {
      if (el.parentNode) el.parentNode.removeChild(el)
    })

    jest.clearAllMocks()
  })

  describe('Constructor and Initialization', () => {
    test('should initialize with correct default values', () => {
      scrollManager = new ScrollManager()

      expect(scrollManager.threshold).toBe(300)
      expect(scrollManager.isVisible).toBe(false)
      expect(scrollManager.navHeight).toBe(80)
    })

    test('should handle missing back-to-top button', () => {
      document.body.removeChild(mockBackToTopBtn)

      expect(() => {
        scrollManager = new ScrollManager()
      }).not.toThrow()
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
      // First make the button visible (set initial state)
      window.pageYOffset = 400
      scrollManager.toggleVisibility()

      // Then hide it by scrolling below threshold
      window.pageYOffset = 200
      scrollManager.toggleVisibility()

      expect(mockBackToTopBtn.style.display).toBe('none')
      expect(mockBackToTopBtn.getAttribute('aria-hidden')).toBe('true')
      expect(scrollManager.isVisible).toBe(false)
    })
  })

  describe('Scroll-to-Top Functionality', () => {
    beforeEach(() => {
      scrollManager = new ScrollManager()
    })

    test('should scroll to top with smooth behavior', () => {
      scrollManager.scrollToTop()

      expect(window.scrollTo).toHaveBeenCalledWith({
        top: 0,
        behavior: 'smooth'
      })
    })

    test('should focus on first heading after scroll', async () => {
      const mockHeading = TestUtils.createMockElement('h1')
      mockHeading.focus = jest.fn()
      document.body.appendChild(mockHeading)

      scrollManager.scrollToTop()

      await TestUtils.waitFor(
        () => mockHeading.focus.mock.calls.length > 0,
        200
      )

      expect(mockHeading.focus).toHaveBeenCalled()

      document.body.removeChild(mockHeading)
    })
  })

  describe('Smooth Section Scrolling', () => {
    beforeEach(() => {
      scrollManager = new ScrollManager()
    })

    test('should scroll to section with offset for navigation', () => {
      scrollManager.scrollToSection('about')

      const expectedTop = 500 + 0 - 80
      expect(window.scrollTo).toHaveBeenCalledWith({
        top: expectedTop,
        behavior: 'smooth'
      })
    })

    test('should update URL hash when scrolling to section', () => {
      const pushStateSpy = jest.spyOn(history, 'pushState').mockImplementation()

      scrollManager.scrollToSection('about')

      expect(pushStateSpy).toHaveBeenCalledWith(null, null, '#about')

      pushStateSpy.mockRestore()
    })

    test('should handle missing target section gracefully', () => {
      expect(() => {
        scrollManager.scrollToSection('nonexistent')
      }).not.toThrow()

      expect(window.scrollTo).not.toHaveBeenCalled()
    })
  })

  describe('Active Navigation Link Management', () => {
    beforeEach(() => {
      scrollManager = new ScrollManager()
    })

    test('should update active navigation link', () => {
      const activeLink = mockNavLinks[0]

      // Recreate classList spies after jest.clearAllMocks() in afterEach
      mockNavLinks.forEach((link) => {
        link.classList.add = jest.fn()
        link.classList.remove = jest.fn()
        link.classList.toggle = jest.fn()
        link.classList.contains = jest.fn().mockReturnValue(false)
        link.setAttribute = jest.fn()
        link.removeAttribute = jest.fn()
      })

      scrollManager.updateActiveNavLink(activeLink)

      expect(activeLink.classList.add).toHaveBeenCalledWith('active')
      expect(activeLink.setAttribute).toHaveBeenCalledWith(
        'aria-current',
        'page'
      )

      mockNavLinks.slice(1).forEach(link => {
        expect(link.classList.remove).toHaveBeenCalledWith('active')
        expect(link.removeAttribute).toHaveBeenCalledWith('aria-current')
      })
    })
  })

  describe('Event Listener Management', () => {
    test('should use passive scroll listener for better performance', () => {
      const addEventListenerSpy = jest.spyOn(window, 'addEventListener')

      scrollManager = new ScrollManager()

      expect(addEventListenerSpy).toHaveBeenCalledWith(
        'scroll',
        expect.any(Function),
        { passive: true }
      )

      addEventListenerSpy.mockRestore()
    })

    test('should throttle scroll events with requestAnimationFrame', () => {
      scrollManager = new ScrollManager()

      window.dispatchEvent(new Event('scroll'))

      expect(window.requestAnimationFrame).toHaveBeenCalled()
    })
  })

  describe('Accessibility Features', () => {
    beforeEach(() => {
      scrollManager = new ScrollManager()
    })

    test('should manage ARIA attributes for back-to-top button', () => {
      window.pageYOffset = 400
      scrollManager.toggleVisibility()

      expect(mockBackToTopBtn.getAttribute('aria-hidden')).toBe('false')

      window.pageYOffset = 100
      scrollManager.toggleVisibility()

      expect(mockBackToTopBtn.getAttribute('aria-hidden')).toBe('true')
    })

    test('should set aria-current on active navigation links', () => {
      const activeLink = mockNavLinks[0]

      scrollManager.updateActiveNavLink(activeLink)

      expect(activeLink.setAttribute).toHaveBeenCalledWith(
        'aria-current',
        'page'
      )
    })
  })
})
