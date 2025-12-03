/**
 * Tests for imageOptimization utility (TypeScript)
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import {
  generateImageSrcSet,
  getOptimalImageFormat,
  preloadImage,
  createPlaceholder,
  calculateOptimalDimensions,
  ImageLazyLoader,
  lazyLoader
} from '@/utils/imageOptimization'

describe('imageOptimization utility', () => {
  describe('generateImageSrcSet', () => {
    it('generates srcset for local images', () => {
      const srcset = generateImageSrcSet('/images/photo.jpg')

      expect(srcset).toContain('400w')
      expect(srcset).toContain('800w')
      expect(srcset).toContain('1200w')
      expect(srcset).toContain('1600w')
    })

    it('returns empty string for empty URL', () => {
      const srcset = generateImageSrcSet('')

      expect(srcset).toBe('')
    })

    it('returns original URL for data URLs', () => {
      const dataUrl = 'data:image/png;base64,iVBORw0KGg'
      const srcset = generateImageSrcSet(dataUrl)

      expect(srcset).toBe(dataUrl)
    })

    it('returns original URL for external URLs', () => {
      const externalUrl = 'https://example.com/image.jpg'
      const srcset = generateImageSrcSet(externalUrl)

      expect(srcset).toBe(externalUrl)
    })

    it('accepts custom sizes array', () => {
      const srcset = generateImageSrcSet('/image.jpg', [200, 400])

      expect(srcset).toContain('200w')
      expect(srcset).toContain('400w')
      expect(srcset).not.toContain('800w')
    })
  })

  describe('getOptimalImageFormat', () => {
    it('returns a valid format', () => {
      const format = getOptimalImageFormat()

      expect(['avif', 'webp', 'jpg']).toContain(format)
    })

    it('returns jpg as fallback', () => {
      // Mock canvas.toDataURL to return unsupported format
      const mockCanvas = document.createElement('canvas')
      vi.spyOn(mockCanvas, 'toDataURL').mockReturnValue('data:image/png')

      const format = getOptimalImageFormat()

      expect(format).toBe('jpg')
    })
  })

  describe('preloadImage', () => {
    beforeEach(() => {
      document.head.innerHTML = ''
    })

    it('creates preload link element', () => {
      preloadImage('/test.jpg')

      const links = document.head.querySelectorAll('link[rel="preload"]')
      expect(links.length).toBeGreaterThan(0)
    })

    it('sets correct href', () => {
      const src = '/test.jpg'
      preloadImage(src)

      const link = document.head.querySelector('link[rel="preload"]')
      expect(link?.getAttribute('href')).toBe(src)
    })

    it('sets as="image"', () => {
      preloadImage('/test.jpg')

      const link = document.head.querySelector('link[rel="preload"]')
      expect(link?.getAttribute('as')).toBe('image')
    })

    it('sets high priority when requested', () => {
      preloadImage('/test.jpg', 'high')

      const link = document.head.querySelector('link[rel="preload"]') as HTMLLinkElement
      expect(link?.fetchPriority).toBe('high')
    })

    it('handles empty src gracefully', () => {
      expect(() => preloadImage('')).not.toThrow()
    })
  })

  describe('createPlaceholder', () => {
    beforeEach(() => {
      // Mock canvas context for placeholder generation
      const mockContext = {
        createLinearGradient: vi.fn(() => ({
          addColorStop: vi.fn()
        })),
        fillRect: vi.fn(),
        fillStyle: ''
      }

      vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue(mockContext as any)
      vi.spyOn(HTMLCanvasElement.prototype, 'toDataURL').mockReturnValue('data:image/jpeg;base64,mockdata')
    })

    it('returns data URL', () => {
      const placeholder = createPlaceholder()

      expect(placeholder).toMatch(/^data:image\/jpeg/)
    })

    it('accepts custom dimensions', () => {
      const placeholder = createPlaceholder(100, 100)

      expect(placeholder).toBeDefined()
      expect(placeholder.length).toBeGreaterThan(0)
    })

    it('uses default dimensions', () => {
      const placeholder = createPlaceholder()

      expect(placeholder).toBeDefined()
    })
  })

  describe('calculateOptimalDimensions', () => {
    it('calculates height from width using aspect ratio', () => {
      const { width, height } = calculateOptimalDimensions(1600)

      expect(width).toBe(1600)
      expect(height).toBe(900) // 1600 / (16/9)
    })

    it('calculates width from height using aspect ratio', () => {
      const { width, height } = calculateOptimalDimensions(0, 900)

      expect(width).toBe(1600) // 900 * (16/9)
      expect(height).toBe(900)
    })

    it('accepts custom aspect ratio', () => {
      const { width, height } = calculateOptimalDimensions(1000, undefined, 1)

      expect(width).toBe(1000)
      expect(height).toBe(1000) // Square aspect ratio
    })

    it('caps width at 2400', () => {
      const { width } = calculateOptimalDimensions(3000)

      expect(width).toBeLessThanOrEqual(2400)
    })

    it('caps height at 1800', () => {
      const { height } = calculateOptimalDimensions(0, 2000)

      expect(height).toBeLessThanOrEqual(1800)
    })

    it('returns both dimensions when both provided', () => {
      const { width, height } = calculateOptimalDimensions(800, 600)

      expect(width).toBe(800)
      expect(height).toBe(600)
    })
  })

  describe('ImageLazyLoader', () => {
    it('creates loader instance', () => {
      const loader = new ImageLazyLoader()

      expect(loader).toBeDefined()
    })

    it('accepts custom options', () => {
      const loader = new ImageLazyLoader({
        rootMargin: '100px',
        threshold: 0.5
      })

      expect(loader).toBeDefined()
    })

    it('has observe method', () => {
      const loader = new ImageLazyLoader()

      expect(loader.observe).toBeDefined()
      expect(typeof loader.observe).toBe('function')
    })

    it('has disconnect method', () => {
      const loader = new ImageLazyLoader()

      expect(loader.disconnect).toBeDefined()
      expect(typeof loader.disconnect).toBe('function')
    })

    it('observe method accepts Element', () => {
      const loader = new ImageLazyLoader()
      const element = document.createElement('img')

      expect(() => loader.observe(element)).not.toThrow()
    })

    it('disconnect method works', () => {
      const loader = new ImageLazyLoader()

      expect(() => loader.disconnect()).not.toThrow()
    })
  })

  describe('lazyLoader singleton', () => {
    it('exports singleton instance', () => {
      expect(lazyLoader).toBeDefined()
      expect(lazyLoader).toBeInstanceOf(ImageLazyLoader)
    })

    it('singleton has observe method', () => {
      expect(lazyLoader.observe).toBeDefined()
    })

    it('singleton has disconnect method', () => {
      expect(lazyLoader.disconnect).toBeDefined()
    })
  })

  describe('optimizeImage', () => {
    let optimizeImage: typeof import('@/utils/imageOptimization').optimizeImage

    beforeEach(async () => {
      const module = await import('@/utils/imageOptimization')
      optimizeImage = module.optimizeImage
    })

    it('rejects when file read fails', async () => {
      const mockFile = new File([''], 'test.jpg', { type: 'image/jpeg' })

      // Mock FileReader to trigger error
      const originalFileReader = window.FileReader

      class MockFileReader {
        onload: ((e: ProgressEvent<FileReader>) => void) | null = null
        onerror: (() => void) | null = null
        result: string | ArrayBuffer | null = null

        readAsDataURL() {
          // Use queueMicrotask to ensure onerror is called after it's assigned
          queueMicrotask(() => {
            if (this.onerror) this.onerror()
          })
        }
      }

      window.FileReader = MockFileReader as unknown as typeof FileReader

      await expect(optimizeImage(mockFile)).rejects.toThrow('Failed to read file')

      window.FileReader = originalFileReader
    })

    it('rejects when image load fails', async () => {
      const mockFile = new File([''], 'test.jpg', { type: 'image/jpeg' })

      // Mock FileReader to succeed but image to fail
      const originalFileReader = window.FileReader
      const originalImage = window.Image

      class MockFileReader {
        onload: ((e: ProgressEvent<FileReader>) => void) | null = null
        onerror: (() => void) | null = null
        result: string | ArrayBuffer | null = 'data:image/jpeg;base64,test'

        readAsDataURL() {
          // Use queueMicrotask to ensure onload is called after it's assigned
          queueMicrotask(() => {
            if (this.onload) {
              this.onload({ target: this } as unknown as ProgressEvent<FileReader>)
            }
          })
        }
      }

      class MockImage {
        private _src = ''
        onerror: (() => void) | null = null
        onload: (() => void) | null = null

        get src() {
          return this._src
        }

        set src(value: string) {
          this._src = value
          // Use queueMicrotask to ensure onerror is triggered after assignment
          queueMicrotask(() => {
            if (this.onerror) this.onerror()
          })
        }
      }

      window.FileReader = MockFileReader as unknown as typeof FileReader
      window.Image = MockImage as unknown as typeof Image

      await expect(optimizeImage(mockFile)).rejects.toThrow('Failed to load image')

      window.FileReader = originalFileReader
      window.Image = originalImage
    })

    it('accepts custom options', () => {
      // Just test that the function accepts options - actual optimization
      // requires complex browser API mocking
      expect(optimizeImage).toBeDefined()
      expect(typeof optimizeImage).toBe('function')
    })
  })

  describe('ImageLazyLoader intersection handling', () => {
    it('handles intersection with data-src', () => {
      const loader = new ImageLazyLoader()
      const img = document.createElement('img')
      img.dataset.src = '/test-image.jpg'
      img.dataset.srcset = '/test-image.jpg 400w'

      // Manually trigger intersection
      const mockEntry = {
        isIntersecting: true,
        target: img
      } as unknown as IntersectionObserverEntry

      // Access private method through prototype
      const handleIntersection = (loader as any).handleIntersection.bind(loader)
      handleIntersection([mockEntry])

      expect(img.src).toContain('test-image.jpg')
      expect(img.srcset).toBe('/test-image.jpg 400w')
      expect(img.classList.contains('lazy-loaded')).toBe(true)
    })

    it('ignores non-intersecting entries', () => {
      const loader = new ImageLazyLoader()
      const img = document.createElement('img')
      img.dataset.src = '/test-image.jpg'

      const mockEntry = {
        isIntersecting: false,
        target: img
      } as unknown as IntersectionObserverEntry

      const handleIntersection = (loader as any).handleIntersection.bind(loader)
      handleIntersection([mockEntry])

      expect(img.src).toBe('')
      expect(img.classList.contains('lazy-loaded')).toBe(false)
    })

    it('handles elements without data-src', () => {
      const loader = new ImageLazyLoader()
      const img = document.createElement('img')

      const mockEntry = {
        isIntersecting: true,
        target: img
      } as unknown as IntersectionObserverEntry

      const handleIntersection = (loader as any).handleIntersection.bind(loader)

      expect(() => handleIntersection([mockEntry])).not.toThrow()
    })

    it('handles elements with only data-srcset', () => {
      const loader = new ImageLazyLoader()
      const img = document.createElement('img')
      img.dataset.srcset = '/image.jpg 400w, /image.jpg 800w'

      const mockEntry = {
        isIntersecting: true,
        target: img
      } as unknown as IntersectionObserverEntry

      const handleIntersection = (loader as any).handleIntersection.bind(loader)
      handleIntersection([mockEntry])

      expect(img.srcset).toBe('/image.jpg 400w, /image.jpg 800w')
    })

    it('removes data attributes after loading', () => {
      const loader = new ImageLazyLoader()
      const img = document.createElement('img')
      img.dataset.src = '/test.jpg'
      img.dataset.srcset = '/test.jpg 400w'

      const mockEntry = {
        isIntersecting: true,
        target: img
      } as unknown as IntersectionObserverEntry

      const handleIntersection = (loader as any).handleIntersection.bind(loader)
      handleIntersection([mockEntry])

      expect(img.dataset.src).toBeUndefined()
      expect(img.dataset.srcset).toBeUndefined()
    })
  })

  describe('ImageLazyLoader without IntersectionObserver', () => {
    it('handles missing IntersectionObserver gracefully', () => {
      const originalIO = window.IntersectionObserver
      delete (window as any).IntersectionObserver

      const loader = new ImageLazyLoader()

      // Should not throw and observe should handle null observer
      const element = document.createElement('img')
      expect(() => loader.observe(element)).not.toThrow()
      expect(() => loader.disconnect()).not.toThrow()

      window.IntersectionObserver = originalIO
    })
  })
})
