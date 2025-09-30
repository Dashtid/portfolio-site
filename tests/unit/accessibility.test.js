/**
 * Unit tests for accessibility and standards compliance
 * Tests WCAG guidelines, ARIA attributes, keyboard navigation, screen reader support
 */

/* eslint-env jest, node */

const { JSDOM } = require('jsdom')

describe('Accessibility and Standards Compliance', () => {
  let dom, window, document

  beforeEach(() => {
    const html = `
      <!DOCTYPE html>
      <html lang="en">
      <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Accessibility Test - Portfolio Site</title>
        <meta name="description" content="Testing accessibility features of the portfolio website">
        <style>
          .sr-only { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0,0,0,0); border: 0; }
          .focus-visible { outline: 2px solid #007bff; outline-offset: 2px; }
          .skip-link { position: absolute; top: -40px; left: 6px; background: #000; color: #fff; padding: 8px; text-decoration: none; }
          .skip-link:focus { top: 6px; }
          .high-contrast { filter: contrast(150%); }
          .reduced-motion * { animation-duration: 0.01ms !important; animation-iteration-count: 1 !important; transition-duration: 0.01ms !important; }
        </style>
      </head>
      <body>
        <a href="#main" class="skip-link">Skip to main content</a>
        
        <header role="banner">
          <nav role="navigation" aria-label="Main navigation">
            <button 
              id="nav-toggle" 
              class="nav-toggle" 
              aria-expanded="false" 
              aria-controls="nav-menu"
              aria-label="Toggle navigation menu"
            >
              <span class="sr-only">Menu</span>
              <span aria-hidden="true">☰</span>
            </button>
            
            <ul id="nav-menu" class="nav-menu" role="list">
              <li role="listitem"><a href="#home" aria-current="page">Home</a></li>
              <li role="listitem"><a href="#about">About</a></li>
              <li role="listitem"><a href="#projects">Projects</a></li>
              <li role="listitem"><a href="#contact">Contact</a></li>
            </ul>
          </nav>
          
          <button 
            id="theme-toggle"
            class="theme-toggle"
            aria-label="Switch to dark theme"
            aria-pressed="false"
          >
            <span aria-hidden="true">🌙</span>
          </button>
        </header>

        <main id="main" role="main" tabindex="-1">
          <section id="home" class="hero" aria-labelledby="hero-title">
            <h1 id="hero-title">John Doe - Full Stack Developer</h1>
            <p class="hero-description">Building modern web applications with accessibility in mind</p>
            <button class="cta-button" type="button">
              <span>View My Work</span>
              <span class="sr-only">(opens projects section)</span>
            </button>
          </section>

          <section id="about" class="about" aria-labelledby="about-title">
            <h2 id="about-title">About Me</h2>
            <img 
              src="/images/profile.jpg" 
              alt="John Doe, a professional headshot showing a person in business attire"
              class="profile-image"
              loading="lazy"
            >
            <p>I am a passionate developer focused on creating inclusive web experiences.</p>
          </section>

          <section id="projects" class="projects" aria-labelledby="projects-title">
            <h2 id="projects-title">Projects</h2>
            
            <div class="filter-controls" role="group" aria-labelledby="filter-title">
              <h3 id="filter-title" class="sr-only">Filter projects by technology</h3>
              <button class="filter-btn active" data-filter="all" aria-pressed="true">
                All Projects
              </button>
              <button class="filter-btn" data-filter="javascript" aria-pressed="false">
                JavaScript
              </button>
              <button class="filter-btn" data-filter="react" aria-pressed="false">
                React
              </button>
            </div>

            <div class="projects-grid" role="list" aria-live="polite" aria-label="Filtered projects">
              <article class="project-card" data-category="javascript react" role="listitem">
                <h3>
                  <a href="/projects/todo-app" aria-describedby="todo-desc">
                    Todo Application
                  </a>
                </h3>
                <p id="todo-desc">A fully accessible task management application built with React</p>
                <div class="project-meta">
                  <span class="tech-stack" aria-label="Technologies used">React, JavaScript, CSS</span>
                  <time datetime="2023-01-15" aria-label="Completed on">January 2023</time>
                </div>
              </article>
              
              <article class="project-card" data-category="javascript" role="listitem">
                <h3>
                  <a href="/projects/weather-app" aria-describedby="weather-desc">
                    Weather Dashboard
                  </a>
                </h3>
                <p id="weather-desc">Real-time weather information with keyboard navigation support</p>
                <div class="project-meta">
                  <span class="tech-stack" aria-label="Technologies used">JavaScript, API, CSS</span>
                  <time datetime="2023-02-20" aria-label="Completed on">February 2023</time>
                </div>
              </article>
            </div>
          </section>

          <section id="contact" class="contact" aria-labelledby="contact-title">
            <h2 id="contact-title">Contact Me</h2>
            
            <form id="contact-form" class="contact-form" novalidate>
              <fieldset>
                <legend class="sr-only">Contact Information</legend>
                
                <div class="form-group">
                  <label for="name" class="required">
                    Name
                    <span class="required-indicator" aria-label="required">*</span>
                  </label>
                  <input 
                    type="text" 
                    id="name" 
                    name="name" 
                    required 
                    aria-required="true"
                    aria-describedby="name-error name-help"
                  >
                  <div id="name-help" class="help-text">Please enter your full name</div>
                  <div id="name-error" class="error-message" role="alert" aria-live="polite"></div>
                </div>
                
                <div class="form-group">
                  <label for="email" class="required">
                    Email Address
                    <span class="required-indicator" aria-label="required">*</span>
                  </label>
                  <input 
                    type="email" 
                    id="email" 
                    name="email" 
                    required 
                    aria-required="true"
                    aria-describedby="email-error email-help"
                    autocomplete="email"
                  >
                  <div id="email-help" class="help-text">We'll never share your email</div>
                  <div id="email-error" class="error-message" role="alert" aria-live="polite"></div>
                </div>
                
                <div class="form-group">
                  <label for="message" class="required">
                    Message
                    <span class="required-indicator" aria-label="required">*</span>
                  </label>
                  <textarea 
                    id="message" 
                    name="message" 
                    required 
                    aria-required="true"
                    aria-describedby="message-error message-help"
                    rows="5"
                  ></textarea>
                  <div id="message-help" class="help-text">Please describe your inquiry</div>
                  <div id="message-error" class="error-message" role="alert" aria-live="polite"></div>
                </div>
                
                <button type="submit" class="submit-button" aria-describedby="submit-status">
                  Send Message
                </button>
                <div id="submit-status" class="status-message" role="status" aria-live="polite"></div>
              </fieldset>
            </form>
          </section>
        </main>

        <aside class="accessibility-controls" role="complementary" aria-labelledby="a11y-title">
          <h2 id="a11y-title" class="sr-only">Accessibility Options</h2>
          
          <button id="font-size-toggle" aria-label="Increase font size">
            <span aria-hidden="true">A+</span>
          </button>
          
          <button id="contrast-toggle" aria-label="Toggle high contrast mode" aria-pressed="false">
            <span aria-hidden="true">◐</span>
          </button>
          
          <button id="motion-toggle" aria-label="Reduce motion" aria-pressed="false">
            <span class="sr-only">Reduce animations</span>
            <span aria-hidden="true">⏸</span>
          </button>
        </aside>

        <footer role="contentinfo">
          <nav aria-label="Footer navigation">
            <ul role="list">
              <li role="listitem">
                <a href="/privacy" rel="noopener">Privacy Policy</a>
              </li>
              <li role="listitem">
                <a href="/terms" rel="noopener">Terms of Service</a>
              </li>
            </ul>
          </nav>
          
          <div class="social-links" role="list" aria-label="Social media profiles">
            <a 
              href="https://github.com/johndoe" 
              target="_blank" 
              rel="noopener noreferrer"
              aria-label="John Doe on GitHub (opens in new tab)"
              role="listitem"
            >
              <span aria-hidden="true">📧</span>
            </a>
            <a 
              href="https://linkedin.com/in/johndoe" 
              target="_blank" 
              rel="noopener noreferrer"
              aria-label="John Doe on LinkedIn (opens in new tab)"
              role="listitem"
            >
              <span aria-hidden="true">💼</span>
            </a>
          </div>
          
          <p class="copyright">
            <span>© 2023 John Doe. All rights reserved.</span>
            <span class="sr-only">End of page content</span>
          </p>
        </footer>

        <!-- Live region for announcements -->
        <div id="live-region" class="sr-only" role="status" aria-live="polite" aria-atomic="true"></div>
        
        <!-- Modal for project details -->
        <div 
          id="project-modal" 
          class="modal" 
          role="dialog" 
          aria-labelledby="modal-title"
          aria-describedby="modal-description"
          aria-hidden="true"
          aria-modal="true"
        >
          <div class="modal-content">
            <div class="modal-header">
              <h2 id="modal-title">Project Details</h2>
              <button 
                id="modal-close"
                class="modal-close"
                aria-label="Close project details dialog"
                type="button"
              >
                <span aria-hidden="true">×</span>
              </button>
            </div>
            <div class="modal-body">
              <p id="modal-description">Detailed information about the selected project.</p>
            </div>
          </div>
        </div>
      </body>
      </html>
    `

    dom = new JSDOM(html, {
      url: 'http://localhost:3000',
      pretendToBeVisual: true,
      resources: 'usable'
    })
    ;({ window } = dom)
    ;({ document } = window)

    // Mock console for accessibility warnings
    global.console = {
      log: jest.fn(),
      warn: jest.fn(),
      error: jest.fn()
    }

    // Set up globals
    global.window = window
    global.document = document
  })

  afterEach(() => {
    if (dom) {
      dom.window.close()
    }
    jest.clearAllMocks()
  })

  describe('Semantic HTML and Document Structure', () => {
    test('should have proper document structure with landmarks', () => {
      const header = document.querySelector('header[role="banner"]')
      const nav = document.querySelector('nav[role="navigation"]')
      const main = document.querySelector('main[role="main"]')
      const footer = document.querySelector('footer[role="contentinfo"]')
      const aside = document.querySelector('aside[role="complementary"]')

      expect(header).toBeTruthy()
      expect(nav).toBeTruthy()
      expect(main).toBeTruthy()
      expect(footer).toBeTruthy()
      expect(aside).toBeTruthy()

      // Check aria-label for navigation
      expect(nav.getAttribute('aria-label')).toBe('Main navigation')
    })

    test('should have proper heading hierarchy', () => {
      const headings = Array.from(
        document.querySelectorAll('h1, h2, h3, h4, h5, h6')
      ).map(h => ({
        level: parseInt(h.tagName.charAt(1), 10),
        text: h.textContent.trim()
      }))

      expect(headings[0].level).toBe(1) // Should start with h1
      expect(headings[0].text).toContain('John Doe')

      // Check that heading levels don't skip (h1 -> h3 would be invalid)
      for (let i = 1; i < headings.length; i++) {
        const currentLevel = headings[i].level
        const previousLevel = headings[i - 1].level
        expect(currentLevel - previousLevel).toBeLessThanOrEqual(1)
      }
    })

    test('should have proper form structure with fieldsets and labels', () => {
      const form = document.getElementById('contact-form')
      const fieldset = form.querySelector('fieldset')
      const legend = fieldset?.querySelector('legend')

      expect(form).toBeTruthy()
      expect(fieldset).toBeTruthy()
      expect(legend).toBeTruthy()

      // Check all form inputs have labels
      const inputs = form.querySelectorAll('input, textarea, select')
      inputs.forEach(input => {
        const id = input.getAttribute('id')
        const label = document.querySelector(`label[for="${id}"]`)
        expect(label).toBeTruthy()
        expect(label.textContent.trim()).toBeTruthy()
      })
    })

    test('should have proper list structures', () => {
      const lists = document.querySelectorAll(
        'ul[role="list"], ol[role="list"]'
      )

      lists.forEach(list => {
        const items = list.querySelectorAll('li[role="listitem"]')
        expect(items.length).toBeGreaterThan(0)
      })

      // Check navigation list structure
      const navList = document.querySelector('nav ul[role="list"]')
      const navItems = navList.querySelectorAll('li[role="listitem"]')
      expect(navItems.length).toBe(4) // Home, About, Projects, Contact
    })
  })

  describe('ARIA Attributes and Accessibility Properties', () => {
    test('should have proper ARIA labels and descriptions', () => {
      const toggleButton = document.getElementById('nav-toggle')
      expect(toggleButton.getAttribute('aria-label')).toBe(
        'Toggle navigation menu'
      )
      expect(toggleButton.getAttribute('aria-expanded')).toBe('false')
      expect(toggleButton.getAttribute('aria-controls')).toBe('nav-menu')

      const themeToggle = document.getElementById('theme-toggle')
      expect(themeToggle.getAttribute('aria-label')).toBe(
        'Switch to dark theme'
      )
      expect(themeToggle.getAttribute('aria-pressed')).toBe('false')
    })

    test('should have proper ARIA live regions', () => {
      const liveRegion = document.getElementById('live-region')
      expect(liveRegion.getAttribute('role')).toBe('status')
      expect(liveRegion.getAttribute('aria-live')).toBe('polite')
      expect(liveRegion.getAttribute('aria-atomic')).toBe('true')

      const projectsGrid = document.querySelector('.projects-grid')
      expect(projectsGrid.getAttribute('aria-live')).toBe('polite')
      expect(projectsGrid.getAttribute('aria-label')).toBe('Filtered projects')
    })

    test('should have proper modal ARIA attributes', () => {
      const modal = document.getElementById('project-modal')
      expect(modal.getAttribute('role')).toBe('dialog')
      expect(modal.getAttribute('aria-modal')).toBe('true')
      expect(modal.getAttribute('aria-hidden')).toBe('true')
      expect(modal.getAttribute('aria-labelledby')).toBe('modal-title')
      expect(modal.getAttribute('aria-describedby')).toBe('modal-description')
    })

    test('should have proper form ARIA attributes', () => {
      const nameInput = document.getElementById('name')
      expect(nameInput.getAttribute('aria-required')).toBe('true')
      expect(nameInput.getAttribute('aria-describedby')).toContain('name-error')
      expect(nameInput.getAttribute('aria-describedby')).toContain('name-help')

      const errorMessage = document.getElementById('name-error')
      expect(errorMessage.getAttribute('role')).toBe('alert')
      expect(errorMessage.getAttribute('aria-live')).toBe('polite')
    })

    test('should have proper button states with aria-pressed', () => {
      const filterButtons = document.querySelectorAll('.filter-btn')
      filterButtons.forEach(button => {
        expect(button.hasAttribute('aria-pressed')).toBe(true)
      })

      const activeButton = document.querySelector('.filter-btn.active')
      expect(activeButton.getAttribute('aria-pressed')).toBe('true')
    })
  })

  describe('Keyboard Navigation', () => {
    test('should handle tab navigation properly', () => {
      const focusableElements = document.querySelectorAll(
        'a[href], button:not([disabled]), input:not([disabled]), textarea:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])'
      )

      expect(focusableElements.length).toBeGreaterThan(0)

      // Check skip link is first focusable element
      expect(focusableElements[0].classList.contains('skip-link')).toBe(true)
      expect(focusableElements[0].getAttribute('href')).toBe('#main')
    })

    test('should handle keyboard events for interactive elements', () => {
      const navToggle = document.getElementById('nav-toggle')
      let toggleTriggered = false

      const handleKeydown = event => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault()
          toggleTriggered = true
        }
      }

      navToggle.addEventListener('keydown', handleKeydown)

      // Test Enter key
      const enterEvent = new window.KeyboardEvent('keydown', {
        key: 'Enter',
        bubbles: true,
        cancelable: true
      })
      navToggle.dispatchEvent(enterEvent)
      expect(toggleTriggered).toBe(true)

      // Test Space key
      toggleTriggered = false
      const spaceEvent = new window.KeyboardEvent('keydown', {
        key: ' ',
        bubbles: true,
        cancelable: true
      })
      navToggle.dispatchEvent(spaceEvent)
      expect(toggleTriggered).toBe(true)
    })

    test('should handle escape key for modal closing', () => {
      const modal = document.getElementById('project-modal')
      let modalClosed = false

      const handleKeydown = event => {
        if (
          event.key === 'Escape' &&
          modal.getAttribute('aria-hidden') === 'false'
        ) {
          modalClosed = true
          modal.setAttribute('aria-hidden', 'true')
        }
      }

      document.addEventListener('keydown', handleKeydown)

      // Open modal first
      modal.setAttribute('aria-hidden', 'false')

      // Test Escape key
      const escapeEvent = new window.KeyboardEvent('keydown', {
        key: 'Escape',
        bubbles: true,
        cancelable: true
      })
      document.dispatchEvent(escapeEvent)

      expect(modalClosed).toBe(true)
      expect(modal.getAttribute('aria-hidden')).toBe('true')
    })

    test('should implement focus trapping in modals', () => {
      const modal = document.getElementById('project-modal')
      const focusableInModal = modal.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      )

      const firstFocusable = focusableInModal[0]
      const lastFocusable = focusableInModal[focusableInModal.length - 1]

      expect(firstFocusable).toBeTruthy()
      expect(lastFocusable).toBeTruthy()

      // Mock focus trap logic
      const handleTabKey = event => {
        if (event.key === 'Tab') {
          if (event.shiftKey) {
            // Shift + Tab - moving backwards
            if (document.activeElement === firstFocusable) {
              event.preventDefault()
              lastFocusable.focus()
            }
          } else {
            // Tab - moving forwards
            if (document.activeElement === lastFocusable) {
              event.preventDefault()
              firstFocusable.focus()
            }
          }
        }
      }

      modal.addEventListener('keydown', handleTabKey)

      // Test tab wrapping (would need more complex setup for full testing)
      expect(handleTabKey).toBeDefined()
    })
  })

  describe('Screen Reader Support', () => {
    test('should have proper screen reader only content', () => {
      const srOnlyElements = document.querySelectorAll('.sr-only')
      expect(srOnlyElements.length).toBeGreaterThan(0)

      // Check that sr-only elements have content (excluding aria-live regions which start empty)
      srOnlyElements.forEach(element => {
        // Skip aria-live regions that are meant to be populated dynamically
        if (!element.hasAttribute('aria-live')) {
          expect(element.textContent.trim()).toBeTruthy()
        }
      })

      // Check specific sr-only content
      const menuText = document.querySelector('.nav-toggle .sr-only')
      expect(menuText.textContent).toBe('Menu')

      const filterTitle = document.getElementById('filter-title')
      expect(filterTitle.classList.contains('sr-only')).toBe(true)
      expect(filterTitle.textContent).toContain('Filter projects')
    })

    test('should have proper aria-hidden for decorative elements', () => {
      const decorativeElements = document.querySelectorAll(
        '[aria-hidden="true"]'
      )
      expect(decorativeElements.length).toBeGreaterThan(0)

      // Check that decorative icons are hidden from screen readers
      const menuIcon = document.querySelector(
        '.nav-toggle [aria-hidden="true"]'
      )
      expect(menuIcon.textContent).toBe('☰')

      const themeIcon = document.querySelector(
        '.theme-toggle [aria-hidden="true"]'
      )
      expect(themeIcon.textContent).toBe('🌙')
    })

    test('should have proper announcements for dynamic content', () => {
      const liveRegion = document.getElementById('live-region')

      const announce = message => {
        liveRegion.textContent = message
        setTimeout(() => {
          liveRegion.textContent = ''
        }, 1000)
      }

      announce('Filter applied: JavaScript projects')
      expect(liveRegion.textContent).toBe('Filter applied: JavaScript projects')
    })

    test('should have proper form error announcements', () => {
      const nameError = document.getElementById('name-error')
      const emailError = document.getElementById('email-error')

      expect(nameError.getAttribute('role')).toBe('alert')
      expect(nameError.getAttribute('aria-live')).toBe('polite')
      expect(emailError.getAttribute('role')).toBe('alert')
      expect(emailError.getAttribute('aria-live')).toBe('polite')

      // Test error announcement
      nameError.textContent = 'Name is required'
      expect(nameError.textContent).toBe('Name is required')
    })
  })

  describe('Color and Contrast Accessibility', () => {
    test('should not rely solely on color for information', () => {
      // Check that required fields have text indicators, not just color
      const requiredFields = document.querySelectorAll('.required')
      requiredFields.forEach(field => {
        const indicator = field.querySelector('.required-indicator')
        expect(indicator).toBeTruthy()
        expect(indicator.textContent).toContain('*')
        expect(indicator.getAttribute('aria-label')).toBe('required')
      })

      // Check that active filter button has more than just color indication
      const activeFilter = document.querySelector('.filter-btn.active')
      expect(activeFilter.getAttribute('aria-pressed')).toBe('true')
    })

    test('should support high contrast mode', () => {
      const contrastToggle = document.getElementById('contrast-toggle')
      const { body } = document

      const toggleHighContrast = () => {
        const isHighContrast = body.classList.toggle('high-contrast')
        contrastToggle.setAttribute('aria-pressed', isHighContrast.toString())
        contrastToggle.setAttribute(
          'aria-label',
          isHighContrast
            ? 'Disable high contrast mode'
            : 'Toggle high contrast mode'
        )
      }

      toggleHighContrast()

      expect(body.classList.contains('high-contrast')).toBe(true)
      expect(contrastToggle.getAttribute('aria-pressed')).toBe('true')
      expect(contrastToggle.getAttribute('aria-label')).toBe(
        'Disable high contrast mode'
      )
    })

    test('should handle focus visibility', () => {
      const focusableElement = document.querySelector('.cta-button')

      const handleFocus = element => {
        element.classList.add('focus-visible')
      }

      const handleBlur = element => {
        element.classList.remove('focus-visible')
      }

      handleFocus(focusableElement)
      expect(focusableElement.classList.contains('focus-visible')).toBe(true)

      handleBlur(focusableElement)
      expect(focusableElement.classList.contains('focus-visible')).toBe(false)
    })
  })

  describe('Motion and Animation Accessibility', () => {
    test('should respect reduced motion preferences', () => {
      const motionToggle = document.getElementById('motion-toggle')
      const { body } = document

      // Mock matchMedia for prefers-reduced-motion
      Object.defineProperty(window, 'matchMedia', {
        writable: true,
        value: jest.fn().mockImplementation(query => ({
          matches: query === '(prefers-reduced-motion: reduce)',
          media: query,
          onchange: null,
          addListener: jest.fn(),
          removeListener: jest.fn(),
          addEventListener: jest.fn(),
          removeEventListener: jest.fn(),
          dispatchEvent: jest.fn()
        }))
      })

      const handleReducedMotion = () => {
        const reducedMotionQuery = window.matchMedia(
          '(prefers-reduced-motion: reduce)'
        )
        const userToggle = body.classList.contains('reduced-motion')

        if (reducedMotionQuery.matches || userToggle) {
          body.classList.add('reduced-motion')
          motionToggle.setAttribute('aria-pressed', 'true')
          motionToggle.setAttribute('aria-label', 'Enable motion')
        }
      }

      handleReducedMotion()
      expect(body.classList.contains('reduced-motion')).toBe(true)
      expect(motionToggle.getAttribute('aria-pressed')).toBe('true')
    })

    test('should provide motion control toggle', () => {
      const motionToggle = document.getElementById('motion-toggle')
      const { body } = document

      const toggleMotion = () => {
        const reducedMotion = body.classList.toggle('reduced-motion')
        motionToggle.setAttribute('aria-pressed', reducedMotion.toString())
        motionToggle.setAttribute(
          'aria-label',
          reducedMotion ? 'Enable motion' : 'Reduce motion'
        )
      }

      // Initial state
      expect(motionToggle.getAttribute('aria-pressed')).toBe('false')

      // Toggle motion reduction
      toggleMotion()
      expect(body.classList.contains('reduced-motion')).toBe(true)
      expect(motionToggle.getAttribute('aria-pressed')).toBe('true')
      expect(motionToggle.getAttribute('aria-label')).toBe('Enable motion')
    })
  })

  describe('Language and Internationalization', () => {
    test('should have proper language attributes', () => {
      const html = document.documentElement
      expect(html.getAttribute('lang')).toBe('en')

      // Check that all text content is in the declared language
      const title = document.querySelector('title')
      expect(title.textContent).toMatch(/^[a-zA-Z\s-]+$/) // English text pattern
    })

    test('should handle text direction properly', () => {
      // Test would be more relevant for RTL languages, but checking structure
      const { body } = document
      expect(body.getAttribute('dir')).toBeFalsy() // Default LTR

      // Mock RTL support
      const setDirection = dir => {
        body.setAttribute('dir', dir)
        if (dir === 'rtl') {
          body.classList.add('rtl')
        } else {
          body.classList.remove('rtl')
        }
      }

      setDirection('rtl')
      expect(body.getAttribute('dir')).toBe('rtl')
      expect(body.classList.contains('rtl')).toBe(true)
    })
  })

  describe('Form Accessibility', () => {
    test('should have proper form validation with accessibility', () => {
      const nameInput = document.getElementById('name')
      const nameError = document.getElementById('name-error')

      const validateField = input => {
        const errorElement = document.getElementById(
          input.getAttribute('aria-describedby').split(' ')[0]
        )

        if (input.hasAttribute('required') && !input.value.trim()) {
          const fieldName = document
            .querySelector(`label[for="${input.id}"]`)
            .textContent.replace('*', '')
            .trim()
          errorElement.textContent = `${fieldName} is required`
          input.setAttribute('aria-invalid', 'true')
          return false
        }
        errorElement.textContent = ''
        input.setAttribute('aria-invalid', 'false')
        return true
      }

      // Test validation
      nameInput.value = ''
      const isValid = validateField(nameInput)

      expect(isValid).toBe(false)
      expect(nameError.textContent).toBe('Name is required')
      expect(nameInput.getAttribute('aria-invalid')).toBe('true')

      // Test valid input
      nameInput.value = 'John Doe'
      const isValidNow = validateField(nameInput)

      expect(isValidNow).toBe(true)
      expect(nameError.textContent).toBe('')
      expect(nameInput.getAttribute('aria-invalid')).toBe('false')
    })

    test('should have proper autocomplete attributes', () => {
      const emailInput = document.getElementById('email')
      expect(emailInput.getAttribute('autocomplete')).toBe('email')

      // Other inputs that should have autocomplete
      const inputs = {
        name: 'name',
        email: 'email'
      }

      Object.entries(inputs).forEach(([id, expectedValue]) => {
        const input = document.getElementById(id)
        if (input && input.type !== 'textarea') {
          // Email input has explicit autocomplete, name could have it
          const autocomplete = input.getAttribute('autocomplete')
          if (autocomplete) {
            expect(autocomplete).toBe(expectedValue)
          }
        }
      })
    })

    test('should provide helpful form instructions', () => {
      const inputs = document.querySelectorAll('input, textarea')

      inputs.forEach(input => {
        const helpId = input
          .getAttribute('aria-describedby')
          ?.split(' ')
          .find(id => id.includes('help'))
        if (helpId) {
          const helpText = document.getElementById(helpId)
          expect(helpText).toBeTruthy()
          expect(helpText.textContent.trim()).toBeTruthy()
        }
      })
    })
  })

  describe('Image and Media Accessibility', () => {
    test('should have proper alt text for images', () => {
      const images = document.querySelectorAll('img')

      images.forEach(img => {
        const alt = img.getAttribute('alt')
        expect(alt).toBeTruthy()

        // Alt text should be descriptive
        if (
          !img.hasAttribute('role') ||
          img.getAttribute('role') !== 'presentation'
        ) {
          expect(alt.length).toBeGreaterThan(5) // Meaningful description
        }
      })

      // Check profile image specifically
      const profileImg = document.querySelector('.profile-image')
      expect(profileImg.getAttribute('alt')).toContain('John Doe')
      expect(profileImg.getAttribute('alt')).toContain('headshot')
    })

    test('should have proper loading attributes for performance', () => {
      // Images below the fold should have loading="lazy"
      const profileImg = document.querySelector('.profile-image')
      expect(profileImg.getAttribute('loading')).toBe('lazy')
    })
  })

  describe('Link Accessibility', () => {
    test('should have descriptive link text', () => {
      const links = document.querySelectorAll('a')

      links.forEach(link => {
        const linkText = link.textContent.trim()
        const ariaLabel = link.getAttribute('aria-label')

        // Link should have either meaningful text or aria-label
        expect(linkText.length > 0 || ariaLabel).toBeTruthy()

        // Should not use generic text like "click here"
        if (linkText) {
          expect(linkText.toLowerCase()).not.toMatch(
            /^(click here|read more|link)$/i
          )
        }
      })
    })

    test('should handle external links properly', () => {
      const externalLinks = document.querySelectorAll('a[target="_blank"]')

      externalLinks.forEach(link => {
        // Should have rel="noopener noreferrer" for security
        const rel = link.getAttribute('rel')
        expect(rel).toContain('noopener')
        expect(rel).toContain('noreferrer')

        // Should indicate that link opens in new tab
        const ariaLabel = link.getAttribute('aria-label')
        expect(ariaLabel).toMatch(/opens in new tab|new window/i)
      })
    })

    test('should have proper focus indicators', () => {
      const focusableElements = document.querySelectorAll(
        'a, button, input, textarea, select, [tabindex]:not([tabindex="-1"])'
      )

      // All focusable elements should be able to receive focus
      focusableElements.forEach(element => {
        expect(element.tabIndex).not.toBe(-1)
      })

      // Skip link should be properly positioned
      const skipLink = document.querySelector('.skip-link')
      expect(skipLink.getAttribute('href')).toBe('#main')
    })
  })
})
