module.exports = {
  ci: {
    collect: {
      // URLs to test (for local development server)
      url: ['http://localhost:3000/'],
      startServerCommand: 'npm run dev',
      startServerReadyPattern: 'Server running at',
      startServerReadyTimeout: 30000,
      numberOfRuns: 3,
      settings: {
        // Run in headless mode for CI
        chromeFlags: '--no-sandbox --headless',
        // Preset configurations
        preset: 'desktop',
        // Throttling settings for consistent results
        throttling: {
          rttMs: 40,
          throughputKbps: 10240,
          cpuSlowdownMultiplier: 1,
          requestLatencyMs: 0,
          downloadThroughputKbps: 0,
          uploadThroughputKbps: 0
        },
        // Skip certain audits that may be flaky in CI
        skipAudits: ['uses-http2', 'canonical']
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
        'categories:performance': ['error', { minScore: 0.85 }],
        'categories:accessibility': ['error', { minScore: 0.95 }],
        'categories:best-practices': ['error', { minScore: 0.9 }],
        'categories:seo': ['error', { minScore: 0.95 }],
        'categories:pwa': ['warn', { minScore: 0.8 }],

        // Core Web Vitals
        'first-contentful-paint': ['warn', { maxNumericValue: 2000 }],
        'largest-contentful-paint': ['error', { maxNumericValue: 2500 }],
        'cumulative-layout-shift': ['error', { maxNumericValue: 0.1 }],
        'speed-index': ['warn', { maxNumericValue: 3000 }],

        // Additional performance metrics
        'total-blocking-time': ['warn', { maxNumericValue: 300 }],
        interactive: ['warn', { maxNumericValue: 3000 }],

        // Security and best practices
        'uses-https': 'error',
        vulnerabilities: 'error',
        'no-document-write': 'error',
        'external-anchors-use-rel-noopener': 'error',

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
