/**
 * Unit tests for external API integrations
 * Tests GitHub API, social media widgets, analytics, and third-party services
 */

/* eslint-env jest, node */
/* eslint-disable prefer-destructuring, consistent-return, promise/param-names */

const { JSDOM } = require('jsdom')

// Mock fetch globally
global.fetch = jest.fn()

describe('External API Integrations', () => {
  let dom, window, document, originalCreateElement

  beforeEach(() => {
    const html = `
      <!DOCTYPE html>
      <html lang="en">
      <head>
        <meta charset="UTF-8">
        <title>API Integration Test</title>
      </head>
      <body>
        <div id="github-repos" class="github-section">
          <h3>GitHub Repositories</h3>
          <div class="repos-container" id="repos-container"></div>
          <div class="loading" id="loading">Loading repositories...</div>
          <div class="error hidden" id="error-message">Error loading repositories</div>
        </div>

        <div id="github-stats" class="stats-section">
          <div class="stat-item" data-stat="followers">
            <span class="stat-value" id="followers-count">-</span>
            <span class="stat-label">Followers</span>
          </div>
          <div class="stat-item" data-stat="repos">
            <span class="stat-value" id="repos-count">-</span>
            <span class="stat-label">Repositories</span>
          </div>
        </div>

        <div id="social-widgets">
          <div class="twitter-widget" data-widget="timeline"></div>
          <div class="linkedin-badge" data-profile="username"></div>
        </div>

        <div id="analytics-tracker" data-ga-id="UA-123456789-1"></div>

        <form id="contact-form" class="contact-form">
          <input type="text" name="name" required>
          <input type="email" name="email" required>
          <textarea name="message" required></textarea>
          <button type="submit">Send</button>
        </form>
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

    // Save original createElement for restoration after each test
    originalCreateElement = document.createElement.bind(document)

    // Mock console methods
    window.console = {
      log: jest.fn(),
      error: jest.fn(),
      warn: jest.fn()
    }

    // Mock performance API
    Object.defineProperty(window, 'performance', {
      value: {
        now: jest.fn(() => Date.now())
      },
      writable: true
    })

    // Set up globals
    global.window = window
    global.document = document
    global.console = window.console

    // Reset fetch mock
    fetch.mockClear()
  })

  afterEach(() => {
    // Restore all mocks to prevent test pollution
    jest.restoreAllMocks()

    // Restore original document.createElement
    if (document && originalCreateElement) {
      document.createElement = originalCreateElement
    }

    if (dom) {
      dom.window.close()
    }
  })

  describe('GitHub API integration', () => {
    const mockUserData = {
      login: 'testuser',
      name: 'Test User',
      followers: 42,
      public_repos: 15,
      avatar_url: 'https://github.com/avatar.jpg',
      html_url: 'https://github.com/testuser'
    }

    const mockReposData = [
      {
        id: 1,
        name: 'awesome-project',
        description: 'An awesome project',
        html_url: 'https://github.com/testuser/awesome-project',
        stargazers_count: 25,
        language: 'JavaScript',
        updated_at: '2023-01-15T10:00:00Z'
      },
      {
        id: 2,
        name: 'cool-library',
        description: 'A cool library',
        html_url: 'https://github.com/testuser/cool-library',
        stargazers_count: 8,
        language: 'Python',
        updated_at: '2023-01-10T15:30:00Z'
      }
    ]

    test('should fetch and display GitHub user stats', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockUserData
      })

      // Simulate GitHub API call
      const fetchGitHubUser = async username => {
        const response = await fetch(`https://api.github.com/users/${username}`)
        if (!response.ok) throw new Error('Failed to fetch user')
        return response.json()
      }

      const updateUserStats = userData => {
        document.getElementById('followers-count').textContent =
          userData.followers
        document.getElementById('repos-count').textContent =
          userData.public_repos
      }

      const userData = await fetchGitHubUser('testuser')
      updateUserStats(userData)

      expect(fetch).toHaveBeenCalledWith(
        'https://api.github.com/users/testuser'
      )
      expect(document.getElementById('followers-count').textContent).toBe('42')
      expect(document.getElementById('repos-count').textContent).toBe('15')
    })

    test('should fetch and display GitHub repositories', async () => {
      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockReposData
      })

      const fetchGitHubRepos = async (username, limit = 10) => {
        const response = await fetch(
          `https://api.github.com/users/${username}/repos?sort=updated&per_page=${limit}`
        )
        if (!response.ok) throw new Error('Failed to fetch repositories')
        return response.json()
      }

      const displayRepositories = repos => {
        const container = document.getElementById('repos-container')
        container.innerHTML = ''

        repos.forEach(repo => {
          const repoElement = document.createElement('div')
          repoElement.className = 'repo-card'
          repoElement.innerHTML = `
            <h4><a href="${repo.html_url}" target="_blank">${repo.name}</a></h4>
            <p>${repo.description || 'No description'}</p>
            <div class="repo-meta">
              <span class="language">${repo.language || 'Unknown'}</span>
              <span class="stars">★ ${repo.stargazers_count}</span>
            </div>
          `
          container.appendChild(repoElement)
        })

        document.getElementById('loading').style.display = 'none'
      }

      const repos = await fetchGitHubRepos('testuser', 5)
      displayRepositories(repos)

      expect(fetch).toHaveBeenCalledWith(
        'https://api.github.com/users/testuser/repos?sort=updated&per_page=5'
      )

      const repoCards = document.querySelectorAll('.repo-card')
      expect(repoCards.length).toBe(2)
      expect(repoCards[0].querySelector('h4 a').textContent).toBe(
        'awesome-project'
      )
      expect(repoCards[0].querySelector('.stars').textContent).toBe('★ 25')
    })

    test('should handle GitHub API rate limiting', async () => {
      fetch.mockResolvedValueOnce({
        ok: false,
        status: 403,
        json: async () => ({
          message: 'API rate limit exceeded'
        })
      })

      const fetchWithRateLimit = async url => {
        const response = await fetch(url)

        if (response.status === 403) {
          const errorData = await response.json()
          if (errorData.message.includes('rate limit')) {
            throw new Error(
              'GitHub API rate limit exceeded. Please try again later.'
            )
          }
        }

        if (!response.ok) throw new Error('API request failed')
        return response.json()
      }

      await expect(
        fetchWithRateLimit('https://api.github.com/users/testuser')
      ).rejects.toThrow('GitHub API rate limit exceeded')

      expect(fetch).toHaveBeenCalledWith(
        'https://api.github.com/users/testuser'
      )
    })

    test('should implement caching for API responses', async () => {
      const cache = new Map()
      const CACHE_DURATION = 5 * 60 * 1000 // 5 minutes

      const fetchWithCache = async url => {
        const cached = cache.get(url)
        const now = Date.now()

        if (cached && now - cached.timestamp < CACHE_DURATION) {
          return cached.data
        }

        const response = await fetch(url)
        if (!response.ok) throw new Error('API request failed')

        const data = await response.json()
        cache.set(url, { data, timestamp: now })

        return data
      }

      fetch.mockResolvedValue({
        ok: true,
        json: async () => mockUserData
      })

      // First call should hit the API
      await fetchWithCache('https://api.github.com/users/testuser')
      expect(fetch).toHaveBeenCalledTimes(1)

      // Second call should use cache
      await fetchWithCache('https://api.github.com/users/testuser')
      expect(fetch).toHaveBeenCalledTimes(1) // Still only one call

      expect(cache.has('https://api.github.com/users/testuser')).toBe(true)
    })

    test('should handle network errors gracefully', async () => {
      fetch.mockRejectedValueOnce(new Error('Network error'))

      const handleApiError = error => {
        // eslint-disable-next-line no-console
        console.error('GitHub API Error:', error.message)
        document.getElementById('loading').style.display = 'none'
        document.getElementById('error-message').classList.remove('hidden')
      }

      try {
        await fetch('https://api.github.com/users/testuser')
      } catch (error) {
        handleApiError(error)
      }

      // eslint-disable-next-line no-console
      expect(console.error).toHaveBeenCalledWith(
        'GitHub API Error:',
        'Network error'
      )
      expect(
        document.getElementById('error-message').classList.contains('hidden')
      ).toBe(false)
    })
  })

  describe('Social media widget integration', () => {
    test('should load Twitter widget script', () => {
      const loadTwitterWidget = () => {
        return new Promise((resolve, reject) => {
          const script = document.createElement('script')
          script.src = 'https://platform.twitter.com/widgets.js'
          script.async = true
          script.onload = resolve
          script.onerror = reject
          document.head.appendChild(script)
        })
      }

      // Execute function to create script element
      loadTwitterWidget()

      // Find the added script element
      const addedScript = document.querySelector(
        'script[src="https://platform.twitter.com/widgets.js"]'
      )

      expect(addedScript).toBeTruthy()
      expect(addedScript.src).toBe('https://platform.twitter.com/widgets.js')
      expect(addedScript.async).toBe(true)
    })

    test('should handle Twitter widget loading failure', async () => {
      const loadTwitterWidget = () => {
        return new Promise((resolve, reject) => {
          const script = document.createElement('script')
          script.src = 'https://platform.twitter.com/widgets.js'
          script.onerror = () =>
            reject(new Error('Failed to load Twitter widgets'))
          document.head.appendChild(script)
        })
      }

      const promise = loadTwitterWidget()

      // Find the added script and manually trigger error
      const addedScript = document.querySelector(
        'script[src="https://platform.twitter.com/widgets.js"]'
      )

      // Manually trigger the onerror callback
      if (addedScript && addedScript.onerror) {
        addedScript.onerror()
      }

      await expect(promise).rejects.toThrow('Failed to load Twitter widgets')
    })

    test('should initialize LinkedIn badge', () => {
      const initLinkedInBadge = () => {
        const badge = document.querySelector('.linkedin-badge')
        if (!badge) return

        const profile = badge.getAttribute('data-profile')
        if (profile) {
          badge.innerHTML = `
            <div class="linkedin-content">
              <a href="https://linkedin.com/in/${profile}" target="_blank">
                LinkedIn Profile
              </a>
            </div>
          `
        }
      }

      initLinkedInBadge()

      const badge = document.querySelector('.linkedin-badge')
      const link = badge.querySelector('a')

      expect(link.href).toBe('https://linkedin.com/in/username')
      expect(link.target).toBe('_blank')
    })
  })

  describe('Analytics integration', () => {
    test('should initialize Google Analytics', () => {
      const initGA = trackingId => {
        // Simulate GA initialization
        window.dataLayer = window.dataLayer || []
        window.gtag = function () {
          // Convert arguments to array and push
          window.dataLayer.push(Array.from(arguments))
        }

        window.gtag('config', trackingId)
      }

      initGA('UA-123456789-1')

      expect(window.dataLayer).toBeDefined()
      expect(window.gtag).toBeDefined()
      expect(window.dataLayer).toContainEqual(['config', 'UA-123456789-1'])
    })

    test('should track page views', () => {
      window.dataLayer = []
      window.gtag = function () {
        // Convert arguments to array and push
        window.dataLayer.push(Array.from(arguments))
      }

      const trackPageView = path => {
        window.gtag('event', 'page_view', {
          page_location: `${window.location.origin}${path}`,
          page_path: path
        })
      }

      trackPageView('/about')

      expect(window.dataLayer).toContainEqual([
        'event',
        'page_view',
        {
          page_location: 'http://localhost:3000/about',
          page_path: '/about'
        }
      ])
    })

    test('should track custom events', () => {
      window.dataLayer = []
      window.gtag = function () {
        // Convert arguments to array and push
        window.dataLayer.push(Array.from(arguments))
      }

      const trackEvent = (action, category, label, value) => {
        window.gtag('event', action, {
          event_category: category,
          event_label: label,
          value
        })
      }

      trackEvent('click', 'button', 'hero-cta', 1)

      expect(window.dataLayer).toContainEqual([
        'event',
        'click',
        {
          event_category: 'button',
          event_label: 'hero-cta',
          value: 1
        }
      ])
    })

    test('should handle analytics opt-out', () => {
      // Mock navigator.doNotTrack BEFORE defining the function
      Object.defineProperty(window.navigator, 'doNotTrack', {
        value: '1',
        writable: true,
        configurable: true
      })

      const handleAnalyticsOptOut = () => {
        // Check for DNT header or user preference
        const dntEnabled = window.navigator.doNotTrack === '1'
        const optedOut = localStorage.getItem('analytics-opt-out') === 'true'

        return dntEnabled || optedOut
      }

      const shouldSkipAnalytics = handleAnalyticsOptOut()
      expect(shouldSkipAnalytics).toBe(true)
    })
  })

  describe('Form submission to external services', () => {
    test('should submit contact form to external service', async () => {
      const mockFormData = {
        name: 'John Doe',
        email: 'john@example.com',
        message: 'Hello world'
      }

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({ success: true, id: 'msg-123' })
      })

      const submitContactForm = async formData => {
        const response = await fetch('/api/contact', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(formData)
        })

        if (!response.ok) throw new Error('Form submission failed')
        return response.json()
      }

      const result = await submitContactForm(mockFormData)

      expect(fetch).toHaveBeenCalledWith('/api/contact', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(mockFormData)
      })

      expect(result.success).toBe(true)
      expect(result.id).toBe('msg-123')
    })

    test('should handle form submission errors', async () => {
      fetch.mockResolvedValueOnce({
        ok: false,
        status: 400,
        json: async () => ({ error: 'Invalid email format' })
      })

      const submitForm = async formData => {
        const response = await fetch('/api/contact', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(formData)
        })

        if (!response.ok) {
          const errorData = await response.json()
          throw new Error(errorData.error || 'Form submission failed')
        }

        return response.json()
      }

      await expect(submitForm({ email: 'invalid-email' })).rejects.toThrow(
        'Invalid email format'
      )
    })

    test('should implement form submission with retry logic', async () => {
      let attempts = 0
      fetch.mockImplementation(() => {
        attempts++
        if (attempts < 3) {
          return Promise.reject(new Error('Network error'))
        }
        return Promise.resolve({
          ok: true,
          json: async () => ({ success: true })
        })
      })

      const submitWithRetry = async (formData, maxRetries = 3) => {
        let lastError

        for (let i = 0; i < maxRetries; i++) {
          try {
            const response = await fetch('/api/contact', {
              method: 'POST',
              body: JSON.stringify(formData)
            })

            if (!response.ok) throw new Error('HTTP error')
            return response.json()
          } catch (error) {
            lastError = error
            if (i < maxRetries - 1) {
              await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)))
            }
          }
        }

        throw lastError
      }

      const result = await submitWithRetry({ name: 'Test' })
      expect(result.success).toBe(true)
      expect(attempts).toBe(3)
    })
  })

  describe('External script loading and management', () => {
    test('should load external scripts asynchronously', () => {
      const loadScript = (src, options = {}) => {
        return new Promise((resolve, reject) => {
          const script = document.createElement('script')
          script.src = src
          script.async = options.async !== false
          script.defer = options.defer === true
          script.onload = resolve
          script.onerror = reject

          if (options.attributes) {
            Object.entries(options.attributes).forEach(([key, value]) => {
              script.setAttribute(key, value)
            })
          }

          document.head.appendChild(script)
        })
      }

      loadScript('https://example.com/widget.js', {
        async: true,
        defer: true,
        attributes: { 'data-key': 'abc123' }
      })

      // Find the added script element
      const addedScript = document.querySelector(
        'script[src="https://example.com/widget.js"]'
      )

      expect(addedScript).toBeTruthy()
      expect(addedScript.src).toBe('https://example.com/widget.js')
      expect(addedScript.async).toBe(true)
      expect(addedScript.defer).toBe(true)
      expect(addedScript.getAttribute('data-key')).toBe('abc123')
    })

    test('should handle script loading timeouts', async () => {
      const loadScriptWithTimeout = (src, timeout = 10000) => {
        return Promise.race([
          new Promise((resolve, reject) => {
            const script = document.createElement('script')
            script.src = src
            script.onload = resolve
            script.onerror = reject
            document.head.appendChild(script)
          }),
          new Promise((_, reject) =>
            setTimeout(() => reject(new Error('Script load timeout')), timeout)
          )
        ])
      }

      const promise = loadScriptWithTimeout(
        'https://slow-script.com/widget.js',
        100
      )

      // Don't trigger onload/onerror, let the timeout promise win the race
      await expect(promise).rejects.toThrow('Script load timeout')
    })

    test('should manage script dependencies', async () => {
      const scriptManager = {
        loaded: new Set(),
        loading: new Map(),

        async load(src, dependencies = []) {
          if (this.loaded.has(src)) return

          if (this.loading.has(src)) {
            return this.loading.get(src)
          }

          // Wait for dependencies
          await Promise.all(dependencies.map(dep => this.load(dep)))

          const promise = new Promise((resolve, reject) => {
            const script = document.createElement('script')
            script.src = src
            script.onload = () => {
              this.loaded.add(src)
              this.loading.delete(src)
              resolve()
            }
            script.onerror = () => {
              this.loading.delete(src)
              reject(new Error(`Failed to load ${src}`))
            }
            document.head.appendChild(script)
          })

          this.loading.set(src, promise)
          return promise
        }
      }

      // Start loading (this will create jquery script first due to dependency)
      const loadPromise = scriptManager.load('https://example.com/widget.js', [
        'https://example.com/jquery.js'
      ])

      // Wait a bit for the jquery dependency script to be created
      await new Promise(resolve => setTimeout(resolve, 10))

      // Manually trigger onload for jquery dependency first
      const jqueryScript = document.querySelector(
        'script[src="https://example.com/jquery.js"]'
      )
      if (jqueryScript && jqueryScript.onload) {
        jqueryScript.onload()
      }

      // Wait for widget script to be created (after jquery loads)
      await new Promise(resolve => setTimeout(resolve, 10))

      // Then trigger onload for the main widget script
      const widgetScript = document.querySelector(
        'script[src="https://example.com/widget.js"]'
      )
      if (widgetScript && widgetScript.onload) {
        widgetScript.onload()
      }

      await loadPromise
      expect(scriptManager.loaded.has('https://example.com/jquery.js')).toBe(
        true
      )
      expect(scriptManager.loaded.has('https://example.com/widget.js')).toBe(
        true
      )
    })
  })

  describe('API error handling and resilience', () => {
    test('should implement exponential backoff for retries', async () => {
      let attempts = 0
      const delays = []

      fetch.mockImplementation(() => {
        attempts++
        return Promise.reject(new Error('API Error'))
      })

      const fetchWithBackoff = async (url, maxRetries = 3) => {
        for (let i = 0; i < maxRetries; i++) {
          try {
            return await fetch(url)
          } catch (error) {
            if (i === maxRetries - 1) throw error

            const delay = Math.pow(2, i) * 1000 // Exponential backoff
            delays.push(delay)
            await new Promise(resolve => setTimeout(resolve, delay))
          }
        }
      }

      await expect(
        fetchWithBackoff('https://api.example.com/data')
      ).rejects.toThrow('API Error')

      expect(attempts).toBe(3)
      expect(delays).toEqual([1000, 2000]) // 2^0 * 1000, 2^1 * 1000
    })

    test('should implement circuit breaker pattern', async () => {
      const circuitBreaker = {
        failures: 0,
        threshold: 3,
        timeout: 60000,
        state: 'CLOSED', // CLOSED, OPEN, HALF_OPEN
        lastFailureTime: null,

        async call(fn) {
          if (this.state === 'OPEN') {
            if (Date.now() - this.lastFailureTime > this.timeout) {
              this.state = 'HALF_OPEN'
            } else {
              throw new Error('Circuit breaker is OPEN')
            }
          }

          try {
            const result = await fn()
            if (this.state === 'HALF_OPEN') {
              this.state = 'CLOSED'
              this.failures = 0
            }
            return result
          } catch (error) {
            this.failures++
            this.lastFailureTime = Date.now()

            if (this.failures >= this.threshold) {
              this.state = 'OPEN'
            }

            throw error
          }
        }
      }

      const failingApi = () => Promise.reject(new Error('API Error'))

      // Trigger failures to open circuit
      for (let i = 0; i < 3; i++) {
        await expect(circuitBreaker.call(failingApi)).rejects.toThrow(
          'API Error'
        )
      }

      expect(circuitBreaker.state).toBe('OPEN')

      // Next call should be rejected by circuit breaker
      await expect(circuitBreaker.call(failingApi)).rejects.toThrow(
        'Circuit breaker is OPEN'
      )
    })
  })
})
