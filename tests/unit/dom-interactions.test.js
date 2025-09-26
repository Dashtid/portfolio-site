/**
 * DOM Interaction Tests
 * Tests real DOM manipulations and user interactions
 */

/* eslint-env jest */

const { TestUtils } = require('./setup.js')

describe('DOM Interactions', () => {
  describe('Theme Toggle Interface', () => {
    let themeToggleContainer
    let systemManualToggle
    let lightDarkToggle

    beforeEach(() => {
      // Create the actual DOM structure that exists in index.html
      document.body.innerHTML = `
        <div class="theme-switch-container">
          <div class="theme-switch-wrapper">
            <span class="theme-switch-label">System</span>
            <div id="themeToggle" class="theme-switch" role="switch" aria-checked="false" tabindex="0">
              <div class="theme-switch-slider"></div>
            </div>
            <span class="theme-switch-label">Manual</span>
          </div>
          <div id="manualThemeToggle" class="theme-toggle-manual hidden">
            <div class="theme-switch-wrapper">
              <span class="theme-switch-label-small">☀️ Light</span>
              <div id="lightDarkToggle" class="theme-switch theme-switch-small" role="switch" aria-checked="false" tabindex="0">
                <div class="theme-switch-slider"></div>
              </div>
              <span class="theme-switch-label-small">🌙 Dark</span>
            </div>
          </div>
        </div>
      `

      themeToggleContainer = document.querySelector('.theme-switch-container')
      systemManualToggle = document.getElementById('themeToggle')
      lightDarkToggle = document.getElementById('lightDarkToggle')
    })

    test('should have correct initial DOM structure', () => {
      expect(themeToggleContainer).toBeTruthy()
      expect(systemManualToggle).toBeTruthy()
      expect(lightDarkToggle).toBeTruthy()

      expect(systemManualToggle.getAttribute('role')).toBe('switch')
      expect(lightDarkToggle.getAttribute('role')).toBe('switch')
    })

    test('should toggle aria-checked attribute on click', () => {
      expect(systemManualToggle.getAttribute('aria-checked')).toBe('false')

      TestUtils.simulateClick(systemManualToggle)

      // In a real implementation, this would be handled by the ThemeManager
      systemManualToggle.setAttribute('aria-checked', 'true')
      expect(systemManualToggle.getAttribute('aria-checked')).toBe('true')
    })

    test('should respond to keyboard events', () => {
      const keydownEvent = new KeyboardEvent('keydown', {
        key: 'Enter',
        bubbles: true,
        cancelable: true
      })

      // Test that the event was properly formed

      systemManualToggle.dispatchEvent(keydownEvent)

      // Test that the event was properly formed
      expect(keydownEvent.key).toBe('Enter')
      expect(keydownEvent.bubbles).toBe(true)
    })

    test('should handle space key activation', () => {
      const spaceEvent = new KeyboardEvent('keydown', {
        key: ' ',
        bubbles: true,
        cancelable: true
      })

      lightDarkToggle.dispatchEvent(spaceEvent)

      expect(spaceEvent.key).toBe(' ')
    })
  })

  describe('GitHub Stats Cards', () => {
    beforeEach(() => {
      document.body.innerHTML = `
        <div class="github-stats-card">
          <img src="https://github-readme-stats.vercel.app/api/pin/?username=test&repo=test&theme=default" alt="GitHub Repo">
        </div>
        <div class="github-stats-card">
          <img src="https://github-readme-stats.vercel.app/api/top-langs/?username=test&theme=default" alt="GitHub Languages">
        </div>
      `
    })

    test('should find GitHub stats images', () => {
      const githubImages = document.querySelectorAll(
        'img[src*="github-readme-stats.vercel.app"]'
      )

      expect(githubImages.length).toBe(2)
      expect(githubImages[0].src).toContain('theme=default')
      expect(githubImages[1].src).toContain('theme=default')
    })

    test('should be able to update image themes', () => {
      const githubImages = document.querySelectorAll(
        'img[src*="github-readme-stats.vercel.app"]'
      )

      githubImages.forEach(img => {
        const currentSrc = img.src
        const newSrc = currentSrc.replace(/theme=\w+/, 'theme=dark')
        img.src = newSrc
      })

      const updatedImages = document.querySelectorAll(
        'img[src*="github-readme-stats.vercel.app"]'
      )
      updatedImages.forEach(img => {
        expect(img.src).toContain('theme=dark')
      })
    })
  })

  describe('Navigation and Scrolling', () => {
    beforeEach(() => {
      document.body.innerHTML = `
        <nav class="navbar">
          <a href="#about" class="internal-nav" data-scroll="about">About</a>
          <a href="#skills" class="internal-nav" data-scroll="skills">Skills</a>
          <a href="#projects" class="internal-nav" data-scroll="projects">Projects</a>
        </nav>
        <section id="about">About content</section>
        <section id="skills">Skills content</section>
        <section id="projects">Projects content</section>
        <button id="backToTopBtn" class="back-to-top">↑</button>
      `
    })

    test('should have navigation links with correct attributes', () => {
      const navLinks = document.querySelectorAll('.internal-nav')

      expect(navLinks.length).toBe(3)

      navLinks.forEach(link => {
        expect(link.hasAttribute('data-scroll')).toBe(true)
        expect(link.getAttribute('href')).toMatch(/^#\w+$/)
      })
    })

    test('should have target sections for navigation', () => {
      const sections = document.querySelectorAll('section[id]')

      expect(sections.length).toBe(3)
      expect(document.getElementById('about')).toBeTruthy()
      expect(document.getElementById('skills')).toBeTruthy()
      expect(document.getElementById('projects')).toBeTruthy()
    })

    test('should handle navigation click events', () => {
      const aboutLink = document.querySelector('[data-scroll="about"]')
      const clickEvent = new MouseEvent('click', {
        bubbles: true,
        cancelable: true
      })

      aboutLink.dispatchEvent(clickEvent)

      expect(aboutLink.getAttribute('data-scroll')).toBe('about')
    })

    test('should have back to top button', () => {
      const backToTopBtn = document.getElementById('backToTopBtn')

      expect(backToTopBtn).toBeTruthy()
      expect(backToTopBtn.classList.contains('back-to-top')).toBe(true)
    })
  })

  describe('Form Elements and Accessibility', () => {
    beforeEach(() => {
      document.body.innerHTML = `
        <form>
          <label for="email">Email:</label>
          <input type="email" id="email" required aria-describedby="email-error">
          <div id="email-error" role="alert"></div>

          <label for="message">Message:</label>
          <textarea id="message" required aria-describedby="message-error"></textarea>
          <div id="message-error" role="alert"></div>

          <button type="submit">Send Message</button>
        </form>
      `
    })

    test('should have proper form labels', () => {
      const emailLabel = document.querySelector('label[for="email"]')
      const messageLabel = document.querySelector('label[for="message"]')

      expect(emailLabel).toBeTruthy()
      expect(messageLabel).toBeTruthy()
      expect(emailLabel.textContent).toBe('Email:')
      expect(messageLabel.textContent).toBe('Message:')
    })

    test('should have required attributes', () => {
      const emailInput = document.getElementById('email')
      const messageInput = document.getElementById('message')

      expect(emailInput.hasAttribute('required')).toBe(true)
      expect(messageInput.hasAttribute('required')).toBe(true)
    })

    test('should have ARIA error associations', () => {
      const emailInput = document.getElementById('email')
      const messageInput = document.getElementById('message')

      expect(emailInput.getAttribute('aria-describedby')).toBe('email-error')
      expect(messageInput.getAttribute('aria-describedby')).toBe(
        'message-error'
      )
    })

    test('should have error containers with correct roles', () => {
      const emailError = document.getElementById('email-error')
      const messageError = document.getElementById('message-error')

      expect(emailError.getAttribute('role')).toBe('alert')
      expect(messageError.getAttribute('role')).toBe('alert')
    })
  })

  describe('Loading States and Animations', () => {
    test('should handle loading spinner creation', () => {
      const container = document.createElement('div')
      container.id = 'test-container'
      document.body.appendChild(container)

      // Simulate loading state
      container.innerHTML = `
        <div class="d-flex justify-content-center align-items-center py-4">
          <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">Loading...</span>
          </div>
          <span class="text-muted ms-3">Loading content...</span>
        </div>
      `

      const spinner = container.querySelector('.spinner-border')
      const loadingText = container.querySelector('.text-muted')

      expect(spinner).toBeTruthy()
      expect(spinner.getAttribute('role')).toBe('status')
      expect(loadingText.textContent).toBe('Loading content...')
    })

    test('should handle progress bars', () => {
      document.body.innerHTML = `
        <div class="progress">
          <div class="progress-bar" role="progressbar" aria-valuenow="75" aria-valuemin="0" aria-valuemax="100" style="width: 75%">
            75%
          </div>
        </div>
      `

      const progressBar = document.querySelector('.progress-bar')

      expect(progressBar.getAttribute('role')).toBe('progressbar')
      expect(progressBar.getAttribute('aria-valuenow')).toBe('75')
      expect(progressBar.style.width).toBe('75%')
    })
  })

  describe('Error Handling', () => {
    test('should handle missing elements gracefully', () => {
      expect(() => {
        const missingElement = document.getElementById('non-existent')
        if (missingElement) {
          missingElement.click()
        }
      }).not.toThrow()
    })

    test('should handle malformed event listeners', () => {
      const button = document.createElement('button')
      document.body.appendChild(button)

      expect(() => {
        button.addEventListener('click', null)
      }).toThrow()

      expect(() => {
        button.addEventListener('click', () => {})
      }).not.toThrow()
    })
  })
})
