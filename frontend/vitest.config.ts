import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
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
      reporter: ['text', 'json', 'html', 'lcov'],
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
      thresholds: {
        lines: 74,
        functions: 74,
        branches: 64,
        statements: 74
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
