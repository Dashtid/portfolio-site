/**
 * Jest Configuration for Portfolio Site
 * Comprehensive testing setup for unit and integration tests
 */

module.exports = {
  // Test environment
  testEnvironment: 'jsdom',

  // Root directories
  rootDir: '..',
  roots: [
    '<rootDir>/tests/unit',
    '<rootDir>/site/static/js',
    '<rootDir>/scripts',
    '<rootDir>/build'
  ],

  // Test file patterns
  testMatch: [
    '<rootDir>/tests/unit/**/*.test.js',
    '<rootDir>/tests/integration/**/*.test.js'
  ],

  // Setup files
  setupFilesAfterEnv: ['<rootDir>/tests/unit/setup.js'],

  // Module paths
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/site/static/js/$1',
    '^@scripts/(.*)$': '<rootDir>/scripts/$1',
    '^@build/(.*)$': '<rootDir>/build/$1',
    '^@tests/(.*)$': '<rootDir>/tests/$1'
  },

  // Coverage configuration
  collectCoverageFrom: [
    'site/static/js/**/*.js',
    'scripts/**/*.js',
    'build/**/*.js',
    '!**/node_modules/**',
    '!**/tests/**',
    '!**/*.config.js'
  ],

  coverageDirectory: 'coverage',
  coverageReporters: ['text', 'lcov', 'html', 'json-summary'],

  coverageThreshold: {
    global: {
      branches: 70,
      functions: 80,
      lines: 85,
      statements: 85
    }
  },

  // Transform configuration
  transform: {
    '^.+\\.js$': 'babel-jest'
  },

  // Mock configuration
  moduleFileExtensions: ['js', 'json'],

  // Test timeout
  testTimeout: 10000,

  // Verbose output
  verbose: true,

  // Clear mocks between tests
  clearMocks: true,
  restoreMocks: true,

  // Global test setup
  globals: {
    window: {},
    document: {},
    localStorage: {},
    sessionStorage: {}
  }
}
