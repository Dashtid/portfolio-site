// Service Worker Configuration
const CACHE_VERSION = '4.1.0'
const CACHE_NAME = `dashti-portfolio-v${CACHE_VERSION}`
const API_CACHE_NAME = `dashti-api-v${CACHE_VERSION}`

// API cache settings
const API_CACHE_MAX_AGE = 24 * 60 * 60 * 1000 // 24 hours
const API_NETWORK_TIMEOUT = 5000 // 5 seconds

// Debug mode - set to false for production to reduce console noise
// Can be enabled via: navigator.serviceWorker.controller.postMessage({type: 'DEBUG_ON'})
let DEBUG = false

// Debug logging helper - only logs when DEBUG is true
const log = (...args) => DEBUG && console.log('[SW]', ...args)
const logError = (...args) => console.error('[SW]', ...args) // Errors always logged

// Request coalescing - prevent duplicate network requests
const pendingRequests = new Map()
const STATIC_CACHE_URLS = [
  '/',
  '/index.html',
  '/offline.html',
  '/manifest.webmanifest',
  // Hero images - responsive with AVIF/WebP/JPEG fallback
  '/images/optimized/stockholm-mobile.avif',
  '/images/optimized/stockholm-mobile.webp',
  '/images/optimized/stockholm-tablet.avif',
  '/images/optimized/stockholm-tablet.webp',
  '/images/optimized/stockholm-desktop.avif',
  '/images/optimized/stockholm-desktop.webp',
  // Logo/branding
  '/images/D.svg',
  '/images/D-white.svg',
  // SVG icons
  '/images/experience.svg',
  '/images/experience-white.svg',
  '/images/education.svg',
  '/images/education-white.svg',
  '/images/github.svg',
  '/images/github-white.svg',
  '/images/about.svg',
  '/images/about-white.svg',
  '/images/contact.svg',
  '/images/contact-white.svg'
]

// Install event - cache static assets
self.addEventListener('install', event => {
  log('Installing...', CACHE_NAME)
  event.waitUntil(
    caches
      .open(CACHE_NAME)
      .then(cache => {
        log('Caching static assets')
        return cache.addAll(STATIC_CACHE_URLS)
      })
      .then(() => {
        log('Installation complete, skipping waiting')
        return self.skipWaiting()
      })
      .catch(error => {
        logError('Installation failed:', error)
        throw error // Re-throw to prevent faulty SW from activating
      })
  )
})

// Activate event - cleanup old caches
self.addEventListener('activate', event => {
  log('Activating...', CACHE_NAME)
  const validCaches = [CACHE_NAME, API_CACHE_NAME]
  event.waitUntil(
    caches
      .keys()
      .then(cacheNames => {
        const oldCaches = cacheNames.filter(cacheName => !validCaches.includes(cacheName))
        if (oldCaches.length > 0) {
          log('Deleting old caches:', oldCaches)
        }
        return Promise.all(
          oldCaches.map(cacheName => {
            return caches.delete(cacheName)
          })
        )
      })
      .then(() => {
        log('Cleaning up current cache')
        return cleanupCache(CACHE_NAME)
      })
      .then(() => {
        log('Enabling navigation preload')
        // Enable navigation preload if available
        if (self.registration.navigationPreload) {
          return self.registration.navigationPreload.enable()
        }
        return Promise.resolve()
      })
      .then(() => {
        log('Activation complete, claiming clients')
        return self.clients.claim()
      })
      .catch(error => {
        logError('Activation failed:', error)
        throw error
      })
  )
})

// Cache management constants
const MAX_CACHE_SIZE = 50 // Maximum number of cached items
const MAX_CACHE_AGE = 7 * 24 * 60 * 60 * 1000 // 7 days in milliseconds

// Helper function to clean up old cache entries
async function cleanupCache(cacheName) {
  const cache = await caches.open(cacheName)
  const keys = await cache.keys()

  // Remove excess items if cache is too large
  if (keys.length > MAX_CACHE_SIZE) {
    const deleteCount = keys.length - MAX_CACHE_SIZE
    console.log(
      `[ServiceWorker] Cache size (${keys.length}) exceeds limit (${MAX_CACHE_SIZE}), removing ${deleteCount} oldest items`
    )
    // Delete oldest items first (FIFO)
    for (let i = 0; i < deleteCount; i++) {
      await cache.delete(keys[i])
    }
  }

  // Remove items older than MAX_CACHE_AGE
  const now = Date.now()
  for (const request of keys) {
    const response = await cache.match(request)
    if (response) {
      const dateHeader = response.headers.get('date')
      if (dateHeader) {
        const cacheDate = new Date(dateHeader).getTime()
        const age = now - cacheDate
        if (age > MAX_CACHE_AGE) {
          console.log(
            `[ServiceWorker] Removing expired cache entry (${Math.floor(age / (24 * 60 * 60 * 1000))} days old):`,
            request.url
          )
          await cache.delete(request)
        }
      }
    }
  }
}

