import { test, expect } from '@playwright/test'

test.describe('Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('navigates to sections via navbar links', async ({ page }) => {
    // Click on Experience link
    await page.getByRole('link', { name: /experience/i }).first().click()
    await page.waitForTimeout(500) // Wait for smooth scroll

    // Check that we scrolled to experience section
    const experienceSection = page.locator('#experience')
    await expect(experienceSection).toBeInViewport()
  })

  test('navigates to Education section', async ({ page }) => {
    await page.getByRole('link', { name: /education/i }).first().click()
    await page.waitForTimeout(500)

    const educationSection = page.locator('#education')
    await expect(educationSection).toBeInViewport()
  })

  test('navigates to Projects section', async ({ page }) => {
    await page.getByRole('link', { name: /projects/i }).first().click()
    await page.waitForTimeout(500)

    const projectsSection = page.locator('#projects')
    await expect(projectsSection).toBeInViewport()
  })

  test('navigates to About section', async ({ page }) => {
    await page.getByRole('link', { name: /about/i }).first().click()
    await page.waitForTimeout(500)

    const aboutSection = page.locator('#about')
    await expect(aboutSection).toBeInViewport()
  })

  test('navigates to Contact section', async ({ page }) => {
    await page.getByRole('link', { name: /contact/i }).first().click()
    await page.waitForTimeout(500)

    const contactSection = page.locator('#contact')
    await expect(contactSection).toBeInViewport()
  })

  test('home link navigates to hero', async ({ page }) => {
    // First navigate away from hero
    await page.getByRole('link', { name: /contact/i }).first().click()
    await page.waitForTimeout(500)

    // Click home link
    await page.getByRole('link', { name: /home/i }).first().click()
    await page.waitForTimeout(500)

    // Should be back at hero
    const heroSection = page.locator('#hero')
    await expect(heroSection).toBeInViewport()
  })

  test('logo link navigates to top', async ({ page }) => {
    // Scroll down
    await page.getByRole('link', { name: /contact/i }).first().click()
    await page.waitForTimeout(500)

    // Click logo/brand
    await page.locator('.navbar-brand').click()
    await page.waitForTimeout(500)

    // Should be at top
    const heroSection = page.locator('#hero')
    await expect(heroSection).toBeInViewport()
  })

  test('navbar remains visible while scrolling', async ({ page }) => {
    const navbar = page.locator('nav')

    // Initially visible
    await expect(navbar).toBeVisible()

    // Scroll down
    await page.evaluate(() => window.scrollTo(0, 1000))
    await page.waitForTimeout(300)

    // Still visible (sticky/fixed)
    await expect(navbar).toBeVisible()
  })

  test('mobile menu toggle works', async ({ page, isMobile }) => {
    // Only test on mobile viewports
    if (!isMobile) {
      test.skip()
      return
    }

    // Mobile menu toggle should be visible
    const toggle = page.locator('.navbar-toggler')
    await expect(toggle).toBeVisible()

    // Menu should be collapsed initially
    const menu = page.locator('.navbar-collapse')
    const isCollapsed = await menu.evaluate(el => !el.classList.contains('show'))
    expect(isCollapsed).toBeTruthy()

    // Click toggle to open
    await toggle.click()
    await page.waitForTimeout(300)

    // Menu should be visible
    await expect(menu).toHaveClass(/show/)
  })

  test('back to top button appears after scrolling', async ({ page }) => {
    // Initially, button should not be visible
    const backToTopButton = page.locator('.back-to-top')

    // Scroll down significantly
    await page.evaluate(() => window.scrollTo(0, 500))
    await page.waitForTimeout(500)

    // Button should now be visible
    await expect(backToTopButton).toBeVisible()
  })

  test('back to top button scrolls to top', async ({ page }) => {
    // Scroll down
    await page.evaluate(() => window.scrollTo(0, 1000))
    await page.waitForTimeout(500)

    // Click back to top
    const backToTopButton = page.locator('.back-to-top')
    await backToTopButton.click()
    await page.waitForTimeout(1000) // Wait for smooth scroll

    // Should be at top
    const scrollY = await page.evaluate(() => window.scrollY)
    expect(scrollY).toBeLessThan(100)
  })

  test('external links open in new tab', async ({ page, context }) => {
    // Get LinkedIn link
    const linkedInLink = page.getByRole('link', { name: /linkedin/i }).first()

    // Should have target="_blank"
    const target = await linkedInLink.getAttribute('target')
    expect(target).toBe('_blank')

    // Should have rel="noopener"
    const rel = await linkedInLink.getAttribute('rel')
    expect(rel).toContain('noopener')
  })
})
