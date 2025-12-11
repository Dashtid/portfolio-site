import { test, expect } from '@playwright/test'

/**
 * Visual Regression Tests
 *
 * These tests capture screenshots and compare them against baseline images.
 * On first run, baselines are created. Subsequent runs compare against baselines.
 *
 * Update baselines: npx playwright test --update-snapshots
 */
test.describe('Visual Regression', () => {
  test.describe('Home Page', () => {
    test('hero section should match baseline', async ({ page }) => {
      await page.goto('/')
      await page.waitForLoadState('domcontentloaded')
      await page.waitForSelector('#hero', { state: 'visible' })
      // Wait for images and fonts to load
      await page.waitForTimeout(1000)

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
      await page.waitForTimeout(1000)

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
      await page.waitForTimeout(1000)

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
      await page.waitForTimeout(1000)

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
      await page.waitForTimeout(1500)

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
      await page.waitForTimeout(500)

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
      await page.waitForTimeout(1000)

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
      await page.waitForTimeout(1000)

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
      await page.waitForTimeout(1000)

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
      await page.waitForTimeout(500)

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
      await page.waitForTimeout(500)

      const footer = page.locator('footer').first()
      await expect(footer).toHaveScreenshot('footer.png', {
        maxDiffPixels: 50,
        threshold: 0.2
      })
    })
  })
})
