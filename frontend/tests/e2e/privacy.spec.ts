import { test, expect } from '@playwright/test'

/**
 * /privacy is a prerendered page that every footer links to. Its opt-out
 * switch exists only once the client has mounted, so these checks run in a
 * real browser against the built site: the served HTML, the footer link, and
 * the switch with and without a browser signal.
 */

const OPT_OUT_KEY = 'portfolio-analytics-opt-out'

test.describe('Privacy page', () => {
  test('answers 200 with its heading in the served HTML', async ({ request }) => {
    const response = await request.get('/privacy')
    expect(response.status()).toBe(200)
    expect(await response.text()).toMatch(/<h1[^>]*>\s*Privacy\s*<\/h1>/)
  })

  test('is reached from the footer link on the home page', async ({ page }) => {
    await page.goto('/')
    await page.locator('footer').getByRole('link', { name: 'Privacy', exact: true }).click()
    await page.waitForURL(url => new URL(url).pathname === '/privacy')
    await expect(page.locator('h1')).toHaveText('Privacy')
  })

  test('names every storage key a visit leaves in the browser', async ({ page }) => {
    await page.goto('/')
    await page.locator('footer').getByRole('link', { name: 'Privacy', exact: true }).click()
    await page.waitForURL(url => new URL(url).pathname === '/privacy')
    await expect(page.locator('h1')).toHaveText('Privacy')
    const keys = await page.evaluate(() => ({
      local: Object.keys(localStorage).sort(),
      session: Object.keys(sessionStorage).sort()
    }))
    // Local storage: the colour theme and the opt-out. Session storage: Vue
    // Router's saved scroll positions, and main.ts's reload time, which it
    // writes just before an automatic reload onto a new deploy, after a
    // failed chunk load or when a new service worker takes over.
    const named = {
      local: ['portfolio-theme', OPT_OUT_KEY],
      session: ['vue-router:scroll', 'chunk-reload-at']
    }
    expect(keys.local.filter(key => !named.local.includes(key))).toEqual([])
    expect(keys.session.filter(key => !named.session.includes(key))).toEqual([])
    expect(keys.session).toContain('vue-router:scroll')
    const items = await page.locator('main li').allTextContents()
    expect(items.map(item => item.trim())).toContain(
      'where you had scrolled to on each page, in session storage, so that going back returns you there;'
    )
  })

  test('switches counting off and on again, and keeps the choice', async ({ page }) => {
    // The reload hydrates the page over a stored choice the prerender never
    // saw; Vue logs this line when the first client render differs.
    const mismatches: string[] = []
    page.on('console', message => {
      if (message.text().includes('Hydration completed but contains mismatches')) {
        mismatches.push(message.text())
      }
    })
    await page.goto('/privacy')
    await page.getByRole('button', { name: 'Stop counting my visits' }).click()
    await expect(
      page.getByText(
        'Visits from this browser are not counted. The choice is saved in this browser only.'
      )
    ).toBeVisible()
    expect(await page.evaluate(key => localStorage.getItem(key), OPT_OUT_KEY)).toBe('1')

    await page.reload()
    await page.getByRole('button', { name: 'Count my visits again' }).click()
    await expect(
      page.getByText('Visits from this browser are counted, as described above.')
    ).toBeVisible()
    expect(await page.evaluate(key => localStorage.getItem(key), OPT_OUT_KEY)).toBeNull()
    expect(mismatches).toEqual([])
  })

  test('shows the Global Privacy Control signal instead of the switch', async ({ page }) => {
    await page.addInitScript(() => {
      Object.defineProperty(Navigator.prototype, 'globalPrivacyControl', { get: () => true })
    })
    await page.goto('/privacy')
    await expect(
      page.getByText(
        'Your browser sends Global Privacy Control or Do Not Track, so this site counts nothing from it.'
      )
    ).toBeVisible()
    await expect(page.locator('main button')).toHaveCount(0)
  })
})
