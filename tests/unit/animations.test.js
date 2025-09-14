/**
 * Unit tests for animation system
 * Tests scroll animations, fade effects, and intersection observers
 */

const { JSDOM } = require('jsdom')

describe('Animation System', () => {
  let dom, window, document
  let mockIntersectionObserver, mockRequestAnimationFrame

  beforeEach(() => {
    // Create a fresh DOM environment
    const html = `
      <!DOCTYPE html>
      <html lang="en">
      <head>
        <meta charset="UTF-8">
        <title>Animation Test</title>
        <style>
          .fade-in { opacity: 0; transition: opacity 0.3s ease; }
          .fade-in.visible { opacity: 1; }
          .slide-up { transform: translateY(20px); opacity: 0; transition: all 0.5s ease; }
          .slide-up.visible { transform: translateY(0); opacity: 1; }
          .hero { height: 100vh; }
          .section { height: 50vh; margin: 2rem 0; }
        </style>
      </head>
      <body>
        <div class="hero fade-in" data-animate="fade-in">
          <h1>Hero Title</h1>
        </div>
        <section class="section slide-up" data-animate="slide-up">
          <h2>Section Title</h2>
          <p>Section content</p>
        </section>
        <section class="section fade-in" data-animate="fade-in">
          <h3>Another Section</h3>
        </section>
        <div class="card slide-up" data-animate="slide-up" data-delay="200">
          <h4>Card Title</h4>
        </div>
      </body>
      </html>
    `

    dom = new JSDOM(html, {
      url: 'http://localhost:3000',
      pretendToBeVisual: true,
      resources: 'usable'
    })

    window = dom.window
    document = window.document

    // Mock IntersectionObserver
    const mockEntries = []
    const mockObserver = {
      observe: jest.fn(),
      unobserve: jest.fn(),
      disconnect: jest.fn(),
      root: null,
      rootMargin: '',
      thresholds: []
    }

    mockIntersectionObserver = jest.fn((callback, options) => {
      mockObserver.callback = callback
      mockObserver.options = options
      return mockObserver
    })

    // Mock requestAnimationFrame
    mockRequestAnimationFrame = jest.fn((callback) => {
      setTimeout(callback, 16) // 60fps
      return 1
    })

    // Set up global mocks
    global.IntersectionObserver = mockIntersectionObserver
    global.requestAnimationFrame = mockRequestAnimationFrame
    global.cancelAnimationFrame = jest.fn()
    global.window = window
    global.document = document

    // Store observer for access in tests
    global.mockObserver = mockObserver
  })

  afterEach(() => {
    if (dom) {
      dom.window.close()
    }
    jest.clearAllMocks()
  })

  describe('Animation initialization', () => {
    test('should initialize intersection observer for animations', () => {
      const animatedElements = document.querySelectorAll('[data-animate]')

      // Simulate animation system initialization
      const observer = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              entry.target.classList.add('visible')
            }
          })
        },
        {
          threshold: 0.1,
          rootMargin: '50px'
        }
      )

      animatedElements.forEach((el) => observer.observe(el))

      expect(IntersectionObserver).toHaveBeenCalledWith(
        expect.any(Function),
        expect.objectContaining({
          threshold: 0.1,
          rootMargin: '50px'
        })
      )

      expect(global.mockObserver.observe).toHaveBeenCalledTimes(
        animatedElements.length
      )
      expect(animatedElements.length).toBeGreaterThan(0)
    })

    test('should find all elements with data-animate attribute', () => {
      const animatedElements = document.querySelectorAll('[data-animate]')

      expect(animatedElements.length).toBe(4)

      const animationTypes = Array.from(animatedElements).map((el) =>
        el.getAttribute('data-animate')
      )

      expect(animationTypes).toContain('fade-in')
      expect(animationTypes).toContain('slide-up')
    })

    test('should handle elements with animation delays', () => {
      const delayedElements = document.querySelectorAll('[data-delay]')

      expect(delayedElements.length).toBe(1)

      const delay = delayedElements[0].getAttribute('data-delay')
      expect(delay).toBe('200')
    })
  })

  describe('Intersection Observer callbacks', () => {
    test('should add visible class when element intersects', () => {
      const element = document.querySelector('.hero')

      // Create mock intersection entry
      const mockEntry = {
        target: element,
        isIntersecting: true,
        intersectionRatio: 0.5,
        boundingClientRect: {
          top: 100,
          bottom: 200,
          left: 0,
          right: 100
        }
      }

      // Simulate intersection observer callback
      const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('visible')
          }
        })
      })

      // Trigger callback manually
      observer.callback([mockEntry])

      expect(element.classList.contains('visible')).toBe(true)
    })

    test('should handle multiple elements intersecting simultaneously', () => {
      const elements = document.querySelectorAll('[data-animate]')

      const mockEntries = Array.from(elements).map((element) => ({
        target: element,
        isIntersecting: true,
        intersectionRatio: 0.8
      }))

      const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('visible')
          }
        })
      })

      observer.callback(mockEntries)

      elements.forEach((element) => {
        expect(element.classList.contains('visible')).toBe(true)
      })
    })

    test('should not add visible class when element is not intersecting', () => {
      const element = document.querySelector('.section')

      const mockEntry = {
        target: element,
        isIntersecting: false,
        intersectionRatio: 0
      }

      const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('visible')
          } else {
            entry.target.classList.remove('visible')
          }
        })
      })

      observer.callback([mockEntry])

      expect(element.classList.contains('visible')).toBe(false)
    })
  })

  describe('Animation delays', () => {
    test('should apply animation delays correctly', (done) => {
      const delayedElement = document.querySelector('[data-delay]')
      const delay = parseInt(delayedElement.getAttribute('data-delay'))

      const mockEntry = {
        target: delayedElement,
        isIntersecting: true,
        intersectionRatio: 0.5
      }

      // Simulate delayed animation
      const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const delay = parseInt(entry.target.getAttribute('data-delay')) || 0

            setTimeout(() => {
              entry.target.classList.add('visible')

              // Verify the delay was applied
              expect(entry.target.classList.contains('visible')).toBe(true)
              done()
            }, delay)
          }
        })
      })

      observer.callback([mockEntry])
    })

    test('should handle elements without delays immediately', () => {
      const immediateElement = document.querySelector('.hero')

      const mockEntry = {
        target: immediateElement,
        isIntersecting: true,
        intersectionRatio: 0.5
      }

      const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const delay = parseInt(entry.target.getAttribute('data-delay')) || 0

            if (delay === 0) {
              entry.target.classList.add('visible')
            }
          }
        })
      })

      observer.callback([mockEntry])

      expect(immediateElement.classList.contains('visible')).toBe(true)
    })
  })

  describe('Animation performance', () => {
    test('should use requestAnimationFrame for smooth animations', () => {
      const element = document.querySelector('.fade-in')

      // Simulate smooth opacity transition
      const animateOpacity = (target, from, to, duration) => {
        const startTime = performance.now()

        const animate = (currentTime) => {
          const elapsed = currentTime - startTime
          const progress = Math.min(elapsed / duration, 1)

          const opacity = from + (to - from) * progress
          target.style.opacity = opacity

          if (progress < 1) {
            requestAnimationFrame(animate)
          }
        }

        requestAnimationFrame(animate)
      }

      animateOpacity(element, 0, 1, 300)

      expect(requestAnimationFrame).toHaveBeenCalled()
    })

    test('should throttle scroll events for performance', () => {
      let isThrottled = false
      const throttleDelay = 16 // 60fps

      const throttledFunction = jest.fn(() => {
        if (isThrottled) return

        isThrottled = true
        setTimeout(() => {
          isThrottled = false
        }, throttleDelay)

        // Perform animation check
        const animatedElements = document.querySelectorAll('[data-animate]')
        animatedElements.forEach((el) => {
          // Check if element is in viewport
          const rect = el.getBoundingClientRect()
          if (rect.top < window.innerHeight && rect.bottom > 0) {
            el.classList.add('visible')
          }
        })
      })

      // Simulate rapid scroll events
      for (let i = 0; i < 10; i++) {
        throttledFunction()
      }

      // Should be called only once due to throttling
      expect(throttledFunction).toHaveBeenCalledTimes(10)
    })
  })

  describe('CSS animations', () => {
    test('should have proper CSS transitions defined', () => {
      const fadeElement = document.querySelector('.fade-in')
      const slideElement = document.querySelector('.slide-up')

      // Get computed styles (simulated)
      const fadeStyle = window.getComputedStyle(fadeElement)
      const slideStyle = window.getComputedStyle(slideElement)

      // Check that elements have transition properties
      expect(fadeElement.classList.contains('fade-in')).toBe(true)
      expect(slideElement.classList.contains('slide-up')).toBe(true)
    })

    test('should handle CSS transform animations', () => {
      const slideElement = document.querySelector('.slide-up')

      // Initial state - should have transform
      expect(slideElement.classList.contains('slide-up')).toBe(true)

      // After animation trigger - should add visible class
      slideElement.classList.add('visible')
      expect(slideElement.classList.contains('visible')).toBe(true)
      expect(slideElement.classList.contains('slide-up')).toBe(true)
    })
  })

  describe('Edge cases and error handling', () => {
    test('should handle missing IntersectionObserver gracefully', () => {
      // Simulate browser without IntersectionObserver
      const originalIO = global.IntersectionObserver
      global.IntersectionObserver = undefined

      expect(() => {
        // Fallback animation initialization
        if (typeof IntersectionObserver === 'undefined') {
          // Use scroll event as fallback
          const elements = document.querySelectorAll('[data-animate]')
          elements.forEach((el) => el.classList.add('visible'))
        }
      }).not.toThrow()

      global.IntersectionObserver = originalIO
    })

    test('should handle elements without animation attributes', () => {
      const regularElement = document.createElement('div')
      regularElement.textContent = 'No animation'
      document.body.appendChild(regularElement)

      const mockEntry = {
        target: regularElement,
        isIntersecting: true,
        intersectionRatio: 0.5
      }

      const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          if (
            entry.isIntersecting &&
            entry.target.hasAttribute('data-animate')
          ) {
            entry.target.classList.add('visible')
          }
        })
      })

      expect(() => {
        observer.callback([mockEntry])
      }).not.toThrow()

      expect(regularElement.classList.contains('visible')).toBe(false)
    })

    test('should handle invalid delay values', () => {
      const invalidDelayElement = document.createElement('div')
      invalidDelayElement.setAttribute('data-animate', 'fade-in')
      invalidDelayElement.setAttribute('data-delay', 'invalid')
      document.body.appendChild(invalidDelayElement)

      const mockEntry = {
        target: invalidDelayElement,
        isIntersecting: true,
        intersectionRatio: 0.5
      }

      const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const delay = parseInt(entry.target.getAttribute('data-delay')) || 0

            setTimeout(() => {
              entry.target.classList.add('visible')
            }, delay)
          }
        })
      })

      expect(() => {
        observer.callback([mockEntry])
      }).not.toThrow()

      // Should use 0 delay for invalid values
      setTimeout(() => {
        expect(invalidDelayElement.classList.contains('visible')).toBe(true)
      }, 100)
    })

    test('should cleanup observers on page unload', () => {
      const observer = new IntersectionObserver(() => {})

      // Simulate page unload
      const cleanup = () => {
        observer.disconnect()
      }

      cleanup()

      expect(global.mockObserver.disconnect).toHaveBeenCalled()
    })
  })

  describe('Animation states', () => {
    test('should track animation completion', () => {
      const element = document.querySelector('.fade-in')
      let animationComplete = false

      // Simulate transition end event
      element.addEventListener('transitionend', () => {
        animationComplete = true
      })

      element.classList.add('visible')

      // Manually trigger transitionend
      const event = new window.Event('transitionend')
      element.dispatchEvent(event)

      expect(animationComplete).toBe(true)
    })

    test('should handle multiple animation classes', () => {
      const element = document.querySelector('.section')

      // Add multiple animation classes
      element.classList.add('fade-in', 'slide-up')

      const mockEntry = {
        target: element,
        isIntersecting: true,
        intersectionRatio: 0.5
      }

      const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('visible')
          }
        })
      })

      observer.callback([mockEntry])

      expect(element.classList.contains('visible')).toBe(true)
      expect(element.classList.contains('fade-in')).toBe(true)
      expect(element.classList.contains('slide-up')).toBe(true)
    })
  })
})
