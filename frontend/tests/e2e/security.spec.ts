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

  // The former 'proper CSP meta tag' test was deleted (D3-CI-03): the
  // site sets CSP via Vercel headers, no meta tag exists, and the test
  // wrapped all assertions in `if (count > 0)` — it asserted nothing.
  // The post-deploy smoke step in ci-cd.yml owns CSP verification.
})

// D3-CI-03: these tests previously passed vacuously — the script payload
// called alert(1) but the assertion checked a window.__xss_triggered
// sentinel nothing ever set, and the raw-HTML check grepped page.content()
// for an unquoted literal that DOM re-serialization would never emit even
// when injected. Payloads now set the sentinel themselves and the DOM is
// queried structurally, so execution/injection actually fails the test.
test.describe('XSS Prevention', () => {
  test('should not execute scripts injected via URL parameters', async ({ page }) => {
    let dialogOpened = false
    page.on('dialog', async dialog => {
      dialogOpened = true
      await dialog.dismiss()
    })

    // Payload sets the exact sentinel the assertion reads — if this ever
    // executes, the test fails.
    await page.goto('/?test=<script>window.__xss_triggered=true</script>')
    await page.waitForLoadState('networkidle')

    const sentinelSet = await page.evaluate(() => {
      return (window as unknown as { __xss_triggered?: boolean }).__xss_triggered === true
    })
    expect(sentinelSet).toBe(false)
    expect(dialogOpened).toBe(false)
  })

  test('should not render injected HTML elements from URL parameters', async ({ page }) => {
    let dialogOpened = false
    page.on('dialog', async dialog => {
      dialogOpened = true
      await dialog.dismiss()
    })

    await page.goto('/?name=<img id=xss-probe src=x onerror=window.__xss_triggered=true>')
    await page.waitForLoadState('networkidle')

    // Structural check: the element must not exist in the DOM at all —
    // immune to the attribute-quoting that defeated the old string grep.
    await expect(page.locator('#xss-probe')).toHaveCount(0)

    const sentinelSet = await page.evaluate(() => {
      return (window as unknown as { __xss_triggered?: boolean }).__xss_triggered === true
    })
    expect(sentinelSet).toBe(false)
    expect(dialogOpened).toBe(false)
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

// The former 'Form Security' CSRF describe was deleted (D3-CI-03): it
// contained zero expect() calls — its only output was a console.log — so
// it could never fail. CSRF protection is a backend contract (OAuth state
// + SameSite cookies) covered by backend tests, not something a public
// SSG page with no cross-origin forms can meaningfully assert.
