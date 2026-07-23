import { marked } from 'marked'

/**
 * D4-PERF: the markdown renderer, split out of data/writing.ts so `marked`
 * (~13KB gzip) is imported ONLY here. Its single consumer is the lazy
 * WritingArticleView route, so the vite.config manualChunks 'marked' branch
 * places it in its own chunk that loads with the article page instead of on
 * the eager homepage.
 *
 * Input is repo-committed, owner-reviewed markdown (see data/writing.ts), so
 * this is trusted-input rendering — the resulting HTML is mounted with
 * v-html downstream, not user-content XSS surface.
 */
export const renderMarkdown = (body: string): string => marked.parse(body, { async: false })
