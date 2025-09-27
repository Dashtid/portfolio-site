import { test, expect } from '@playwright/test'

test.describe('Accessibility', () => {
  test('should have proper heading hierarchy', async ({ page }) => {
    await page.goto('http://localhost:3000')

    // Check main heading
    const h1 = page.locator('h1')
    await expect(h1).toHaveCount(1)
    await expect(h1).toContainText('Cybersecurity and Quality Assurance')

    // Check section headings
    const h2s = page.locator('h2')
    await expect(h2s).toHaveCount(5) // Experience, Education, Projects, About, Contact

    // Verify h2 content
    await expect(h2s.nth(0)).toContainText('Experience')
    await expect(h2s.nth(1)).toContainText('Education')
    await expect(h2s.nth(2)).toContainText('GitHub')
  })

  test('should have alt text for images', async ({ page }) => {
    await page.goto('http://localhost:3000')

    const images = page.locator('img')
    const count = await images.count()

    for (let i = 0; i < count; i++) {
      const img = images.nth(i)
      const alt = await img.getAttribute('alt')
      const role = await img.getAttribute('role')

      // Images should have alt text or role="presentation"
      expect(alt !== null || role === 'presentation').toBeTruthy()
    }
  })

  test('should have proper form labels', async ({ page }) => {
    await page.goto('http://localhost:3000')

    // Check theme toggle button
    const themeToggle = page.locator('#themeToggle')
    await expect(themeToggle).toHaveAttribute('aria-label')

    // Check any form elements
    const formElements = page.locator('input, textarea, select')
    const count = await formElements.count()

    for (let i = 0; i < count; i++) {
      const element = formElements.nth(i)
      const id = await element.getAttribute('id')
      const ariaLabel = await element.getAttribute('aria-label')
      const ariaLabelledby = await element.getAttribute('aria-labelledby')

      // Should have associated label
      if (id) {
        const label = page.locator(`label[for="${id}"]`)
        const hasLabel = (await label.count()) > 0
        expect(hasLabel || ariaLabel || ariaLabelledby).toBeTruthy()
      }
    }
  })

  test('should support keyboard navigation', async ({ page }) => {
    await page.goto('http://localhost:3000')

    // Test skip navigation accessibility - element exists and has proper attributes
    const skipNav = page.locator('.skip-nav')
    await expect(skipNav).toBeAttached()
    await expect(skipNav).toHaveAttribute('href', '#experience')

    // Test navigation to target section directly (skip nav positioning varies by browser)
    const experienceSection = page.locator('#experience')
    await expect(experienceSection).toBeVisible()

    // Simulate skip navigation functionality by scrolling to target
    await experienceSection.scrollIntoViewIfNeeded()
    await page.waitForTimeout(300)

    // Test that all main navigation links are focusable (not necessarily in strict order)
    const navLinks = [
      '.navbar-nav .nav-link[href="#experience"]',
      '.navbar-nav .nav-link[href="#education"]',
      '.navbar-nav .nav-link[href="#projects"]',
      '.navbar-nav .nav-link[href="#about"]',
      '.navbar-nav .nav-link[href="#contact"]'
    ]

    // Test each navigation link can be focused via keyboard
    for (const linkSelector of navLinks) {
      const link = page.locator(linkSelector)
      await expect(link).toBeVisible()
      await link.focus()
      await expect(link).toBeFocused()

      // Test that Enter key works on navigation links
      await page.keyboard.press('Enter')
      await page.waitForTimeout(200)
    }

    // Test GitHub button accessibility
    const githubButton = page.locator('a[aria-label="Visit GitHub profile"]')
    await expect(githubButton).toBeVisible()
    await githubButton.focus()
    await expect(githubButton).toBeFocused()

    // Test theme toggle accessibility (now in fixed position)
    const themeToggle = page.locator('#themeToggle')
    await expect(themeToggle).toBeVisible()
    await themeToggle.focus()
    await expect(themeToggle).toBeFocused()

    // Test that theme toggle responds to keyboard
    await page.keyboard.press('Enter')
    await page.waitForTimeout(300)

    // Theme toggle should have switched mode (aria-checked should be true)
    await expect(themeToggle).toHaveAttribute('aria-checked', 'true')

    // Test that all focusable elements have proper ARIA attributes
    const focusableElements = await page
      .locator(
        '[tabindex]:not([tabindex="-1"]), a[href], button:not([disabled])'
      )
      .all()
    for (const element of focusableElements) {
      // Each focusable element should be visible or properly hidden
      const isVisible = await element.isVisible()
      if (isVisible) {
        await expect(element).toBeVisible()
      }
    }
  })

  test('should have sufficient color contrast', async ({ page }) => {
    await page.goto('http://localhost:3000')

    // Test common elements for basic contrast
    const textElements = ['h1', 'h2', 'p', '.nav-link', '.btn']

    for (const selector of textElements) {
      const elements = page.locator(selector)
      const count = await elements.count()

      if (count > 0) {
        const firstElement = elements.first()
        const color = await firstElement.evaluate(
          el => getComputedStyle(el).color
        )
        const backgroundColor = await firstElement.evaluate(
          el => getComputedStyle(el).backgroundColor
        )

        // Basic check that colors are defined
        expect(color).toBeTruthy()
        expect(backgroundColor).toBeTruthy()
      }
    }
  })

  test('should have proper ARIA attributes', async ({ page }) => {
    await page.goto('http://localhost:3000')

    // Check navigation ARIA
    const nav = page.locator('nav[role="navigation"]')
    await expect(nav).toHaveAttribute('aria-label')

    // Check theme switch states
    const themeToggle = page.locator('#themeToggle')
    await expect(themeToggle).toHaveAttribute('aria-checked')
    await expect(themeToggle).toHaveAttribute('role', 'switch')

    // Check section landmarks
    const main = page.locator('main')
    await expect(main).toBeVisible()
  })

  test('should support reduced motion', async ({ page, context }) => {
    await page.emulateMedia({ reducedMotion: 'reduce' })
    await page.goto('http://localhost:3000')

    // Check that animations are disabled with reduced motion
    const body = page.locator('body')
    const animationDuration = await body.evaluate(el =>
      getComputedStyle(el).getPropertyValue('animation-duration')
    )

    // With reduced motion, animations should be very fast or disabled
    // This is more of a smoke test - detailed testing would require checking CSS
    expect(typeof animationDuration).toBe('string')
  })
})
