const CACHE_NAME = 'dashti-portfolio-v2.1.0'
const API_CACHE_NAME = 'dashti-portfolio-api-v2.1.0'
const IMAGE_CACHE_NAME = 'dashti-portfolio-images-v2.1.0'

const STATIC_CACHE_URLS = [
  '/',
  '/index.html',
  '/offline.html',
  '/static/css/style.css',
  '/static/js/theme.js',
  // Optimized responsive images
  '/static/images/optimized/stockholm-desktop.webp',
  '/static/images/optimized/stockholm-desktop.jpg',
  '/static/images/cropped.png',
  '/static/images/D.svg',
  '/static/images/D-white.svg',
  // Critical UI icons
  '/static/images/experience.svg',
  '/static/images/education.svg',
  '/static/images/github.svg',
  '/static/images/about.svg',
  '/static/images/contact.svg',
  '/static/images/LinkedIn.svg'
]

// API endpoints to cache with different strategies
const API_CACHE_CONFIG = {
  'github-readme-stats.vercel.app': {
    strategy: 'stale-while-revalidate',
    maxAge: 6 * 60 * 60 * 1000, // 6 hours
    maxEntries: 20
  },
  'api.github.com': {
    strategy: 'network-first',
    maxAge: 30 * 60 * 1000, // 30 minutes
    maxEntries: 10
  }
}

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
  const currentCaches = [CACHE_NAME, API_CACHE_NAME, IMAGE_CACHE_NAME]

  event.waitUntil(
    caches
      .keys()
      .then(cacheNames => {
        return Promise.all(
          cacheNames
            .filter(cacheName => {
              return !currentCaches.includes(cacheName)
            })
            .map(cacheName => {
              // eslint-disable-next-line no-console
              console.log('Deleting old cache:', cacheName)
              return caches.delete(cacheName)
            })
        )
      })
      .then(() => {
        return self.clients.claim()
      })
  )
})

// Fetch event - intelligent caching with multiple strategies
self.addEventListener('fetch', event => {
  // Only handle GET requests
  if (event.request.method !== 'GET') {
    return
  }

  const url = new URL(event.request.url)

  // Handle different types of requests with appropriate strategies
  if (isAPIRequest(url)) {
    event.respondWith(handleAPIRequest(event.request, url))
  } else if (isImageRequest(url)) {
    event.respondWith(handleImageRequest(event.request, url))
  } else if (isStaticAsset(url)) {
    event.respondWith(handleStaticAsset(event.request))
  } else if (isHTMLRequest(event.request)) {
    event.respondWith(handleHTMLRequest(event.request))
  }
})

// Check if request is to an API endpoint
function isAPIRequest(url) {
  return Object.keys(API_CACHE_CONFIG).some(domain =>
    url.hostname.includes(domain)
  )
}

// Check if request is for an image
function isImageRequest(url) {
  return url.pathname.match(/\.(jpg|jpeg|png|gif|webp|svg|ico)$/i)
}

// Check if request is for a static asset
function isStaticAsset(url) {
  return (
    url.origin === self.location.origin &&
    (url.pathname.startsWith('/static/') ||
      url.pathname.endsWith('.css') ||
      url.pathname.endsWith('.js'))
  )
}

// Check if request is for HTML
function isHTMLRequest(request) {
  return (
    request.headers.get('accept') &&
    request.headers.get('accept').includes('text/html')
  )
}

// Handle API requests with configured caching strategies
async function handleAPIRequest(request, url) {
  const config = getAPIConfig(url.hostname)

  if (config.strategy === 'stale-while-revalidate') {
    return handleStaleWhileRevalidate(request, API_CACHE_NAME, config)
  } else if (config.strategy === 'network-first') {
    return handleNetworkFirst(request, API_CACHE_NAME, config)
  }

  // Default to network-first
  return handleNetworkFirst(request, API_CACHE_NAME, config)
}

