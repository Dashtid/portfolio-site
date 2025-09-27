import { test, expect } from '@playwright/test'

test.describe('Theme System', () => {
  test('should toggle between light and dark themes', async ({ page }) => {
    await page.goto('http://localhost:3000')

    // Check initial state (should be light theme by default)
    const html = page.locator('html')
    await expect(html).not.toHaveAttribute('data-theme', 'dark')

    // Find system/manual toggle first
    const themeToggle = page.locator('#themeToggle')
    await expect(themeToggle).toBeVisible()

    // Click to switch to manual mode
    await themeToggle.click()
    await page.waitForTimeout(500) // Wait for animation

    // Now find the light/dark toggle
    const lightDarkToggle = page.locator('#lightDarkToggle')
    await expect(lightDarkToggle).toBeVisible()

    // Click to switch to dark theme
    await lightDarkToggle.click()
    await expect(html).toHaveAttribute('data-theme', 'dark')

    // Click to switch back to light theme
    await lightDarkToggle.click()
    await expect(html).toHaveAttribute('data-theme', 'light')
  })

  test('should persist theme preference', async ({ page }) => {
    await page.goto('http://localhost:3000')

    // Switch to manual mode first
    const themeToggle = page.locator('#themeToggle')
    await themeToggle.click()
    await page.waitForTimeout(500)

    // Switch to dark theme
    const lightDarkToggle = page.locator('#lightDarkToggle')
    await lightDarkToggle.click()
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark')

    // Verify localStorage was set
    const themeInStorage = await page.evaluate(() =>
      localStorage.getItem('theme')
    )
    expect(themeInStorage).toBe('dark')

    // Verify manual mode was set
    const modeInStorage = await page.evaluate(() =>
      localStorage.getItem('theme-mode')
    )
    expect(modeInStorage).toBe('manual')

    // Reload page and check if theme persists
    await page.reload({ waitUntil: 'networkidle' })
    await page.waitForTimeout(1000)

    // Check theme restoration
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark')

    // Check that manual toggle is visible
    await expect(page.locator('#manualThemeToggle')).toBeVisible()
  })

  test('should respect system theme preference', async ({ page }) => {
    await page.goto('http://localhost:3000')

    // Clear any existing preferences
    await page.evaluate(() => {
      localStorage.removeItem('theme')
      localStorage.removeItem('theme-mode')
    })

    // Reload to reset to system mode
    await page.reload({ waitUntil: 'networkidle' })
    await page.waitForTimeout(500)

    // Should be in system mode by default
    const themeToggle = page.locator('#themeToggle')
    await expect(themeToggle).toHaveAttribute('aria-checked', 'false')

    // Manual toggle should be hidden
    const manualToggle = page.locator('#manualThemeToggle')
    await expect(manualToggle).toHaveClass(/hidden/)
  })

  test('should have proper ARIA attributes', async ({ page }) => {
    await page.goto('http://localhost:3000')

    // Check system/manual toggle ARIA
    const themeToggle = page.locator('#themeToggle')
    await expect(themeToggle).toHaveAttribute('role', 'switch')
    await expect(themeToggle).toHaveAttribute('aria-checked')
    await expect(themeToggle).toHaveAttribute('title')

    // Switch to manual mode to test light/dark toggle
    await themeToggle.click()
    await page.waitForTimeout(500)

    // Check light/dark toggle ARIA
    const lightDarkToggle = page.locator('#lightDarkToggle')
    await expect(lightDarkToggle).toHaveAttribute('role', 'switch')
    await expect(lightDarkToggle).toHaveAttribute('aria-checked')
    await expect(lightDarkToggle).toHaveAttribute('title')
  })

  test('should support keyboard navigation', async ({ page }) => {
    await page.goto('http://localhost:3000')

    // Test that the fixed theme toggle is accessible
    const themeToggle = page.locator('#themeToggle')
    await expect(themeToggle).toBeVisible()
    await themeToggle.focus()
    await expect(themeToggle).toBeFocused()

    // Test keyboard activation with Enter
    await page.keyboard.press('Enter')
    await page.waitForTimeout(500)

    // Check if aria-checked attribute updated
    await expect(themeToggle).toHaveAttribute('aria-checked', 'true')

    // Manual toggle should now be accessible
    const lightDarkToggle = page.locator('#lightDarkToggle')

    // Try to access the light/dark toggle
    if (await lightDarkToggle.isVisible()) {
      await lightDarkToggle.focus()
      await expect(lightDarkToggle).toBeFocused()
    } else {
      // If not visible, test that it's still accessible programmatically
      await expect(lightDarkToggle).toBeAttached()
    }

    // Test keyboard activation with Space
    await page.keyboard.press(' ')
    await page.waitForTimeout(200)

    // Theme should have changed
    const html = page.locator('html')
    await expect(html).toHaveAttribute('data-theme', 'dark')
  })
})
