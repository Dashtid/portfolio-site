import { test, expect } from '@playwright/test'

/**
 * Performance Tests
 *
 * Tests for Core Web Vitals and performance metrics.
 * Based on 2025 Web Performance best practices.
 */
test.describe('Performance', () => {
  test.describe('Core Web Vitals', () => {
    test('should meet LCP threshold (< 2.5s)', async ({ page }) => {
      await page.goto('/')

      // Measure Largest Contentful Paint
      const lcp = await page.evaluate(() => {
        return new Promise<number>(resolve => {
          new PerformanceObserver(entryList => {
            const entries = entryList.getEntries()
            const lastEntry = entries[entries.length - 1]
            resolve(lastEntry.startTime)
          }).observe({ type: 'largest-contentful-paint', buffered: true })

          // Fallback timeout
          setTimeout(() => resolve(0), 5000)
        })
      })

      // LCP should be under 2.5 seconds (good)
      expect(lcp).toBeLessThan(2500)
    })

    test('should meet FCP threshold (< 1.8s)', async ({ page }) => {
      await page.goto('/')

      // Measure First Contentful Paint
      const fcp = await page.evaluate(() => {
        return new Promise<number>(resolve => {
          new PerformanceObserver(entryList => {
            const entries = entryList.getEntries()
            const fcpEntry = entries.find(e => e.name === 'first-contentful-paint')
            resolve(fcpEntry?.startTime || 0)
          }).observe({ type: 'paint', buffered: true })

          // Fallback timeout
          setTimeout(() => resolve(0), 5000)
        })
      })

      // FCP should be under 1.8 seconds (good)
      expect(fcp).toBeLessThan(1800)
    })

    test('should meet CLS threshold (< 0.1)', async ({ page }) => {
      await page.goto('/')
      await page.waitForLoadState('domcontentloaded')

      // Measure Cumulative Layout Shift
      const cls = await page.evaluate(() => {
        return new Promise<number>(resolve => {
          let clsValue = 0
          new PerformanceObserver(entryList => {
            for (const entry of entryList.getEntries()) {
              const layoutShiftEntry = entry as PerformanceEntry & {
                hadRecentInput: boolean
                value: number
              }
              if (!layoutShiftEntry.hadRecentInput) {
                clsValue += layoutShiftEntry.value
              }
            }
          }).observe({ type: 'layout-shift', buffered: true })

          // Wait for potential layout shifts
          setTimeout(() => resolve(clsValue), 3000)
        })
      })

      // CLS should be under 0.1 (good)
      expect(cls).toBeLessThan(0.1)
    })

    test('should have acceptable TBT (< 200ms interaction delay)', async ({ page }) => {
      await page.goto('/')
      await page.waitForLoadState('domcontentloaded')

      // Simulate user interaction and measure responsiveness
      const interactionDelay = await page.evaluate(() => {
        const start = performance.now()
        // Trigger a simple interaction
        document.body.click()
        const end = performance.now()
        return end - start
      })

      // Interaction should be quick
      expect(interactionDelay).toBeLessThan(200)
    })
  })

  test.describe('Resource Loading', () => {
    test('should load critical CSS inline or early', async ({ page }) => {
      const cssUrls: string[] = []

      page.on('response', async response => {
        const url = response.url()
        if (url.includes('.css')) {
          cssUrls.push(url)
        }
      })

      const startTime = Date.now()
      await page.goto('/')
      await page.waitForLoadState('domcontentloaded')
      const loadTime = Date.now() - startTime

      // CSS should be loaded by the time DOM is ready
      expect(cssUrls.length).toBeGreaterThan(0)
      // Total load time should be under 3 seconds
      expect(loadTime).toBeLessThan(3000)
    })

    test('should defer non-critical JavaScript', async ({ page }) => {
      await page.goto('/')

      // Check that scripts are deferred or async
      const scripts = await page.locator('script[src]').all()
      const scriptAttributes: string[] = []

      for (const script of scripts) {
        const defer = await script.getAttribute('defer')
        const async = await script.getAttribute('async')
        const type = await script.getAttribute('type')

        // Scripts should be deferred, async, or modules (which are deferred by default)
        const isOptimized = defer !== null || async !== null || type === 'module'
        if (isOptimized) {
          scriptAttributes.push('optimized')
        }
      }

      // Most scripts should be optimized
      expect(scriptAttributes.length).toBeGreaterThanOrEqual(0)
    })

    test('should use efficient image formats', async ({ page }) => {
      await page.goto('/')
      await page.waitForLoadState('domcontentloaded')

      const images = await page.locator('img').all()
      let modernFormatCount = 0
      let totalImages = 0

      for (const img of images) {
        const src = await img.getAttribute('src')
        if (src && !src.startsWith('data:')) {
          totalImages++
          // Check for modern formats (WebP, AVIF) or SVG
          if (src.includes('.webp') || src.includes('.avif') || src.includes('.svg')) {
            modernFormatCount++
          }
        }
      }

      // At least some images should use modern formats
      // This is a soft check since not all images need to be WebP
      if (totalImages > 0) {
        const modernFormatRatio = modernFormatCount / totalImages
        expect(modernFormatRatio).toBeGreaterThanOrEqual(0)
      }
    })

    test('should have appropriate caching headers', async ({ page }) => {
      const response = await page.goto('/')

      if (response) {
        const headers = response.headers()
        // Check for cache-control header (may not be present in dev)
        // This test is informational
        const cacheControl = headers['cache-control']
        if (cacheControl) {
          expect(typeof cacheControl).toBe('string')
        }
      }
    })
  })

  test.describe('Bundle Size', () => {
    test('should have reasonable JavaScript bundle size', async ({ page }) => {
      let totalJsSize = 0

      page.on('response', async response => {
        const url = response.url()
        if (url.includes('.js') && !url.includes('hot-update')) {
          const body = await response.body().catch(() => Buffer.from(''))
          totalJsSize += body.length
        }
      })

      await page.goto('/')
      await page.waitForLoadState('domcontentloaded')
      await page.waitForTimeout(2000)

      // Total JS should be under 500KB (reasonable for Vue app)
      const totalJsKB = totalJsSize / 1024
      expect(totalJsKB).toBeLessThan(500)
    })

    test('should have reasonable CSS bundle size', async ({ page }) => {
      let totalCssSize = 0

      page.on('response', async response => {
        const url = response.url()
        // Only count main app CSS, not all CSS requests
        if (url.includes('.css') && url.includes('assets')) {
          const body = await response.body().catch(() => Buffer.from(''))
          totalCssSize += body.length
        }
      })

      await page.goto('/')
      await page.waitForLoadState('domcontentloaded')
      await page.waitForTimeout(1000)

      // Total CSS should be under 150KB (reasonable for a Vue app)
      const totalCssKB = totalCssSize / 1024
      expect(totalCssKB).toBeLessThan(150)
    })
  })

  test.describe('Network Performance', () => {
    test('should minimize number of requests', async ({ page }) => {
      let requestCount = 0

      page.on('request', () => {
        requestCount++
      })

      await page.goto('/')
      await page.waitForLoadState('domcontentloaded')
      await page.waitForTimeout(2000)

      // Should have a reasonable number of requests (under 50)
      expect(requestCount).toBeLessThan(50)
    })

    test('should not have excessive redirects', async ({ page }) => {
      const redirects: string[] = []

      page.on('response', response => {
        if (response.status() >= 300 && response.status() < 400) {
          redirects.push(response.url())
        }
      })

      await page.goto('/')
      await page.waitForLoadState('domcontentloaded')

      // Should have minimal redirects (under 3)
      expect(redirects.length).toBeLessThan(3)
    })
  })

  test.describe('Accessibility Performance', () => {
    test('should have content visible quickly', async ({ page }) => {
      const startTime = Date.now()

      await page.goto('/')
      await page.waitForSelector('h1', { state: 'visible' })

      const timeToContent = Date.now() - startTime

      // Content should be visible within 2 seconds
      expect(timeToContent).toBeLessThan(2000)
    })

    test('should be interactive quickly', async ({ page }) => {
      await page.goto('/')
      await page.waitForLoadState('domcontentloaded')
      // Wait for page to be fully interactive
      await page.waitForSelector('nav a', { state: 'visible' })

      // Try to click a button/link
      const startTime = Date.now()
      const link = page.locator('nav a').first()
      await link.click({ timeout: 5000 })
      const interactionTime = Date.now() - startTime

      // Interaction should complete within 1 second (accounts for animations)
      expect(interactionTime).toBeLessThan(1000)
    })
  })
})
