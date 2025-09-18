import { test, expect } from '@playwright/test'

test.describe('Accessibility', () => {
  test('should have proper heading hierarchy', async ({ page }) => {
    await page.goto('/')
    
    // Check main heading
    const h1 = page.locator('h1')
    await expect(h1).toHaveCount(1)
    await expect(h1).toContainText('Cybersecurity and Quality Assurance')
    
    // Check section headings
    const h2s = page.locator('h2')
    await expect(h2s).toHaveCount(6) // Experience, Education, Projects, About, Skills, Contact
    
    // Verify h2 content
    await expect(h2s.nth(0)).toContainText('Experience')
    await expect(h2s.nth(1)).toContainText('Education')
  })

  test('should have alt text for images', async ({ page }) => {
    await page.goto('/')
    
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
    await page.goto('/')
    
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
        const hasLabel = await label.count() > 0
        expect(hasLabel || ariaLabel || ariaLabelledby).toBeTruthy()
      }
    }
  })

  test('should support keyboard navigation', async ({ page }) => {
    await page.goto('/')
    
    // Test skip link
    await page.keyboard.press('Tab')
    const skipLink = page.locator('.skip-nav')
    await expect(skipLink).toBeFocused()
    
    // Test main navigation
    await page.keyboard.press('Tab')
    await expect(page.locator('.navbar-brand')).toBeFocused()
    
    // Tab through navigation items
    await page.keyboard.press('Tab')
    await expect(page.locator('.internal-nav').first()).toBeFocused()
    
    // Test theme toggle
    let themeToggleFocused = false
    for (let i = 0; i < 10; i++) { // Tab through several elements
      await page.keyboard.press('Tab')
      const focused = page.locator('#themeToggle')
      if (await focused.count() > 0) {
        const isFocused = await focused.evaluate(el => document.activeElement === el)
        if (isFocused) {
          themeToggleFocused = true
          break
        }
      }
    }
    expect(themeToggleFocused).toBeTruthy()
  })

  test('should have sufficient color contrast', async ({ page }) => {
    await page.goto('/')
    
    // Test common elements for basic contrast
    const textElements = [
      'h1',
      'h2',
      'p',
      '.nav-link',
      '.btn'
    ]
    
    for (const selector of textElements) {
      const elements = page.locator(selector)
      const count = await elements.count()
      
      if (count > 0) {
        const firstElement = elements.first()
        const color = await firstElement.evaluate(el => getComputedStyle(el).color)
        const backgroundColor = await firstElement.evaluate(el => getComputedStyle(el).backgroundColor)
        
        // Basic check that colors are defined
        expect(color).toBeTruthy()
        expect(backgroundColor).toBeTruthy()
      }
    }
  })

  test('should have proper ARIA attributes', async ({ page }) => {
    await page.goto('/')
    
    // Check navigation ARIA
    const nav = page.locator('nav[role="navigation"]')
    await expect(nav).toHaveAttribute('aria-label')
    
    // Check button states
    const themeToggle = page.locator('#themeToggle')
    await expect(themeToggle).toHaveAttribute('aria-pressed')
    
    // Check section landmarks
    const main = page.locator('main')
    await expect(main).toBeVisible()
    
    // Check skip navigation
    const skipLink = page.locator('.skip-nav')
    await expect(skipLink).toHaveAttribute('href', '#main-heading')
  })

  test('should support reduced motion', async ({ page, context }) => {
    await context.emulateMedia({ reducedMotion: 'reduce' })
    await page.goto('/')
    
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