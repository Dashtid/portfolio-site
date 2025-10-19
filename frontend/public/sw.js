// Service Worker for Portfolio PWA
const CACHE_NAME = 'portfolio-v1';
const urlsToCache = [
  '/',
  '/manifest.webmanifest',
  '/images/stockholm.webp',
  '/images/D-dark.svg',
  '/images/icon-192.png',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css'
];

// Install Service Worker
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => {
        console.log('[SW] Caching app shell');
        return cache.addAll(urlsToCache);
      })
  );
  self.skipWaiting();
});

// Activate Service Worker
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME) {
            console.log('[SW] Removing old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  self.clients.claim();
});

// Fetch Event - Network First with Cache Fallback
self.addEventListener('fetch', event => {
  // Skip cross-origin requests and API calls
  if (!event.request.url.startsWith(self.location.origin) &&
      !event.request.url.includes('cdn.jsdelivr.net')) {
    return;
  }

  // Skip API requests (don't cache them)
  if (event.request.url.includes('/api/')) {
    return;
  }

  event.respondWith(
    fetch(event.request)
      .then(response => {
        // Check if valid response
        if (!response || response.status !== 200 || response.type === 'opaque') {
          return response;
        }

        // Clone the response
        const responseToCache = response.clone();

        caches.open(CACHE_NAME)
          .then(cache => {
            cache.put(event.request, responseToCache);
          });

        return response;
      })
      .catch(() => {
        // Return cached version on network failure
        return caches.match(event.request)
          .then(response => {
            if (response) {
              return response;
            }

            // Return offline page for navigation requests
            if (event.request.mode === 'navigate') {
              return caches.match('/');
            }
          });
      })
  );
});

// Background sync for form submissions
self.addEventListener('sync', event => {
  if (event.tag === 'sync-portfolio-data') {
    event.waitUntil(syncPortfolioData());
  }
});

async function syncPortfolioData() {
  // Placeholder for syncing data when back online
  console.log('[SW] Syncing portfolio data...');
}