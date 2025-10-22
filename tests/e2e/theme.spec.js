import { test, expect } from '@playwright/test'

test.describe('Theme Switching', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
    // Clear localStorage to start fresh
    await page.evaluate(() => localStorage.clear())
  })

  test('theme toggle button is visible', async ({ page }) => {
    const themeToggle = page.locator('.theme-toggle')
    await expect(themeToggle).toBeVisible()
  })

  test('toggles theme from light to dark', async ({ page }) => {
    // Click theme toggle
    const themeToggle = page.locator('.theme-toggle')
    await themeToggle.click()
    await page.waitForTimeout(300)

    // HTML should have data-theme="dark" attribute
    const theme = await page.evaluate(() =>
      document.documentElement.getAttribute('data-theme')
    )
    expect(theme).toBe('dark')
  })

  test('toggles theme from dark back to light', async ({ page }) => {
    const themeToggle = page.locator('.theme-toggle')

    // Toggle to dark
    await themeToggle.click()
    await page.waitForTimeout(300)

    // Toggle back to light
    await themeToggle.click()
    await page.waitForTimeout(300)

    const theme = await page.evaluate(() =>
      document.documentElement.getAttribute('data-theme')
    )
    expect(theme).toBe('light')
  })

  test('persists theme preference in localStorage', async ({ page }) => {
    const themeToggle = page.locator('.theme-toggle')

    // Toggle to dark
    await themeToggle.click()
    await page.waitForTimeout(300)

    // Check localStorage
    const storedTheme = await page.evaluate(() =>
      localStorage.getItem('portfolio-theme')
    )
    expect(storedTheme).toBeTruthy()
  })

  test('theme persists across page reloads', async ({ page }) => {
    const themeToggle = page.locator('.theme-toggle')

    // Toggle to dark
    await themeToggle.click()
    await page.waitForTimeout(300)

    // Reload page
    await page.reload()
    await page.waitForTimeout(500)

    // Theme should still be dark
    const theme = await page.evaluate(() =>
      document.documentElement.getAttribute('data-theme')
    )
    expect(theme).toBe('dark')
  })

  test('theme toggle icon changes', async ({ page }) => {
    const themeToggle = page.locator('.theme-toggle')

    // Get initial SVG
    const initialSvg = await themeToggle.locator('svg').innerHTML()

    // Toggle theme
    await themeToggle.click()
    await page.waitForTimeout(500) // Wait for transition

    // SVG should have changed
    const newSvg = await themeToggle.locator('svg').innerHTML()
    expect(newSvg).not.toBe(initialSvg)
  })

  test('dark theme applies to all sections', async ({ page }) => {
    const themeToggle = page.locator('.theme-toggle')

    // Toggle to dark
    await themeToggle.click()
    await page.waitForTimeout(300)

    // Check that body/html has dark theme attribute
    const htmlTheme = await page.evaluate(() =>
      document.documentElement.getAttribute('data-theme')
    )
    expect(htmlTheme).toBe('dark')

    // Verify CSS variables are applied (check computed style)
    const bgColor = await page.evaluate(() =>
      window.getComputedStyle(document.documentElement).getPropertyValue('--bg-primary')
    )
    // Should have dark mode value
    expect(bgColor).toBeTruthy()
  })

  test('theme toggle is keyboard accessible', async ({ page }) => {
    const themeToggle = page.locator('.theme-toggle')

    // Focus the button
    await themeToggle.focus()

    // Press Enter
    await page.keyboard.press('Enter')
    await page.waitForTimeout(300)

    // Theme should toggle
    const theme = await page.evaluate(() =>
      document.documentElement.getAttribute('data-theme')
    )
    expect(theme).toBe('dark')
  })

  test('theme toggle has proper ARIA attributes', async ({ page }) => {
    const themeToggle = page.locator('.theme-toggle')

    // Should have aria-label
    const ariaLabel = await themeToggle.getAttribute('aria-label')
    expect(ariaLabel).toBeTruthy()
    expect(ariaLabel).toMatch(/theme|mode|dark|light/i)

    // Should have title
    const title = await themeToggle.getAttribute('title')
    expect(title).toBeTruthy()
  })

  test('respects prefers-color-scheme on first visit', async ({ page, colorScheme }) => {
    // This test checks if system preference is respected
    // Note: colorScheme comes from the browser/device settings

    await page.goto('/')
    await page.waitForTimeout(500)

    const theme = await page.evaluate(() =>
      document.documentElement.getAttribute('data-theme')
    )

    // Theme should be set (either light or dark based on system)
    expect(theme).toBeTruthy()
  })
})
