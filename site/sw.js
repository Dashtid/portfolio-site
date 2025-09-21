const CACHE_NAME = 'dashti-portfolio-v1.0.0'
const STATIC_CACHE_URLS = [
  '/',
  '/index.html',
  '/offline.html',
  '/static/css/style.css',
  '/static/js/theme.js',
  '/static/js/trading-widgets.js',
  '/static/images/stockholm.webp',
  '/static/images/stockholm.jpg',
  '/static/images/cropped.png',
  '/static/images/D.svg',
  // Add other critical images
  '/static/images/experience.svg',
  '/static/images/education.svg',
  '/static/images/github.svg',
  '/static/images/market.svg',
  '/static/images/about.svg',
  '/static/images/contact.svg'
]

// Install event - cache static assets
self.addEventListener('install', event => {
  event.waitUntil(
    caches
      .open(CACHE_NAME)
      .then(cache => {
        return cache.addAll(STATIC_CACHE_URLS)
      })
      .then(() => {
        return self.skipWaiting()
      })
  )
})

// Activate event - cleanup old caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches
      .keys()
      .then(cacheNames => {
        return Promise.all(
          cacheNames
            .filter(cacheName => {
              return cacheName !== CACHE_NAME
            })
            .map(cacheName => {
              return caches.delete(cacheName)
            })
        )
      })
      .then(() => {
        return self.clients.claim()
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
    caches.match(event.request).then(cachedResponse => {
      // Return cached version or fetch from network
      if (cachedResponse) {
        return cachedResponse
      }

      return fetch(event.request)
        .then(response => {
          // Don't cache if not a valid response
          if (
            !response ||
            response.status !== 200 ||
            response.type !== 'basic'
          ) {
            return response
          }

          // Clone the response
          const responseToCache = response.clone()

          caches.open(CACHE_NAME).then(cache => {
            cache.put(event.request, responseToCache)
          })

          return response
        })
        .catch(() => {
          // Return offline page for HTML requests
          if (
            event.request.headers.get('accept') &&
            event.request.headers.get('accept').includes('text/html')
          ) {
            return caches.match('/offline.html')
          }
          // Return a default response for other requests
          return new Response('Offline', { status: 200, statusText: 'OK' })
        })
    })
  )
})

// Background sync for analytics or other tasks
self.addEventListener('sync', event => {
  if (event.tag === 'portfolio-sync') {
    event.waitUntil(
      // Add any background sync logic here
      Promise.resolve()
    )
  }
})
