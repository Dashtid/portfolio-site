/**
 * Unit Tests for Actual AnimationManager Class
 * Tests the real implementation from theme.js with comprehensive scenarios
 */

/* eslint-env jest, node */
/* global AnimationManager */

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

    // Simulate entry intersection
    this.triggerIntersection = entries => {
      this.callback(entries)
    }
  })

// Evaluate the theme.js code in our test environment
// eslint-disable-next-line no-eval
eval(themeCode)

describe('AnimationManager (Real Implementation)', () => {
  let animationManager
  let mockSections
  let mockProgressBars
  let mockCards

  beforeEach(() => {
    // Reset DOM
    document.documentElement.innerHTML = ''
    document.head.innerHTML = ''
    document.body.innerHTML = ''

    // Create sections for scroll animations (Skills section removed from site)
    mockSections = [
      TestUtils.createMockElement('section', { id: 'about' }),
      TestUtils.createMockElement('section', { id: 'projects' })
    ]

    mockSections.forEach(section => {
      document.body.appendChild(section)
    })

    // Create progress bars for animation testing
    mockProgressBars = [
      TestUtils.createMockElement('div', {
        class: 'progress-bar',
        'aria-valuenow': '85'
      }),
      TestUtils.createMockElement('div', {
        class: 'progress-bar',
        'aria-valuenow': '70'
      }),
      TestUtils.createMockElement('div', {
        class: 'progress-bar',
        'aria-valuenow': '95'
      })
    ]

    // Add general progress bars to body
    mockProgressBars.forEach(bar => {
      document.body.appendChild(bar)
    })

    // Create cards for animation testing
    mockCards = [
      TestUtils.createMockElement('div', { class: 'card' }),
      TestUtils.createMockElement('div', { class: 'card' }),
      TestUtils.createMockElement('div', { class: 'card' })
    ]

    mockCards.forEach(card => {
      document.body.appendChild(card)
    })

    // Setup timers
    jest.useFakeTimers()

    // Reset mocks
    jest.clearAllMocks()
  })

  afterEach(() => {
    // Clean up DOM
    document.body.innerHTML = ''
    jest.useRealTimers()
    jest.clearAllMocks()
  })

  describe('Constructor and Initialization', () => {
    test('should initialize with empty animated elements set', () => {
      animationManager = new AnimationManager()

      expect(animationManager.animatedElements).toBeInstanceOf(Set)
      expect(animationManager.animatedElements.size).toBe(0)
    })

    test('should call all initialization methods', () => {
      const setupScrollAnimationsSpy = jest.spyOn(
        AnimationManager.prototype,
        'setupScrollAnimations'
      )
      const animateProgressBarsSpy = jest.spyOn(
        AnimationManager.prototype,
        'animateProgressBars'
      )
      const setupCardAnimationsSpy = jest.spyOn(
        AnimationManager.prototype,
        'setupCardAnimations'
      )

      animationManager = new AnimationManager()

      expect(setupScrollAnimationsSpy).toHaveBeenCalled()
      expect(animateProgressBarsSpy).toHaveBeenCalled()
      expect(setupCardAnimationsSpy).toHaveBeenCalled()

      setupScrollAnimationsSpy.mockRestore()
      animateProgressBarsSpy.mockRestore()
      setupCardAnimationsSpy.mockRestore()
    })

    test('should create intersection observers for different element types', () => {
      animationManager = new AnimationManager()

      // Should create observers for sections, progress bars, and cards
      expect(IntersectionObserver).toHaveBeenCalledTimes(3)
    })
  })

  describe('Section Scroll Animations', () => {
    beforeEach(() => {
      animationManager = new AnimationManager()
    })

    test('should add section-animate class to all sections', () => {
      mockSections.forEach(section => {
        expect(section.classList.add).toHaveBeenCalledWith('section-animate')
      })
    })

    test('should create intersection observer with correct options for sections', () => {
      const sectionObserverCall = IntersectionObserver.mock.calls[0]

      expect(sectionObserverCall[1]).toEqual({
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
      })
    })

    test('should observe all sections', () => {
      const sectionObserver = IntersectionObserver.mock.instances[0]

      expect(sectionObserver.observe).toHaveBeenCalledTimes(mockSections.length)
      mockSections.forEach(section => {
        expect(sectionObserver.observe).toHaveBeenCalledWith(section)
      })
    })

    test('should animate sections when they intersect', () => {
      const sectionObserver = IntersectionObserver.mock.instances[0]

      const mockEntry = {
        isIntersecting: true,
        target: mockSections[0]
      }

      sectionObserver.triggerIntersection([mockEntry])

      expect(mockSections[0].classList.add).toHaveBeenCalledWith(
        'section-animate',
        'visible'
      )
    })

    test('should not trigger skills animation for non-skills sections', () => {
      // Skills section was removed, so animateSkillsBars should never be called
      const animateSkillsBarsSpy = jest.spyOn(
        animationManager,
        'animateSkillsBars'
      )
      const sectionObserver = IntersectionObserver.mock.instances[0]

      // Test with actual sections (about, projects)
      mockSections.forEach(section => {
        const mockEntry = {
          isIntersecting: true,
          target: section
        }
        sectionObserver.triggerIntersection([mockEntry])
      })

      // animateSkillsBars should NOT be called for any section
      expect(animateSkillsBarsSpy).not.toHaveBeenCalled()
    })

    test('should not animate sections when they are not intersecting', () => {
      const sectionObserver = IntersectionObserver.mock.instances[0]

      const mockEntry = {
        isIntersecting: false,
        target: mockSections[0]
      }

      // Clear previous calls
      jest.clearAllMocks()

      sectionObserver.triggerIntersection([mockEntry])

      expect(mockSections[0].classList.add).not.toHaveBeenCalledWith('visible')
    })
  })

  describe('Skills Progress Bar Animation', () => {
    beforeEach(() => {
      animationManager = new AnimationManager()
    })

    test('should handle animateSkillsBars when no skills section exists', () => {
      // Skills section was removed from the site, so this tests realistic behavior
      // Method should not crash when no elements are found
      expect(() => {
        animationManager.animateSkillsBars()
      }).not.toThrow()

      // Verify no elements are found (realistic scenario)
      const skillsBars = document.querySelectorAll('#skills .progress-bar')
      expect(skillsBars.length).toBe(0)
    })

    test('should handle skills section with no progress bars', () => {
      // Skills section doesn't exist, so this already tests the realistic scenario
      expect(() => {
        animationManager.animateSkillsBars()
      }).not.toThrow()

      // Verify querySelector finds no elements
      const skillsBars = document.querySelectorAll('#skills .progress-bar')
      expect(skillsBars.length).toBe(0)
    })
  })

  describe('Progress Bar Animation', () => {
    beforeEach(() => {
      animationManager = new AnimationManager()
    })

    test('should create intersection observer for progress bars', () => {
      const progressBarObserverCall = IntersectionObserver.mock.calls[1]

      expect(progressBarObserverCall[1]).toEqual({ threshold: 0.5 })
    })

    test('should observe all progress bars', () => {
      const progressBarObserver = IntersectionObserver.mock.instances[1]

      expect(progressBarObserver.observe).toHaveBeenCalledTimes(
        mockProgressBars.length
      )
      mockProgressBars.forEach(bar => {
        expect(progressBarObserver.observe).toHaveBeenCalledWith(bar)
      })
    })

    test('should animate progress bar when it intersects for the first time', () => {
      const progressBarObserver = IntersectionObserver.mock.instances[1]
      const targetBar = mockProgressBars[0]

      const mockEntry = {
        isIntersecting: true,
        target: targetBar
      }

      progressBarObserver.triggerIntersection([mockEntry])

      // Should reset width to 0%
      expect(targetBar.style.width).toBe('0%')

      // Should animate to target width after delay
      jest.advanceTimersByTime(200)
      expect(targetBar.style.width).toBe('85%')

      // Should track as animated
      expect(animationManager.animatedElements.has(targetBar)).toBe(true)
    })

    test('should not animate same progress bar twice', () => {
      const progressBarObserver = IntersectionObserver.mock.instances[1]
      const targetBar = mockProgressBars[0]

      // Add to animated elements to simulate previous animation
      animationManager.animatedElements.add(targetBar)
      targetBar.style.width = '50%'

      const mockEntry = {
        isIntersecting: true,
        target: targetBar
      }

      progressBarObserver.triggerIntersection([mockEntry])

      // Width should remain unchanged
      expect(targetBar.style.width).toBe('50%')
    })

    test('should handle progress bars without aria-valuenow attribute', () => {
      const barWithoutValue = TestUtils.createMockElement('div', {
        class: 'progress-bar'
      })
      document.body.appendChild(barWithoutValue)

      const progressBarObserver = IntersectionObserver.mock.instances[1]

      const mockEntry = {
        isIntersecting: true,
        target: barWithoutValue
      }

      expect(() => {
        progressBarObserver.triggerIntersection([mockEntry])
      }).not.toThrow()
    })

    test('should not animate when progress bar is not intersecting', () => {
      const progressBarObserver = IntersectionObserver.mock.instances[1]
      const targetBar = mockProgressBars[0]
      const initialWidth = targetBar.style.width

      const mockEntry = {
        isIntersecting: false,
        target: targetBar
      }

      progressBarObserver.triggerIntersection([mockEntry])

      expect(targetBar.style.width).toBe(initialWidth)
      expect(animationManager.animatedElements.has(targetBar)).toBe(false)
    })
  })

  describe('Card Animation', () => {
    beforeEach(() => {
      animationManager = new AnimationManager()
    })

    test('should create intersection observer for cards', () => {
      const cardObserverCall = IntersectionObserver.mock.calls[2]

      expect(cardObserverCall[1]).toEqual({ threshold: 0.1 })
    })

    test('should observe all cards', () => {
      const cardObserver = IntersectionObserver.mock.instances[2]

      expect(cardObserver.observe).toHaveBeenCalledTimes(mockCards.length)
      mockCards.forEach(card => {
        expect(cardObserver.observe).toHaveBeenCalledWith(card)
      })
    })

    test('should add fade-in class to cards when they intersect for the first time', () => {
      const cardObserver = IntersectionObserver.mock.instances[2]
      const targetCard = mockCards[0]

      const mockEntry = {
        isIntersecting: true,
        target: targetCard
      }

      cardObserver.triggerIntersection([mockEntry])

      expect(targetCard.classList.add).toHaveBeenCalledWith('fade-in')
      expect(animationManager.animatedElements.has(targetCard)).toBe(true)
    })

    test('should not animate same card twice', () => {
      const cardObserver = IntersectionObserver.mock.instances[2]
      const targetCard = mockCards[0]

      // Add to animated elements
      animationManager.animatedElements.add(targetCard)

      const mockEntry = {
        isIntersecting: true,
        target: targetCard
      }

      // Clear previous calls
      jest.clearAllMocks()

      cardObserver.triggerIntersection([mockEntry])

      expect(targetCard.classList.add).not.toHaveBeenCalledWith('fade-in')
    })

    test('should not animate cards when they are not intersecting', () => {
      const cardObserver = IntersectionObserver.mock.instances[2]
      const targetCard = mockCards[0]

      const mockEntry = {
        isIntersecting: false,
        target: targetCard
      }

      cardObserver.triggerIntersection([mockEntry])

      expect(targetCard.classList.add).not.toHaveBeenCalledWith('fade-in')
      expect(animationManager.animatedElements.has(targetCard)).toBe(false)
    })
  })

  describe('Loading State Management', () => {
    test('should show loading spinner with proper structure', () => {
      const mockElement = document.createElement('div')
      document.body.appendChild(mockElement)

      animationManager = new AnimationManager()
      animationManager.showLoading(mockElement)

      expect(mockElement.innerHTML).toContain('spinner-border')
      expect(mockElement.innerHTML).toContain('text-primary')
      expect(mockElement.innerHTML).toContain('Loading...')
      expect(mockElement.innerHTML).toContain('Loading content...')
    })

    test('should handle showLoading with null element', () => {
      animationManager = new AnimationManager()

      expect(() => {
        animationManager.showLoading(null)
      }).not.toThrow()
    })

    test('should hide loading spinner correctly', () => {
      const mockElement = document.createElement('div')
      mockElement.innerHTML = `
        <div class="d-flex">
          <div class="spinner-border"></div>
        </div>
      `
      document.body.appendChild(mockElement)

      animationManager = new AnimationManager()
      animationManager.hideLoading(mockElement)

      expect(mockElement.querySelector('.spinner-border')).toBeNull()
    })

    test('should handle hideLoading with null element', () => {
      animationManager = new AnimationManager()

      expect(() => {
        animationManager.hideLoading(null)
      }).not.toThrow()
    })

    test('should handle hideLoading when no spinner exists', () => {
      const mockElement = document.createElement('div')
      mockElement.innerHTML = '<p>No spinner here</p>'
      document.body.appendChild(mockElement)

      animationManager = new AnimationManager()

      expect(() => {
        animationManager.hideLoading(mockElement)
      }).not.toThrow()
    })
  })

  describe('Content Reveal Animation', () => {
    beforeEach(() => {
      animationManager = new AnimationManager()
    })

    test('should reveal content with fade-in effect', () => {
      const mockElement = document.createElement('div')
      document.body.appendChild(mockElement)

      const content = '<p>New content</p>'

      animationManager.revealContent(mockElement, content)

      expect(mockElement.style.opacity).toBe('0')
      expect(mockElement.innerHTML).toBe(content)

      jest.advanceTimersByTime(50)
      expect(mockElement.style.transition).toBe('opacity 0.3s ease-in-out')
      expect(mockElement.style.opacity).toBe('1')
    })

    test('should handle revealContent with empty content', () => {
      const mockElement = document.createElement('div')
      document.body.appendChild(mockElement)

      expect(() => {
        animationManager.revealContent(mockElement, '')
      }).not.toThrow()

      expect(mockElement.innerHTML).toBe('')
    })

    test('should throw when revealContent receives null element', () => {
      // Real implementation doesn't have null checks, so it throws
      expect(() => {
        animationManager.revealContent(null, 'content')
      }).toThrow()
    })
  })

  describe('Performance and Error Handling', () => {
    test('should handle missing DOM elements gracefully during initialization', () => {
      // Remove all elements
      document.body.innerHTML = ''

      expect(() => {
        animationManager = new AnimationManager()
      }).not.toThrow()

      // Should still initialize with empty sets
      expect(animationManager.animatedElements).toBeInstanceOf(Set)
    })

    test('should prevent duplicate animations with Set tracking', () => {
      animationManager = new AnimationManager()
      const targetElement = mockProgressBars[0]

      animationManager.animatedElements.add(targetElement)
      expect(animationManager.animatedElements.has(targetElement)).toBe(true)
      expect(animationManager.animatedElements.size).toBe(1)

      // Adding same element again should not increase size
      animationManager.animatedElements.add(targetElement)
      expect(animationManager.animatedElements.size).toBe(1)
    })

    test('should throw when intersection observer receives null target', () => {
      // Real implementation doesn't validate entry.target before use
      animationManager = new AnimationManager()
      const sectionObserver = IntersectionObserver.mock.instances[0]

      const badEntry = {
        isIntersecting: true,
        target: null
      }

      expect(() => {
        sectionObserver.triggerIntersection([badEntry])
      }).toThrow()
    })

    test('should not error when skills section does not exist', () => {
      // Skills section removed from site - realistic scenario has no elements
      animationManager = new AnimationManager()

      // With no skills section, animateSkillsBars finds no elements and completes without error
      expect(() => {
        animationManager.animateSkillsBars()
      }).not.toThrow()

      // Verify no elements are found
      const skillsBars = document.querySelectorAll('#skills .progress-bar')
      expect(skillsBars.length).toBe(0)
    })
  })

  describe('Animation Timing and Coordination', () => {
    beforeEach(() => {
      animationManager = new AnimationManager()
    })

    test('should handle animateSkillsBars with no skills section', () => {
      // Skills section removed from site - verify no crash when no elements found
      expect(() => {
        animationManager.animateSkillsBars()
      }).not.toThrow()

      // Advance timers to ensure no errors occur
      jest.advanceTimersByTime(1000)
    })

    test('should use consistent timing for progress bar animations', () => {
      const progressBarObserver = IntersectionObserver.mock.instances[1]
      const targetBar = mockProgressBars[0]

      const mockEntry = {
        isIntersecting: true,
        target: targetBar
      }

      progressBarObserver.triggerIntersection([mockEntry])

      // Should have 200ms delay
      jest.advanceTimersByTime(199)
      expect(targetBar.style.width).toBe('0%')

      jest.advanceTimersByTime(1)
      expect(targetBar.style.width).toBe('85%')
    })

    test('should use consistent timing for content reveal', () => {
      const mockElement = document.createElement('div')
      document.body.appendChild(mockElement)

      animationManager.revealContent(mockElement, '<p>Test</p>')

      expect(mockElement.style.opacity).toBe('0')

      // Should have 50ms delay
      jest.advanceTimersByTime(49)
      expect(mockElement.style.opacity).toBe('0')

      jest.advanceTimersByTime(1)
      expect(mockElement.style.opacity).toBe('1')
    })
  })

  describe('Integration with Real DOM Behavior', () => {
    test('should work with actual DOM queries', () => {
      // Test with sections that actually exist (about, projects)
      const realSection = document.createElement('section')
      realSection.id = 'about'
      document.body.appendChild(realSection)

      const realProgressBar = document.createElement('div')
      realProgressBar.className = 'progress-bar'
      realProgressBar.setAttribute('aria-valuenow', '75')
      realProgressBar.style.width = '75%'
      document.body.appendChild(realProgressBar)

      animationManager = new AnimationManager()

      // Test that real DOM queries work for actual sections
      const sections = document.querySelectorAll('section')
      expect(sections.length).toBeGreaterThan(0)

      // Test that progress bars can be found
      const progressBars = document.querySelectorAll('.progress-bar')
      expect(progressBars.length).toBeGreaterThan(0)
    })

    test('should handle multiple intersection observers working together', () => {
      animationManager = new AnimationManager()

      // All observers should be created
      expect(IntersectionObserver).toHaveBeenCalledTimes(3)

      const sectionObserver = IntersectionObserver.mock.instances[0]
      const progressBarObserver = IntersectionObserver.mock.instances[1]
      const cardObserver = IntersectionObserver.mock.instances[2]

      // Trigger all types of intersections
      sectionObserver.triggerIntersection([
        {
          isIntersecting: true,
          target: mockSections[0]
        }
      ])

      progressBarObserver.triggerIntersection([
        {
          isIntersecting: true,
          target: mockProgressBars[0]
        }
      ])

      cardObserver.triggerIntersection([
        {
          isIntersecting: true,
          target: mockCards[0]
        }
      ])

      // All should work independently
      expect(mockSections[0].classList.add).toHaveBeenCalledWith(
        'section-animate',
        'visible'
      )
      expect(mockProgressBars[0].style.width).toBe('0%')
      expect(mockCards[0].classList.add).toHaveBeenCalledWith('fade-in')
    })
  })
})
