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

/**
 * Get optimal image format based on browser support
 */
export function getOptimalImageFormat(): 'avif' | 'webp' | 'jpg' {
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
  const ctx = canvas.getContext('2d')!

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
}

interface OptimizedImage {
  blob: Blob
  dataUrl: string
  width: number
  height: number
  size: number
  format: string
}

/**
 * Convert image to optimized format
 */
export async function optimizeImage(
  file: File,
  options: OptimizeImageOptions = {}
): Promise<OptimizedImage> {
  const { maxWidth = 1920, maxHeight = 1080, quality = 0.85, format = 'webp' } = options

  return new Promise<OptimizedImage>((resolve, reject) => {
    const reader = new FileReader()

    reader.onload = e => {
      const img = new Image()

      img.onload = () => {
        const canvas = document.createElement('canvas')
        const ctx = canvas.getContext('2d')!

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

      img.src = e.target!.result as string
    }

    reader.onerror = () => {
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
        this.observer!.unobserve(img)
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
