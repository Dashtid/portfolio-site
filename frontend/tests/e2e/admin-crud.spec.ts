import { test, expect, type Page, type Route } from '@playwright/test'

/**
 * E2E coverage for the admin CRUD round-trip: navigate to a managed
 * resource list, exercise the create / edit / delete handlers, and
 * verify the request payloads reach the backend (FRONTEND-TESTS-04).
 *
 * The backend is mocked at the Playwright request layer. The point is
 * NOT to test the backend (covered by pytest) — it's to confirm the
 * admin SPA wires up its forms, list, and delete-confirmation flow
 * correctly and that the requests it emits match what the backend
 * expects to receive.
 */

const ADMIN_USER = {
  id: 'admin-id-1',
  username: 'adminuser',
  email: 'admin@example.com',
  name: 'Admin User',
  avatar_url: 'https://example.com/admin.png',
  is_admin: true
}

const SEED_COMPANY = {
  id: 'company-1',
  name: 'Seed Company',
  title: 'Engineer',
  description: 'desc',
  location: 'SE',
  start_date: '2020-01-01',
  end_date: null,
  order_index: 1,
  logo_url: null,
  website: null,
  detailed_description: null,
  video_url: null,
  video_title: null,
  map_url: null,
  map_title: null,
  responsibilities: [],
  technologies: [],
  projects: [],
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z'
}

interface CompanyMockState {
  companies: Array<typeof SEED_COMPANY>
  posts: Array<unknown>
  puts: Array<{ id: string; body: unknown }>
  deletes: Array<string>
}

async function authedAsAdmin(page: Page) {
  await page.route('**/api/v1/auth/me', route =>
    route.fulfill({ status: 200, body: JSON.stringify(ADMIN_USER) })
  )
  await page.route('**/api/v1/admin/sentry-panel', route =>
    route.fulfill({ status: 200, body: JSON.stringify({ enabled: false, issues_url: null }) })
  )
}

async function mockCompaniesEndpoints(page: Page, state: CompanyMockState) {
  await page.route('**/api/v1/companies/**', async (route: Route) => {
    const request = route.request()
    const method = request.method()
    const url = request.url()

    // GET /api/v1/companies (list)
    if (method === 'GET' && /\/companies\/?$/.test(url)) {
      return route.fulfill({ status: 200, body: JSON.stringify(state.companies) })
    }
    // POST /api/v1/companies (create)
    if (method === 'POST') {
      const body = request.postDataJSON()
      state.posts.push(body)
      const created = {
        ...SEED_COMPANY,
        ...(body as object),
        id: `company-${state.companies.length + 1}`
      }
      state.companies.push(created)
      return route.fulfill({ status: 201, body: JSON.stringify(created) })
    }
    // PUT /api/v1/companies/{id}
    if (method === 'PUT') {
      const id = url.split('/').pop() || ''
      const body = request.postDataJSON()
      state.puts.push({ id, body })
      const updated = state.companies.find(c => c.id === id) || SEED_COMPANY
      Object.assign(updated, body)
      return route.fulfill({ status: 200, body: JSON.stringify(updated) })
    }
    // DELETE /api/v1/companies/{id}
    if (method === 'DELETE') {
      const id = url.split('/').pop() || ''
      state.deletes.push(id)
      state.companies = state.companies.filter(c => c.id !== id)
      return route.fulfill({ status: 204, body: '' })
    }
    return route.continue()
  })
  // Routes the dashboard fans out to on mount — silence them.
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
}

test.describe('Admin CRUD round-trip (Companies, mocked backend)', () => {
  test('GET fans out on /admin/companies entry', async ({ page }) => {
    const state: CompanyMockState = {
      companies: [SEED_COMPANY],
      posts: [],
      puts: [],
      deletes: []
    }
    await authedAsAdmin(page)
    await mockCompaniesEndpoints(page, state)

    await page.goto('/admin/companies')
    await expect(page.locator('h2')).toContainText('Manage Companies')
    // Seed row is rendered.
    await expect(page.getByText('Seed Company')).toBeVisible()
  })

  test('POST is emitted when the operator submits the create form', async ({ page }) => {
    const state: CompanyMockState = {
      companies: [],
      posts: [],
      puts: [],
      deletes: []
    }
    await authedAsAdmin(page)
    await mockCompaniesEndpoints(page, state)

    await page.goto('/admin/companies')

    // Open the "add" modal. AdminCompanies uses an "Add Company" CTA.
    const addButton = page.getByRole('button', { name: /add company/i })
    await addButton.click()

    // Fill in the minimum-required fields.
    await page.locator('input#company-name').fill('New Inc')
    await page.locator('input#company-title').fill('CTO')
    await page.locator('textarea#company-description').fill('a description')
    await page.locator('input#company-location').fill('Stockholm')
    await page.locator('input#company-start-date').fill('2024-01-01')

    await page.getByRole('button', { name: /^add company$/i }).click()
    await expect.poll(() => state.posts.length).toBeGreaterThanOrEqual(1)

    const posted = state.posts[0] as Record<string, unknown>
    expect(posted.name).toBe('New Inc')
    expect(posted.title).toBe('CTO')
  })

  test('DELETE fires after the confirm dialog is accepted', async ({ page }) => {
    const state: CompanyMockState = {
      companies: [SEED_COMPANY],
      posts: [],
      puts: [],
      deletes: []
    }
    await authedAsAdmin(page)
    await mockCompaniesEndpoints(page, state)

    // Accept the confirm() popup the delete button triggers.
    page.on('dialog', dialog => dialog.accept())

    await page.goto('/admin/companies')

    // The delete button lives inside AdminCardActions for the seed row.
    const deleteButton = page.locator('.action-btn.delete').first()
    await deleteButton.click()

    await expect.poll(() => state.deletes.length).toBeGreaterThanOrEqual(1)
    expect(state.deletes[0]).toBe(SEED_COMPANY.id)
  })

  test('DELETE is NOT fired when the operator dismisses the confirm', async ({ page }) => {
    const state: CompanyMockState = {
      companies: [SEED_COMPANY],
      posts: [],
      puts: [],
      deletes: []
    }
    await authedAsAdmin(page)
    await mockCompaniesEndpoints(page, state)

    // Reject the confirm() to simulate the operator changing their mind.
    page.on('dialog', dialog => dialog.dismiss())

    await page.goto('/admin/companies')
    const deleteButton = page.locator('.action-btn.delete').first()
    await deleteButton.click()

    // Wait a beat; the request should NOT have fired.
    await page.waitForTimeout(150)
    expect(state.deletes.length).toBe(0)
  })
})
