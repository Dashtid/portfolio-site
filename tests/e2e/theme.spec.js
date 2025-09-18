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
    await page.reload({ waitUntil: 'networkidle' })
    await page.waitForTimeout(500) // Give theme time to initialize
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark')
    await expect(page.locator('#themeToggle')).toContainText('Light')
  })

  test('should respect system theme preference', async ({ page, context }) => {
    // Clear any existing theme preference and cookies
    await page.goto('/')
    await page.evaluate(() => {
      localStorage.clear()
      sessionStorage.clear()
    })

    // Set system to prefer dark mode BEFORE navigation
    await page.emulateMedia({ colorScheme: 'dark' })
    await page.goto('/', { waitUntil: 'networkidle' })

    // Wait for theme initialization with multiple checks
    await page.waitForFunction(
      () => document.documentElement.hasAttribute('data-theme'),
      { timeout: 5000 }
    )
    await page.waitForTimeout(1500) // Extra time for Firefox

    // Should start with dark theme
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark')

    // Clear storage again and switch to light theme preference
    await page.evaluate(() => {
      localStorage.clear()
      sessionStorage.clear()
    })
    await page.emulateMedia({ colorScheme: 'light' })
    await page.goto('/', { waitUntil: 'networkidle' })

    // Wait for theme initialization again
    await page.waitForFunction(
      () => document.documentElement.hasAttribute('data-theme'),
      { timeout: 5000 }
    )
    await page.waitForTimeout(1500) // Extra time for Firefox

    // Should start with light theme (or no dark theme attribute)
    const htmlElement = page.locator('html')
    const hasDataTheme = await htmlElement.getAttribute('data-theme')
    expect(hasDataTheme).not.toBe('dark')
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
