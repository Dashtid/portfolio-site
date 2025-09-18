import { test, expect } from '@playwright/test'

test.describe('Theme System', () => {
  test('should toggle between light and dark themes', async ({ page }) => {
    await page.goto('/')

    // Check initial state (should be light theme by default)
    const html = page.locator('html')
    await expect(html).not.toHaveAttribute('data-theme', 'dark')

    // Find and click theme toggle
    const themeToggle = page.locator('#themeToggle')
    await expect(themeToggle).toBeVisible()

    // Click to switch to dark theme
    await themeToggle.click()
    await expect(html).toHaveAttribute('data-theme', 'dark')
    await expect(themeToggle).toContainText('Light')

    // Click to switch back to light theme
    await themeToggle.click()
    await expect(html).not.toHaveAttribute('data-theme', 'dark')
    await expect(themeToggle).toContainText('Dark')
  })

  test('should persist theme preference', async ({ page }) => {
    await page.goto('/')

    // Switch to dark theme
    await page.locator('#themeToggle').click()
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark')

    // Reload page and check if theme persists
    await page.reload()
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark')
    await expect(page.locator('#themeToggle')).toContainText('Light')
  })

  test('should respect system theme preference', async ({ page, context }) => {
    // Set system to prefer dark mode
    await page.emulateMedia({ colorScheme: 'dark' })
    await page.goto('/')

    // Should start with dark theme
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark')

    // Switch to light theme preference
    await page.emulateMedia({ colorScheme: 'light' })
    await page.reload()

    // Should start with light theme
    await expect(page.locator('html')).not.toHaveAttribute('data-theme', 'dark')
  })

  test('should have proper ARIA attributes', async ({ page }) => {
    await page.goto('/')

    const themeToggle = page.locator('#themeToggle')
    await expect(themeToggle).toHaveAttribute(
      'aria-label',
      /Switch to .* theme/
    )
    await expect(themeToggle).toHaveAttribute('aria-pressed', 'false')

    // Click and check ARIA updates
    await themeToggle.click()
    await expect(themeToggle).toHaveAttribute(
      'aria-label',
      /Switch to .* theme/
    )
  })
})
