/**
 * Image optimization utilities
 */

/**
 * Generate optimized image URLs for different sizes
 */
export function generateImageSrcSet(
  baseUrl: string,
  sizes: number[] = [400, 800, 1200, 1600]
): string {
  if (!baseUrl) return ''

  // If it's already a data URL or external URL, return as-is
  if (baseUrl.startsWith('data:') || baseUrl.startsWith('http')) {
    return baseUrl
  }

  // Generate srcset for local images
  return sizes.map(size => `${baseUrl}?w=${size} ${size}w`).join(', ')
}

// Cache format support results
let cachedAvifSupport: boolean | null = null
let cachedWebpSupport: boolean | null = null

// Timeout for AVIF detection (ms)
const AVIF_DETECTION_TIMEOUT = 3000

/**
 * Check if browser supports AVIF format
 * Uses a tiny AVIF test image for detection with timeout fallback
 */
async function checkAvifSupport(): Promise<boolean> {
  if (cachedAvifSupport !== null) return cachedAvifSupport

  return new Promise(resolve => {
    let resolved = false
    const img = new Image()

    // Timeout fallback to prevent hanging promise
    const timeoutId = setTimeout(() => {
      if (!resolved) {
        resolved = true
        cachedAvifSupport = false
        resolve(false)
      }
    }, AVIF_DETECTION_TIMEOUT)

    // Tiny 1x1 AVIF image (smallest valid AVIF)
    img.src =
      'data:image/avif;base64,AAAAIGZ0eXBhdmlmAAAAAGF2aWZtaWYxbWlhZk1BMUIAAADybWV0YQAAAAAAAAAoaGRscgAAAAAAAAAAcGljdAAAAAAAAAAAAAAAAGxpYmF2aWYAAAAADnBpdG0AAAAAAAEAAAAeaWxvYwAAAABEAAABAAEAAAABAAABGgAAAB0AAAAoaWluZgAAAAAAAQAAABppbmZlAgAAAAABAABhdjAxQ29sb3IAAAAAamlwcnAAAABLaXBjbwAAABRpc3BlAAAAAAAAAAEAAAABAAAAEHBpeGkAAAAAAwgICAAAAAxhdjFDgQ0MAAAAABNjb2xybmNseAACAAIAAYAAAAAXaXBtYQAAAAAAAAABAAEEAQKDBAAAACVtZGF0EgAKBzgABpAQ0AIAAwAAAAAAAAD/////8A=='
    img.onload = () => {
      if (!resolved) {
        resolved = true
        clearTimeout(timeoutId)
        cachedAvifSupport = img.width === 1 && img.height === 1
        resolve(cachedAvifSupport)
      }
    }
    img.onerror = () => {
      if (!resolved) {
        resolved = true
        clearTimeout(timeoutId)
        cachedAvifSupport = false
        resolve(false)
      }
    }
  })
}

/**
 * Check if browser supports WebP format
 */
function checkWebpSupport(): boolean {
  if (cachedWebpSupport !== null) return cachedWebpSupport

  const canvas = document.createElement('canvas')
  canvas.width = canvas.height = 1
  cachedWebpSupport = canvas.toDataURL('image/webp').indexOf('image/webp') === 5
  return cachedWebpSupport
}

/**
 * Get optimal image format based on browser support
 * Returns synchronously using cached values or conservative default
 */
export function getOptimalImageFormat(): 'avif' | 'webp' | 'jpg' {
  // Use cached AVIF result if available
  if (cachedAvifSupport === true) return 'avif'

  // Check WebP synchronously
  if (checkWebpSupport()) return 'webp'

  return 'jpg'
}

/**
 * Get optimal image format with async AVIF detection
 * Use this for better accuracy when async is acceptable
 */
export async function getOptimalImageFormatAsync(): Promise<'avif' | 'webp' | 'jpg'> {
  const supportsAvif = await checkAvifSupport()
  if (supportsAvif) return 'avif'

  if (checkWebpSupport()) return 'webp'

  return 'jpg'
}

/**
 * Preload critical images
 */
