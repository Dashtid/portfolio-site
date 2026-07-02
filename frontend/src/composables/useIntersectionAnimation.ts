import { onMounted, onBeforeUnmount, ref } from 'vue'

/**
 * IntersectionObserver-driven entrance animation for batches of elements.
 *
 * Replaces ``useGsapBatchAnimation`` (FRONTEND-PERF-03). The previous
 * composable pulled `gsap` and the `ScrollTrigger` plugin into the home
 * page's initial chunk (~45 KB gzipped after tree-shaking) just to fade
 * cards in as the user scrolls — IntersectionObserver hits the same
 * brief; the actual animation is a CSS transition on a single class
 * toggle.
 *
 * Usage:
 *   useIntersectionAnimation('.experience-card', { stagger: 0.08 })
 *
 * On mount: every matching element gets `data-anim="hidden"`; an
 * IntersectionObserver flips it to `data-anim="visible"` (with a
 * per-element transition-delay so the batch staggers in) the first time
 * it enters the viewport. The host page is expected to style
 * `[data-anim="hidden"]` and `[data-anim="visible"]` — the composable
 * does NOT inject CSS, keeping the visual choices in the consuming
 * component.
 *
 * Respects ``prefers-reduced-motion``: under the reduced-motion media
 * query elements are jumped straight to ``visible`` with no transition.
 */
export interface IntersectionAnimationOptions {
  /** Seconds between successive element reveals. Default 0.1. */
  stagger?: number
  /** IntersectionObserver rootMargin. Default '0px 0px -10% 0px' (reveal slightly before fully in view). */
  rootMargin?: string
  /** Intersection ratio to consider visible. Default 0.1. */
  threshold?: number
}

export function useIntersectionAnimation(
  selector: string,
  options: IntersectionAnimationOptions = {}
) {
  const { stagger = 0.1, rootMargin = '0px 0px -10% 0px', threshold = 0.1 } = options
  const isComplete = ref(false)

  let observer: IntersectionObserver | null = null
  let trackedCount = 0
  let revealedCount = 0

  const ensureObserver = (): IntersectionObserver => {
    if (observer) return observer
    observer = new IntersectionObserver(
      entries => {
        for (const entry of entries) {
          if (!entry.isIntersecting) continue
          const target = entry.target as HTMLElement
          // Each element of the batch receives its index-based delay
          // exactly once. Reading it back from `dataset.animIndex` keeps
          // the delay deterministic even if the observer fires elements
          // out of order (which it does when the user scrolls fast).
          const idxStr = target.dataset.animIndex ?? '0'
          const idx = Number.parseInt(idxStr, 10) || 0
          target.style.transitionDelay = `${idx * stagger}s`
          target.dataset.anim = 'visible'
          observer?.unobserve(target)
          revealedCount += 1
          if (revealedCount >= trackedCount) {
            isComplete.value = true
          }
        }
      },
      { rootMargin, threshold }
    )
    return observer
  }

  // Queries the selector and starts observing any elements not yet
  // tracked. Runs once on mount; content that renders later (e.g. cards
  // for data fetched in onMounted) is picked up by calling the returned
  // `refresh()` after the DOM has updated.
  const scan = (): void => {
    // SSG pre-render guard: window is undefined during the build pass.
    if (typeof window === 'undefined') return

    const elements = Array.from(document.querySelectorAll(selector)).filter(
      el => (el as HTMLElement).dataset.animIndex === undefined
    )
    if (!elements.length) {
      if (trackedCount === 0) isComplete.value = true
      return
    }
    isComplete.value = false

    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches

    if (prefersReducedMotion) {
      // Reduced motion: skip the observer entirely and reveal in place.
      for (const el of elements) {
        ;(el as HTMLElement).dataset.animIndex = 'static'
        ;(el as HTMLElement).dataset.anim = 'visible'
        ;(el as HTMLElement).style.transitionDuration = '0s'
      }
      if (trackedCount === revealedCount) isComplete.value = true
      return
    }

    // Initial state: hide everything. The transition is owned by host CSS
    // on `[data-anim="hidden"]` / `[data-anim="visible"]`.
    const io = ensureObserver()
    for (const el of elements) {
      const htmlEl = el as HTMLElement
      htmlEl.dataset.anim = 'hidden'
      htmlEl.dataset.animIndex = String(trackedCount)
      trackedCount += 1
      io.observe(htmlEl)
    }
  }

  // NOTE: must be invoked from synchronous setup (or before the first
  // await in an async setup) — after an await inside an onMounted callback
  // there is no active component instance, so these hooks silently never
  // register and the whole animation becomes dead code.
  onMounted(scan)

  onBeforeUnmount(() => {
    if (observer) {
      // Disconnect first so no late callbacks fire; per-element unobserve
      // is redundant after disconnect but cheap.
      observer.disconnect()
      observer = null
    }
  })

  return { isComplete, refresh: scan }
}
