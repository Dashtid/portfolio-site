/**
 * Image optimization utilities
 */

/**
 * Generate optimized image URLs for different sizes
 */
export function generateImageSrcSet(baseUrl, sizes = [400, 800, 1200, 1600]) {
  if (!baseUrl) return ''

  // If it's already a data URL or external URL, return as-is
  if (baseUrl.startsWith('data:') || baseUrl.startsWith('http')) {
    return baseUrl
  }

  // Generate srcset for local images
  return sizes
    .map(size => `${baseUrl}?w=${size} ${size}w`)
    .join(', ')
}

/**
 * Get optimal image format based on browser support
 */
export function getOptimalImageFormat() {
  const canvas = document.createElement('canvas')
  canvas.width = canvas.height = 1

  // Check WebP support
  const supportsWebP = canvas.toDataURL('image/webp').indexOf('image/webp') === 5

  // Check AVIF support (more complex, usually requires feature detection)
  const supportsAvif = false // Simplified for now

  if (supportsAvif) return 'avif'
  if (supportsWebP) return 'webp'
  return 'jpg'
}

/**
 * Preload critical images
 */
export function preloadImage(src, priority = 'auto') {
  if (!src) return

  const link = document.createElement('link')
  link.rel = 'preload'
  link.as = 'image'
  link.href = src

  if (priority === 'high') {
    link.fetchPriority = 'high'
  }

  document.head.appendChild(link)
}

/**
 * Create a blurred placeholder from an image
 */
export function createPlaceholder(width = 40, height = 30) {
  const canvas = document.createElement('canvas')
  const ctx = canvas.getContext('2d')

  canvas.width = width
  canvas.height = height

  // Create a gradient placeholder
  const gradient = ctx.createLinearGradient(0, 0, width, height)
  gradient.addColorStop(0, '#f0f0f0')
  gradient.addColorStop(0.5, '#e0e0e0')
  gradient.addColorStop(1, '#f0f0f0')

  ctx.fillStyle = gradient
  ctx.fillRect(0, 0, width, height)

  return canvas.toDataURL('image/jpeg', 0.1)
}

/**
 * Calculate optimal image dimensions based on container
 */
export function calculateOptimalDimensions(containerWidth, containerHeight, aspectRatio = 16/9) {
  let width = containerWidth
  let height = containerHeight

  if (!containerHeight) {
    height = Math.round(containerWidth / aspectRatio)
  } else if (!containerWidth) {
    width = Math.round(containerHeight * aspectRatio)
  }

  // Ensure dimensions are reasonable
  width = Math.min(width, 2400)  // Max width
  height = Math.min(height, 1800) // Max height

  return { width, height }
}

/**
 * Convert image to optimized format
 */
export async function optimizeImage(file, options = {}) {
  const {
    maxWidth = 1920,
    maxHeight = 1080,
    quality = 0.85,
    format = 'webp'
  } = options

  return new Promise((resolve, reject) => {
    const reader = new FileReader()

    reader.onload = (e) => {
      const img = new Image()

      img.onload = () => {
        const canvas = document.createElement('canvas')
        const ctx = canvas.getContext('2d')

        // Calculate new dimensions
        let { width, height } = img

        if (width > maxWidth || height > maxHeight) {
          const ratio = Math.min(maxWidth / width, maxHeight / height)
          width *= ratio
          height *= ratio
        }

        canvas.width = width
        canvas.height = height

        // Draw and compress
        ctx.drawImage(img, 0, 0, width, height)

        canvas.toBlob(
          (blob) => {
            if (blob) {
              resolve({
                blob,
                dataUrl: URL.createObjectURL(blob),
                width,
                height,
                size: blob.size,
                format
              })
            } else {
              reject(new Error('Failed to optimize image'))
            }
          },
          `image/${format}`,
          quality
        )
      }

      img.onerror = () => {
        reject(new Error('Failed to load image'))
      }

      img.src = e.target.result
    }

    reader.onerror = () => {
      reject(new Error('Failed to read file'))
    }

    reader.readAsDataURL(file)
  })
}

/**
 * Lazy load images using Intersection Observer
 */
export class ImageLazyLoader {
  constructor(options = {}) {
    this.options = {
      root: options.root || null,
      rootMargin: options.rootMargin || '50px',
      threshold: options.threshold || 0.01
    }

    this.observer = null
    this.init()
  }

  init() {
    if ('IntersectionObserver' in window) {
      this.observer = new IntersectionObserver(
        this.handleIntersection.bind(this),
        this.options
      )
    }
  }

  handleIntersection(entries) {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const img = entry.target
        const src = img.dataset.src
        const srcset = img.dataset.srcset

        if (src) {
          img.src = src
          img.removeAttribute('data-src')
        }

        if (srcset) {
          img.srcset = srcset
          img.removeAttribute('data-srcset')
        }

        img.classList.add('lazy-loaded')
        this.observer.unobserve(img)
      }
    })
  }

  observe(element) {
    if (this.observer && element) {
      this.observer.observe(element)
    }
  }

  disconnect() {
    if (this.observer) {
      this.observer.disconnect()
    }
  }
}

// Export a singleton instance
export const lazyLoader = new ImageLazyLoader()