module.exports = {
  ci: {
    collect: {
      // URLs to test (assumes server is already running)
      url: ['http://localhost:3000/'],
      numberOfRuns: process.env.CI ? 3 : 1, // Reduce runs locally for faster testing
      settings: {
        // Run in headless mode for CI, more permissive for local dev
        chromeFlags: process.env.CI
          ? '--no-sandbox --headless --disable-dev-shm-usage --disable-extensions'
          : '--headless',
        // Preset configurations
        preset: 'desktop',
        // More lenient throttling for CI stability
        throttling: {
          rttMs: 40,
          throughputKbps: 10240,
          cpuSlowdownMultiplier: 1,
          requestLatencyMs: 0,
          downloadThroughputKbps: 0,
          uploadThroughputKbps: 0
        },
        // Skip audits that may be flaky in CI or cause NaN values
        skipAudits: [
          'uses-http2',
          'canonical',
          'unsized-images', // Can cause issues with external images
          'preload-lcp-image' // Can be inconsistent with lazy loading
        ],
        // Additional settings for stability
        maxWaitForLoad: 45000,
        maxWaitForFcp: 15000,
        pauseAfterLoadMs: 1000,
        // Output path for better debugging
        output: ['html', 'json']
      }
    },
    upload: {
      // Only upload if token is available
      target: 'temporary-public-storage'
      // Alternative: upload to GitHub if token is available
      // target: 'lhci',
      // serverBaseUrl: 'https://your-lhci-server.com',
      // token: process.env.LHCI_GITHUB_APP_TOKEN
    },
    assert: {
      // Performance thresholds
      assertions: {
        'categories:performance': ['warn', { minScore: 0.8 }], // Lowered for external widgets
        'categories:accessibility': ['error', { minScore: 0.95 }],
        'categories:best-practices': ['warn', { minScore: 0.8 }], // External widgets impact
        'categories:seo': ['warn', { minScore: 0.9 }],
        'categories:pwa': ['warn', { minScore: 0.8 }],

        // Core Web Vitals - more lenient for CI stability
        'first-contentful-paint': ['warn', { maxNumericValue: 2500 }],
        'largest-contentful-paint': ['warn', { maxNumericValue: 3000 }], // Increased for external content
        'cumulative-layout-shift': ['warn', { maxNumericValue: 0.15 }],
        'speed-index': ['warn', { maxNumericValue: 3500 }],

        // Additional performance metrics
        'total-blocking-time': ['warn', { maxNumericValue: 300 }],
        interactive: ['warn', { maxNumericValue: 3000 }],

        // Security and best practices (removed obsolete audits)
        'no-document-write': 'error',

        // SEO essentials
        'document-title': 'error',
        'meta-description': 'error',
        'html-has-lang': 'error',
        'meta-viewport': 'error',

        // Accessibility essentials
        'color-contrast': 'error',
        'image-alt': 'error',
        label: 'error',
        'link-name': 'error',
        'button-name': 'error'
      }
    }
  }
}