// Handle image requests with cache-first strategy
async function handleImageRequest(request, url) {
  const cache = await caches.open(IMAGE_CACHE_NAME)
  const cachedResponse = await cache.match(request)

  if (cachedResponse) {
    return cachedResponse
  }

  try {
    const response = await fetch(request)
    if (response.ok) {
      // Cache successful image responses
      cache.put(request, response.clone())
    }
    return response
  } catch (error) {
    // Return a placeholder or error response for images
    return new Response('', {
      status: 404,
      statusText: 'Image not found'
    })
  }
}

// Handle static assets with cache-first strategy
async function handleStaticAsset(request) {
  const cache = await caches.open(CACHE_NAME)
  const cachedResponse = await cache.match(request)

  if (cachedResponse) {
    return cachedResponse
  }

  const response = await fetch(request)
  if (response.ok) {
    cache.put(request, response.clone())
  }
  return response
}

// Handle HTML requests with network-first strategy
async function handleHTMLRequest(request) {
  try {
    const response = await fetch(request)

    // Cache successful HTML responses
    if (response.ok) {
      const cache = await caches.open(CACHE_NAME)
      cache.put(request, response.clone())
    }

    return response
  } catch (error) {
    // Return cached version or offline page
    const cache = await caches.open(CACHE_NAME)
    const cachedResponse = await cache.match(request)

    if (cachedResponse) {
      return cachedResponse
    }

    // Return offline page as last resort
    return (
      cache.match('/offline.html') ||
      new Response('Offline', { status: 200, statusText: 'OK' })
    )
  }
}

// Stale-while-revalidate strategy
async function handleStaleWhileRevalidate(request, cacheName, config) {
  const cache = await caches.open(cacheName)
  const cachedResponse = await cache.match(request)

  // Always attempt to fetch in the background
  const fetchPromise = fetch(request)
    .then(response => {
      if (response.ok) {
        cache.put(request, response.clone())
        cleanupCache(cacheName, config.maxEntries)
      }
      return response
    })
    .catch(() => {
      // Network error - return cached version if available
      return cachedResponse
    })

  // Return cached version immediately if available and not expired
  if (cachedResponse && !isExpired(cachedResponse, config.maxAge)) {
    // Update in background
    fetchPromise.catch(() => {}) // Prevent unhandled rejection
    return cachedResponse
  }

  // Wait for network response
  return fetchPromise
}

// Network-first strategy
async function handleNetworkFirst(request, cacheName, config) {
  try {
    const response = await fetch(request)

    if (response.ok) {
      const cache = await caches.open(cacheName)
      cache.put(request, response.clone())
      cleanupCache(cacheName, config.maxEntries)
    }

    return response
  } catch (error) {
    // Network failed, try cache
    const cache = await caches.open(cacheName)
    const cachedResponse = await cache.match(request)

    if (cachedResponse && !isExpired(cachedResponse, config.maxAge)) {
      return cachedResponse
    }

    throw error
  }
}

// Helper functions
function getAPIConfig(hostname) {
  for (const [domain, config] of Object.entries(API_CACHE_CONFIG)) {
    if (hostname.includes(domain)) {
      return config
    }
  }
  return API_CACHE_CONFIG['api.github.com'] // Default config
}

function isExpired(response, maxAge) {
  if (!maxAge) return false

  const cached = response.headers.get('sw-cached-date')
  if (!cached) return true

  const cachedDate = new Date(cached)
  return Date.now() - cachedDate.getTime() > maxAge
}

async function cleanupCache(cacheName, maxEntries) {
  if (!maxEntries) return

  const cache = await caches.open(cacheName)
  const keys = await cache.keys()

  if (keys.length > maxEntries) {
    const keysToDelete = keys.slice(0, keys.length - maxEntries)
    await Promise.all(keysToDelete.map(key => cache.delete(key)))
  }
}

// Background sync for analytics or other tasks
self.addEventListener('sync', event => {
  if (event.tag === 'portfolio-sync') {
    event.waitUntil(
      // Add any background sync logic here
      Promise.resolve()
    )
  }
})
