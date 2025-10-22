import { test, expect } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'

test.describe('Accessibility (WCAG 2.1 AA)', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('homepage should not have automatically detectable accessibility issues', async ({ page }) => {
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze()

    expect(accessibilityScanResults.violations).toEqual([])
  })

  test('experience section has no accessibility violations', async ({ page }) => {
    // Navigate to experience section
    await page.locator('#experience').scrollIntoViewIfNeeded()
    await page.waitForTimeout(500)

    const accessibilityScanResults = await new AxeBuilder({ page })
      .include('#experience')
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze()

    expect(accessibilityScanResults.violations).toEqual([])
  })

  test('education section has no accessibility violations', async ({ page }) => {
    await page.locator('#education').scrollIntoViewIfNeeded()
    await page.waitForTimeout(500)

    const accessibilityScanResults = await new AxeBuilder({ page })
      .include('#education')
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze()

    expect(accessibilityScanResults.violations).toEqual([])
  })

  test('navigation has no accessibility violations', async ({ page }) => {
    const accessibilityScanResults = await new AxeBuilder({ page })
      .include('nav')
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze()

    expect(accessibilityScanResults.violations).toEqual([])
  })

  test('keyboard navigation works for all interactive elements', async ({ page }) => {
    // Tab through page
    await page.keyboard.press('Tab')
    let focusedElement = await page.evaluate(() => document.activeElement.tagName)
    expect(focusedElement).toBeTruthy()

    // Should be able to tab to nav links
    let tabCount = 0
    let navLinkFocused = false

    while (tabCount < 20 && !navLinkFocused) {
      await page.keyboard.press('Tab')
      tabCount++

      const className = await page.evaluate(() => document.activeElement.className)
      if (className && className.includes('nav-link')) {
        navLinkFocused = true
      }
    }

    expect(navLinkFocused).toBeTruthy()
  })

  test('all images have alt text', async ({ page }) => {
    const imagesWithoutAlt = await page.locator('img:not([alt])').count()
    expect(imagesWithoutAlt).toBe(0)

    // Check that alt text is not empty
    const images = await page.locator('img').all()
    for (const img of images) {
      const alt = await img.getAttribute('alt')
      expect(alt).toBeTruthy() // Alt should not be null or empty
    }
  })

  test('links have discernible text', async ({ page }) => {
    const links = await page.locator('a').all()

    for (const link of links) {
      const text = await link.textContent()
      const ariaLabel = await link.getAttribute('aria-label')

      // Link should have either text content or aria-label
      expect(text || ariaLabel).toBeTruthy()
    }
  })

  test('form elements have associated labels', async ({ page }) => {
    // Check if there are any inputs without labels
    const unlabeledInputs = await page.locator('input:not([type="hidden"]):not([aria-label])').count()

    // All visible inputs should have labels or aria-label
    const inputs = await page.locator('input:not([type="hidden"])').all()
    for (const input of inputs) {
      const ariaLabel = await input.getAttribute('aria-label')
      const id = await input.getAttribute('id')

      let hasLabel = false
      if (ariaLabel) {
        hasLabel = true
      } else if (id) {
        const label = await page.locator(`label[for="${id}"]`).count()
        if (label > 0) hasLabel = true
      }

      // Input should have label or be inside a label
      const parentLabel = await input.evaluate(el => el.closest('label') !== null)
      expect(hasLabel || parentLabel).toBeTruthy()
    }
  })

  test('headings are in hierarchical order', async ({ page }) => {
    const headings = await page.locator('h1, h2, h3, h4, h5, h6').all()

    let previousLevel = 0
    for (const heading of headings) {
      const tagName = await heading.evaluate(el => el.tagName)
      const currentLevel = parseInt(tagName.charAt(1))

      // Heading level should not skip (e.g., h1 -> h3)
      if (previousLevel > 0) {
        expect(currentLevel - previousLevel).toBeLessThanOrEqual(1)
      }

      previousLevel = currentLevel
    }
  })

  test('color contrast meets WCAG AA standards', async ({ page }) => {
    const contrastResults = await new AxeBuilder({ page })
      .withTags(['wcag2aa'])
      .include('body')
      .analyze()

    const contrastViolations = contrastResults.violations.filter(v =>
      v.id === 'color-contrast'
    )

    expect(contrastViolations).toEqual([])
  })

  test('theme toggle is accessible', async ({ page }) => {
    const themeToggle = page.locator('.theme-toggle')

    // Should be focusable
    await themeToggle.focus()
    const isFocused = await themeToggle.evaluate(el => el === document.activeElement)
    expect(isFocused).toBeTruthy()

    // Should be operable with keyboard
    await page.keyboard.press('Enter')
    await page.waitForTimeout(300)

    // Theme should have changed
    const theme = await page.evaluate(() =>
      document.documentElement.getAttribute('data-theme')
    )
    expect(theme).toBeTruthy()
  })

  test('back to top button is accessible', async ({ page }) => {
    // Scroll down to make button appear
    await page.evaluate(() => window.scrollTo(0, 1000))
    await page.waitForTimeout(500)

    const backToTop = page.locator('.back-to-top')
    await expect(backToTop).toBeVisible()

    // Should have accessible name
    const ariaLabel = await backToTop.getAttribute('aria-label')
    expect(ariaLabel).toBeTruthy()

    // Should be keyboard accessible
    await backToTop.focus()
    await page.keyboard.press('Enter')
    await page.waitForTimeout(1000)

    // Should scroll to top
    const scrollY = await page.evaluate(() => window.scrollY)
    expect(scrollY).toBeLessThan(100)
  })

  test('no ARIA misuse', async ({ page }) => {
    const ariaResults = await new AxeBuilder({ page })
      .withTags(['best-practice', 'wcag2a', 'wcag2aa'])
      .analyze()

    // Filter for ARIA-related violations
    const ariaViolations = ariaResults.violations.filter(v =>
      v.id.includes('aria')
    )

    expect(ariaViolations).toEqual([])
  })

  test('language is defined', async ({ page }) => {
    const lang = await page.locator('html').getAttribute('lang')
    expect(lang).toBe('en')
  })

  test('page has a main landmark', async ({ page }) => {
    const main = await page.locator('main, [role="main"]').count()
    expect(main).toBeGreaterThan(0)
  })

  test('skip navigation link is present', async ({ page }) => {
    // Check for skip link (may be visually hidden)
    const skipLink = await page.locator('a[href^="#"]').first()

    // Tab to it (it should be first focusable element)
    await page.keyboard.press('Tab')

    const focused = await page.evaluate(() => {
      const el = document.activeElement
      return {
        tag: el.tagName,
        href: el.getAttribute('href')
      }
    })

    // First tab should focus a link to an anchor
    expect(focused.tag).toBe('A')
    expect(focused.href).toMatch(/^#/)
  })
})
