module.exports = {
  extends: ['standard'],
  env: {
    browser: true,
    es2022: true,
    serviceworker: true
  },
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'script'
  },
  rules: {
    // Code quality
    'no-console': 'warn',
    'prefer-const': 'error',
    'no-var': 'error',
    'no-unused-vars': ['error', { args: 'none' }],

    // Accessibility
    'no-global-assign': 'error',
    'no-implicit-globals': 'error',

    // Security
    'no-eval': 'error',
    'no-implied-eval': 'error',
    'no-script-url': 'error',

    // Modern JavaScript
    'prefer-arrow-callback': 'error',
    'prefer-template': 'error',
    'object-shorthand': 'error',

    // Spacing and formatting (handled by Prettier mostly)
    'space-before-function-paren': ['error', 'always'],
    'comma-dangle': ['error', 'never']
  },
  overrides: [
    {
      files: ['site/static/js/**/*.js'],
      rules: {
        // Allow browser globals
        'no-undef': 'error'
      },
      globals: {
        // Browser globals
        window: 'readonly',
        document: 'readonly',
        navigator: 'readonly',
        localStorage: 'readonly',
        sessionStorage: 'readonly',
        console: 'readonly',
        setTimeout: 'readonly',
        setInterval: 'readonly',
        clearTimeout: 'readonly',
        clearInterval: 'readonly',
        requestAnimationFrame: 'readonly',
        fetch: 'readonly',

        // Service Worker globals
        self: 'readonly',
        caches: 'readonly',
        clients: 'readonly',

        // Third-party globals
        createRepoWidget: 'readonly',
        bootstrap: 'readonly'
      }
    },
    {
      files: ['scripts/**/*.js', 'tests/**/*.js'],
      env: {
        node: true
      }
    }
  ]
}