// Helper function to coalesce duplicate requests
function coalescedFetch(request) {
  const key = request.url

  // If request is already pending, return the existing promise
  if (pendingRequests.has(key)) {
    log('Coalescing duplicate request:', key)
    return pendingRequests.get(key)
  }

  // Create new fetch promise
  const fetchPromise = fetch(request)
    .then(response => {
      pendingRequests.delete(key)
      return response
    })
    .catch(error => {
      pendingRequests.delete(key)
      throw error
    })

  pendingRequests.set(key, fetchPromise)
  return fetchPromise
}

// Helper function to determine if request is for HTML
function isHTMLRequest(request) {
  const acceptHeader = request.headers.get('accept')
  return (
    acceptHeader &&
    (acceptHeader.includes('text/html') ||
      request.url.endsWith('/') ||
      request.url.endsWith('.html'))
  )
}

// Helper function to determine if request is for API
function isAPIRequest(request) {
  const url = new URL(request.url)
  // Check if request is to the FastAPI backend
  return url.pathname.startsWith('/api/') || url.port === '8001'
}

// Cacheable API endpoints (portfolio data that rarely changes)
const CACHEABLE_API_PATTERNS = [
  /\/api\/v1\/companies/,
  /\/api\/v1\/education/,
  /\/api\/v1\/projects/,
  /\/api\/v1\/skills/,
  /\/api\/v1\/github\/repos/
]

// Check if API request should be cached
function isCacheableAPI(url) {
  return CACHEABLE_API_PATTERNS.some(pattern => pattern.test(url))
}

// Handle API requests with network-first strategy and cache fallback
async function handleAPIRequest(request) {
  const url = request.url

  // Only cache GET requests for specific endpoints
  if (request.method !== 'GET' || !isCacheableAPI(url)) {
    log('API request (no cache):', url)
    return fetch(request)
  }

  log('API request (cacheable):', url)

  try {
    // Try network first with timeout
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), API_NETWORK_TIMEOUT)

    const networkResponse = await fetch(request, { signal: controller.signal })
    clearTimeout(timeoutId)

    // Cache successful responses
    if (networkResponse.ok) {
      const responseToCache = networkResponse.clone()
      const cache = await caches.open(API_CACHE_NAME)

      // Add timestamp header for cache expiration
      const headers = new Headers(responseToCache.headers)
      headers.set('sw-cache-time', Date.now().toString())

      const cachedResponse = new Response(await responseToCache.blob(), {
        status: responseToCache.status,
        statusText: responseToCache.statusText,
        headers
      })

      cache.put(request, cachedResponse)
      log('Cached API response:', url)
    }

    return networkResponse
  } catch (error) {
    log('Network failed, checking cache:', url, error.message)

    // Fallback to cache
    const cache = await caches.open(API_CACHE_NAME)
    const cachedResponse = await cache.match(request)

    if (cachedResponse) {
      // Check cache age
      const cacheTime = cachedResponse.headers.get('sw-cache-time')
      if (cacheTime) {
        const age = Date.now() - parseInt(cacheTime, 10)
        if (age < API_CACHE_MAX_AGE) {
          log('Serving cached API response (age:', Math.round(age / 1000 / 60), 'min):', url)
          return cachedResponse
        }
        log('Cache expired, deleting:', url)
        await cache.delete(request)
      }
    }

    // No valid cache, return error response
    return new Response(JSON.stringify({ error: 'Offline', message: 'No cached data available' }), {
      status: 503,
      headers: { 'Content-Type': 'application/json' }
    })
  }
}

