import { defineConfig, devices } from '@playwright/test'

/**
 * Playwright E2E test configuration
 * @see https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  testDir: './tests/e2e',
  outputDir: '.test-results',
  snapshotDir: './tests/e2e/__snapshots__',
  fullyParallel: false, // Disable to prevent auth state conflicts between tests
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ['html', { outputFolder: '.playwright-report', open: 'never' }],
    ['list'],
    ...(process.env.CI ? [['github' as const]] : [])
  ],
  expect: {
    toHaveScreenshot: {
      // Absolute cap, not a ratio. maxDiffPixelRatio 0.01 scaled with image
      // area: on a full-page shot "1%" was ~100k pixels, enough to hide an
      // entire changed nav row — which is exactly what happened, three
      // times (footer/CV link, projects/offensive-toolkit card, hero/OSS
      // nav item each stayed stale for ~6 weeks while the suite passed).
      // The environment is pinned (one Docker image, one browser build), so
      // legitimate variance is anti-aliasing at the 3-5 px scale; 100 px
      // absorbs that on every shot size while any real content change —
      // a word of text is hundreds of pixels — fails loudly.
      maxDiffPixels: 100,
      threshold: 0.2,
      animations: 'disabled',
      // Neutralize per-commit content (the footer build stamp) in every
      // screenshot comparison — see the css file for why visibility.
      stylePath: './tests/e2e/screenshot.css'
    }
  },
  use: {
    baseURL: process.env.E2E_BASE_URL || 'http://localhost:4173',
    // No e2e spec exercises the service worker; leaving it active made
    // tests race its NetworkFirst timeouts and offline fallback under CI
    // load.
    serviceWorkers: 'block',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'on-first-retry'
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] }
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] }
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] }
    },
    {
      name: 'mobile-chrome',
      use: { ...devices['Pixel 5'] }
    },
    {
      name: 'mobile-safari',
      use: { ...devices['iPhone 12'] }
    }
  ],

  webServer: {
    // In CI the `frontend-quality` job builds and uploads `dist/` as an
    // artifact; the e2e job downloads it before invoking playwright, so we
    // skip the build here. Locally there's no upstream build, so chain it.
    command: process.env.CI ? 'npm run preview' : 'npm run build:ssg && npm run preview',
    url: 'http://localhost:4173',
    reuseExistingServer: !process.env.CI,
    timeout: 180 * 1000,
    stdout: 'pipe',
    stderr: 'pipe'
  }
})
