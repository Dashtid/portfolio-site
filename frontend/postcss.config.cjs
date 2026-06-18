/**
 * PostCSS configuration.
 *
 * Phase 6 dropped @fullhuman/postcss-purgecss. Tailwind v4's JIT only emits
 * the utility classes it sees referenced in @source-scanned files, so PurgeCSS
 * was redundant for Tailwind output — and Bootstrap is no longer shipped to
 * the public site, so there is nothing left for PurgeCSS to prune.
 *
 * Two prior production incidents were caused by PurgeCSS misreading content:
 *   - `variables: true` (the option name is inverted in PurgeCSS — `true`
 *     means "DO purge") stripped --primary-500/600 used inside gradient
 *     stops, making hero accent text render invisibly.
 *   - The default extractor regex `/[A-Za-z0-9_-]+/g` did not match `:`,
 *     `[]`, or `/`, so Tailwind classes like `lg:flex` and `tracking-[0.25em]`
 *     were purged. The fix required a custom extractor.
 *
 * Removing PurgeCSS removes both failure modes. Bundle impact is negative
 * because the Bootstrap drop more than offsets re-shipping any classes
 * Tailwind might (it doesn't — JIT handles this).
 */
module.exports = {
  plugins: []
}
