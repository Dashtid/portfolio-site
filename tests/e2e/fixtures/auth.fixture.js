/**
 * Authentication Fixtures for E2E Testing
 *
 * This file provides utilities for setting up authenticated state in E2E tests.
 * For production use:
 * 1. Replace mock tokens with valid test tokens
 * 2. Or use environment variables for test credentials
 * 3. Or set up a mock OAuth server
 */

/**
 * Mock user data for testing
 */
export const mockUser = {
  id: 'test-user-id',
  username: 'testuser',
  name: 'Test User',
  email: 'testuser@example.com',
  avatar_url: 'https://avatars.githubusercontent.com/u/1234567?v=4',
  github_id: '1234567',
}

/**
 * Set up authenticated state in localStorage
 * @param {import('@playwright/test').Page} page - Playwright page
 * @param {object} options - Configuration options
 */
export const setupAuthentication = async (page, options = {}) => {
  const {
    accessToken = 'test-access-token',
    refreshToken = 'test-refresh-token',
    user = mockUser,
  } = options

  // Navigate to a page first to set localStorage
  await page.goto('/admin/login')

  // Set authentication tokens in localStorage
  await page.evaluate(
    ({ accessToken, refreshToken }) => {
      localStorage.setItem('accessToken', accessToken)
      localStorage.setItem('refreshToken', refreshToken)
    },
    { accessToken, refreshToken }
  )

  return { accessToken, refreshToken, user }
}

/**
 * Clear authentication state
 * @param {import('@playwright/test').Page} page - Playwright page
 */
export const clearAuthentication = async (page) => {
  await page.evaluate(() => {
    localStorage.removeItem('accessToken')
    localStorage.removeItem('refreshToken')
  })
}

/**
 * Check if user is authenticated
 * @param {import('@playwright/test').Page} page - Playwright page
 * @returns {Promise<boolean>}
 */
export const isAuthenticated = async (page) => {
  return await page.evaluate(() => {
    return !!localStorage.getItem('accessToken')
  })
}

/**
 * Create an authenticated page context
 * This is useful for tests that require authentication
 *
 * Usage:
 * ```js
 * import { test } from '@playwright/test'
 * import { withAuth } from './fixtures/auth.fixture.js'
 *
 * test('authenticated test', async ({ page }) => {
 *   await withAuth(page, async (authenticatedPage) => {
 *     await authenticatedPage.goto('/admin')
 *     // ... test authenticated functionality
 *   })
 * })
 * ```
 */
export const withAuth = async (page, callback) => {
  await setupAuthentication(page)
  try {
    await callback(page)
  } finally {
    await clearAuthentication(page)
  }
}

/**
 * Environment-based configuration for E2E tests
 * Set these environment variables for different test environments:
 * - E2E_ACCESS_TOKEN: Valid access token for testing
 * - E2E_REFRESH_TOKEN: Valid refresh token for testing
 * - E2E_TEST_USER_ID: Test user GitHub ID
 */
export const getTestConfig = () => {
  return {
    accessToken: process.env.E2E_ACCESS_TOKEN || 'test-access-token',
    refreshToken: process.env.E2E_REFRESH_TOKEN || 'test-refresh-token',
    testUserId: process.env.E2E_TEST_USER_ID || 'test-user-id',
    backendUrl: process.env.E2E_BACKEND_URL || 'http://localhost:8000',
    frontendUrl: process.env.E2E_FRONTEND_URL || 'http://localhost:3000',
  }
}

/**
 * Wait for authentication to complete
 * Useful after OAuth callback
 * @param {import('@playwright/test').Page} page
 * @param {number} timeout
 */
export const waitForAuth = async (page, timeout = 5000) => {
  await page.waitForFunction(
    () => !!localStorage.getItem('accessToken'),
    { timeout }
  )
}

/**
 * Intercept and mock authentication API calls
 * Useful for testing without a real backend
 * @param {import('@playwright/test').Page} page
 */
export const mockAuthAPI = async (page) => {
  // Mock the OAuth callback endpoint
  await page.route('**/api/v1/auth/github/callback**', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        access_token: 'mocked-access-token',
        refresh_token: 'mocked-refresh-token',
        token_type: 'bearer',
        user: mockUser,
      }),
    })
  })

  // Mock the current user endpoint
  await page.route('**/api/v1/auth/me', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(mockUser),
    })
  })

  // Mock the token refresh endpoint
  await page.route('**/api/v1/auth/refresh', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        access_token: 'refreshed-access-token',
        token_type: 'bearer',
      }),
    })
  })
}

/**
 * Intercept and mock portfolio API calls
 * @param {import('@playwright/test').Page} page
 * @param {object} data - Mock data to return
 */
export const mockPortfolioAPI = async (page, data = {}) => {
  const {
    companies = [],
    skills = [],
    projects = [],
    education = [],
  } = data

  // Mock companies endpoint
  await page.route('**/api/v1/companies**', async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(companies),
      })
    } else {
      await route.continue()
    }
  })

  // Mock skills endpoint
  await page.route('**/api/v1/skills**', async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(skills),
      })
    } else {
      await route.continue()
    }
  })

  // Mock projects endpoint
  await page.route('**/api/v1/projects**', async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(projects),
      })
    } else {
      await route.continue()
    }
  })

  // Mock education endpoint
  await page.route('**/api/v1/education**', async (route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(education),
      })
    } else {
      await route.continue()
    }
  })
}
