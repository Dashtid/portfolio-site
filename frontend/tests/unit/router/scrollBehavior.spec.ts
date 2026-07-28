import { describe, it, expect, vi, afterEach } from 'vitest'
import { scrollBehavior } from '@/router'
import type { RouteLocationNormalized } from 'vue-router'

// scrollBehavior contract (owner-reported navbar-cut bug, 2026-07-28):
// route changes must jump to top INSTANTLY (no smooth animation to race the
// page transition), smooth stays reserved for in-page anchors, and exotic
// URL-bar hashes must never throw through querySelector.

const route = (hash = ''): RouteLocationNormalized =>
  ({ hash, path: '/', fullPath: `/${hash}` }) as RouteLocationNormalized

describe('router scrollBehavior', () => {
  afterEach(() => {
    vi.restoreAllMocks()
    vi.useRealTimers()
  })

  it('restores savedPosition verbatim (back/forward)', () => {
    const saved = { left: 0, top: 640 }
    expect(scrollBehavior(route(), route(), saved)).toBe(saved)
  })

  it('jumps to top with EXPLICIT instant behavior on plain route changes', () => {
    const result = scrollBehavior(route(), route(), null)
    // 'instant' must be explicit: html carries `scroll-behavior: smooth`
    // (style.css), and an omitted/auto behavior defers to that CSS — the
    // jump silently re-animates (~700ms) and wheel input mid-animation
    // cancels it, landing pages half-scrolled under the navbar.
    expect(result).toEqual({ top: 0, behavior: 'instant' })
  })

  it('scrolls to the element for a hash whose target exists', async () => {
    const el = document.createElement('div')
    el.id = 'experience'
    document.body.appendChild(el)

    const result = await scrollBehavior(route('#experience'), route(), null)
    expect(result).toMatchObject({ el: '#experience' })

    el.remove()
  })

  it('does not throw on exotic hashes and falls back to top instantly', async () => {
    // '#1abc' is an invalid CSS selector — raw querySelector(to.hash) throws
    // SyntaxError. The sanitized path must resolve instead of rejecting.
    const result = await scrollBehavior(route('#1abc'), route(), null)
    expect(result).toEqual({ top: 0, behavior: 'instant' })
  })

  it('degrades gracefully on CSS-meaningful hash characters (no throw, no rejection)', async () => {
    // Real browsers resolve the escaped selector to the element; happy-dom's
    // parser rejects escapes, exercising the try/catch fallback instead.
    // Either way the promise must RESOLVE with a usable target — never throw.
    const el = document.createElement('div')
    el.id = 'foo[bar'
    document.body.appendChild(el)

    const result = await scrollBehavior(route('#foo[bar'), route(), null)
    expect(typeof result).toBe('object')
    const r = result as Record<string, unknown>
    expect('el' in r || r.top === 0).toBe(true)

    el.remove()
  })
})
