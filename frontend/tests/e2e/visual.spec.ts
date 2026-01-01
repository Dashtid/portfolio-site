import { test, expect } from '@playwright/test'

/**
 * Visual regression tests for portfolio site
 * Run with: npm run test:e2e:visual
 * Update baselines with: npm run test:e2e:visual:update
 *
 * These tests capture baseline screenshots of the UI and compare
 * future runs against them to detect unintended visual changes.
 */

// Helper to wait for page to be stable
async function waitForStableUI(page: import('@playwright/test').Page) {
  await page.waitForLoadState('networkidle')
  // Wait for animations and transitions to complete
  await page.waitForTimeout(500)
}

test.describe('Visual Regression Tests', () => {
  test.describe('Home Page Sections', () => {
    test('hero section - light mode', async ({ page }) => {
      await page.goto('/')
      await waitForStableUI(page)
      await expect(page.locator('#hero')).toHaveScreenshot('hero-light.png')
    })

    test('hero section - dark mode', async ({ page }) => {
      await page.goto('/')
      await waitForStableUI(page)
      // Toggle to dark mode
      const themeToggle = page.locator('[data-testid="theme-toggle"]')
      if (await themeToggle.isVisible()) {
        await themeToggle.click()
        await page.waitForTimeout(300)
      }
      await expect(page.locator('#hero')).toHaveScreenshot('hero-dark.png')
    })

    test('experience section', async ({ page }) => {
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      await page.locator('#experience').scrollIntoViewIfNeeded()
      // Wait for scroll animations
      await page.waitForTimeout(800)
      await expect(page.locator('#experience')).toHaveScreenshot('experience.png')
    })

    test('education section', async ({ page }) => {
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      await page.locator('#education').scrollIntoViewIfNeeded()
      await page.waitForTimeout(800)
      await expect(page.locator('#education')).toHaveScreenshot('education.png')
    })

    test('projects section', async ({ page }) => {
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      await page.locator('#projects').scrollIntoViewIfNeeded()
      await page.waitForTimeout(800)
      await expect(page.locator('#projects')).toHaveScreenshot('projects.png')
    })

    test('about section', async ({ page }) => {
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      await page.locator('#about').scrollIntoViewIfNeeded()
      await page.waitForTimeout(800)
      await expect(page.locator('#about')).toHaveScreenshot('about.png')
    })

    test('footer section', async ({ page }) => {
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight))
      await page.waitForTimeout(500)
      await expect(page.locator('footer')).toHaveScreenshot('footer.png')
    })
  })

  test.describe('Responsive Breakpoints', () => {
    test('mobile viewport (375px)', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 })
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      await page.waitForTimeout(500)
      await expect(page).toHaveScreenshot('home-mobile.png', { fullPage: true })
    })

    test('tablet viewport (768px)', async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 })
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      await page.waitForTimeout(500)
      await expect(page).toHaveScreenshot('home-tablet.png', { fullPage: true })
    })

    test('desktop viewport (1920px)', async ({ page }) => {
      await page.setViewportSize({ width: 1920, height: 1080 })
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      await page.waitForTimeout(500)
      await expect(page).toHaveScreenshot('home-desktop.png', { fullPage: true })
    })
  })

  test.describe('Component States', () => {
    test('navigation bar', async ({ page }) => {
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      await expect(page.locator('nav')).toHaveScreenshot('nav-default.png')
    })

    test('navigation bar - scrolled', async ({ page }) => {
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      // Scroll down to trigger navbar style change
      await page.evaluate(() => window.scrollTo(0, 200))
      await page.waitForTimeout(300)
      await expect(page.locator('nav')).toHaveScreenshot('nav-scrolled.png')
    })

    test('theme toggle states', async ({ page }) => {
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      const themeToggle = page.locator('[data-testid="theme-toggle"]')
      if (await themeToggle.isVisible()) {
        await expect(themeToggle).toHaveScreenshot('theme-toggle-light.png')
        await themeToggle.click()
        await page.waitForTimeout(300)
        await expect(themeToggle).toHaveScreenshot('theme-toggle-dark.png')
      }
    })
  })

  test.describe('Interactive Elements', () => {
    test('experience card hover state', async ({ page }) => {
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      await page.locator('#experience').scrollIntoViewIfNeeded()
      await page.waitForTimeout(800)

      const card = page.locator('.experience-card').first()
      if (await card.isVisible()) {
        await card.hover()
        await page.waitForTimeout(300)
        await expect(card).toHaveScreenshot('experience-card-hover.png')
      }
    })

    test('project card hover state', async ({ page }) => {
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      await page.locator('#projects').scrollIntoViewIfNeeded()
      await page.waitForTimeout(800)

      const card = page.locator('.project-card').first()
      if (await card.isVisible()) {
        await card.hover()
        await page.waitForTimeout(300)
        await expect(card).toHaveScreenshot('project-card-hover.png')
      }
    })
  })

  test.describe('Detail Pages', () => {
    test('experience detail page - scania', async ({ page }) => {
      await page.goto('/experience/scania')
      await waitForStableUI(page)
      await expect(page).toHaveScreenshot('experience-detail-scania.png', { fullPage: true })
    })

    test('experience detail page - hermes', async ({ page }) => {
      await page.goto('/experience/hermes')
      await waitForStableUI(page)
      await expect(page).toHaveScreenshot('experience-detail-hermes.png', { fullPage: true })
    })

    test('experience detail page - mobile viewport', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 })
      await page.goto('/experience/scania')
      await waitForStableUI(page)
      await expect(page).toHaveScreenshot('experience-detail-mobile.png', { fullPage: true })
    })

    test('experience detail page - dark mode', async ({ page }) => {
      await page.goto('/experience/scania')
      await waitForStableUI(page)
      const themeToggle = page.locator('[data-testid="theme-toggle"]')
      if (await themeToggle.isVisible()) {
        await themeToggle.click()
        await page.waitForTimeout(300)
      }
      await expect(page).toHaveScreenshot('experience-detail-dark.png', { fullPage: true })
    })
  })

  test.describe('Error States', () => {
    test('404 page - invalid experience', async ({ page }) => {
      await page.goto('/experience/nonexistent-company')
      await waitForStableUI(page)
      // Capture whatever error/not found state is displayed
      await expect(page).toHaveScreenshot('experience-not-found.png', { fullPage: true })
    })
  })

  test.describe('Print Styles', () => {
    test('home page print view', async ({ page }) => {
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      await page.emulateMedia({ media: 'print' })
      await page.waitForTimeout(300)
      await expect(page).toHaveScreenshot('home-print.png', { fullPage: true })
    })
  })

  test.describe('Reduced Motion', () => {
    test('home page with reduced motion', async ({ page }) => {
      await page.emulateMedia({ reducedMotion: 'reduce' })
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      await page.waitForTimeout(300)
      await expect(page).toHaveScreenshot('home-reduced-motion.png', { fullPage: true })
    })
  })
})
