import { marked } from 'marked'

/**
 * D3-FEAT-03: markdown-driven writing pipeline. Articles live in
 * frontend/content/writing/*.md with a YAML-ish frontmatter block; the
 * eager raw glob pulls them in at build time, so the whole surface is
 * prerendered by vite-ssg with zero backend involvement.
 *
 * Content is repo-committed and review-gated (articles land only after
 * owner approval), so rendering with v-html downstream is trusted-input
 * rendering, not a user-content XSS surface.
 *
 * Bundle note: the eager raw glob inlines full article text into any
 * chunk importing this module (HomeView's Words block included). Fine at
 * a handful of articles; if the archive grows, split meta and body into
 * separate modules and lazy-load bodies in the article view.
 */

export interface WritingPost {
  slug: string
  title: string
  description: string
  /** ISO date (YYYY-MM-DD) */
  date: string
  /** Canonical URL override for cross-posted pieces; null = self-canonical */
  canonical: string | null
  html: string
}

const rawModules = import.meta.glob('../../content/writing/*.md', {
  query: '?raw',
  import: 'default',
  eager: true
}) as Record<string, string>

interface Frontmatter {
  meta: Record<string, string>
  body: string
}

// Minimal frontmatter parser: a leading `---` block of `key: value`
// lines. Deliberately not YAML — no nesting, no arrays — so the format
// can't drift into something this parser silently misreads.
export function parseFrontmatter(text: string): Frontmatter {
  const normalized = text.replace(/\r\n/g, '\n')
  if (!normalized.startsWith('---\n')) return { meta: {}, body: normalized }
  const end = normalized.indexOf('\n---', 4)
  if (end === -1) return { meta: {}, body: normalized }

  const meta: Record<string, string> = {}
  for (const line of normalized.slice(4, end).split('\n')) {
    const sep = line.indexOf(':')
    if (sep === -1) continue
    const key = line.slice(0, sep).trim()
    const value = line
      .slice(sep + 1)
      .trim()
      .replace(/^['"]|['"]$/g, '')
    if (key) meta[key] = value
  }
  const body = normalized.slice(end + 4).replace(/^-*\n?/, '')
  return { meta, body }
}

const buildPosts = (): WritingPost[] => {
  const posts: WritingPost[] = []
  for (const [path, raw] of Object.entries(rawModules)) {
    const { meta, body } = parseFrontmatter(raw)
    // Non-article files (README) and unapproved drafts never publish
    if (path.endsWith('README.md') || meta.draft === 'true') continue
    if (!meta.title || !meta.date) continue

    const filename = path.split('/').pop() ?? ''
    posts.push({
      slug: meta.slug || filename.replace(/\.md$/, ''),
      title: meta.title,
      description: meta.description ?? '',
      date: meta.date,
      canonical: meta.canonical || null,
      html: marked.parse(body, { async: false })
    })
  }
  return posts.sort((a, b) => b.date.localeCompare(a.date))
}

export const writingPosts: WritingPost[] = buildPosts()

export const findPost = (slug: string): WritingPost | undefined =>
  writingPosts.find(p => p.slug === slug)
