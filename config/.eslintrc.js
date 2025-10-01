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
    'no-undef': 'error',
    'no-unreachable': 'error',
    'no-duplicate-imports': 'error',

    // Accessibility
    'no-global-assign': 'error',
    'no-implicit-globals': 'error',

    // Security
    'no-eval': 'error',
    'no-implied-eval': 'error',
    'no-script-url': 'error',
    'no-new-func': 'error',

    // Modern JavaScript
    'prefer-arrow-callback': 'error',
    'prefer-template': 'error',
    'object-shorthand': 'error',
    'prefer-destructuring': ['error', { object: true, array: false }],

    // Error prevention
    'array-callback-return': 'error',
    'consistent-return': 'error',
    'no-constant-condition': 'error',
    'no-dupe-args': 'error',
    'no-dupe-keys': 'error',
    'no-duplicate-case': 'error',
    'no-empty': 'error',
    'no-extra-boolean-cast': 'error',
    'no-extra-semi': 'error',
    'no-func-assign': 'error',
    'no-invalid-regexp': 'error',
    'no-irregular-whitespace': 'error',
    'no-obj-calls': 'error',
    'no-sparse-arrays': 'error',
    'no-unexpected-multiline': 'error',
    'valid-typeof': 'error',

    // Best practices
    curly: 'error',
    'dot-notation': 'error',
    eqeqeq: ['error', 'always'],
    'no-alert': 'warn',
    'no-caller': 'error',
    'no-else-return': 'error',
    'no-empty-function': 'warn',
    'no-eq-null': 'error',
    'no-floating-decimal': 'error',
    'no-lone-blocks': 'error',
    'no-multi-spaces': 'error',
    'no-new': 'error',
    'no-new-wrappers': 'error',
    'no-redeclare': 'error',
    'no-self-assign': 'error',
    'no-self-compare': 'error',
    'no-sequences': 'error',
    'no-throw-literal': 'error',
    'no-unused-expressions': 'error',
    'no-useless-call': 'error',
    'no-useless-concat': 'error',
    'no-useless-return': 'error',
    radix: 'error',
    yoda: 'error',

    // Spacing and formatting (handled by Prettier mostly)
    'space-before-function-paren': 'off', // Disabled to avoid conflict with Prettier
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
        node: true,
        jest: true
      },
      parserOptions: {
        ecmaVersion: 'latest',
        sourceType: 'module'
      }
    }
  ]
}
