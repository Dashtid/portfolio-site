import { onBeforeUnmount, onMounted } from 'vue'
import { useRoute } from 'vue-router'

/**
 * Post-settle correction for hash landings.
 *
 * The router's scrollBehavior scrolls to `#section` as soon as the element
 * exists — but on a cross-route landing (/experience/:id → /#publications)
 * the home page is still settling: the hero canvas mounts behind
 * requestIdleCallback, logos and client-fetched strips land late, and every
 * one of those shifts the layout ABOVE the target after the scroll has
 * already finished. Measured on the built site: sections ended 10–23px off,
 * and #experience up to 60px, on the cross-route path, while same-page
 * clicks and fresh loads (which scroll after layout is quiet) land within
 * ±0.5px.
 *
 * Strategy: once scrolling goes quiet, measure the residual misalignment
 * between the section top and the navbar's bottom edge and snap it away
 * (instant — this is a sub-frame nudge, not motion). Then keep watching
 * briefly for late layout shifts (a slow image above the target) and
 * correct once more if needed. The moment the user scrolls or presses a
 * key themselves, every pending correction is cancelled — their intent
 * wins over our alignment.
 */
export function useHashAlignment(): void {
  const route = useRoute()

  let cancelled = false
  let rafId = 0
  let secondPassTimer: ReturnType<typeof setTimeout> | undefined

  const cancel = (): void => {
    cancelled = true
    if (rafId) cancelAnimationFrame(rafId)
    if (secondPassTimer) clearTimeout(secondPassTimer)
  }

  const USER_INPUT_EVENTS = ['wheel', 'touchstart', 'mousedown', 'keydown'] as const
  const onUserInput = (): void => cancel()

  const navbarHeight = (): number => {
    const raw = getComputedStyle(document.documentElement).getPropertyValue('--navbar-height')
    const parsed = parseInt(raw, 10)
    return Number.isFinite(parsed) && parsed > 0 ? parsed : 72
  }

  const targetElement = (): HTMLElement | null => {
    const id = route.hash.slice(1)
    if (!id) return null
    return document.getElementById(id)
  }

  const correctIfNeeded = (): void => {
    const el = targetElement()
    if (!el || cancelled) return
    const delta = el.getBoundingClientRect().top - navbarHeight()
    // Sub-2px is rendering noise; anything more is a visible misalignment.
    if (Math.abs(delta) > 2) {
      window.scrollTo({ top: window.scrollY + delta, behavior: 'instant' })
    }
  }

  const whenScrollSettles = (done: () => void): void => {
    let lastY = window.scrollY
    let stable = 0
    const tick = (): void => {
      if (cancelled) return
      if (window.scrollY === lastY) {
        stable++
      } else {
        stable = 0
        lastY = window.scrollY
      }
      // ~10 quiet frames ≈ 160ms of no movement = the router's smooth
      // scroll (and any momentum) is over.
      if (stable >= 10) {
        done()
        return
      }
      rafId = requestAnimationFrame(tick)
    }
    rafId = requestAnimationFrame(tick)
  }

  onMounted(() => {
    if (!route.hash) return

    for (const evt of USER_INPUT_EVENTS) {
      window.addEventListener(evt, onUserInput, { passive: true, once: true })
    }

    whenScrollSettles(() => {
      correctIfNeeded()
      // Second pass: a slow image or late-mounting block above the target
      // can shift layout again after the first correction. One more check,
      // then we stop — endless re-anchoring would fight the user.
      secondPassTimer = setTimeout(correctIfNeeded, 1200)
    })
  })

  onBeforeUnmount(() => {
    cancel()
    for (const evt of USER_INPUT_EVENTS) {
      window.removeEventListener(evt, onUserInput)
    }
  })
}
