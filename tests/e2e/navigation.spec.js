import { test, expect } from '@playwright/test'

test.describe('Navigation', () => {
  test('should navigate to all internal sections', async ({ page }) => {
    await page.goto('/')

    const sections = [
      { link: '[data-scroll="experience"]', target: '#experience' },
      { link: '[data-scroll="education"]', target: '#education' },
      { link: '[data-scroll="github-repos"]', target: '#github-repos' },
      { link: '[data-scroll="skills"]', target: '#skills' },
      { link: '[data-scroll="about"]', target: '#about' },
      { link: '[data-scroll="contact"]', target: '#contact' }
    ]

    for (const section of sections) {
      await page.locator(section.link).click()
      await page.waitForTimeout(500) // Allow smooth scroll to complete

      // Check if section is visible
      await expect(page.locator(section.target)).toBeInViewport()

      // Check URL hash
      expect(page.url()).toContain(section.target)
    }
  })

  test('should highlight active navigation items', async ({ page }) => {
    await page.goto('/')

    // Click on experience section
    await page.locator('[data-scroll="experience"]').click()
    await page.waitForTimeout(1500) // More time for Firefox scrolling and intersection observer

    // Check if experience nav item has active class
    await expect(page.locator('[data-scroll="experience"]')).toHaveClass(
      /active/
    )

    // Click on another section
    await page.locator('[data-scroll="skills"]').click()
    await page.waitForTimeout(1500) // More time for Firefox

    // Check if skills nav item has active class and experience doesn't
    await expect(page.locator('[data-scroll="skills"]')).toHaveClass(/active/)
    await expect(page.locator('[data-scroll="experience"]')).not.toHaveClass(
      /active/
    )
  })

  test('should navigate to external pages', async ({ page, context }) => {
    await page.goto('/')

    const externalLinks = [
      { link: 'a[href="experience/scania.html"]', expectedTitle: /Scania/ },
      { link: 'a[href="experience/hermes.html"]', expectedTitle: /Hermes/ },
      {
        link: 'a[href="experience/karolinska.html"]',
        expectedTitle: /Karolinska/
      }
    ]

    for (const external of externalLinks) {
      // Navigate to the page directly since these are same-tab navigation
      await page.locator(external.link).first().click()
      await page.waitForLoadState('networkidle')

      // Check the title
      await expect(page).toHaveTitle(external.expectedTitle)

      // Go back to main page for next test
      await page.goBack()
      await page.waitForLoadState('networkidle')
    }
  })

  test('should work on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })
    await page.goto('/')

    // Open mobile menu
    const menuToggle = page.locator('.navbar-toggler')
    await expect(menuToggle).toBeVisible()
    await menuToggle.click()

    // Check if menu is expanded
    const navMenu = page.locator('.navbar-collapse')
    await expect(navMenu).toHaveClass(/show/)

    // Click on a navigation item
    await page.locator('[data-scroll="experience"]').click()

    // Menu should close after navigation
    await expect(navMenu).not.toHaveClass(/show/)

    // Should navigate to section
    await expect(page.locator('#experience')).toBeInViewport()
  })

  test('should handle back-to-top functionality', async ({ page }) => {
    await page.goto('/')

    // Scroll down to make back-to-top visible
    await page.evaluate(() => window.scrollTo(0, 1000))
    await page.waitForTimeout(1000) // More time for Firefox

    // Back to top button should be visible
    const backToTop = page.locator('#backToTopBtn')
    await expect(backToTop).toBeVisible()

    // Click back to top
    await backToTop.click()

    // Wait for scroll to complete - different approach for Firefox
    await page.waitForFunction(() => window.pageYOffset < 100, {
      timeout: 5000
    })
    await page.waitForTimeout(500) // Additional buffer

    // Should be back at top
    const scrollY = await page.evaluate(() => window.pageYOffset)
    expect(scrollY).toBeLessThan(100) // Less strict for Firefox compatibility
  })
})
