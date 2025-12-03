import { test, expect } from '@playwright/test'

/**
 * E2E tests for Admin CRUD Operations
 *
 * Note: These tests require authentication to work properly.
 * For full E2E testing in production:
 * 1. Set up test environment with pre-authenticated state
 * 2. Use test fixtures to inject auth tokens
 * 3. Or use a dedicated test user with GitHub OAuth
 *
 * For now, these tests verify the UI elements and flow
 * without actual backend operations.
 */

// Helper to set up authentication state
const setupAuthState = async (page) => {
  // In a real setup, you would inject valid tokens here
  // This is a placeholder for the authentication setup
  await page.evaluate(() => {
    const mockUser = {
      id: 'test-user-id',
      username: 'testuser',
      name: 'Test User',
      avatar_url: 'https://avatars.githubusercontent.com/u/1234567?v=4',
    }
    localStorage.setItem('accessToken', 'test-access-token')
    localStorage.setItem('refreshToken', 'test-refresh-token')
    // Note: In real tests, these would be valid tokens
  })
}

test.describe('Admin Dashboard UI', () => {
  test.beforeEach(async ({ page }) => {
    // For UI-only tests, we can test the login page
    await page.goto('/admin/login')
  })

  test('login page has proper structure', async ({ page }) => {
    await expect(page.locator('.admin-login')).toBeVisible()
    await expect(page.locator('.login-container')).toBeVisible()
    await expect(page.locator('.login-card')).toBeVisible()
  })

  test('login page is responsive on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })
    await expect(page.locator('.login-card')).toBeVisible()

    // Card should still be usable on mobile
    const card = page.locator('.login-card')
    const box = await card.boundingBox()
    expect(box?.width).toBeLessThanOrEqual(375)
  })
})

test.describe('Admin Companies Page UI', () => {
  test.skip('displays companies management page structure', async ({ page }) => {
    // This test requires authentication
    await page.goto('/admin/companies')

    await expect(page.locator('.admin-companies')).toBeVisible()
    await expect(page.locator('.page-header')).toBeVisible()
    await expect(page.locator('.page-title')).toContainText('Experience')
    await expect(page.locator('.add-button')).toBeVisible()
  })

  test.skip('can open add company modal', async ({ page }) => {
    await page.goto('/admin/companies')

    // Click add button
    await page.locator('.add-button').click()

    // Modal should appear
    await expect(page.locator('.modal-overlay')).toBeVisible()
    await expect(page.locator('.modal-content')).toBeVisible()
    await expect(page.locator('.modal-title')).toContainText('Add')
  })

  test.skip('add company form has all required fields', async ({ page }) => {
    await page.goto('/admin/companies')
    await page.locator('.add-button').click()

    // Check all form fields exist
    await expect(page.locator('#name')).toBeVisible()
    await expect(page.locator('#title')).toBeVisible()
    await expect(page.locator('#start_date')).toBeVisible()
    await expect(page.locator('#end_date')).toBeVisible()
    await expect(page.locator('#location')).toBeVisible()
    await expect(page.locator('#description')).toBeVisible()
    await expect(page.locator('#technologies')).toBeVisible()
    await expect(page.locator('#order_index')).toBeVisible()
  })

  test.skip('can close add company modal', async ({ page }) => {
    await page.goto('/admin/companies')
    await page.locator('.add-button').click()

    // Click cancel button
    await page.locator('.btn-cancel').click()

    // Modal should close
    await expect(page.locator('.modal-overlay')).not.toBeVisible()
  })

  test.skip('can close modal by clicking overlay', async ({ page }) => {
    await page.goto('/admin/companies')
    await page.locator('.add-button').click()

    // Click overlay background
    await page.locator('.modal-overlay').click({ position: { x: 10, y: 10 } })

    // Modal should close
    await expect(page.locator('.modal-overlay')).not.toBeVisible()
  })
})

test.describe('Admin Skills Page UI', () => {
  test.skip('displays skills management page structure', async ({ page }) => {
    await page.goto('/admin/skills')

    // Check basic structure exists
    const hasSkillsPage = await page.locator('[class*="admin-skills"]').count() > 0
    const hasTitle = await page.locator('h2').count() > 0

    expect(hasSkillsPage || hasTitle).toBeTruthy()
  })
})

test.describe('Admin Projects Page UI', () => {
  test.skip('displays projects management page', async ({ page }) => {
    await page.goto('/admin/projects')

    await expect(page.locator('.admin-projects')).toBeVisible()
    await expect(page.locator('h2')).toContainText('Manage Projects')
  })
})

