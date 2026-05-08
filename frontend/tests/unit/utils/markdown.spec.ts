import { describe, it, expect } from 'vitest'
import { escapeHtml, renderInlineMarkdown, formatDescription } from '@/utils/markdown'

describe('markdown', () => {
  describe('escapeHtml', () => {
    it('escapes & first so following replacements do not double-encode', () => {
      expect(escapeHtml('a & b')).toBe('a &amp; b')
    })

    it('escapes < and >', () => {
      expect(escapeHtml('<div>')).toBe('&lt;div&gt;')
    })

    it('escapes double quotes', () => {
      expect(escapeHtml('say "hi"')).toBe('say &quot;hi&quot;')
    })

    it('escapes single quotes / apostrophes', () => {
      expect(escapeHtml("it's")).toBe('it&#39;s')
    })

    it('escapes a tag-like payload end-to-end without leaving raw <', () => {
      const out = escapeHtml('<script>alert(1)</script>')
      expect(out).toBe('&lt;script&gt;alert(1)&lt;/script&gt;')
      expect(out).not.toContain('<')
      expect(out).not.toContain('>')
    })

    it('returns empty string unchanged', () => {
      expect(escapeHtml('')).toBe('')
    })
  })

  describe('renderInlineMarkdown', () => {
    it('renders **bold** as <strong>', () => {
      expect(renderInlineMarkdown('I am **strong** today')).toBe(
        'I am <strong>strong</strong> today'
      )
    })

    it('renders *italic* as <em>', () => {
      expect(renderInlineMarkdown('not *that* one')).toBe('not <em>that</em> one')
    })

    // Regex ordering: bold must run before italic, otherwise `**foo**` would
    // be matched as `*` + `*foo*` + `*` and produce `<em>foo</em>*`.
    it('does not mangle **bold** into <em>bold</em>', () => {
      const out = renderInlineMarkdown('**title**')
      expect(out).toBe('<strong>title</strong>')
      expect(out).not.toContain('<em>')
    })

    it('handles bold and italic together', () => {
      expect(renderInlineMarkdown('**big** and *small*')).toBe(
        '<strong>big</strong> and <em>small</em>'
      )
    })

    it('handles italic at the start of the string (the (^|[^*]) lookbehind)', () => {
      expect(renderInlineMarkdown('*lead* word')).toBe('<em>lead</em> word')
    })

    it('escapes raw HTML before applying markdown so injection is impossible', () => {
      const out = renderInlineMarkdown('<script>alert(1)</script>')
      expect(out).toBe('&lt;script&gt;alert(1)&lt;/script&gt;')
      expect(out).not.toContain('<script>')
    })

    it('does not match across newlines (per [^*\\n] guards)', () => {
      // A `**` opening on one line and `**` on the next must not collapse
      // into a single bold span — keeps newline-insensitive prose safe.
      const out = renderInlineMarkdown('**open\nclose**')
      expect(out).not.toContain('<strong>')
    })

    it('returns empty string unchanged', () => {
      expect(renderInlineMarkdown('')).toBe('')
    })
  })

  describe('formatDescription', () => {
    it('returns empty string for null', () => {
      expect(formatDescription(null)).toBe('')
    })

    it('returns empty string for undefined', () => {
      expect(formatDescription(undefined)).toBe('')
    })

    it('returns empty string for empty string', () => {
      expect(formatDescription('')).toBe('')
    })

    it('wraps a single paragraph in <p>', () => {
      expect(formatDescription('hello')).toBe('<p>hello</p>')
    })

    it('splits blank-line-separated paragraphs into multiple <p> tags', () => {
      expect(formatDescription('first\n\nsecond\n\nthird')).toBe(
        '<p>first</p><p>second</p><p>third</p>'
      )
    })

    it('preserves single newlines inside a paragraph (no <br> conversion)', () => {
      expect(formatDescription('line one\nline two')).toBe('<p>line one\nline two</p>')
    })

    it('applies markdown + escape inside each paragraph', () => {
      expect(formatDescription('a **b** c\n\n<x>')).toBe(
        '<p>a <strong>b</strong> c</p><p>&lt;x&gt;</p>'
      )
    })
  })
})
