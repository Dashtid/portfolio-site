import { test, expect } from '@playwright/test'
import { HomePage } from './pages'

test.describe('Home Page', () => {
  let homePage: HomePage

  test.beforeEach(async ({ page }) => {
    homePage = new HomePage(page)
    await homePage.goto()
  })

  test.describe('Initial Load', () => {
    test('should load the home page successfully', async ({ page }) => {
      await expect(page).toHaveTitle(/David Dashti/)
    })

    test('should display the hero section', async () => {
      await homePage.verifyHeroSection()
    })

    test('should display the navigation bar', async () => {
      await homePage.verifyNavigation()
    })

    test('should have all main sections', async () => {
      await homePage.verifySectionsExist()
    })
  })

  test.describe('Navigation', () => {
    test('should navigate to different sections via nav links', async ({ page }) => {
      // Click on About link if it exists
      const aboutLink = page.locator('nav a[href*="about"], nav a:has-text("About")')
      if ((await aboutLink.count()) > 0) {
        await aboutLink.first().click()
        await page.waitForTimeout(500)
        // Verify we scrolled
        const scrollY = await page.evaluate(() => window.scrollY)
        expect(scrollY).toBeGreaterThan(0)
      }
    })

    test('should have working external links with correct attributes', async ({ page }) => {
      const externalLinks = page.locator('a[target="_blank"]')
      const count = await externalLinks.count()

      for (let i = 0; i < count; i++) {
        const link = externalLinks.nth(i)
        // External links should have rel="noopener noreferrer" for security
        const rel = await link.getAttribute('rel')
        expect(rel).toContain('noopener')
      }
    })
  })

  test.describe('Theme Toggle', () => {
    test('should toggle between light and dark themes', async ({ page }) => {
      const themeToggle = page.locator(
        '[data-testid="theme-toggle"], button:has([class*="sun"]), button:has([class*="moon"])'
      )

      if ((await themeToggle.count()) > 0) {
        const html = page.locator('html')
        const initialClass = await html.getAttribute('class')

        await themeToggle.first().click()
        await page.waitForTimeout(300)

        const newClass = await html.getAttribute('class')
        // Theme class should have changed
        expect(newClass).not.toBe(initialClass)
      }
    })

    test('should persist theme preference', async ({ page, context }) => {
      const themeToggle = page.locator(
        '[data-testid="theme-toggle"], button:has([class*="sun"]), button:has([class*="moon"])'
      )

      if ((await themeToggle.count()) > 0) {
        await themeToggle.first().click()
        await page.waitForTimeout(300)

        const html = page.locator('html')
        const themeAfterToggle = await html.getAttribute('class')

        // Reload the page
        await page.reload()
        await page.waitForLoadState('networkidle')

        // Theme should persist (via localStorage)
        const themeAfterReload = await html.getAttribute('class')
        expect(themeAfterReload).toBe(themeAfterToggle)
      }
    })
  })

  test.describe('Responsive Design', () => {
    test('should display correctly on mobile viewport', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 })
      await page.reload()

      // Page should still be functional
      await expect(page.locator('h1')).toBeVisible()

      // Navigation might be collapsed
      const mobileMenu = page.locator('[data-testid="mobile-menu"], button[aria-label*="menu"]')
      if ((await mobileMenu.count()) > 0) {
        await expect(mobileMenu.first()).toBeVisible()
      }
    })

    test('should display correctly on tablet viewport', async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 })
      await page.reload()

      await expect(page.locator('h1')).toBeVisible()
    })

    test('should display correctly on desktop viewport', async ({ page }) => {
      await page.setViewportSize({ width: 1920, height: 1080 })
      await page.reload()

      await expect(page.locator('h1')).toBeVisible()
    })
  })

  test.describe('Accessibility', () => {
    test('should have proper heading hierarchy', async ({ page }) => {
      const h1Count = await page.locator('h1').count()
      expect(h1Count).toBe(1) // Should have exactly one h1

      // H2s should come after h1
      const headings = await page.locator('h1, h2, h3').all()
      expect(headings.length).toBeGreaterThan(0)
    })

    test('should have alt text on images', async ({ page }) => {
      const images = page.locator('img')
      const count = await images.count()

      for (let i = 0; i < count; i++) {
        const img = images.nth(i)
        const alt = await img.getAttribute('alt')
        const ariaHidden = await img.getAttribute('aria-hidden')

        // Images should have alt text unless they're decorative (aria-hidden)
        if (ariaHidden !== 'true') {
          expect(alt).toBeTruthy()
        }
      }
    })

    test('should have focusable interactive elements', async ({ page }) => {
      // Tab through the page
      await page.keyboard.press('Tab')
      const focusedElement = await page.evaluate(() => document.activeElement?.tagName)
      expect(focusedElement).toBeTruthy()
    })

    test('should respect reduced motion preference', async ({ page }) => {
      // Enable reduced motion
      await page.emulateMedia({ reducedMotion: 'reduce' })
      await page.reload()

      // Page should still load correctly
      await expect(page.locator('h1')).toBeVisible()
    })
  })

  test.describe('Performance', () => {
    test('should load within acceptable time', async ({ page }) => {
      const startTime = Date.now()
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      const loadTime = Date.now() - startTime

      // Page should load within 5 seconds
      expect(loadTime).toBeLessThan(5000)
    })

    test('should not have broken images', async ({ page }) => {
      const images = page.locator('img')
      const count = await images.count()

      for (let i = 0; i < count; i++) {
        const img = images.nth(i)
        const naturalWidth = await img.evaluate((el: HTMLImageElement) => el.naturalWidth)
        // Images with 0 naturalWidth are broken
        expect(naturalWidth).toBeGreaterThan(0)
      }
    })
  })

  test.describe('SEO', () => {
    test('should have meta description', async ({ page }) => {
      const metaDescription = page.locator('meta[name="description"]')
      const content = await metaDescription.getAttribute('content')
      expect(content).toBeTruthy()
      expect(content!.length).toBeGreaterThan(50)
    })

    test('should have Open Graph tags', async ({ page }) => {
      const ogTitle = page.locator('meta[property="og:title"]')
      const ogDescription = page.locator('meta[property="og:description"]')

      await expect(ogTitle).toBeAttached()
      await expect(ogDescription).toBeAttached()
    })

    test('should have canonical URL', async ({ page }) => {
      const canonical = page.locator('link[rel="canonical"]')
      await expect(canonical).toBeAttached()
    })
  })
})
