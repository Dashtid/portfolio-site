/**
 * Minimal SSR-safe markdown helpers used to render company description text
 * to v-html safely. No DOM dependency (unlike DOMPurify) so they run during
 * vite-ssg's Node-side render.
 */

// Escape HTML special chars so any < > & " ' in the source text can't reach
// the DOM as markup. Run BEFORE markdown so the strong/em tags we emit aren't
// themselves escaped.
export const escapeHtml = (s: string): string =>
  s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')

// Minimal markdown: **bold** and *italic*. Input is pre-escaped so the only
// HTML in the output is the strong/em tags this function emits.
// Order matters: do ** before * so **foo** doesn't get mangled into <em>.
export const renderInlineMarkdown = (text: string): string => {
  return escapeHtml(text)
    .replace(/\*\*([^*\n]+)\*\*/g, '<strong>$1</strong>')
    .replace(/(^|[^*])\*([^*\n]+)\*(?!\*)/g, '$1<em>$2</em>')
}

// Format description: split on blank lines into <p>, escape + render markdown
// inside each paragraph. Output is safe to v-html since input is escaped first
// and only the controlled strong/em tags are introduced.
export const formatDescription = (desc: string | null | undefined): string => {
  if (!desc) return ''
  return desc
    .split('\n\n')
    .map(p => `<p>${renderInlineMarkdown(p)}</p>`)
    .join('')
}
