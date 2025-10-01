/* eslint-disable no-console */
// Console statements are intentional for service worker debugging
const CACHE_VERSION = '2.2.0'
const CACHE_NAME = `dashti-portfolio-v${CACHE_VERSION}`
const STATIC_CACHE_URLS = [
  '/',
  '/index.html',
  '/offline.html',
  '/static/css/style.css',
  '/static/css/style.min.css',
  '/static/js/theme.js',
  '/static/js/bundle.min.js',
  '/static/js/dist/content-D48O2rLc.js',
  '/static/js/dist/core-DOf8aIKG.js',
  '/static/js/dist/ui-CAeZwmDR.js',
  '/static/images/stockholm.webp',
  '/static/images/stockholm.jpg',
  '/static/images/cropped.png',
  '/static/images/D.svg',
  // Add other critical images
  '/static/images/experience.svg',
  '/static/images/education.svg',
  '/static/images/github.svg',
  '/static/images/about.svg',
  '/static/images/contact.svg'
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
        const oldCaches = cacheNames.filter(
          cacheName => cacheName !== CACHE_NAME
        )
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

// Fetch event - network-first for HTML, cache-first for assets
self.addEventListener('fetch', event => {
  // Only handle GET requests
  if (event.request.method !== 'GET') {
    return
  }

  // Skip external requests
  if (!event.request.url.startsWith(self.location.origin)) {
    return
  }

  // Network-first strategy for HTML to ensure fresh content
  if (isHTMLRequest(event.request)) {
    event.respondWith(
      fetch(event.request)
        .then(response => {
          // Cache the fresh HTML response
          if (
            response &&
            response.status === 200 &&
            response.type === 'basic'
          ) {
            const responseToCache = response.clone()
            caches
              .open(CACHE_NAME)
              .then(cache => {
                console.log(
                  '[ServiceWorker] Caching fresh HTML:',
                  event.request.url
                )
                return cache.put(event.request, responseToCache)
              })
              .catch(error => {
                console.error(
                  '[ServiceWorker] Failed to cache HTML:',
                  event.request.url,
                  error
                )
              })
          }
          return response
        })
        .catch(error => {
          console.error(
            '[ServiceWorker] Network fetch failed for HTML:',
            event.request.url,
            error
          )
          // Fallback to cached version if network fails
          return caches.match(event.request).then(cachedResponse => {
            if (cachedResponse) {
              console.log(
                '[ServiceWorker] Serving cached HTML (offline):',
                event.request.url
              )
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
  const isStyleOrScript =
    url.pathname.endsWith('.css') || url.pathname.endsWith('.js')

  // Stale-while-revalidate for CSS/JS - serve cached, update in background
  if (isStyleOrScript) {
    event.respondWith(
      caches.match(event.request).then(cachedResponse => {
        const fetchPromise = fetch(event.request)
          .then(response => {
            // Update cache in background
            if (
              response &&
              response.status === 200 &&
              response.type === 'basic'
            ) {
              const responseToCache = response.clone()
              caches.open(CACHE_NAME).then(cache => {
                console.log(
                  '[ServiceWorker] Background update:',
                  event.request.url
                )
                cache.put(event.request, responseToCache)
              })
            }
            return response
          })
          .catch(error => {
            console.warn(
              '[ServiceWorker] Background fetch failed:',
              event.request.url,
              error
            )
            return cachedResponse // Fallback to cached if update fails
          })

        // Return cached immediately, or wait for network if no cache
        if (cachedResponse) {
          console.log(
            '[ServiceWorker] Serving cached (revalidating):',
            event.request.url
          )
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
            if (
              !response ||
              response.status !== 200 ||
              response.type !== 'basic'
            ) {
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
                console.log(
                  '[ServiceWorker] Caching new resource:',
                  event.request.url
                )
                return cache.put(event.request, responseToCache)
              })
              .catch(error => {
                console.error(
                  '[ServiceWorker] Failed to cache resource:',
                  event.request.url,
                  error
                )
              })

            return response
          })
          .catch(error => {
            console.error(
              '[ServiceWorker] Fetch failed:',
              event.request.url,
              error
            )
            // Return offline response for failed asset requests
            console.log('[ServiceWorker] Serving offline response')
            return new Response('Offline', { status: 200, statusText: 'OK' })
          })
      })
      .catch(error => {
        console.error(
          '[ServiceWorker] Cache match failed:',
          event.request.url,
          error
        )
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
