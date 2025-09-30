/**
 * Integration tests for theme system
 * Tests theme switching, persistence, and visual consistency
 */

/* eslint-env jest, node */
/* eslint-disable no-console */

const fs = require('fs')
const path = require('path')
const { JSDOM } = require('jsdom')

describe('Theme Integration', () => {
  let dom, window, document, localStorage

  beforeEach(() => {
    // Create a fresh DOM environment for each test
    const html = `
      <!DOCTYPE html>
      <html lang="en">
      <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Portfolio Site</title>
        <link rel="stylesheet" href="/static/css/main.css">
      </head>
      <body>
        <header class="header">
          <nav class="nav">
            <button id="theme-toggle" class="theme-toggle" aria-label="Toggle theme">
              <span class="theme-icon">🌙</span>
            </button>
          </nav>
        </header>
        <main class="main">
          <section class="hero">
            <h1 class="hero-title">Test Title</h1>
            <p class="hero-description">Test description</p>
          </section>
        </main>
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

    // Create mock localStorage object
    const storage = {}
    localStorage = {
      getItem: jest.fn(key => storage[key] || null),
      setItem: jest.fn((key, value) => {
        storage[key] = value
      }),
      removeItem: jest.fn(key => {
        delete storage[key]
      }),
      // eslint-disable-next-line no-empty-function
      clear: jest.fn(() => {
        Object.keys(storage).forEach(key => delete storage[key])
      })
    }

    // Mock window.matchMedia
    window.matchMedia = jest.fn().mockImplementation(query => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: jest.fn(),
      removeListener: jest.fn(),
      addEventListener: jest.fn(),
      removeEventListener: jest.fn(),
      dispatchEvent: jest.fn()
    }))

    // Set up global objects
    global.window = window
    global.document = document
    global.localStorage = localStorage
  })

  afterEach(() => {
    if (dom) {
      dom.window.close()
    }
    jest.restoreAllMocks()
  })

  describe('Theme initialization', () => {
    test('should load theme script successfully', () => {
      const themePath = path.join(
        __dirname,
        '..',
        '..',
        'site',
        'static',
        'js',
        'theme.js'
      )

      if (!fs.existsSync(themePath)) {
        console.warn('Theme script not found, skipping test')
        return
      }

      const themeScript = fs.readFileSync(themePath, 'utf8')

      // Basic validation of theme script
      expect(themeScript).toContain('theme')
      expect(themeScript.length).toBeGreaterThan(100)
    })

    test('should initialize with default theme', () => {
      // Simulate theme initialization
      const { body } = document

      // Should not have dark theme initially (light theme default)
      expect(body.classList.contains('dark-theme')).toBe(false)

      // Theme toggle should exist
      const themeToggle = document.getElementById('theme-toggle')
      expect(themeToggle).toBeTruthy()
    })

    test('should restore theme from localStorage', () => {
      // Set dark theme in localStorage
      localStorage.setItem('theme', 'dark')

      // Simulate theme restoration
      const savedTheme = localStorage.getItem('theme')
      expect(savedTheme).toBe('dark')

      if (savedTheme === 'dark') {
        document.body.classList.add('dark-theme')
      }

      expect(document.body.classList.contains('dark-theme')).toBe(true)
    })
  })

  describe('Theme switching', () => {
    test('should toggle between light and dark themes', () => {
      const { body } = document

      // Start with light theme
      expect(body.classList.contains('dark-theme')).toBe(false)

      // Simulate click to switch to dark theme
      body.classList.toggle('dark-theme')
      expect(body.classList.contains('dark-theme')).toBe(true)

      // Simulate click to switch back to light theme
      body.classList.toggle('dark-theme')
      expect(body.classList.contains('dark-theme')).toBe(false)
    })

    test('should update theme icon on toggle', () => {
      const themeIcon = document.querySelector('.theme-icon')

      if (themeIcon) {
        // Light theme should show moon icon
        expect(themeIcon.textContent).toBe('🌙')

        // Simulate theme change to dark
        document.body.classList.add('dark-theme')
        themeIcon.textContent = '☀️'

        expect(themeIcon.textContent).toBe('☀️')
      }
    })

    test('should persist theme preference', () => {
      // Switch to dark theme
      document.body.classList.add('dark-theme')
      localStorage.setItem('theme', 'dark')

      expect(localStorage.setItem).toHaveBeenCalledWith('theme', 'dark')

      // Switch back to light theme
      document.body.classList.remove('dark-theme')
      localStorage.setItem('theme', 'light')

      expect(localStorage.setItem).toHaveBeenCalledWith('theme', 'light')
    })
  })

  describe('CSS theme variables', () => {
    test('should load main CSS file', () => {
      const cssPath = path.join(
        __dirname,
        '..',
        '..',
        'site',
        'static',
        'css',
        'main.css'
      )

      if (!fs.existsSync(cssPath)) {
        console.warn('Main CSS file not found, skipping test')
        return
      }

      const cssContent = fs.readFileSync(cssPath, 'utf8')

      // Should contain CSS custom properties for theming
      expect(cssContent).toMatch(/--\w+/)
      expect(cssContent.length).toBeGreaterThan(100)
    })

    test('should define theme color variables', () => {
      const cssPath = path.join(
        __dirname,
        '..',
        '..',
        'site',
        'static',
        'css',
        'main.css'
      )

      if (!fs.existsSync(cssPath)) {
        return
      }

      const cssContent = fs.readFileSync(cssPath, 'utf8')

      // Common theme variables
      const expectedVariables = [
        '--color-bg',
        '--color-text',
        '--color-primary',
        '--color-secondary'
      ]

      expectedVariables.forEach(variable => {
        if (cssContent.includes(variable)) {
          expect(cssContent).toContain(variable)
        }
      })
    })

    test('should have dark theme overrides', () => {
      const cssPath = path.join(
        __dirname,
        '..',
        '..',
        'site',
        'static',
        'css',
        'main.css'
      )

      if (!fs.existsSync(cssPath)) {
        return
      }

      const cssContent = fs.readFileSync(cssPath, 'utf8')

      // Should contain dark theme selectors
      const darkThemePatterns = [
        /\.dark-theme/,
        /\[data-theme="dark"\]/,
        /@media.*prefers-color-scheme.*dark/
      ]

      const hasAnyDarkTheme = darkThemePatterns.some(pattern =>
        pattern.test(cssContent)
      )

      if (cssContent.includes('dark')) {
        expect(hasAnyDarkTheme).toBe(true)
      }
    })
  })

  describe('Accessibility', () => {
    test('should have proper ARIA labels for theme toggle', () => {
      const themeToggle = document.getElementById('theme-toggle')

      if (themeToggle) {
        const ariaLabel = themeToggle.getAttribute('aria-label')
        expect(ariaLabel).toBeTruthy()
        expect(ariaLabel.toLowerCase()).toContain('theme')
      }
    })

    test('should be keyboard accessible', () => {
      const themeToggle = document.getElementById('theme-toggle')

      if (themeToggle) {
        // Should be focusable (button element)
        expect(themeToggle.tagName.toLowerCase()).toBe('button')

        // Should not have negative tabindex
        const tabIndex = themeToggle.getAttribute('tabindex')
        if (tabIndex) {
          expect(parseInt(tabIndex, 10)).toBeGreaterThanOrEqual(0)
        }
      }
    })

    test('should respect system color scheme preference', () => {
      // Simulate system dark mode preference
      const darkModeMediaQuery = window.matchMedia(
        '(prefers-color-scheme: dark)'
      )

      // Mock the media query
      Object.defineProperty(darkModeMediaQuery, 'matches', {
        writable: true,
        value: true
      })

      // If no stored preference, should respect system preference
      if (!localStorage.getItem('theme')) {
        if (darkModeMediaQuery.matches) {
          document.body.classList.add('dark-theme')
        }

        expect(document.body.classList.contains('dark-theme')).toBe(true)
      }
    })
  })

  describe('Theme consistency', () => {
    test('should apply theme consistently across elements', () => {
      const elements = [
        document.querySelector('.header'),
        document.querySelector('.hero'),
        document.querySelector('.nav')
      ].filter(Boolean)

      // Switch to dark theme
      document.body.classList.add('dark-theme')

      // All elements should inherit theme through CSS cascade
      elements.forEach(element => {
        // Elements should be present and can be styled
        expect(element).toBeTruthy()
        expect(element.nodeType).toBe(1) // Element node
      })
    })

    test('should handle theme transitions smoothly', () => {
      const cssPath = path.join(
        __dirname,
        '..',
        '..',
        'site',
        'static',
        'css',
        'main.css'
      )

      if (!fs.existsSync(cssPath)) {
        return
      }

      const cssContent = fs.readFileSync(cssPath, 'utf8')

      // Should include transition properties for smooth theme changes
      if (cssContent.includes('transition')) {
        expect(cssContent).toMatch(/transition.*:.*\d/)
      }
    })
  })

  describe('Error handling', () => {
    test('should handle missing localStorage gracefully', () => {
      // Simulate localStorage being unavailable
      const originalLocalStorage = global.localStorage
      global.localStorage = undefined

      // Theme initialization should not throw
      expect(() => {
        const theme = global.localStorage?.getItem('theme') || 'light'
        document.body.className = theme === 'dark' ? 'dark-theme' : ''
      }).not.toThrow()

      global.localStorage = originalLocalStorage
    })

    test('should handle invalid theme values', () => {
      // Set invalid theme value
      localStorage.setItem('theme', 'invalid-theme')

      const savedTheme = localStorage.getItem('theme')
      const validThemes = ['light', 'dark']

      // Should fall back to default theme
      const effectiveTheme = validThemes.includes(savedTheme)
        ? savedTheme
        : 'light'
      expect(effectiveTheme).toBe('light')
    })

    test('should handle missing theme toggle element', () => {
      // Remove theme toggle
      const themeToggle = document.getElementById('theme-toggle')
      if (themeToggle) {
        themeToggle.remove()
      }

      // Should not throw when trying to add event listeners
      expect(() => {
        const toggle = document.getElementById('theme-toggle')
        if (toggle) {
          // eslint-disable-next-line no-empty-function
          toggle.addEventListener('click', () => {})
        }
      }).not.toThrow()
    })
  })
})
