import { describe, it, expect } from 'vitest'
import { parseFrontmatter, writingPosts, findPost, findPostBody } from '@/data/writing'

describe('writing content pipeline (D3-FEAT-03)', () => {
  describe('parseFrontmatter', () => {
    it('parses a basic frontmatter block', () => {
      const { meta, body } = parseFrontmatter(
        '---\ntitle: Hello\ndate: 2026-07-21\n---\n\nBody text.'
      )
      expect(meta.title).toBe('Hello')
      expect(meta.date).toBe('2026-07-21')
      expect(body.trim()).toBe('Body text.')
    })

    it('normalizes CRLF input (Windows checkouts)', () => {
      const { meta, body } = parseFrontmatter('---\r\ntitle: Hello\r\n---\r\nBody.')
      expect(meta.title).toBe('Hello')
      expect(body.trim()).toBe('Body.')
    })

    it('strips surrounding quotes from values', () => {
      const { meta } = parseFrontmatter('---\ntitle: "Quoted: with colon"\n---\nx')
      expect(meta.title).toBe('Quoted: with colon')
    })

    it('treats text without a frontmatter block as pure body', () => {
      const { meta, body } = parseFrontmatter('Just markdown.')
      expect(meta).toEqual({})
      expect(body).toBe('Just markdown.')
    })

    it('keeps values containing colons intact (URLs)', () => {
      const { meta } = parseFrontmatter('---\ncanonical: https://dashti.se/writing/x\n---\nx')
      expect(meta.canonical).toBe('https://dashti.se/writing/x')
    })
  })

  describe('writingPosts', () => {
    it('excludes the content README and unapproved drafts from the surface', () => {
      // The content dir currently holds only README.md (articles are
      // owner-gated); the pipeline must not surface it as a post.
      expect(Array.isArray(writingPosts)).toBe(true)
      expect(writingPosts.every(p => p.slug !== 'README')).toBe(true)
      expect(writingPosts.every(p => p.title && p.date)).toBe(true)
    })

    it('findPost returns undefined for unknown slugs', () => {
      expect(findPost('does-not-exist')).toBeUndefined()
    })

    it('keeps article bodies as raw markdown, not pre-rendered HTML (D4-PERF split)', () => {
      // The homepage and /writing index import writingPosts (metadata only);
      // bodies stay RAW markdown and are rendered lazily in the article view
      // via renderMarkdown — that separation is what keeps `marked` off the
      // eager homepage chunk. writingPosts is empty until the first article
      // ships, so a value check on the list is vacuous; this pins the split at
      // the parse layer (the same buildPosts path) instead.
      const { meta, body } = parseFrontmatter(
        '---\ntitle: T\ndate: 2026-01-01\n---\n\n## Heading\n\n**bold** body.'
      )
      expect(meta.title).toBe('T')
      // The body the data module carries is unrendered markdown syntax, with
      // no HTML tags — rendering happens only in renderMarkdown().
      expect(body).toContain('## Heading')
      expect(body).toContain('**bold**')
      expect(body).not.toMatch(/<[a-z]/i)
    })

    it('findPostBody returns undefined for unknown slugs', () => {
      expect(findPostBody('does-not-exist')).toBeUndefined()
    })
  })
})
