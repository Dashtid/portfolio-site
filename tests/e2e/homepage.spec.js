import { test, expect } from '@playwright/test'

test.describe('Homepage', () => {
  test('should load successfully', async ({ page }) => {
    await page.goto('http://localhost:3000')

    // Check that page loads
    await expect(page).toHaveTitle(/David Dashti/)

    // Check hero section
    await expect(page.locator('h1')).toContainText(
      'Cybersecurity and Quality Assurance'
    )

    // Check navigation is present
    await expect(page.locator('.navbar')).toBeVisible()

    // Check main sections exist
    await expect(page.locator('#experience')).toBeVisible()
    await expect(page.locator('#education')).toBeVisible()
    await expect(page.locator('#skills')).toBeVisible()
    await expect(page.locator('#about')).toBeVisible()
    await expect(page.locator('#contact')).toBeVisible()
  })

  test('should have proper meta tags', async ({ page }) => {
    await page.goto('http://localhost:3000')

    // Check essential meta tags
    const description = await page
      .locator('meta[name="description"]')
      .getAttribute('content')
    expect(description).toContain(
      'Biomedical Engineer and Cybersecurity Specialist'
    )

    // Check Open Graph tags
    const ogTitle = await page
      .locator('meta[property="og:title"]')
      .getAttribute('content')
    expect(ogTitle).toContain('David Dashti')

    // Check structured data
    const jsonLd = await page
      .locator('script[type="application/ld+json"]')
      .textContent()
    expect(jsonLd).toContain('"@type": "Person"')
  })

  test('should be responsive', async ({ page }) => {
    // Test desktop
    await page.setViewportSize({ width: 1920, height: 1080 })
    await page.goto('http://localhost:3000')
    await expect(page.locator('.hero')).toBeVisible()

    // Test tablet
    await page.setViewportSize({ width: 768, height: 1024 })
    await expect(page.locator('.hero')).toBeVisible()

    // Test mobile
    await page.setViewportSize({ width: 375, height: 667 })
    await expect(page.locator('.hero')).toBeVisible()
    await expect(page.locator('.navbar-toggler')).toBeVisible()
  })

  test('should have accessible navigation', async ({ page }) => {
    await page.goto('http://localhost:3000')

    // Check skip link
    const skipLink = page.locator('.skip-nav')
    await expect(skipLink).toHaveAttribute('href', '#main-heading')

    // Test keyboard navigation
    await page.keyboard.press('Tab')
    await expect(skipLink).toBeFocused()

    // Check ARIA attributes
    const nav = page.locator('.navbar')
    await expect(nav).toHaveAttribute('role', 'navigation')
    await expect(nav).toHaveAttribute('aria-label', 'Main navigation')
  })
})
