/* eslint-disable no-console */
// Console statements are intentional for service worker debugging
const CACHE_NAME = 'dashti-portfolio-v2.0.0'
const STATIC_CACHE_URLS = [
  '/',
  '/index.html',
  '/offline.html',
  '/static/css/style.css',
  '/static/js/theme.js',
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
        console.log('[ServiceWorker] Activation complete, claiming clients')
        return self.clients.claim()
      })
      .catch(error => {
        console.error('[ServiceWorker] Activation failed:', error)
        throw error
      })
  )
})

// Fetch event - serve from cache with network fallback
self.addEventListener('fetch', event => {
  // Only handle GET requests
  if (event.request.method !== 'GET') {
    return
  }

  // Skip external requests
  if (!event.request.url.startsWith(self.location.origin)) {
    return
  }

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
            // Return offline page for HTML requests
            if (
              event.request.headers.get('accept') &&
              event.request.headers.get('accept').includes('text/html')
            ) {
              console.log('[ServiceWorker] Serving offline page')
              return caches.match('/offline.html')
            }
            // Return a default response for other requests
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
