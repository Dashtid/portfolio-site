import js from '@eslint/js'
import globals from 'globals'
import tseslint from '@typescript-eslint/eslint-plugin'
import tsparser from '@typescript-eslint/parser'
import vuePlugin from 'eslint-plugin-vue'
import vueParser from 'vue-eslint-parser'
import prettierConfig from 'eslint-config-prettier'
import prettierPlugin from 'eslint-plugin-prettier'

// [!] This file's own blocks anchor their patterns and the tsconfig path to
// THIS directory (basePath, tsconfigRootDir), not to wherever eslint runs.
// `npm run lint` runs in frontend/, but the pre-commit eslint hook runs from
// the repository root with `--config frontend/eslint.config.js`, and eslint
// resolves a --config file's patterns against the working directory. Without
// the anchors that run cannot read ./tsconfig.json (a parse error on every
// .ts file), lints the *.config.ts files ignored below and loses the tests
// override. A new block with a path pattern needs `basePath: here` as well.
// The vue and prettier presets below need none: their only patterns are
// *.vue and **/*.vue.
const here = import.meta.dirname

export default [
  // Global ignores
  {
    basePath: here,
    ignores: [
      'dist/**',
      'node_modules/**',
      'coverage/**',
      '*.config.js',
      '*.config.ts',
      '.vscode/**',
      'public/**',
      // Playwright artifacts: the HTML report bundles minified vendor JS
      // (CodeMirror etc.) that floods lint with 700+ errors. CI lints
      // before any report exists, so without these ignores local `npm run
      // lint` and CI disagree.
      '.playwright-report/**',
      'playwright-report/**',
      'test-results/**',
      // Gitignored local tooling (image conversion etc.) — never in CI.
      'scripts/**'
    ]
  },

  // Base JavaScript/TypeScript configuration
  {
    basePath: here,
    files: ['**/*.{js,mjs,cjs,ts,vue}'],
    languageOptions: {
      ecmaVersion: 'latest',
      sourceType: 'module',
      // Use the `globals` package rather than a hand-maintained list — the
      // latter silently rotted (e.g. `getComputedStyle` was used in source
      // but never added, so `no-undef` fired and CI went red).
      globals: {
        ...globals.browser,
        ...globals.node,
        ...globals.vitest,
        // Compile-time constants from vite.config `define` (build stamp).
        __BUILD_COMMIT__: 'readonly',
        __BUILD_DATE__: 'readonly'
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
    basePath: here,
    files: ['**/*.ts', '**/*.tsx'],
    languageOptions: {
      parser: tsparser,
      parserOptions: {
        ecmaVersion: 'latest',
        sourceType: 'module',
        project: './tsconfig.json',
        tsconfigRootDir: here
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

  // Test files - allow non-null assertions (common pattern in tests)
  {
    basePath: here,
    files: ['tests/**/*.ts', 'tests/**/*.spec.ts'],
    rules: {
      '@typescript-eslint/no-non-null-assertion': 'off'
    }
  },

  // Vue configuration
  ...vuePlugin.configs['flat/recommended'],
  {
    basePath: here,
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
