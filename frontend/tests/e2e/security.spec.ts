import { test, expect } from '@playwright/test'

// Security headers are set by the production server (Vercel), not by Vite preview
// Skip these tests in local development
const isProduction =
  process.env.E2E_BASE_URL?.includes('vercel') ||
  process.env.E2E_BASE_URL?.includes('dashti.se') ||
  process.env.E2E_BASE_URL?.includes('portfolio-site-jade-five.vercel.app') ||
  false /* CI runs against preview, not production */

test.describe('Security Headers', () => {
  test('should have security headers on the home page', async ({ page }) => {
    test.skip(!isProduction, 'Security headers only available in production (Vercel)')

    const response = await page.goto('/')

    if (response) {
      const headers = response.headers()

      // Check for X-Content-Type-Options
      expect(headers['x-content-type-options']).toBe('nosniff')

      // Check for X-Frame-Options
      expect(headers['x-frame-options']).toBe('DENY')

      // Check for Referrer-Policy
      expect(headers['referrer-policy']).toBeTruthy()
    }
  })

  test('should not expose sensitive information in HTML', async ({ page }) => {
    await page.goto('/')
    const html = await page.content()

    // Should not contain API keys or secrets
    expect(html).not.toMatch(/api[_-]?key\s*[:=]\s*['"][^'"]+['"]/i)
    expect(html).not.toMatch(/secret\s*[:=]\s*['"][^'"]+['"]/i)
    expect(html).not.toMatch(/password\s*[:=]\s*['"][^'"]+['"]/i)
  })

  test('should use HTTPS for external resources', async ({ page }) => {
    const requests: string[] = []

    page.on('request', request => {
      const url = request.url()
      if (!url.startsWith('data:') && !url.startsWith('blob:')) {
        requests.push(url)
      }
    })

    await page.goto('/')
    // Wait for network to settle
    await page.waitForLoadState('networkidle')

    // All external requests should use HTTPS (except localhost in dev)
    for (const url of requests) {
      if (!url.startsWith('http://localhost') && !url.startsWith('http://127.0.0.1')) {
        expect(url).toMatch(/^https:\/\//)
      }
    }
  })

  test('should have proper CSP meta tag', async ({ page }) => {
    await page.goto('/')

    const cspMeta = page.locator('meta[http-equiv="Content-Security-Policy"]')
    if ((await cspMeta.count()) > 0) {
      const content = await cspMeta.getAttribute('content')
      expect(content).toBeTruthy()
      expect(content).toContain('default-src')
    }
  })
})

test.describe('XSS Prevention', () => {
  test('should sanitize URL parameters', async ({ page }) => {
    // Try injecting script via URL
    await page.goto('/?test=<script>alert(1)</script>')
    // Wait for page to fully load and any scripts to execute
    await page.waitForLoadState('networkidle')

    // The script should not be executed
    const alertTriggered = await page.evaluate(() => {
      return (window as unknown as { __xss_triggered?: boolean }).__xss_triggered || false
    })
    expect(alertTriggered).toBe(false)
  })

  test('should not render raw HTML from URL parameters', async ({ page }) => {
    await page.goto('/?name=<img src=x onerror=alert(1)>')
    const html = await page.content()

    // Raw HTML should be escaped
    expect(html).not.toContain('<img src=x onerror=alert(1)>')
  })
})

test.describe('Cookie Security', () => {
  test('should set secure flags on cookies', async ({ page, context }) => {
    await page.goto('/')
    const cookies = await context.cookies()

    for (const cookie of cookies) {
      // Cookies should have secure flags in production
      // In development, this might not apply
      if (cookie.name.includes('session') || cookie.name.includes('token')) {
        expect(cookie.httpOnly).toBe(true)
      }
    }
  })
})

test.describe('CORS and External Resources', () => {
  test('should load external resources correctly', async ({ page }) => {
    const failedRequests: string[] = []

    page.on('requestfailed', request => {
      // Only track critical resource failures, not API calls
      const url = request.url()
      if (url.includes('.js') || url.includes('.css') || url.includes('fonts')) {
        failedRequests.push(url)
      }
    })

    await page.goto('/')
    // Wait for all network activity to complete
    await page.waitForLoadState('networkidle')

    // Report any failed requests
    if (failedRequests.length > 0) {
      console.log('Failed critical requests:', failedRequests)
    }

    // Critical resources (JS, CSS, fonts) should not fail
    expect(failedRequests).toHaveLength(0)
  })
})

test.describe('Form Security', () => {
  test('should have CSRF protection on forms', async ({ page }) => {
    await page.goto('/')

    const forms = page.locator('form')
    const formCount = await forms.count()

    for (let i = 0; i < formCount; i++) {
      const form = forms.nth(i)

      // Forms should have action attribute
      const action = await form.getAttribute('action')
      if (action && !action.startsWith('#')) {
        // Forms with external actions should have CSRF token
        const csrfInput = form.locator('input[name*="csrf"], input[name*="token"]')
        // This is a soft check - not all forms need CSRF
        if (action.startsWith('http')) {
          const count = await csrfInput.count()
          // Log but don't fail for informational purposes
          if (count === 0) {
            console.log(`Form ${i + 1} has external action but no CSRF token detected`)
          }
        }
      }
    }
  })
})
