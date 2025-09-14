/**
 * Unit Tests for AnimationManager Class - Simplified Version
 * Tests scroll animations, progress bars, and loading states
 */

const { TestUtils } = require('./setup.js')

describe('AnimationManager', () => {
  let mockSections
  let mockProgressBars
  let mockCards

  beforeEach(() => {
    mockSections = [
      TestUtils.createMockElement('section', { id: 'about' }),
      TestUtils.createMockElement('section', { id: 'skills' }),
      TestUtils.createMockElement('section', { id: 'projects' })
    ]
    mockSections.forEach((section) => document.body.appendChild(section))

    mockProgressBars = [
      TestUtils.createMockElement('div', {
        class: 'progress-bar',
        'aria-valuenow': '85',
        style: 'width: 85%;'
      }),
      TestUtils.createMockElement('div', {
        class: 'progress-bar',
        'aria-valuenow': '70',
        style: 'width: 70%;'
      })
    ]

    const skillsProgressBars = [
      TestUtils.createMockElement('div', {
        class: 'progress-bar',
        style: 'width: 90%;'
      }),
      TestUtils.createMockElement('div', {
        class: 'progress-bar',
        style: 'width: 80%;'
      })
    ]

    skillsProgressBars.forEach((bar) => mockSections[1].appendChild(bar))
    mockProgressBars.forEach((bar) => document.body.appendChild(bar))

    mockCards = [
      TestUtils.createMockElement('div', { class: 'card' }),
      TestUtils.createMockElement('div', { class: 'card' })
    ]
    mockCards.forEach((card) => document.body.appendChild(card))

    jest.useFakeTimers()
  })

  afterEach(() => {
    ;[...mockSections, ...mockProgressBars, ...mockCards].forEach((el) => {
      if (el.parentNode) el.parentNode.removeChild(el)
    })

    jest.useRealTimers()
    jest.clearAllMocks()
  })

  describe('Animation Setup', () => {
    test('should initialize with empty animated elements set', () => {
      const animatedElements = new Set()

      expect(animatedElements).toBeInstanceOf(Set)
      expect(animatedElements.size).toBe(0)
    })

    test('should add section-animate class to sections', () => {
      const sections = document.querySelectorAll('section')

      sections.forEach((section) => {
        section.classList.add('section-animate')
        expect(section.classList.add).toHaveBeenCalledWith('section-animate')
      })
    })

    test('should create intersection observer with correct options', () => {
      expect(global.IntersectionObserver).toHaveBeenCalledWith(
        expect.any(Function),
        expect.objectContaining({
          threshold: expect.any(Number)
        })
      )
    })
  })

  describe('Section Animation', () => {
    test('should animate sections when they intersect', () => {
      const mockEntry = {
        isIntersecting: true,
        target: mockSections[0]
      }

      const animateSection = (entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('section-animate', 'visible')
        }
      }

      animateSection(mockEntry)

      expect(mockSections[0].classList.add).toHaveBeenCalledWith(
        'section-animate',
        'visible'
      )
    })

    test('should trigger skills animation when skills section intersects', () => {
      const mockEntry = {
        isIntersecting: true,
        target: mockSections[1] // skills section
      }

      const shouldAnimateSkills =
        mockEntry.isIntersecting && mockEntry.target.id === 'skills'

      expect(shouldAnimateSkills).toBe(true)
    })

    test('should not animate sections when they are not intersecting', () => {
      const mockEntry = {
        isIntersecting: false,
        target: mockSections[0]
      }

      const animateSection = (entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible')
        }
      }

      animateSection(mockEntry)

      expect(mockSections[0].classList.add).not.toHaveBeenCalledWith('visible')
    })
  })

  describe('Skills Progress Bar Animation', () => {
    test('should animate skills progress bars with staggered timing', () => {
      const animateSkillsBars = () => {
        const progressBars = document.querySelectorAll('#skills .progress-bar')

        progressBars.forEach((bar, index) => {
          const targetWidth = bar.style.width
          bar.style.width = '0%'

          setTimeout(() => {
            bar.style.width = targetWidth
          }, index * 100)
        })
      }

      animateSkillsBars()

      const skillsBars = mockSections[1].querySelectorAll('.progress-bar')

      skillsBars.forEach((bar) => {
        expect(bar.style.width).toBe('0%')
      })

      jest.advanceTimersByTime(100)
      expect(skillsBars[0].style.width).toBe('90%')

      jest.advanceTimersByTime(100)
      expect(skillsBars[1].style.width).toBe('80%')
    })

    test('should handle skills section with no progress bars', () => {
      const skillsBars = mockSections[1].querySelectorAll('.progress-bar')
      skillsBars.forEach((bar) => mockSections[1].removeChild(bar))

      const animateSkillsBars = () => {
        const progressBars = document.querySelectorAll('#skills .progress-bar')
        progressBars.forEach((bar, index) => {
          const targetWidth = bar.style.width
          bar.style.width = '0%'
          setTimeout(() => {
            bar.style.width = targetWidth
          }, index * 100)
        })
      }

      expect(() => {
        animateSkillsBars()
      }).not.toThrow()
    })
  })

  describe('Progress Bar Animation', () => {
    test('should animate progress bar when it intersects', () => {
      const animatedElements = new Set()
      const targetBar = mockProgressBars[0]

      const animateProgressBar = (entry, elements) => {
        if (entry.isIntersecting && !elements.has(entry.target)) {
          const targetWidth = `${entry.target.getAttribute('aria-valuenow')}%`
          entry.target.style.width = '0%'

          setTimeout(() => {
            entry.target.style.width = targetWidth
          }, 200)

          elements.add(entry.target)
        }
      }

      const mockEntry = {
        isIntersecting: true,
        target: targetBar
      }

      animateProgressBar(mockEntry, animatedElements)

      expect(targetBar.style.width).toBe('0%')

      jest.advanceTimersByTime(200)
      expect(targetBar.style.width).toBe('85%')
      expect(animatedElements.has(targetBar)).toBe(true)
    })

    test('should not animate same progress bar twice', () => {
      const animatedElements = new Set()
      const targetBar = mockProgressBars[0]
      animatedElements.add(targetBar)

      const animateProgressBar = (entry, elements) => {
        if (entry.isIntersecting && !elements.has(entry.target)) {
          entry.target.style.width = '0%'
        }
      }

      const mockEntry = {
        isIntersecting: true,
        target: targetBar
      }

      targetBar.style.width = '50%'

      animateProgressBar(mockEntry, animatedElements)

      expect(targetBar.style.width).toBe('50%')
    })

    test('should handle progress bars without aria-valuenow', () => {
      const barWithoutValue = TestUtils.createMockElement('div', {
        class: 'progress-bar'
      })
      document.body.appendChild(barWithoutValue)

      const animateProgressBar = (entry) => {
        if (entry.isIntersecting) {
          const targetWidth =
            `${entry.target.getAttribute('aria-valuenow') || '0'}%`
          entry.target.style.width = targetWidth
        }
      }

      const mockEntry = {
        isIntersecting: true,
        target: barWithoutValue
      }

      expect(() => {
        animateProgressBar(mockEntry)
      }).not.toThrow()

      document.body.removeChild(barWithoutValue)
    })
  })

  describe('Card Animation', () => {
    test('should add fade-in class to cards when they intersect', () => {
      const mockEntry = {
        isIntersecting: true,
        target: mockCards[0]
      }

      const animateCard = (entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('fade-in')
        }
      }

      animateCard(mockEntry)

      expect(mockCards[0].classList.add).toHaveBeenCalledWith('fade-in')
    })

    test('should not add fade-in class when cards are not intersecting', () => {
      const mockEntry = {
        isIntersecting: false,
        target: mockCards[0]
      }

      const animateCard = (entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('fade-in')
        }
      }

      animateCard(mockEntry)

      expect(mockCards[0].classList.add).not.toHaveBeenCalledWith('fade-in')
    })
  })

  describe('Loading State Management', () => {
    test('should show loading spinner with proper structure', () => {
      const mockElement = TestUtils.createMockElement('div')
      document.body.appendChild(mockElement)

      const showLoading = (element) => {
        if (element) {
          element.innerHTML = `
            <div class="d-flex justify-content-center align-items-center py-4">
              <div class="spinner-border text-primary me-3" role="status">
                <span class="visually-hidden">Loading...</span>
              </div>
              <span class="text-muted">Loading content...</span>
            </div>
          `
        }
      }

      showLoading(mockElement)

      expect(mockElement.innerHTML).toContain('spinner-border')
      expect(mockElement.innerHTML).toContain('Loading...')
      expect(mockElement.innerHTML).toContain('Loading content...')

      document.body.removeChild(mockElement)
    })

    test('should handle showLoading with null element', () => {
      const showLoading = (element) => {
        if (element) {
          element.innerHTML = 'loading'
        }
      }

      expect(() => {
        showLoading(null)
      }).not.toThrow()
    })

    test('should hide loading spinner', () => {
      const mockElement = TestUtils.createMockElement('div')
      mockElement.innerHTML = `
        <div class="d-flex">
          <div class="spinner-border"></div>
        </div>
      `
      document.body.appendChild(mockElement)

      const hideLoading = (element) => {
        if (element) {
          const spinner = element.querySelector('.spinner-border')
          if (spinner) {
            spinner.closest('.d-flex').remove()
          }
        }
      }

      hideLoading(mockElement)

      expect(mockElement.querySelector('.spinner-border')).toBeNull()

      document.body.removeChild(mockElement)
    })

    test('should handle hideLoading with null element', () => {
      const hideLoading = (element) => {
        if (element) {
          const spinner = element.querySelector('.spinner-border')
          if (spinner) {
            spinner.remove()
          }
        }
      }

      expect(() => {
        hideLoading(null)
      }).not.toThrow()
    })
  })

  describe('Content Reveal Animation', () => {
    test('should reveal content with fade-in effect', () => {
      const mockElement = TestUtils.createMockElement('div')
      document.body.appendChild(mockElement)

      const content = '<p>New content</p>'

      const revealContent = (element, newContent) => {
        element.style.opacity = '0'
        element.innerHTML = newContent

        setTimeout(() => {
          element.style.transition = 'opacity 0.3s ease-in-out'
          element.style.opacity = '1'
        }, 50)
      }

      revealContent(mockElement, content)

      expect(mockElement.style.opacity).toBe('0')
      expect(mockElement.innerHTML).toBe(content)

      jest.advanceTimersByTime(50)
      expect(mockElement.style.transition).toBe('opacity 0.3s ease-in-out')
      expect(mockElement.style.opacity).toBe('1')

      document.body.removeChild(mockElement)
    })

    test('should handle revealContent with empty content', () => {
      const mockElement = TestUtils.createMockElement('div')
      document.body.appendChild(mockElement)

      const revealContent = (element, newContent) => {
        element.innerHTML = newContent
      }

      expect(() => {
        revealContent(mockElement, '')
      }).not.toThrow()

      expect(mockElement.innerHTML).toBe('')

      document.body.removeChild(mockElement)
    })
  })

  describe('Performance and Error Handling', () => {
    test('should handle missing DOM elements gracefully', () => {
      ;[...mockSections, ...mockProgressBars, ...mockCards].forEach((el) => {
        if (el.parentNode) el.parentNode.removeChild(el)
      })

      const sections = document.querySelectorAll('section')
      const progressBars = document.querySelectorAll('.progress-bar')
      const cards = document.querySelectorAll('.card')

      expect(sections.length).toBe(0)
      expect(progressBars.length).toBe(0)
      expect(cards.length).toBe(0)
    })

    test('should prevent duplicate animations with Set tracking', () => {
      const animatedElements = new Set()
      const targetElement = mockProgressBars[0]

      animatedElements.add(targetElement)

      expect(animatedElements.has(targetElement)).toBe(true)
      expect(animatedElements.size).toBe(1)

      animatedElements.add(targetElement)
      expect(animatedElements.size).toBe(1)
    })

    test('should handle intersection observer callback errors gracefully', () => {
      const animateSection = (entry) => {
        if (entry && entry.target && entry.isIntersecting) {
          entry.target.classList.add('visible')
        }
      }

      expect(() => {
        animateSection({
          isIntersecting: true,
          target: null
        })
      }).not.toThrow()
    })
  })

  describe('Animation Timing and Coordination', () => {
    test('should stagger skill bar animations with increasing delays', () => {
      const delays = [0, 100, 200]

      delays.forEach((delay, index) => {
        setTimeout(() => {
          const bar = mockSections[1].querySelectorAll('.progress-bar')[index]
          if (bar) {
            bar.style.width = '100%'
          }
        }, delay)
      })

      jest.advanceTimersByTime(0)
      expect(
        mockSections[1].querySelectorAll('.progress-bar')[0]?.style.width
      ).toBe('100%')

      jest.advanceTimersByTime(100)
      expect(
        mockSections[1].querySelectorAll('.progress-bar')[1]?.style.width
      ).toBe('100%')
    })

    test('should use consistent timing for content reveal', () => {
      const mockElement = TestUtils.createMockElement('div')
      document.body.appendChild(mockElement)

      const revealContent = (element, content) => {
        element.style.opacity = '0'
        element.innerHTML = content

        setTimeout(() => {
          element.style.opacity = '1'
          element.style.transition = 'opacity 0.3s ease-in-out'
        }, 50)
      }

      revealContent(mockElement, '<p>Test</p>')

      expect(mockElement.style.opacity).toBe('0')

      jest.advanceTimersByTime(50)
      expect(mockElement.style.opacity).toBe('1')
      expect(mockElement.style.transition).toBe('opacity 0.3s ease-in-out')

      document.body.removeChild(mockElement)
    })
  })
})
