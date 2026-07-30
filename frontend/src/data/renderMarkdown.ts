import { marked } from 'marked'

/**
 * D4-PERF: the markdown renderer, split out of data/writing.ts so `marked`
 * (~13KB gzip) is imported ONLY here. Its single consumer is the lazy
 * WritingArticleView route, so Rolldown's default splitting ships it with
 * the article page instead of the eager homepage. This import graph IS the
 * invariant's mechanism (the old vite.config manualChunks branch is gone —
 * custom grouping breaks Rolldown 1.2.1 module init); an eager import of
 * this file would regress homepage LCP, and scripts/verify-dist-invariants
 * .mjs fails the build if that happens.
 *
 * Input is repo-committed, owner-reviewed markdown (see data/writing.ts), so
 * this is trusted-input rendering — the resulting HTML is mounted with
 * v-html downstream, not user-content XSS surface.
 */
export const renderMarkdown = (body: string): string => marked.parse(body, { async: false })
