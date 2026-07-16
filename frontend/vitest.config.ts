import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [
    vue({
      template: {
        // @vitejs/plugin-vue v6 defaults includeAbsolute:true when no dev server is
        // running (Vitest context). This transforms /images/foo.svg into an ES import,
        // which Vite resolves to file:///images/foo.svg — an invalid file URL on Windows
        // (no drive letter). Public-directory assets are string literals; don't import them.
        transformAssetUrls: { includeAbsolute: false }
      }
    })
  ],
  define: {
    'import.meta.env.VITE_ERROR_TRACKING_ENABLED': JSON.stringify('true'),
    'import.meta.env.VITE_METRICS_ENABLED': JSON.stringify('true'),
    'import.meta.env.VITE_API_URL': JSON.stringify('http://localhost:8001')
  },
  test: {
    globals: true,
    environment: 'happy-dom',
    setupFiles: ['./tests/setup.ts'],
    env: {
      VITE_ERROR_TRACKING_ENABLED: 'true',
      VITE_METRICS_ENABLED: 'true',
      VITE_API_URL: 'http://localhost:8001'
    },
    coverage: {
      provider: 'v8',
      reportsDirectory: '.coverage',
      // 'json-summary' is REQUIRED: ci-cd.yml's coverage-comment step reads
      // .coverage/coverage-summary.json and ENOENTs the whole job without it
      // (D3-CI-01 — every frontend-touching PR failed on this).
      reporter: ['text', 'json', 'json-summary', 'html', 'lcov'],
      // Report even when thresholds fail, so the PR comment shows WHAT
      // dropped instead of the job dying silent.
      reportOnFailure: true,
      exclude: [
        'node_modules/',
        'tests/',
        '*.config.js',
        '*.config.ts',
        'dist/',
        '.eslintrc.cjs',
        'sentry.production.js',
        '**/sentry.production.js',
        'sentry.production.*',
        'src/composables/useAnimations.ts'
      ],
      // Single source of truth for coverage floors (D3-TEST-01): the curated
      // thresholds below previously lived in vite.config.ts's test block,
      // which Vitest never reads when vitest.config.ts exists — leaving these
      // floors ~10pp below reality. Re-derived 2026-07-16 from actuals
      // (80.6/73.9/81.3/82.1) minus ~2pp headroom.
      // Stricter per-glob gates for `api/` and `stores/` — the user-visible
      // data plumbing where regressions are most expensive.
      thresholds: {
        statements: 78,
        branches: 71,
        functions: 79,
        lines: 80,
        // Recalibrated 2026-07-16 from actuals 82.5/70(funcs)/84.2 — the
        // May-2026 gates (90/85/92) described a fileset Sprint 6 deleted
        // half of, and being dead config nobody noticed the drift.
        'src/api/**': {
          statements: 80,
          branches: 60,
          functions: 68,
          lines: 82
        },
        'src/stores/**': {
          statements: 83,
          branches: 67,
          functions: 90,
          lines: 84
        }
      }
    },
    include: ['tests/unit/**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}'],
    exclude: ['node_modules', 'dist', '.idea', '.git', '.cache', 'tests/e2e'],
    testTimeout: 10000,
    hookTimeout: 10000
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  }
})
