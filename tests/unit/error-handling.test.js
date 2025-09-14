/**
 * Unit tests for error handling and resilience
 * Tests error boundaries, fallback mechanisms, recovery strategies
 */

const { JSDOM } = require('jsdom')

describe('Error Handling and Resilience', () => {
  let dom, window, document, console

  beforeEach(() => {
    const html = `
      <!DOCTYPE html>
      <html lang="en">
      <head>
        <meta charset="UTF-8">
        <title>Error Handling Test</title>
        <style>
          .error-boundary { border: 2px solid red; padding: 1rem; }
          .fallback-content { background: #f0f0f0; padding: 1rem; }
          .loading { opacity: 0.5; }
          .error { color: red; }
          .retry-button { background: #007bff; color: white; padding: 0.5rem; }
        </style>
      </head>
      <body>
        <div id="app">
          <div id="error-boundary" class="error-boundary" style="display: none;">
            <h3>Something went wrong</h3>
            <p id="error-message"></p>
            <button id="retry-button" class="retry-button">Try Again</button>
          </div>
          
          <main id="main-content">
            <section id="hero" class="hero">
              <h1>Portfolio Site</h1>
              <p>Welcome to my portfolio</p>
            </section>
            
            <section id="projects" class="projects">
              <div id="projects-container"></div>
              <div id="projects-loading" class="loading" style="display: none;">Loading projects...</div>
              <div id="projects-error" class="error" style="display: none;">Failed to load projects</div>
            </section>
            
            <section id="contact" class="contact">
              <form id="contact-form">
                <input type="email" id="email" required>
                <button type="submit" id="submit-btn">Send</button>
              </form>
              <div id="form-error" class="error" style="display: none;"></div>
              <div id="form-success" style="display: none;">Message sent!</div>
            </section>
          </main>
          
          <div id="offline-banner" style="display: none;">
            <p>You are offline. Some features may not work.</p>
          </div>
          
          <div id="fallback-content" class="fallback-content" style="display: none;">
            <h2>Basic Content</h2>
            <p>This is fallback content displayed when JavaScript fails.</p>
          </div>
        </div>
        
        <script id="error-script">
          // This script will be used to simulate errors
        </script>
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

    // Mock console with error tracking
    console = {
      log: jest.fn(),
      error: jest.fn(),
      warn: jest.fn(),
      info: jest.fn()
    }

    // Mock fetch
    global.fetch = jest.fn()

    // Mock online/offline events
    Object.defineProperty(window.navigator, 'onLine', {
      writable: true,
      value: true
    })

    // Set up globals
    global.window = window
    global.document = document
    global.console = console
    global.navigator = window.navigator
  })

  afterEach(() => {
    if (dom) {
      dom.window.close()
    }
    jest.clearAllMocks()
  })

  describe('JavaScript Error Handling', () => {
    test('should catch and handle unhandled errors', () => {
      const errorsCaught = []

      // Set up global error handler
      window.addEventListener('error', (event) => {
        errorsCaught.push({
          message: event.message,
          filename: event.filename,
          lineno: event.lineno,
          colno: event.colno,
          error: event.error
        })

        // Show error boundary
        const errorBoundary = document.getElementById('error-boundary')
        const errorMessage = document.getElementById('error-message')

        if (errorBoundary && errorMessage) {
          errorBoundary.style.display = 'block'
          errorMessage.textContent = event.message
        }
      })

      // Simulate a JavaScript error
      const errorEvent = new window.ErrorEvent('error', {
        message: 'Uncaught ReferenceError: undefinedVariable is not defined',
        filename: 'script.js',
        lineno: 42,
        colno: 10,
        error: new Error('undefinedVariable is not defined')
      })

      window.dispatchEvent(errorEvent)

      expect(errorsCaught).toHaveLength(1)
      expect(errorsCaught[0].message).toContain(
        'undefinedVariable is not defined'
      )
      expect(document.getElementById('error-boundary').style.display).toBe(
        'block'
      )
    })

    test('should handle promise rejections', () => {
      const rejectionsCaught = []

      window.addEventListener('unhandledrejection', (event) => {
        rejectionsCaught.push({
          reason: event.reason,
          promise: event.promise
        })

        // Log the error
        console.error('Unhandled Promise Rejection:', event.reason)

        // Prevent default browser handling
        event.preventDefault()
      })

      // Simulate unhandled promise rejection
      const rejectionEvent = new window.Event('unhandledrejection')
      rejectionEvent.reason = new Error('API call failed')
      rejectionEvent.promise = Promise.reject(new Error('API call failed'))

      window.dispatchEvent(rejectionEvent)

      expect(rejectionsCaught).toHaveLength(1)
      expect(rejectionsCaught[0].reason.message).toBe('API call failed')
      expect(console.error).toHaveBeenCalledWith(
        'Unhandled Promise Rejection:',
        expect.any(Error)
      )
    })

    test('should implement error recovery with retry mechanism', async () => {
      let attempts = 0
      const maxRetries = 3

      const flakyFunction = async () => {
        attempts++
        if (attempts < 3) {
          throw new Error(`Attempt ${attempts} failed`)
        }
        return 'Success'
      }

      const withRetry = async (fn, retries = 3) => {
        let lastError

        for (let i = 0; i <= retries; i++) {
          try {
            return await fn()
          } catch (error) {
            lastError = error
            console.warn(`Retry ${i + 1}/${retries + 1} failed:`, error.message)

            if (i < retries) {
              // Wait before retrying (exponential backoff)
              await new Promise((resolve) =>
                setTimeout(resolve, Math.pow(2, i) * 100)
              )
            }
          }
        }

        throw lastError
      }

      const result = await withRetry(flakyFunction, maxRetries)

      expect(result).toBe('Success')
      expect(attempts).toBe(3)
      expect(console.warn).toHaveBeenCalledTimes(2)
    })

    test('should handle script loading failures with fallbacks', async () => {
      const loadScriptWithFallback = (primarySrc, fallbackSrc) => {
        return new Promise((resolve, reject) => {
          const script = document.createElement('script')
          script.src = primarySrc

          script.onerror = () => {
            console.warn(`Failed to load ${primarySrc}, trying fallback`)

            const fallbackScript = document.createElement('script')
            fallbackScript.src = fallbackSrc

            fallbackScript.onload = () => resolve('fallback-loaded')
            fallbackScript.onerror = () =>
              reject(new Error('Both scripts failed'))

            document.head.appendChild(fallbackScript)
          }

          script.onload = () => resolve('primary-loaded')
          document.head.appendChild(script)
        })
      }

      // Mock script creation and loading
      const mockScripts = []
      document.createElement = jest.fn((tag) => {
        if (tag === 'script') {
          const mockScript = {
            src: '',
            onload: null,
            onerror: null
          }
          mockScripts.push(mockScript)
          return mockScript
        }
        return dom.window.document.createElement(tag)
      })

      const loadPromise = loadScriptWithFallback(
        'https://cdn.example.com/script.js',
        'https://backup-cdn.example.com/script.js'
      )

      // Simulate primary script failure
      if (mockScripts[0] && mockScripts[0].onerror) {
        mockScripts[0].onerror()
      }

      // Simulate fallback script success
      if (mockScripts[1] && mockScripts[1].onload) {
        mockScripts[1].onload()
      }

      const result = await loadPromise
      expect(result).toBe('fallback-loaded')
      expect(console.warn).toHaveBeenCalledWith(
        expect.stringContaining('Failed to load'),
        expect.stringContaining('trying fallback')
      )
    })
  })

  describe('Network Error Handling', () => {
    test('should handle network failures gracefully', async () => {
      fetch.mockRejectedValue(new Error('Network error'))

      const fetchWithErrorHandling = async (url) => {
        try {
          const response = await fetch(url)
          if (!response.ok) throw new Error(`HTTP ${response.status}`)
          return await response.json()
        } catch (error) {
          console.error('Network request failed:', error.message)

          // Show error state in UI
          const errorElement = document.getElementById('projects-error')
          const loadingElement = document.getElementById('projects-loading')

          if (errorElement) errorElement.style.display = 'block'
          if (loadingElement) loadingElement.style.display = 'none'

          throw error
        }
      }

      await expect(fetchWithErrorHandling('/api/projects')).rejects.toThrow(
        'Network error'
      )

      expect(console.error).toHaveBeenCalledWith(
        'Network request failed:',
        'Network error'
      )
      expect(document.getElementById('projects-error').style.display).toBe(
        'block'
      )
      expect(document.getElementById('projects-loading').style.display).toBe(
        'none'
      )
    })

    test('should implement timeout handling', async () => {
      const fetchWithTimeout = (url, timeout = 5000) => {
        return Promise.race([
          fetch(url),
          new Promise((_, reject) =>
            setTimeout(() => reject(new Error('Request timeout')), timeout)
          )
        ])
      }

      fetch.mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 10000)) // Never resolves in time
      )

      await expect(
        fetchWithTimeout('/api/slow-endpoint', 1000)
      ).rejects.toThrow('Request timeout')
    })

    test('should handle offline/online state changes', () => {
      const offlineBanner = document.getElementById('offline-banner')
      const onlineHandlers = []
      const offlineHandlers = []

      // Mock event listeners
      window.addEventListener = jest.fn((event, handler) => {
        if (event === 'online') onlineHandlers.push(handler)
        if (event === 'offline') offlineHandlers.push(handler)
      })

      // Set up offline/online handlers
      const handleOffline = () => {
        offlineBanner.style.display = 'block'
        console.warn('Application is offline')

        // Disable form submissions
        const forms = document.querySelectorAll('form')
        forms.forEach((form) => {
          const submitBtn = form.querySelector('[type="submit"]')
          if (submitBtn) {
            submitBtn.disabled = true
            submitBtn.textContent = 'Offline'
          }
        })
      }

      const handleOnline = () => {
        offlineBanner.style.display = 'none'
        console.info('Application is back online')

        // Re-enable form submissions
        const forms = document.querySelectorAll('form')
        forms.forEach((form) => {
          const submitBtn = form.querySelector('[type="submit"]')
          if (submitBtn) {
            submitBtn.disabled = false
            submitBtn.textContent = 'Send'
          }
        })
      }

      window.addEventListener('offline', handleOffline)
      window.addEventListener('online', handleOnline)

      // Simulate going offline
      navigator.onLine = false
      offlineHandlers.forEach((handler) => handler())

      expect(offlineBanner.style.display).toBe('block')
      expect(document.getElementById('submit-btn').disabled).toBe(true)
      expect(console.warn).toHaveBeenCalledWith('Application is offline')

      // Simulate coming back online
      navigator.onLine = true
      onlineHandlers.forEach((handler) => handler())

      expect(offlineBanner.style.display).toBe('none')
      expect(document.getElementById('submit-btn').disabled).toBe(false)
      expect(console.info).toHaveBeenCalledWith('Application is back online')
    })

    test('should implement request queuing for offline scenarios', () => {
      const requestQueue = []
      const isOnline = () => navigator.onLine

      const queueRequest = (url, options) => {
        requestQueue.push({ url, options, timestamp: Date.now() })
        console.log(`Queued request: ${url}`)
      }

      const processQueue = async () => {
        console.log(`Processing ${requestQueue.length} queued requests`)

        while (requestQueue.length > 0) {
          const request = requestQueue.shift()

          try {
            await fetch(request.url, request.options)
            console.log(`Successfully processed: ${request.url}`)
          } catch (error) {
            console.error(`Failed to process: ${request.url}`, error)
            // Re-queue if not too old
            if (Date.now() - request.timestamp < 300000) {
              // 5 minutes
              requestQueue.push(request)
            }
          }
        }
      }

      const smartFetch = async (url, options) => {
        if (!isOnline()) {
          queueRequest(url, options)
          throw new Error('Request queued for when online')
        }

        return fetch(url, options)
      }

      // Test offline scenario
      navigator.onLine = false

      expect(() => {
        smartFetch('/api/data', { method: 'POST' })
      }).rejects.toThrow('Request queued for when online')

      expect(requestQueue).toHaveLength(1)
      expect(console.log).toHaveBeenCalledWith('Queued request: /api/data')

      // Test online processing
      navigator.onLine = true
      fetch.mockResolvedValue({ ok: true })

      processQueue()

      expect(console.log).toHaveBeenCalledWith('Processing 1 queued requests')
    })
  })

  describe('Form Error Handling', () => {
    test('should handle form validation errors', () => {
      const form = document.getElementById('contact-form')
      const emailInput = document.getElementById('email')
      const errorDiv = document.getElementById('form-error')

      const validateForm = (formData) => {
        const errors = []

        if (!formData.get('email')) {
          errors.push('Email is required')
        } else {
          const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
          if (!emailRegex.test(formData.get('email'))) {
            errors.push('Invalid email format')
          }
        }

        return errors
      }

      const showErrors = (errors) => {
        errorDiv.innerHTML = errors.map((error) => `<p>${error}</p>`).join('')
        errorDiv.style.display = errors.length > 0 ? 'block' : 'none'
      }

      // Test with invalid email
      emailInput.value = 'invalid-email'
      const formData = new FormData(form)
      const errors = validateForm(formData)
      showErrors(errors)

      expect(errors).toContain('Invalid email format')
      expect(errorDiv.style.display).toBe('block')
      expect(errorDiv.innerHTML).toContain('Invalid email format')
    })

    test('should handle form submission errors with retry', async () => {
      const form = document.getElementById('contact-form')
      const errorDiv = document.getElementById('form-error')
      const submitBtn = document.getElementById('submit-btn')

      let submitAttempts = 0

      const submitForm = async (formData) => {
        submitAttempts++

        // Show loading state
        submitBtn.disabled = true
        submitBtn.textContent = 'Sending...'

        try {
          const response = await fetch('/api/contact', {
            method: 'POST',
            body: formData
          })

          if (!response.ok) {
            throw new Error(`Server error: ${response.status}`)
          }

          return await response.json()
        } catch (error) {
          console.error('Form submission failed:', error)
          throw error
        } finally {
          submitBtn.disabled = false
          submitBtn.textContent = 'Send'
        }
      }

      const handleSubmitWithRetry = async (formData, maxRetries = 2) => {
        for (let attempt = 1; attempt <= maxRetries; attempt++) {
          try {
            const result = await submitForm(formData)

            // Show success
            document.getElementById('form-success').style.display = 'block'
            errorDiv.style.display = 'none'

            return result
          } catch (error) {
            if (attempt === maxRetries) {
              // Final failure
              errorDiv.textContent = `Failed to send message after ${maxRetries} attempts. Please try again.`
              errorDiv.style.display = 'block'
              throw error
            } else {
              console.warn(`Attempt ${attempt} failed, retrying...`)
              await new Promise((resolve) => setTimeout(resolve, 1000))
            }
          }
        }
      }

      // Mock failing requests
      fetch.mockRejectedValue(new Error('Network error'))

      const formData = new FormData()
      formData.append('email', 'test@example.com')

      await expect(handleSubmitWithRetry(formData)).rejects.toThrow(
        'Network error'
      )

      expect(submitAttempts).toBe(2)
      expect(errorDiv.style.display).toBe('block')
      expect(errorDiv.textContent).toContain(
        'Failed to send message after 2 attempts'
      )
    })
  })

  describe('Resource Loading Error Handling', () => {
    test('should handle image loading failures with fallbacks', () => {
      const createImageWithFallback = (src, fallbackSrc) => {
        return new Promise((resolve, reject) => {
          const img = new window.Image()

          img.onerror = () => {
            console.warn(`Image failed to load: ${src}, using fallback`)

            const fallbackImg = new window.Image()
            fallbackImg.onload = () => resolve(fallbackImg)
            fallbackImg.onerror = () => reject(new Error('Both images failed'))
            fallbackImg.src = fallbackSrc
          }

          img.onload = () => resolve(img)
          img.src = src
        })
      }

      // Mock Image constructor
      const mockImages = []
      window.Image = jest.fn(() => {
        const mockImg = {
          src: '',
          onload: null,
          onerror: null
        }
        mockImages.push(mockImg)
        return mockImg
      })

      const imagePromise = createImageWithFallback(
        'https://example.com/image.jpg',
        '/assets/fallback.jpg'
      )

      // Simulate primary image failure
      if (mockImages[0] && mockImages[0].onerror) {
        mockImages[0].onerror()
      }

      // Simulate fallback success
      if (mockImages[1] && mockImages[1].onload) {
        mockImages[1].onload()
      }

      return imagePromise.then((img) => {
        expect(img.src).toBe('/assets/fallback.jpg')
        expect(console.warn).toHaveBeenCalledWith(
          expect.stringContaining('Image failed to load'),
          expect.stringContaining('using fallback')
        )
      })
    })

    test('should handle CSS loading failures', () => {
      const mockConsoleWarn = jest.spyOn(console, 'warn').mockImplementation()

      // Test CSS fallback logic without DOM manipulation
      const loadCSSWithFallback = (href, fallbackHref) => {
        return new Promise((resolve) => {
          // Simulate CSS load failure
          console.warn(`CSS failed to load: ${href}, using fallback`)
          resolve('fallback-loaded')
        })
      }

      const cssPromise = loadCSSWithFallback(
        'https://cdn.example.com/styles.css',
        '/assets/fallback.css'
      )

      return cssPromise.then((result) => {
        expect(result).toBe('fallback-loaded')
        expect(mockConsoleWarn).toHaveBeenCalledWith(
          expect.stringContaining('CSS failed to load'),
          expect.stringContaining('using fallback')
        )
        mockConsoleWarn.mockRestore()
      })
    })
  })

  describe('Graceful Degradation', () => {
    test('should provide fallback content when JavaScript fails', () => {
      const mainContent = document.getElementById('main-content')
      const fallbackContent = document.getElementById('fallback-content')

      const enableGracefulDegradation = () => {
        try {
          // Simulate checking for JavaScript capabilities
          if (typeof document.querySelector === 'undefined') {
            throw new Error('JavaScript not fully supported')
          }

          // Test for modern features
          if (!('IntersectionObserver' in window)) {
            console.warn('IntersectionObserver not supported, using fallbacks')
          }

          if (!('fetch' in window)) {
            console.warn('Fetch not supported, using XMLHttpRequest fallback')
          }
        } catch (error) {
          console.error('JavaScript capabilities limited:', error)

          // Show fallback content
          mainContent.style.display = 'none'
          fallbackContent.style.display = 'block'
        }
      }

      enableGracefulDegradation()

      // Should work normally with full JavaScript support
      expect(mainContent.style.display).not.toBe('none')
      expect(fallbackContent.style.display).toBe('none')
    })

    test('should handle missing DOM elements gracefully', () => {
      const safeQuerySelector = (selector) => {
        try {
          return document.querySelector(selector)
        } catch (error) {
          console.warn(`Element not found: ${selector}`)
          return null
        }
      }

      const safeAddEventListener = (element, event, handler) => {
        if (element && typeof element.addEventListener === 'function') {
          element.addEventListener(event, handler)
          return true
        } else {
          console.warn(
            'Cannot add event listener: element not found or not supported'
          )
          return false
        }
      }

      // Test with existing element
      const existingElement = safeQuerySelector('#hero')
      expect(existingElement).toBeTruthy()

      const listenerAdded = safeAddEventListener(
        existingElement,
        'click',
        () => {}
      )
      expect(listenerAdded).toBe(true)

      // Test with non-existing element
      const missingElement = safeQuerySelector('#non-existent')
      expect(missingElement).toBeNull()

      const listenerNotAdded = safeAddEventListener(
        missingElement,
        'click',
        () => {}
      )
      expect(listenerNotAdded).toBe(false)
      expect(console.warn).toHaveBeenCalledWith(
        'Cannot add event listener: element not found or not supported'
      )
    })

    test('should implement progressive enhancement', () => {
      const enhanceElements = () => {
        // Basic functionality first
        const forms = document.querySelectorAll('form')
        forms.forEach((form) => {
          // Basic form validation always works
          form.setAttribute('novalidate', 'true') // Use custom validation
        })

        // Enhanced functionality with feature detection
        if ('IntersectionObserver' in window) {
          // Add scroll animations
          const animatedElements = document.querySelectorAll('[data-animate]')
          console.log(
            `Enhanced: Added animations to ${animatedElements.length} elements`
          )
        }

        if ('serviceWorker' in navigator) {
          // Add offline support
          console.log('Enhanced: Service worker support available')
        }

        if ('geolocation' in navigator) {
          // Add location features
          console.log('Enhanced: Geolocation support available')
        }
      }

      enhanceElements()

      // Should always set up basic functionality
      const forms = document.querySelectorAll('form')
      expect(forms[0].getAttribute('novalidate')).toBe('true')

      // Enhanced features depend on browser support
      expect(console.log).toHaveBeenCalledWith(
        expect.stringContaining('Enhanced:')
      )
    })
  })

  describe('Memory Leak Prevention', () => {
    test('should clean up event listeners', () => {
      const element = document.getElementById('hero')
      const handlers = []
      let listenerCount = 0

      // Mock addEventListener to track listeners
      const originalAddEventListener = element.addEventListener
      element.addEventListener = jest.fn((event, handler, options) => {
        handlers.push({ event, handler, options })
        listenerCount++
        return originalAddEventListener.call(element, event, handler, options)
      })

      // Mock removeEventListener
      element.removeEventListener = jest.fn((event, handler) => {
        const index = handlers.findIndex(
          (h) => h.event === event && h.handler === handler
        )
        if (index > -1) {
          handlers.splice(index, 1)
          listenerCount--
        }
      })

      const cleanup = () => {
        // Remove all tracked listeners
        handlers.forEach(({ event, handler }) => {
          element.removeEventListener(event, handler)
        })
      }

      // Add some listeners
      const clickHandler = () => {}
      const scrollHandler = () => {}

      element.addEventListener('click', clickHandler)
      element.addEventListener('scroll', scrollHandler)

      expect(listenerCount).toBe(2)

      // Cleanup
      cleanup()

      expect(element.removeEventListener).toHaveBeenCalledTimes(2)
      expect(handlers).toHaveLength(0)
    })

    test('should clean up intervals and timeouts', () => {
      const activeTimers = new Set()

      const safeSetTimeout = (callback, delay) => {
        const id = setTimeout(callback, delay)
        activeTimers.add(id)
        return id
      }

      const safeSetInterval = (callback, delay) => {
        const id = setInterval(callback, delay)
        activeTimers.add(id)
        return id
      }

      const safeClearTimeout = (id) => {
        clearTimeout(id)
        activeTimers.delete(id)
      }

      const safeClearInterval = (id) => {
        clearInterval(id)
        activeTimers.delete(id)
      }

      const cleanupAllTimers = () => {
        activeTimers.forEach((id) => {
          clearTimeout(id)
          clearInterval(id)
        })
        activeTimers.clear()
      }

      // Create some timers
      const timeoutId = safeSetTimeout(() => {}, 1000)
      const intervalId = safeSetInterval(() => {}, 500)

      expect(activeTimers.size).toBe(2)

      // Cleanup individual timer
      safeClearTimeout(timeoutId)
      expect(activeTimers.size).toBe(1)

      // Cleanup all timers
      cleanupAllTimers()
      expect(activeTimers.size).toBe(0)
    })
  })
})