test.describe('Admin Navigation', () => {
  test.skip('dashboard has navigation links', async ({ page }) => {
    await page.goto('/admin')

    // Check navigation exists
    const nav = page.locator('.admin-nav')
    await expect(nav).toBeVisible()

    // Check all nav links
    await expect(nav.locator('a[href="/admin"]')).toBeVisible()
    await expect(nav.locator('a[href="/admin/companies"]')).toBeVisible()
    await expect(nav.locator('a[href="/admin/skills"]')).toBeVisible()
    await expect(nav.locator('a[href="/admin/projects"]')).toBeVisible()
  })

  test.skip('navigation links work correctly', async ({ page }) => {
    await page.goto('/admin')

    // Click companies link
    await page.locator('.admin-nav a[href="/admin/companies"]').click()
    await expect(page).toHaveURL(/\/admin\/companies/)

    // Click skills link
    await page.locator('.admin-nav a[href="/admin/skills"]').click()
    await expect(page).toHaveURL(/\/admin\/skills/)

    // Click projects link
    await page.locator('.admin-nav a[href="/admin/projects"]').click()
    await expect(page).toHaveURL(/\/admin\/projects/)

    // Click dashboard link
    await page.locator('.admin-nav a[href="/admin"]').click()
    await expect(page).toHaveURL(/\/admin$/)
  })
})

test.describe('Admin Dashboard Stats', () => {
  test.skip('displays statistics cards', async ({ page }) => {
    await page.goto('/admin')

    const statsGrid = page.locator('.stats-grid')
    await expect(statsGrid).toBeVisible()

    // Should have 4 stat cards
    const statCards = page.locator('.stat-card')
    await expect(statCards).toHaveCount(4)
  })

  test.skip('statistics show correct labels', async ({ page }) => {
    await page.goto('/admin')

    const labels = page.locator('.stat-label')
    const labelTexts = await labels.allTextContents()

    expect(labelTexts).toContain('COMPANIES')
    expect(labelTexts).toContain('SKILLS')
    expect(labelTexts).toContain('PROJECTS')
    expect(labelTexts).toContain('FEATURED')
  })

  test.skip('quick actions section exists', async ({ page }) => {
    await page.goto('/admin')

    await expect(page.locator('.quick-actions')).toBeVisible()
    await expect(page.locator('.subsection-title')).toContainText('Quick Actions')

    // Should have action buttons
    const actionButtons = page.locator('.action-button')
    await expect(actionButtons).toHaveCount(4)
  })

  test.skip('view site action opens in new tab', async ({ page }) => {
    await page.goto('/admin')

    const viewSiteLink = page.locator('.action-button[href="/"]')
    const target = await viewSiteLink.getAttribute('target')
    expect(target).toBe('_blank')
  })
})

test.describe('Admin CRUD Form Validation', () => {
  test.skip('company form requires name field', async ({ page }) => {
    await page.goto('/admin/companies')
    await page.locator('.add-button').click()

    // Try to submit without name
    await page.locator('#title').fill('Developer')
    await page.locator('#start_date').fill('2023-01-01')

    // Submit form
    await page.locator('.btn-save').click()

    // Form should not submit (HTML5 validation)
    // Modal should still be visible
    await expect(page.locator('.modal-overlay')).toBeVisible()
  })

  test.skip('company form requires title field', async ({ page }) => {
    await page.goto('/admin/companies')
    await page.locator('.add-button').click()

    // Fill only name
    await page.locator('#name').fill('Test Company')
    await page.locator('#start_date').fill('2023-01-01')

    // Submit form
    await page.locator('.btn-save').click()

    // Form should not submit (HTML5 validation)
    await expect(page.locator('.modal-overlay')).toBeVisible()
  })

  test.skip('company form requires start date field', async ({ page }) => {
    await page.goto('/admin/companies')
    await page.locator('.add-button').click()

    // Fill name and title
    await page.locator('#name').fill('Test Company')
    await page.locator('#title').fill('Developer')

    // Submit without date
    await page.locator('.btn-save').click()

    // Form should not submit (HTML5 validation)
    await expect(page.locator('.modal-overlay')).toBeVisible()
  })
})

test.describe('Admin User Info Display', () => {
  test.skip('displays user information in header', async ({ page }) => {
    await page.goto('/admin')

    const userInfo = page.locator('.user-info')
    await expect(userInfo).toBeVisible()

    // Should show user avatar
    await expect(page.locator('.user-avatar')).toBeVisible()

    // Should show user name
    await expect(page.locator('.user-name')).toBeVisible()
  })

  test.skip('displays logout button', async ({ page }) => {
    await page.goto('/admin')

    const logoutButton = page.locator('.logout-button')
    await expect(logoutButton).toBeVisible()
    await expect(logoutButton).toContainText('Sign Out')
  })
})

test.describe('Admin Responsive Design', () => {
  test.skip('dashboard is usable on tablet', async ({ page }) => {
    await page.setViewportSize({ width: 768, height: 1024 })
    await page.goto('/admin')

    // Navigation should still be visible
    await expect(page.locator('.admin-nav')).toBeVisible()

    // Stats grid should be visible
    await expect(page.locator('.stats-grid')).toBeVisible()
  })

  test.skip('dashboard is usable on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })
    await page.goto('/admin')

    // Content should be accessible
    await expect(page.locator('.admin-dashboard')).toBeVisible()
  })

  test.skip('companies modal is usable on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })
    await page.goto('/admin/companies')

    await page.locator('.add-button').click()

    // Modal should be visible and not overflow
    const modal = page.locator('.modal-content')
    await expect(modal).toBeVisible()

    const box = await modal.boundingBox()
    expect(box?.width).toBeLessThanOrEqual(375)
  })
})