export function preloadImage(src: string, priority: 'auto' | 'high' = 'auto'): void {
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
export function createPlaceholder(width: number = 40, height: number = 30): string {
  const canvas = document.createElement('canvas')
  const ctx = canvas.getContext('2d')

  if (!ctx) {
    // Return a simple gray placeholder if canvas context unavailable
    return 'data:image/gif;base64,R0lGODlhAQABAIAAAMLCwgAAACH5BAAAAAAALAAAAAABAAEAAAICRAEAOw=='
  }

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

interface Dimensions {
  width: number
  height: number
}

/**
 * Calculate optimal image dimensions based on container
 */
export function calculateOptimalDimensions(
  containerWidth: number,
  containerHeight?: number,
  aspectRatio: number = 16 / 9
): Dimensions {
  let width = containerWidth
  let height: number

  if (!containerHeight) {
    height = Math.round(containerWidth / aspectRatio)
  } else if (!containerWidth) {
    height = containerHeight
    width = Math.round(containerHeight * aspectRatio)
  } else {
    height = containerHeight
  }

  // Ensure dimensions are reasonable
  width = Math.min(width, 2400) // Max width
  height = Math.min(height, 1800) // Max height

  return { width, height }
}

interface OptimizeImageOptions {
  maxWidth?: number
  maxHeight?: number
  quality?: number
  format?: 'webp' | 'jpeg' | 'png'
  signal?: AbortSignal
}

interface OptimizedImage {
  blob: Blob
  /** Object URL - call revokeObjectUrl() when done to prevent memory leaks */
  objectUrl: string
  width: number
  height: number
  size: number
  format: string
  /** Revoke the object URL to free memory */
  revokeObjectUrl: () => void
}

/**
 * Convert image to optimized format
 * Supports abort signal for cancellation
 */
export async function optimizeImage(
  file: File,
  options: OptimizeImageOptions = {}
): Promise<OptimizedImage> {
  const { maxWidth = 1920, maxHeight = 1080, quality = 0.85, format = 'webp', signal } = options

  // Check if already aborted
  if (signal?.aborted) {
    throw new DOMException('Image optimization aborted', 'AbortError')
  }

  return new Promise<OptimizedImage>((resolve, reject) => {
    const reader = new FileReader()

    // Handle abort signal
    const abortHandler = () => {
      reader.abort()
      reject(new DOMException('Image optimization aborted', 'AbortError'))
    }
    signal?.addEventListener('abort', abortHandler, { once: true })

    const cleanup = () => {
      signal?.removeEventListener('abort', abortHandler)
    }

    reader.onload = e => {
      // Check if aborted before proceeding
      if (signal?.aborted) {
        cleanup()
        reject(new DOMException('Image optimization aborted', 'AbortError'))
        return
      }

      const img = new Image()

      img.onload = () => {
        // Check if aborted before processing
        if (signal?.aborted) {
          cleanup()
          reject(new DOMException('Image optimization aborted', 'AbortError'))
          return
        }

        const canvas = document.createElement('canvas')
        const ctx = canvas.getContext('2d')

        if (!ctx) {
          cleanup()
          reject(new Error('Canvas context not available'))
          return
        }

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
          blob => {
            cleanup()
            if (signal?.aborted) {
              reject(new DOMException('Image optimization aborted', 'AbortError'))
              return
            }
            if (blob) {
              const objectUrl = URL.createObjectURL(blob)
              resolve({
                blob,
                objectUrl,
                width,
                height,
                size: blob.size,
                format,
                revokeObjectUrl: () => URL.revokeObjectURL(objectUrl)
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
        cleanup()
        reject(new Error('Failed to load image'))
      }

      if (e.target?.result) {
        img.src = e.target.result as string
      } else {
        cleanup()
        reject(new Error('Failed to read file result'))
      }
    }

    reader.onerror = () => {
      cleanup()
      reject(new Error('Failed to read file'))
    }

    reader.readAsDataURL(file)
  })
}

interface LazyLoaderOptions {
  root?: Element | null
  rootMargin?: string
  threshold?: number
}

/**
 * Lazy load images using Intersection Observer
 */
export class ImageLazyLoader {
  private options: Required<LazyLoaderOptions>
  private observer: IntersectionObserver | null

  constructor(options: LazyLoaderOptions = {}) {
    this.options = {
      root: options.root ?? null,
      rootMargin: options.rootMargin || '50px',
      threshold: options.threshold || 0.01
    }

    this.observer = null
    this.init()
  }

  private init(): void {
    if ('IntersectionObserver' in window) {
      this.observer = new IntersectionObserver(this.handleIntersection.bind(this), this.options)
    }
  }

  private handleIntersection(entries: IntersectionObserverEntry[]): void {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const img = entry.target as HTMLImageElement
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
        this.observer?.unobserve(img)
      }
    })
  }

  observe(element: Element): void {
    if (this.observer && element) {
      this.observer.observe(element)
    }
  }

  disconnect(): void {
    if (this.observer) {
      this.observer.disconnect()
    }
  }
}

// Export a singleton instance
export const lazyLoader = new ImageLazyLoader()
