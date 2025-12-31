import { test, expect } from '@playwright/test'

/**
 * Visual regression tests for portfolio site
 * Run with: npm run test:e2e:visual
 * Update baselines with: npm run test:e2e:visual:update
 */

test.describe('Visual Regression Tests', () => {
  test.describe('Home Page Sections', () => {
    test('hero section - light mode', async ({ page }) => {
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      // Wait for any animations to complete
      await page.waitForTimeout(500)
      await expect(page.locator('#hero')).toHaveScreenshot('hero-light.png')
    })

    test('hero section - dark mode', async ({ page }) => {
      await page.goto('/')
      await page.waitForLoadState('networkidle')
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
})