// Fetch event - network-first for HTML, cache-first for assets
self.addEventListener('fetch', event => {
  // Only handle GET requests
  if (event.request.method !== 'GET') {
    return
  }

  // Skip external requests (except for same-origin API calls)
  if (!event.request.url.startsWith(self.location.origin) && !isAPIRequest(event.request)) {
    return
  }

  // Network-first with cache fallback for API requests
  if (isAPIRequest(event.request)) {
    event.respondWith(handleAPIRequest(event.request))
    return
  }

  // Network-first strategy for HTML to ensure fresh content
  if (isHTMLRequest(event.request)) {
    event.respondWith(
      // Use preloaded response if available, otherwise fetch
      (async () => {
        const preloadResponse = await event.preloadResponse
        if (preloadResponse) {
          log('Using preloaded response:', event.request.url)
          return preloadResponse
        }
        return fetch(event.request)
      })()
        .then(response => {
          // Cache the fresh HTML response
          if (response && response.status === 200 && response.type === 'basic') {
            const responseToCache = response.clone()
            caches
              .open(CACHE_NAME)
              .then(cache => {
                log('Caching fresh HTML:', event.request.url)
                return cache.put(event.request, responseToCache)
              })
              .catch(error => {
                logError('Failed to cache HTML:', event.request.url, error)
              })
          }
          return response
        })
        .catch(error => {
          logError('Network fetch failed for HTML:', event.request.url, error)
          // Fallback to cached version if network fails
          return caches.match(event.request).then(cachedResponse => {
            if (cachedResponse) {
              log('Serving cached HTML (offline):', event.request.url)
              return cachedResponse
            }
            // If no cache, serve offline page
            log('Serving offline page')
            return caches.match('/offline.html')
          })
        })
    )
    return
  }

  // Stale-while-revalidate for CSS/JS, cache-first for images
  const url = new URL(event.request.url)
  const isStyleOrScript = url.pathname.endsWith('.css') || url.pathname.endsWith('.js')

  // Stale-while-revalidate for CSS/JS - serve cached, update in background
  if (isStyleOrScript) {
    event.respondWith(
      caches.match(event.request).then(cachedResponse => {
        const fetchPromise = coalescedFetch(event.request)
          .then(response => {
            // Update cache in background
            if (response && response.status === 200 && response.type === 'basic') {
              const responseToCache = response.clone()
              caches.open(CACHE_NAME).then(cache => {
                log('Background update:', event.request.url)
                cache.put(event.request, responseToCache)
              })
            }
            return response
          })
          .catch(error => {
            log('WARN: Background fetch failed:', event.request.url, error)
            return cachedResponse // Fallback to cached if update fails
          })

        // Return cached immediately, or wait for network if no cache
        if (cachedResponse) {
          log('Serving cached (revalidating):', event.request.url)
          return cachedResponse
        }
        return fetchPromise
      })
    )
    return
  }

  // Cache-first strategy for images and other static assets
  event.respondWith(
    caches
      .match(event.request)
      .then(cachedResponse => {
        // Return cached version or fetch from network
        if (cachedResponse) {
          log('Cache hit:', event.request.url)
          return cachedResponse
        }

        log('Fetching from network:', event.request.url)
        return fetch(event.request)
          .then(response => {
            // Don't cache if not a valid response
            if (!response || response.status !== 200 || response.type !== 'basic') {
              console.log(
                '[ServiceWorker] Not caching response:',
                event.request.url,
                'Status:',
                response?.status
              )
              return response
            }

            // Clone the response
            const responseToCache = response.clone()

            caches
              .open(CACHE_NAME)
              .then(cache => {
                log('Caching new resource:', event.request.url)
                return cache.put(event.request, responseToCache)
              })
              .catch(error => {
                logError('Failed to cache resource:', event.request.url, error)
              })

            return response
          })
          .catch(error => {
            logError('Fetch failed:', event.request.url, error)
            // Return offline response for failed asset requests
            log('Serving offline response')
            return new Response('Offline', { status: 200, statusText: 'OK' })
          })
      })
      .catch(error => {
        logError('Cache match failed:', event.request.url, error)
        // Try network as fallback
        return fetch(event.request).catch(() => {
          return new Response('Offline', { status: 200, statusText: 'OK' })
        })
      })
  )
})

// Message handler for skip waiting and debug toggle
self.addEventListener('message', event => {
  log('Message received:', event.data)

  if (event.data && event.data.type === 'SKIP_WAITING') {
    log('Skip waiting requested')
    self.skipWaiting()
  }

  if (event.data && event.data.type === 'DEBUG_ON') {
    DEBUG = true
    console.log('[SW] Debug mode enabled')
  }

  if (event.data && event.data.type === 'DEBUG_OFF') {
    DEBUG = false
    console.log('[SW] Debug mode disabled')
  }

  // Respond to client
  if (event.ports && event.ports[0]) {
    event.ports[0].postMessage({ type: 'ACK', debug: DEBUG })
  }
})

// Background sync for analytics or other tasks
self.addEventListener('sync', event => {
  log('Sync event:', event.tag)
  if (event.tag === 'portfolio-sync') {
    event.waitUntil(
      // Add any background sync logic here
      Promise.resolve().then(() => {
        log('Sync complete:', event.tag)
      })
    )
  }
})
