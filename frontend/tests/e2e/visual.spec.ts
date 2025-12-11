import { test, expect, Page } from '@playwright/test'

/**
 * Visual Regression Tests
 *
 * These tests capture screenshots and compare them against baseline images.
 * On first run, baselines are created. Subsequent runs compare against baselines.
 *
 * Update baselines: npx playwright test --update-snapshots
 */

/**
 * Wait for all images in a section to be fully loaded
 */
async function waitForImagesToLoad(page: Page, selector?: string): Promise<void> {
  await page.waitForLoadState('networkidle')
  await page.waitForFunction(
    (sel: string | undefined) => {
      const container = sel ? document.querySelector(sel) : document
      if (!container) return true
      const images = container.querySelectorAll('img')
      return Array.from(images).every(img => img.complete && img.naturalHeight !== 0)
    },
    selector,
    { timeout: 10000 }
  )
}

test.describe('Visual Regression', () => {
  test.describe('Home Page', () => {
    test('hero section should match baseline', async ({ page }) => {
      await page.goto('/')
      await page.waitForLoadState('domcontentloaded')
      await page.waitForSelector('#hero', { state: 'visible' })
      // Wait for images and fonts to load
      await waitForImagesToLoad(page, '#hero')

      const heroSection = page.locator('#hero')
      await expect(heroSection).toHaveScreenshot('hero-section.png', {
        maxDiffPixels: 100,
        threshold: 0.2
      })
    })

    test('experience section should match baseline', async ({ page }) => {
      await page.goto('/')
      await page.waitForLoadState('domcontentloaded')
      await page.waitForSelector('#experience', { state: 'visible' })
      await page.locator('#experience').scrollIntoViewIfNeeded()
      await waitForImagesToLoad(page, '#experience')

      const experienceSection = page.locator('#experience')
      await expect(experienceSection).toHaveScreenshot('experience-section.png', {
        maxDiffPixels: 100,
        threshold: 0.2
      })
    })

    test('education section should match baseline', async ({ page }) => {
      await page.goto('/')
      await page.waitForLoadState('domcontentloaded')
      await page.waitForSelector('#education', { state: 'visible' })
      await page.locator('#education').scrollIntoViewIfNeeded()
      await waitForImagesToLoad(page, '#education')

      const educationSection = page.locator('#education')
      await expect(educationSection).toHaveScreenshot('education-section.png', {
        maxDiffPixels: 100,
        threshold: 0.2
      })
    })

    test('about section should match baseline', async ({ page }) => {
      await page.goto('/')
      await page.waitForLoadState('domcontentloaded')
      await page.waitForSelector('#about', { state: 'visible' })
      await page.locator('#about').scrollIntoViewIfNeeded()
      await waitForImagesToLoad(page, '#about')

      const aboutSection = page.locator('#about')
      await expect(aboutSection).toHaveScreenshot('about-section.png', {
        maxDiffPixels: 100,
        threshold: 0.2
      })
    })

    test('full page should match baseline', async ({ page }) => {
      await page.goto('/')
      await page.waitForLoadState('domcontentloaded')
      await page.waitForSelector('h1', { state: 'visible' })
      await waitForImagesToLoad(page)

      await expect(page).toHaveScreenshot('full-page.png', {
        fullPage: true,
        maxDiffPixels: 500,
        threshold: 0.2
      })
    })
  })

  test.describe('Dark Mode', () => {
    test('dark mode hero should match baseline', async ({ page }) => {
      await page.goto('/')
      await page.waitForLoadState('domcontentloaded')
      await page.waitForSelector('#hero', { state: 'visible' })

      // Enable dark mode
      await page.evaluate(() => {
        document.documentElement.setAttribute('data-theme', 'dark')
        localStorage.setItem('theme', 'dark')
      })
      // Wait for theme to be applied
      await page.waitForFunction(
        () => document.documentElement.getAttribute('data-theme') === 'dark',
        { timeout: 5000 }
      )
      await waitForImagesToLoad(page, '#hero')

      const heroSection = page.locator('#hero')
      await expect(heroSection).toHaveScreenshot('hero-section-dark.png', {
        maxDiffPixels: 100,
        threshold: 0.2
      })
    })

    test('dark mode full page should match baseline', async ({ page }) => {
      await page.goto('/')
      await page.waitForLoadState('domcontentloaded')
      await page.waitForSelector('h1', { state: 'visible' })

      // Enable dark mode
      await page.evaluate(() => {
        document.documentElement.setAttribute('data-theme', 'dark')
        localStorage.setItem('theme', 'dark')
      })
      // Wait for theme to be applied
      await page.waitForFunction(
        () => document.documentElement.getAttribute('data-theme') === 'dark',
        { timeout: 5000 }
      )
      await waitForImagesToLoad(page)

      await expect(page).toHaveScreenshot('full-page-dark.png', {
        fullPage: true,
        maxDiffPixels: 500,
        threshold: 0.2
      })
    })
  })

  test.describe('Responsive Design', () => {
    test('mobile viewport should match baseline', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 })
      await page.goto('/')
      await page.waitForLoadState('domcontentloaded')
      await page.waitForSelector('h1', { state: 'visible' })
      await waitForImagesToLoad(page)

      await expect(page).toHaveScreenshot('mobile-view.png', {
        maxDiffPixels: 200,
        threshold: 0.2
      })
    })

    test('tablet viewport should match baseline', async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 })
      await page.goto('/')
      await page.waitForLoadState('domcontentloaded')
      await page.waitForSelector('h1', { state: 'visible' })
      await waitForImagesToLoad(page)

      await expect(page).toHaveScreenshot('tablet-view.png', {
        maxDiffPixels: 200,
        threshold: 0.2
      })
    })
  })

  test.describe('Components', () => {
    test('navigation bar should match baseline', async ({ page }) => {
      await page.goto('/')
      await page.waitForLoadState('domcontentloaded')
      await page.waitForSelector('nav', { state: 'visible' })
      await waitForImagesToLoad(page, 'nav')

      const navbar = page.locator('nav').first()
      await expect(navbar).toHaveScreenshot('navbar.png', {
        maxDiffPixels: 50,
        threshold: 0.2
      })
    })

    test('footer should match baseline', async ({ page }) => {
      await page.goto('/')
      await page.waitForLoadState('domcontentloaded')
      await page.waitForSelector('footer', { state: 'visible' })
      await page.locator('footer').scrollIntoViewIfNeeded()
      await waitForImagesToLoad(page, 'footer')

      const footer = page.locator('footer').first()
      await expect(footer).toHaveScreenshot('footer.png', {
        maxDiffPixels: 50,
        threshold: 0.2
      })
    })
  })
})
