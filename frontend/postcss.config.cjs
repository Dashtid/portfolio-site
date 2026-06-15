/**
 * PostCSS configuration — FRONTEND-PERF-01.
 *
 * Strips unused Bootstrap selectors from the final bundle (production
 * build only; dev still ships the full sheet so devtools shows every
 * Bootstrap class). Q6 decision was "drop unused utilities only, no
 * SCSS rewrite", so this keeps the existing
 * `import 'bootstrap/dist/css/bootstrap.min.css'` and prunes the output.
 *
 * Measured impact on a clean build (2026-06-11):
 *   vendor CSS  230,850 -> 83,271 bytes (-64%)
 *   index CSS    75,363 -> 66,066 bytes (-12%)
 *
 * The safelist preserves selectors that are referenced dynamically (Vue
 * `:class` bindings constructed from variables, Bootstrap's own
 * runtime-toggled classes like `.show` / `.collapsing` / `.fade` /
 * `.active`, and the focus/hover pseudo-state suffixes Bootstrap relies
 * on). Adding to the safelist is cheaper than chasing a missing-style
 * bug in prod.
 */
const purgecss = require('@fullhuman/postcss-purgecss')

module.exports = {
  plugins: [
    process.env.NODE_ENV === 'production' &&
      purgecss({
        content: [
          './index.html',
          './src/**/*.vue',
          './src/**/*.ts',
          './src/**/*.js',
          './src/**/*.html'
        ],
        defaultExtractor: content => content.match(/[A-Za-z0-9_-]+/g) || [],
        // Don't purge CSS custom properties or @keyframes — Vue runtime
        // styles and theme variables depend on them. In PurgeCSS the
        // option name reads inverted: `variables: true` means "DO purge
        // unused variables", which was stripping --primary-500/600 (used
        // only inside gradient stops, where PurgeCSS's var() detector
        // missed them) and making the hero accent text render invisibly.
        variables: false,
        keyframes: true,
        safelist: {
          standard: [
            'show',
            'fade',
            'fade-out',
            'collapsing',
            'collapsed',
            'active',
            'disabled',
            'modal-open',
            'modal-backdrop',
            'd-none',
            'd-block',
            'visible',
            'invisible',
            'sr-only',
            'visually-hidden'
          ],
          deep: [
            /^modal/,
            /^tooltip/,
            /^popover/,
            /^carousel/,
            /^dropdown/,
            /^offcanvas/,
            /^toast/,
            /^alert-/,
            /^badge-/,
            /^btn-/,
            /^bg-/,
            /^text-/,
            /^border-/
          ],
          greedy: [/collapse/, /transitioning/]
        }
      })
  ].filter(Boolean)
}
