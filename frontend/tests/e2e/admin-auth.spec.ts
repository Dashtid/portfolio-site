import { test, expect } from '@playwright/test'

/**
 * E2E coverage for the admin login -> dashboard -> refresh -> logout
 * happy path (FRONTEND-TESTS-03).
 *
 * The backend API is mocked at the Playwright request layer — these
 * specs validate the frontend's auth flow, NOT the real OAuth
 * round-trip (which can't run in CI without a fake GitHub identity
 * provider). The backend integration is covered by the pytest suite
 * in `tests/test_auth.py`.
 */

const ADMIN_USER = {
  id: 'admin-id-1',
  username: 'adminuser',
  email: 'admin@example.com',
  name: 'Admin User',
  avatar_url: 'https://example.com/admin.png',
  is_admin: true
}

const PUBLIC_DATA = {
  companies: [],
  projects: [],
  skills: [],
  education: [],
  documents: []
}

test.describe('Admin auth flow (mocked backend)', () => {
  test('redirects an unauthenticated user from /admin to /admin/login', async ({ page }) => {
    // /auth/me returns 401 -> the auth store treats the user as not
    // logged in, the router guard bounces them to /admin/login.
    await page.route('**/api/v1/auth/me', route =>
      route.fulfill({ status: 401, body: JSON.stringify({ detail: 'Not authenticated' }) })
    )
    await page.goto('/admin')
    await expect(page).toHaveURL(/\/admin\/login$/)
  })

  test('authenticated user landing on /admin/login bounces to /admin', async ({ page }) => {
    await page.route('**/api/v1/auth/me', route =>
      route.fulfill({ status: 200, body: JSON.stringify(ADMIN_USER) })
    )
    // Dashboard tries to load portfolio data on mount — keep the mocks
    // from triggering a real network failure that would mask the test.
    await mockPortfolioReads(page)
    await page.goto('/admin/login')
    await expect(page).toHaveURL(/\/admin\/?$/)
  })

  test('authenticated user can reach /admin and sees the dashboard', async ({ page }) => {
    await page.route('**/api/v1/auth/me', route =>
      route.fulfill({ status: 200, body: JSON.stringify(ADMIN_USER) })
    )
    await mockPortfolioReads(page)
    await page.goto('/admin')
    await expect(page).toHaveURL(/\/admin\/?$/)
    await expect(page.locator('.dashboard-title')).toContainText('Portfolio Admin')
    await expect(page.locator('.user-name')).toContainText(ADMIN_USER.name)
  })

  test('logout calls /auth/logout and redirects to /admin/login', async ({ page }) => {
    await page.route('**/api/v1/auth/me', route =>
      route.fulfill({ status: 200, body: JSON.stringify(ADMIN_USER) })
    )
    await mockPortfolioReads(page)

    let logoutCalled = false
    await page.route('**/api/v1/auth/logout', route => {
      logoutCalled = true
      return route.fulfill({ status: 200, body: JSON.stringify({ message: 'Logged out' }) })
    })

    await page.goto('/admin')
    await expect(page.locator('.logout-button')).toBeVisible()

    // After logout, /auth/me must return 401 so the next route resolution
    // sees the unauthenticated state.
    await page.unroute('**/api/v1/auth/me')
    await page.route('**/api/v1/auth/me', route =>
      route.fulfill({ status: 401, body: JSON.stringify({ detail: 'Not authenticated' }) })
    )

    await page.locator('.logout-button').click()
    await expect(page).toHaveURL(/\/admin\/login$/)
    expect(logoutCalled).toBe(true)
  })

  test('refresh path: a 401 on a protected call triggers /auth/refresh', async ({ page }) => {
    /**
     * The auth interceptor in `api/client.ts` catches a 401 on any API
     * call and tries `/auth/refresh` before propagating. We exercise
     * that branch by serving 401 to a portfolio fetch the dashboard
     * makes on mount; the test passes if `/auth/refresh` is hit.
     */
    await page.route('**/api/v1/auth/me', route =>
      route.fulfill({ status: 200, body: JSON.stringify(ADMIN_USER) })
    )

    let refreshCalls = 0
    await page.route('**/api/v1/auth/refresh', route => {
      refreshCalls += 1
      return route.fulfill({ status: 200, body: JSON.stringify({ refreshed: true }) })
    })

    let companiesCalls = 0
    await page.route('**/api/v1/companies**', route => {
      companiesCalls += 1
      // First call returns 401 to force a refresh; subsequent calls succeed.
      if (companiesCalls === 1) {
        return route.fulfill({ status: 401, body: JSON.stringify({ detail: 'expired' }) })
      }
      return route.fulfill({ status: 200, body: JSON.stringify(PUBLIC_DATA.companies) })
    })
    await page.route('**/api/v1/projects**', route =>
      route.fulfill({ status: 200, body: JSON.stringify(PUBLIC_DATA.projects) })
    )
    await page.route('**/api/v1/skills**', route =>
      route.fulfill({ status: 200, body: JSON.stringify(PUBLIC_DATA.skills) })
    )
    await page.route('**/api/v1/education**', route =>
      route.fulfill({ status: 200, body: JSON.stringify(PUBLIC_DATA.education) })
    )
    await page.route('**/api/v1/documents**', route =>
      route.fulfill({ status: 200, body: JSON.stringify(PUBLIC_DATA.documents) })
    )
    await page.route('**/api/v1/admin/sentry-panel', route =>
      route.fulfill({ status: 200, body: JSON.stringify({ enabled: false, issues_url: null }) })
    )

    await page.goto('/admin')
    // Wait for the interceptor to attempt the refresh + retry.
    await page.waitForLoadState('networkidle')
    expect(refreshCalls).toBeGreaterThanOrEqual(1)
  })
})

/**
 * Helper: stub every portfolio-data endpoint the dashboard loads on
 * mount so a single test only has to redefine the ones it cares about.
 */
async function mockPortfolioReads(page: import('@playwright/test').Page) {
  await page.route('**/api/v1/companies**', route =>
    route.fulfill({ status: 200, body: JSON.stringify([]) })
  )
  await page.route('**/api/v1/projects**', route =>
    route.fulfill({ status: 200, body: JSON.stringify([]) })
  )
  await page.route('**/api/v1/skills**', route =>
    route.fulfill({ status: 200, body: JSON.stringify([]) })
  )
  await page.route('**/api/v1/education**', route =>
    route.fulfill({ status: 200, body: JSON.stringify([]) })
  )
  await page.route('**/api/v1/documents**', route =>
    route.fulfill({ status: 200, body: JSON.stringify([]) })
  )
  await page.route('**/api/v1/admin/sentry-panel', route =>
    route.fulfill({ status: 200, body: JSON.stringify({ enabled: false, issues_url: null }) })
  )
}
