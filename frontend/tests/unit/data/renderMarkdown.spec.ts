import { describe, it, expect } from 'vitest'
import { renderMarkdown } from '@/data/renderMarkdown'

// The markdown renderer split out of data/writing.ts (D4-PERF) so `marked`
// ships in the lazy article route's chunk, not on the homepage. These tests
// pin the render contract the article view relies on.
describe('renderMarkdown (D4-PERF)', () => {
  it('renders headings and inline emphasis to HTML', () => {
    const html = renderMarkdown('## Threat model\n\nSecurity is **not** optional.')
    expect(html).toContain('<h2')
    expect(html).toContain('Threat model')
    expect(html).toContain('<strong>not</strong>')
  })

  it('renders links and lists', () => {
    const html = renderMarkdown('- one\n- two\n\n[site](https://dashti.se)')
    expect(html).toContain('<ul>')
    expect(html).toContain('<li>one</li>')
    expect(html).toContain('href="https://dashti.se"')
  })

  it('returns a string synchronously (setup() stays sync for SSG hydration)', () => {
    const html = renderMarkdown('plain paragraph')
    expect(typeof html).toBe('string')
    expect(html).toContain('plain paragraph')
  })
})
