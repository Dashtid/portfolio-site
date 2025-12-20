// Console statements are intentional for service worker debugging
const CACHE_VERSION = '3.0.0'
const CACHE_NAME = `dashti-portfolio-migration-v${CACHE_VERSION}`

// Request coalescing - prevent duplicate network requests
const pendingRequests = new Map()
const STATIC_CACHE_URLS = [
  '/',
  '/index.html',
  '/offline.html',
  '/manifest.webmanifest',
  // Vue app assets (will be cached dynamically after build)
  '/images/stockholm.webp',
  '/images/stockholm.jpg',
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
  console.log('[ServiceWorker] Installing...', CACHE_NAME)
  event.waitUntil(
    caches
      .open(CACHE_NAME)
      .then(cache => {
        console.log('[ServiceWorker] Caching static assets')
        return cache.addAll(STATIC_CACHE_URLS)
      })
      .then(() => {
        console.log('[ServiceWorker] Installation complete, skipping waiting')
        return self.skipWaiting()
      })
      .catch(error => {
        console.error('[ServiceWorker] Installation failed:', error)
        throw error // Re-throw to prevent faulty SW from activating
      })
  )
})

// Activate event - cleanup old caches
self.addEventListener('activate', event => {
  console.log('[ServiceWorker] Activating...', CACHE_NAME)
  event.waitUntil(
    caches
      .keys()
      .then(cacheNames => {
        const oldCaches = cacheNames.filter(cacheName => cacheName !== CACHE_NAME)
        if (oldCaches.length > 0) {
          console.log('[ServiceWorker] Deleting old caches:', oldCaches)
        }
        return Promise.all(
          oldCaches.map(cacheName => {
            return caches.delete(cacheName)
          })
        )
      })
      .then(() => {
        console.log('[ServiceWorker] Cleaning up current cache')
        return cleanupCache(CACHE_NAME)
      })
      .then(() => {
        console.log('[ServiceWorker] Enabling navigation preload')
        // Enable navigation preload if available
        if (self.registration.navigationPreload) {
          return self.registration.navigationPreload.enable()
        }
        return Promise.resolve()
      })
      .then(() => {
        console.log('[ServiceWorker] Activation complete, claiming clients')
        return self.clients.claim()
      })
      .catch(error => {
        console.error('[ServiceWorker] Activation failed:', error)
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
    console.log('[ServiceWorker] Coalescing duplicate request:', key)
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

  // NEVER cache API requests - always go to network
  if (isAPIRequest(event.request)) {
    console.log('[ServiceWorker] API request (no cache):', event.request.url)
    event.respondWith(fetch(event.request))
    return
  }

  // Network-first strategy for HTML to ensure fresh content
  if (isHTMLRequest(event.request)) {
    event.respondWith(
      // Use preloaded response if available, otherwise fetch
      (async () => {
        const preloadResponse = await event.preloadResponse
        if (preloadResponse) {
          console.log('[ServiceWorker] Using preloaded response:', event.request.url)
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
                console.log('[ServiceWorker] Caching fresh HTML:', event.request.url)
                return cache.put(event.request, responseToCache)
              })
              .catch(error => {
                console.error('[ServiceWorker] Failed to cache HTML:', event.request.url, error)
              })
          }
          return response
        })
        .catch(error => {
          console.error('[ServiceWorker] Network fetch failed for HTML:', event.request.url, error)
          // Fallback to cached version if network fails
          return caches.match(event.request).then(cachedResponse => {
            if (cachedResponse) {
              console.log('[ServiceWorker] Serving cached HTML (offline):', event.request.url)
              return cachedResponse
            }
            // If no cache, serve offline page
            console.log('[ServiceWorker] Serving offline page')
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
                console.log('[ServiceWorker] Background update:', event.request.url)
                cache.put(event.request, responseToCache)
              })
            }
            return response
          })
          .catch(error => {
            console.warn('[ServiceWorker] Background fetch failed:', event.request.url, error)
            return cachedResponse // Fallback to cached if update fails
          })

        // Return cached immediately, or wait for network if no cache
        if (cachedResponse) {
          console.log('[ServiceWorker] Serving cached (revalidating):', event.request.url)
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
          console.log('[ServiceWorker] Cache hit:', event.request.url)
          return cachedResponse
        }

        console.log('[ServiceWorker] Fetching from network:', event.request.url)
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
                console.log('[ServiceWorker] Caching new resource:', event.request.url)
                return cache.put(event.request, responseToCache)
              })
              .catch(error => {
                console.error('[ServiceWorker] Failed to cache resource:', event.request.url, error)
              })

            return response
          })
          .catch(error => {
            console.error('[ServiceWorker] Fetch failed:', event.request.url, error)
            // Return offline response for failed asset requests
            console.log('[ServiceWorker] Serving offline response')
            return new Response('Offline', { status: 200, statusText: 'OK' })
          })
      })
      .catch(error => {
        console.error('[ServiceWorker] Cache match failed:', event.request.url, error)
        // Try network as fallback
        return fetch(event.request).catch(() => {
          return new Response('Offline', { status: 200, statusText: 'OK' })
        })
      })
  )
})

// Message handler for skip waiting
self.addEventListener('message', event => {
  console.log('[ServiceWorker] Message received:', event.data)

  if (event.data && event.data.type === 'SKIP_WAITING') {
    console.log('[ServiceWorker] Skip waiting requested')
    self.skipWaiting()
  }

  // Respond to client
  if (event.ports && event.ports[0]) {
    event.ports[0].postMessage({ type: 'ACK' })
  }
})

// Background sync for analytics or other tasks
self.addEventListener('sync', event => {
  console.log('[ServiceWorker] Sync event:', event.tag)
  if (event.tag === 'portfolio-sync') {
    event.waitUntil(
      // Add any background sync logic here
      Promise.resolve().then(() => {
        console.log('[ServiceWorker] Sync complete:', event.tag)
      })
    )
  }
})
