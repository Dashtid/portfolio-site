import js from '@eslint/js'
import tseslint from '@typescript-eslint/eslint-plugin'
import tsparser from '@typescript-eslint/parser'
import vuePlugin from 'eslint-plugin-vue'
import vueParser from 'vue-eslint-parser'
import prettierConfig from 'eslint-config-prettier'
import prettierPlugin from 'eslint-plugin-prettier'

export default [
  // Global ignores
  {
    ignores: [
      'dist/**',
      'node_modules/**',
      'coverage/**',
      '*.config.js',
      '*.config.ts',
      '.vscode/**',
      'public/**'
    ]
  },

  // Base JavaScript/TypeScript configuration
  {
    files: ['**/*.{js,mjs,cjs,ts,vue}'],
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      globals: {
        // Browser globals
        window: 'readonly',
        document: 'readonly',
        navigator: 'readonly',
        console: 'readonly',
        localStorage: 'readonly',
        sessionStorage: 'readonly',
        fetch: 'readonly',
        setTimeout: 'readonly',
        clearTimeout: 'readonly',
        setInterval: 'readonly',
        clearInterval: 'readonly',
        IntersectionObserver: 'readonly',
        IntersectionObserverEntry: 'readonly',
        IntersectionObserverInit: 'readonly',
        ResizeObserver: 'readonly',
        MutationObserver: 'readonly',
        requestAnimationFrame: 'readonly',
        cancelAnimationFrame: 'readonly',
        // Node globals
        process: 'readonly',
        __dirname: 'readonly',
        __filename: 'readonly',
        // Vitest globals
        describe: 'readonly',
        it: 'readonly',
        expect: 'readonly',
        beforeEach: 'readonly',
        afterEach: 'readonly',
        vi: 'readonly'
      }
    },
    plugins: {
      prettier: prettierPlugin
    },
    rules: {
      ...js.configs.recommended.rules,
      'prettier/prettier': 'error',
      'no-console': process.env.NODE_ENV === 'production' ? 'warn' : 'off',
      'no-debugger': process.env.NODE_ENV === 'production' ? 'error' : 'off',
      'no-unused-vars': 'warn',
      'prefer-const': 'error'
    }
  },

  // TypeScript configuration
  {
    files: ['**/*.ts', '**/*.tsx'],
    languageOptions: {
      parser: tsparser,
      parserOptions: {
        ecmaVersion: 'latest',
        sourceType: 'module',
        project: './tsconfig.json'
      }
    },
    plugins: {
      '@typescript-eslint': tseslint
    },
    rules: {
      ...tseslint.configs.recommended.rules,
      '@typescript-eslint/no-unused-vars': [
        'warn',
        {
          argsIgnorePattern: '^_',
          varsIgnorePattern: '^_'
        }
      ],
      '@typescript-eslint/no-explicit-any': 'warn',
      '@typescript-eslint/explicit-function-return-type': 'off',
      '@typescript-eslint/explicit-module-boundary-types': 'off',
      '@typescript-eslint/no-non-null-assertion': 'warn',
      'no-unused-vars': 'off' // Turn off base rule as it can report incorrect errors
    }
  },

  // Vue configuration
  ...vuePlugin.configs['flat/recommended'],
  {
    files: ['**/*.vue'],
    languageOptions: {
      parser: vueParser,
      parserOptions: {
        ecmaVersion: 'latest',
        sourceType: 'module',
        parser: tsparser,
        extraFileExtensions: ['.vue']
      }
    },
    rules: {
      'vue/multi-word-component-names': 'off',
      'vue/require-default-prop': 'off',
      'vue/no-v-html': 'warn',
      'vue/component-name-in-template-casing': ['error', 'PascalCase'],
      'vue/html-self-closing': [
        'error',
        {
          html: {
            void: 'always',
            normal: 'never',
            component: 'always'
          }
        }
      ]
    }
  },

  // Prettier config (must be last to override other configs)
  prettierConfig
]
