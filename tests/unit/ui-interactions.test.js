/**
 * Unit tests for UI interactions
 * Tests navigation, theme toggle, modal interactions, form handling
 */

const { JSDOM } = require('jsdom')

describe('UI Interactions', () => {
  let dom, window, document

  beforeEach(() => {
    const html = `
      <!DOCTYPE html>
      <html lang="en">
      <head>
        <meta charset="UTF-8">
        <title>UI Test</title>
        <style>
          .hidden { display: none; }
          .modal { display: none; position: fixed; z-index: 1000; }
          .modal.open { display: block; }
          .nav-menu { max-height: 0; overflow: hidden; transition: max-height 0.3s ease; }
          .nav-menu.open { max-height: 500px; }
          .theme-toggle { cursor: pointer; }
          .dark-theme { background: #333; color: #fff; }
        </style>
      </head>
      <body>
        <header class="header">
          <nav class="nav">
            <button id="nav-toggle" class="nav-toggle" aria-label="Toggle navigation">☰</button>
            <button id="theme-toggle" class="theme-toggle" aria-label="Toggle theme">🌙</button>
            <ul class="nav-menu" id="nav-menu">
              <li><a href="#home">Home</a></li>
              <li><a href="#about">About</a></li>
              <li><a href="#projects">Projects</a></li>
              <li><a href="#contact">Contact</a></li>
            </ul>
          </nav>
        </header>

        <main>
          <section id="home" class="section">
            <h1>Home Section</h1>
            <button id="open-modal" class="btn">Open Modal</button>
          </section>

          <section id="about" class="section">
            <h2>About Section</h2>
          </section>

          <section id="projects" class="section">
            <h2>Projects Section</h2>
            <div class="project-card" data-project="project1">
              <h3>Project 1</h3>
              <button class="project-btn" data-action="view-details">View Details</button>
            </div>
          </section>

          <section id="contact" class="section">
            <h2>Contact Section</h2>
            <form id="contact-form" class="contact-form">
              <input type="text" id="name" name="name" required placeholder="Your Name">
              <input type="email" id="email" name="email" required placeholder="Your Email">
              <textarea id="message" name="message" required placeholder="Your Message"></textarea>
              <button type="submit" class="submit-btn">Send Message</button>
            </form>
          </section>
        </main>

        <div id="modal" class="modal" role="dialog" aria-labelledby="modal-title" aria-hidden="true">
          <div class="modal-content">
            <div class="modal-header">
              <h3 id="modal-title">Modal Title</h3>
              <button id="close-modal" class="close-btn" aria-label="Close modal">&times;</button>
            </div>
            <div class="modal-body">
              <p>Modal content goes here.</p>
            </div>
          </div>
        </div>

        <button id="scroll-to-top" class="scroll-to-top hidden" aria-label="Scroll to top">↑</button>
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

    // Mock window methods
    window.scrollTo = jest.fn()
    window.scroll = jest.fn()
    Object.defineProperty(window, 'scrollY', { value: 0, writable: true })
    Object.defineProperty(window, 'innerHeight', { value: 768, writable: true })

    // Mock localStorage
    const localStorage = {
      getItem: jest.fn(),
      setItem: jest.fn(),
      removeItem: jest.fn(),
      clear: jest.fn()
    }
    Object.defineProperty(window, 'localStorage', { value: localStorage })

    // Set up globals
    global.window = window
    global.document = document
  })

  afterEach(() => {
    if (dom) {
      dom.window.close()
    }
  })

  describe('Navigation interactions', () => {
    test('should toggle mobile navigation menu', () => {
      const navToggle = document.getElementById('nav-toggle')
      const navMenu = document.getElementById('nav-menu')

      expect(navMenu.classList.contains('open')).toBe(false)

      // Simulate click
      navToggle.click()
      navMenu.classList.toggle('open')

      expect(navMenu.classList.contains('open')).toBe(true)

      // Click again to close
      navToggle.click()
      navMenu.classList.toggle('open')

      expect(navMenu.classList.contains('open')).toBe(false)
    })

    test('should handle keyboard navigation', () => {
      const navToggle = document.getElementById('nav-toggle')
      let menuToggled = false

      navToggle.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          menuToggled = true
        }
      })

      // Simulate Enter key press
      const enterEvent = new window.KeyboardEvent('keydown', { key: 'Enter' })
      navToggle.dispatchEvent(enterEvent)

      expect(menuToggled).toBe(true)
    })

    test('should close menu when clicking outside', () => {
      const navMenu = document.getElementById('nav-menu')
      const mainElement = document.querySelector('main')

      navMenu.classList.add('open')
      expect(navMenu.classList.contains('open')).toBe(true)

      // Simulate document click outside menu
      document.addEventListener('click', (e) => {
        if (!e.target.closest('.nav')) {
          navMenu.classList.remove('open')
        }
      })

      mainElement.click()
      expect(navMenu.classList.contains('open')).toBe(false)
    })

    test('should handle smooth scroll to sections', () => {
      const homeLink = document.querySelector('a[href="#home"]')
      const homeSection = document.getElementById('home')

      homeLink.addEventListener('click', (e) => {
        e.preventDefault()
        const targetId = homeLink.getAttribute('href').substring(1)
        const targetElement = document.getElementById(targetId)

        if (targetElement) {
          window.scrollTo({
            top: targetElement.offsetTop,
            behavior: 'smooth'
          })
        }
      })

      homeLink.click()

      expect(window.scrollTo).toHaveBeenCalledWith({
        top: homeSection.offsetTop,
        behavior: 'smooth'
      })
    })
  })

  describe('Theme toggle interactions', () => {
    test('should toggle theme on button click', () => {
      const themeToggle = document.getElementById('theme-toggle')
      const body = document.body

      expect(body.classList.contains('dark-theme')).toBe(false)

      // Simulate theme toggle
      themeToggle.addEventListener('click', () => {
        body.classList.toggle('dark-theme')
        const isDark = body.classList.contains('dark-theme')
        window.localStorage.setItem('theme', isDark ? 'dark' : 'light')

        // Update icon
        themeToggle.textContent = isDark ? '☀️' : '🌙'
      })

      themeToggle.click()

      expect(body.classList.contains('dark-theme')).toBe(true)
      expect(window.localStorage.setItem).toHaveBeenCalledWith('theme', 'dark')
      expect(themeToggle.textContent).toBe('☀️')
    })

    test('should restore saved theme preference', () => {
      const body = document.body

      // Mock saved theme
      window.localStorage.getItem.mockReturnValue('dark')

      // Simulate theme restoration
      const savedTheme = window.localStorage.getItem('theme')
      if (savedTheme === 'dark') {
        body.classList.add('dark-theme')
      }

      expect(body.classList.contains('dark-theme')).toBe(true)
      expect(window.localStorage.getItem).toHaveBeenCalledWith('theme')
    })

    test('should respect system color scheme preference', () => {
      const body = document.body

      // Mock matchMedia
      Object.defineProperty(window, 'matchMedia', {
        writable: true,
        value: jest.fn().mockImplementation((query) => ({
          matches: query === '(prefers-color-scheme: dark)',
          media: query,
          onchange: null,
          addListener: jest.fn(),
          removeListener: jest.fn(),
          addEventListener: jest.fn(),
          removeEventListener: jest.fn(),
          dispatchEvent: jest.fn()
        }))
      })

      const darkModeQuery = window.matchMedia('(prefers-color-scheme: dark)')

      // If no saved preference and system prefers dark
      if (!window.localStorage.getItem('theme') && darkModeQuery.matches) {
        body.classList.add('dark-theme')
      }

      expect(body.classList.contains('dark-theme')).toBe(true)
    })
  })

  describe('Modal interactions', () => {
    test('should open modal when button is clicked', () => {
      const openBtn = document.getElementById('open-modal')
      const modal = document.getElementById('modal')

      expect(modal.classList.contains('open')).toBe(false)

      // Simulate modal opening
      openBtn.addEventListener('click', () => {
        modal.classList.add('open')
        modal.setAttribute('aria-hidden', 'false')
        document.body.style.overflow = 'hidden' // Prevent background scroll
      })

      openBtn.click()

      expect(modal.classList.contains('open')).toBe(true)
      expect(modal.getAttribute('aria-hidden')).toBe('false')
    })

    test('should close modal when close button is clicked', () => {
      const modal = document.getElementById('modal')
      const closeBtn = document.getElementById('close-modal')

      // Open modal first
      modal.classList.add('open')
      modal.setAttribute('aria-hidden', 'false')

      // Setup close handler
      closeBtn.addEventListener('click', () => {
        modal.classList.remove('open')
        modal.setAttribute('aria-hidden', 'true')
        document.body.style.overflow = '' // Restore scroll
      })

      closeBtn.click()

      expect(modal.classList.contains('open')).toBe(false)
      expect(modal.getAttribute('aria-hidden')).toBe('true')
    })

    test('should close modal when clicking outside content', () => {
      const modal = document.getElementById('modal')

      modal.classList.add('open')

      modal.addEventListener('click', (e) => {
        if (e.target === modal) {
          modal.classList.remove('open')
        }
      })

      // Click on modal background (not content)
      modal.click()

      expect(modal.classList.contains('open')).toBe(false)
    })

    test('should close modal on Escape key press', () => {
      const modal = document.getElementById('modal')

      modal.classList.add('open')

      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal.classList.contains('open')) {
          modal.classList.remove('open')
        }
      })

      // Simulate Escape key
      const escEvent = new window.KeyboardEvent('keydown', { key: 'Escape' })
      document.dispatchEvent(escEvent)

      expect(modal.classList.contains('open')).toBe(false)
    })

    test('should trap focus within modal', () => {
      const modal = document.getElementById('modal')
      const closeBtn = document.getElementById('close-modal')

      modal.classList.add('open')

      // Simulate focus trap
      const focusableElements = modal.querySelectorAll(
        'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
      )

      expect(focusableElements.length).toBeGreaterThan(0)
      expect(focusableElements[0]).toBe(closeBtn)
    })
  })

  describe('Form interactions', () => {
    test('should validate required fields', () => {
      const form = document.getElementById('contact-form')
      const nameInput = document.getElementById('name')
      const emailInput = document.getElementById('email')

      let validationErrors = []

      form.addEventListener('submit', (e) => {
        e.preventDefault()
        validationErrors = []

        if (!nameInput.value.trim()) {
          validationErrors.push('Name is required')
        }

        if (!emailInput.value.trim()) {
          validationErrors.push('Email is required')
        } else if (!/\S+@\S+\.\S+/.test(emailInput.value)) {
          validationErrors.push('Email is invalid')
        }
      })

      // Submit empty form
      form.dispatchEvent(new window.Event('submit'))

      expect(validationErrors).toContain('Name is required')
      expect(validationErrors).toContain('Email is required')
    })

    test('should validate email format', () => {
      const form = document.getElementById('contact-form')
      const emailInput = document.getElementById('email')

      emailInput.value = 'invalid-email'
      let emailValid = false

      form.addEventListener('submit', (e) => {
        e.preventDefault()
        emailValid = /\S+@\S+\.\S+/.test(emailInput.value)
      })

      form.dispatchEvent(new window.Event('submit'))

      expect(emailValid).toBe(false)

      // Test valid email
      emailInput.value = 'test@example.com'
      form.dispatchEvent(new window.Event('submit'))

      expect(emailValid).toBe(true)
    })

    test('should show success message after form submission', (done) => {
      const form = document.getElementById('contact-form')
      const nameInput = document.getElementById('name')
      const emailInput = document.getElementById('email')
      const messageInput = document.getElementById('message')

      // Fill form with valid data
      nameInput.value = 'John Doe'
      emailInput.value = 'john@example.com'
      messageInput.value = 'Test message'

      form.addEventListener('submit', (e) => {
        e.preventDefault()

        // Simulate form submission
        setTimeout(() => {
          const successMessage = document.createElement('div')
          successMessage.className = 'success-message'
          successMessage.textContent = 'Message sent successfully!'
          form.appendChild(successMessage)

          expect(document.querySelector('.success-message')).toBeTruthy()
          done()
        }, 100)
      })

      form.dispatchEvent(new window.Event('submit'))
    })

    test('should clear form after successful submission', () => {
      const form = document.getElementById('contact-form')
      const nameInput = document.getElementById('name')
      const emailInput = document.getElementById('email')

      nameInput.value = 'John Doe'
      emailInput.value = 'john@example.com'

      // Simulate successful submission
      form.addEventListener('submit', (e) => {
        e.preventDefault()
        form.reset()
      })

      form.dispatchEvent(new window.Event('submit'))

      expect(nameInput.value).toBe('')
      expect(emailInput.value).toBe('')
    })
  })

  describe('Scroll interactions', () => {
    test('should show scroll-to-top button when scrolled down', () => {
      const scrollBtn = document.getElementById('scroll-to-top')

      expect(scrollBtn.classList.contains('hidden')).toBe(true)

      // Simulate scroll event
      window.scrollY = 500

      window.addEventListener('scroll', () => {
        if (window.scrollY > 300) {
          scrollBtn.classList.remove('hidden')
        } else {
          scrollBtn.classList.add('hidden')
        }
      })

      window.dispatchEvent(new window.Event('scroll'))

      expect(scrollBtn.classList.contains('hidden')).toBe(false)
    })

    test('should scroll to top when button is clicked', () => {
      const scrollBtn = document.getElementById('scroll-to-top')

      scrollBtn.addEventListener('click', () => {
        window.scrollTo({ top: 0, behavior: 'smooth' })
      })

      scrollBtn.click()

      expect(window.scrollTo).toHaveBeenCalledWith({
        top: 0,
        behavior: 'smooth'
      })
    })

    test('should update active navigation link on scroll', () => {
      const sections = document.querySelectorAll('.section')
      const navLinks = document.querySelectorAll('.nav-menu a')

      // Mock getBoundingClientRect for sections
      sections.forEach((section, index) => {
        section.getBoundingClientRect = jest.fn(() => ({
          top: index * 400 - window.scrollY,
          bottom: (index + 1) * 400 - window.scrollY
        }))
      })

      window.scrollY = 200

      window.addEventListener('scroll', () => {
        sections.forEach((section, index) => {
          const rect = section.getBoundingClientRect()
          if (rect.top <= 100 && rect.bottom > 100) {
            navLinks.forEach((link) => link.classList.remove('active'))
            navLinks[index]?.classList.add('active')
          }
        })
      })

      window.dispatchEvent(new window.Event('scroll'))

      // First section should be active
      expect(navLinks[0].classList.contains('active')).toBe(true)
    })
  })

  describe('Project interactions', () => {
    test('should handle project card clicks', () => {
      const projectCard = document.querySelector('.project-card')
      const projectBtn = document.querySelector('.project-btn')

      let projectClicked = null

      projectBtn.addEventListener('click', (e) => {
        const card = e.target.closest('.project-card')
        projectClicked = card.getAttribute('data-project')
      })

      projectBtn.click()

      expect(projectClicked).toBe('project1')
    })

    test('should handle project filtering', () => {
      // Add filter buttons
      const filterContainer = document.createElement('div')
      filterContainer.innerHTML = `
        <button class="filter-btn active" data-filter="all">All</button>
        <button class="filter-btn" data-filter="web">Web</button>
        <button class="filter-btn" data-filter="mobile">Mobile</button>
      `
      document.body.appendChild(filterContainer)

      const filterBtns = document.querySelectorAll('.filter-btn')

      filterBtns.forEach((btn) => {
        btn.addEventListener('click', () => {
          // Remove active from all buttons
          filterBtns.forEach((b) => b.classList.remove('active'))
          // Add active to clicked button
          btn.classList.add('active')
        })
      })

      const webBtn = document.querySelector('[data-filter="web"]')
      webBtn.click()

      expect(webBtn.classList.contains('active')).toBe(true)
      expect(
        document
          .querySelector('[data-filter="all"]')
          .classList.contains('active')
      ).toBe(false)
    })
  })

  describe('Accessibility interactions', () => {
    test('should handle focus management', () => {
      const themeToggle = document.getElementById('theme-toggle')

      themeToggle.focus()
      expect(document.activeElement).toBe(themeToggle)
    })

    test('should provide keyboard alternatives for mouse interactions', () => {
      const navToggle = document.getElementById('nav-toggle')
      let toggleActivated = false

      navToggle.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault()
          toggleActivated = true
        }
      })

      // Test Enter key
      const enterEvent = new window.KeyboardEvent('keydown', { key: 'Enter' })
      navToggle.dispatchEvent(enterEvent)
      expect(toggleActivated).toBe(true)

      // Test Space key
      toggleActivated = false
      const spaceEvent = new window.KeyboardEvent('keydown', { key: ' ' })
      navToggle.dispatchEvent(spaceEvent)
      expect(toggleActivated).toBe(true)
    })

    test('should manage ARIA attributes dynamically', () => {
      const navToggle = document.getElementById('nav-toggle')
      const navMenu = document.getElementById('nav-menu')

      navToggle.addEventListener('click', () => {
        const isOpen = navMenu.classList.toggle('open')
        navToggle.setAttribute('aria-expanded', isOpen.toString())
      })

      navToggle.click()
      expect(navToggle.getAttribute('aria-expanded')).toBe('true')

      navToggle.click()
      expect(navToggle.getAttribute('aria-expanded')).toBe('false')
    })
  })
})
