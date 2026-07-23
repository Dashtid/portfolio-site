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
 * Bundle note (D4-PERF): this module is METADATA-ONLY on purpose. The
 * homepage Words block and the /writing index import `writingPosts` (title
 * / date / slug), and includedRoutes reads slugs — none need the rendered
 * HTML. So `marked` (~13KB gzip) lives in data/renderMarkdown.ts, imported
 * ONLY by the lazy article view, which keeps the renderer off the eager
 * homepage chunk (it used to ride the eager `vendor` chunk via App.vue's
 * synchronous @unhead/vue import — see vite.config manualChunks 'marked').
 * Raw bodies are exposed through findPostBody() for that view. Bodies still
 * inline here via the eager glob; fine at a handful of articles (currently
 * zero — content/writing holds only README.md).
 */

export interface WritingPost {
  slug: string
  title: string
  description: string
  /** ISO date (YYYY-MM-DD) */
  date: string
  /** Canonical URL override for cross-posted pieces; null = self-canonical */
  canonical: string | null
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

interface BuiltPost extends WritingPost {
  /** Raw markdown body, rendered lazily by the article view (D4-PERF). */
  body: string
}

const buildPosts = (): BuiltPost[] => {
  const posts: BuiltPost[] = []
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
      body
    })
  }
  return posts.sort((a, b) => b.date.localeCompare(a.date))
}

const builtPosts: BuiltPost[] = buildPosts()

/** Public metadata list — carries no body/renderer (keeps `marked` off the
 *  eager homepage chunk). Imported by HomeView, the /writing index and
 *  includedRoutes. */
export const writingPosts: WritingPost[] = builtPosts.map(p => ({
  slug: p.slug,
  title: p.title,
  description: p.description,
  date: p.date,
  canonical: p.canonical
}))

export const findPost = (slug: string): WritingPost | undefined =>
  writingPosts.find(p => p.slug === slug)

/** Raw markdown body for a slug — consumed only by the lazy article view,
 *  which renders it through renderMarkdown(). Keeping the render step out of
 *  this module is what lets `marked` land in the article route chunk. */
export const findPostBody = (slug: string): string | undefined =>
  builtPosts.find(p => p.slug === slug)?.body
