import { ref, onMounted, onBeforeUnmount, type Ref } from 'vue'
import gsap from 'gsap'
import type { ScrollTrigger as ScrollTriggerType } from 'gsap/ScrollTrigger'

// Lazy-loaded ScrollTrigger reference
let ScrollTrigger: typeof ScrollTriggerType | null = null
let scrollTriggerLoaded = false

// Lazy load ScrollTrigger only when needed (saves initial bundle size)
const loadScrollTrigger = async (): Promise<typeof ScrollTriggerType> => {
  if (scrollTriggerLoaded && ScrollTrigger) {
    return ScrollTrigger
  }
  const module = await import('gsap/ScrollTrigger')
  ScrollTrigger = module.ScrollTrigger
  gsap.registerPlugin(ScrollTrigger)
  scrollTriggerLoaded = true
  return ScrollTrigger
}

export type AnimationType =
  | 'fadeIn'
  | 'slideUp'
  | 'slideInLeft'
  | 'slideInRight'
  | 'scaleIn'
  | 'reveal'

export interface GsapAnimationOptions {
  animation?: AnimationType
  duration?: number
  delay?: number
  ease?: string
  scrub?: boolean | number
  markers?: boolean
  start?: string
  end?: string
}

export interface GsapBatchOptions extends GsapAnimationOptions {
  stagger?: number
}

// Animation start and end states
const animationStates: Record<AnimationType, { from: gsap.TweenVars; to: gsap.TweenVars }> = {
  fadeIn: {
    from: { opacity: 0 },
    to: { opacity: 1 }
  },
  slideUp: {
    from: { opacity: 0, y: 50 },
    to: { opacity: 1, y: 0 }
  },
  slideInLeft: {
    from: { opacity: 0, x: -50 },
    to: { opacity: 1, x: 0 }
  },
  slideInRight: {
    from: { opacity: 0, x: 50 },
    to: { opacity: 1, x: 0 }
  },
  scaleIn: {
    from: { opacity: 0, scale: 0.9 },
    to: { opacity: 1, scale: 1 }
  },
  reveal: {
    from: { clipPath: 'inset(0 100% 0 0)' },
    to: { clipPath: 'inset(0 0% 0 0)' }
  }
}

/**
 * GSAP scroll-triggered animation for a single element
 */
export function useGsapScrollAnimation(
  target: Ref<HTMLElement | null>,
  options: GsapAnimationOptions = {}
) {
  const {
    animation = 'fadeIn',
    duration = 0.8,
    delay = 0,
    ease = 'power2.out',
    start = 'top 85%',
    end = 'bottom 15%',
    markers = false
  } = options

  const isAnimated = ref(false)
  let scrollTrigger: ScrollTrigger | null = null
  let tween: gsap.core.Tween | null = null

  // Check for reduced motion preference
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches

  onMounted(async () => {
    if (!target.value) return

    // If user prefers reduced motion, show element immediately
    if (prefersReducedMotion) {
      gsap.set(target.value, animationStates[animation].to)
      isAnimated.value = true
      return
    }

    // Set initial state
    gsap.set(target.value, animationStates[animation].from)

    // Lazy load ScrollTrigger and create animation
    const ST = await loadScrollTrigger()
    scrollTrigger = ST.create({
      trigger: target.value,
      start,
      end,
      markers,
      onEnter: () => {
        tween = gsap.to(target.value, {
          ...animationStates[animation].to,
          duration,
          delay,
          ease,
          onComplete: () => {
            isAnimated.value = true
          }
        })
      }
    })
  })

  onBeforeUnmount(() => {
    tween?.kill()
    scrollTrigger?.kill()
  })

  return { isAnimated }
}

/**
 * GSAP batch animation for multiple elements with stagger
 */
export function useGsapBatchAnimation(selector: string, options: GsapBatchOptions = {}) {
  const {
    animation = 'slideUp',
    duration = 0.6,
    delay = 0,
    ease = 'power2.out',
    stagger = 0.1,
    start = 'top 80%'
  } = options

  const isComplete = ref(false)

  // Check for reduced motion preference
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches

  onMounted(async () => {
    const elements = document.querySelectorAll(selector)
    if (!elements.length) return

    // If user prefers reduced motion, show elements immediately
    if (prefersReducedMotion) {
      gsap.set(elements, animationStates[animation].to)
      isComplete.value = true
      return
    }

    // Set initial state
    gsap.set(elements, animationStates[animation].from)

    // Lazy load ScrollTrigger and create batch animation
    await loadScrollTrigger()
    gsap.to(elements, {
      ...animationStates[animation].to,
      duration,
      delay,
      ease,
      stagger,
      scrollTrigger: {
        trigger: elements[0].parentElement,
        start,
        once: true
      },
      onComplete: () => {
        isComplete.value = true
      }
    })
  })

  onBeforeUnmount(async () => {
    if (ScrollTrigger) {
      ScrollTrigger.getAll().forEach(trigger => trigger.kill())
    }
  })

  return { isComplete }
}

/**
 * Page transition animations for Vue Router
 */
export function usePageTransition() {
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches

  const enter = (el: Element, done: () => void) => {
    if (prefersReducedMotion) {
      done()
      return
    }

    gsap.from(el, {
      opacity: 0,
      y: 20,
      duration: 0.4,
      ease: 'power2.out',
      onComplete: done
    })
  }

  const leave = (el: Element, done: () => void) => {
    if (prefersReducedMotion) {
      done()
      return
    }

    gsap.to(el, {
      opacity: 0,
      y: -20,
      duration: 0.3,
      ease: 'power2.in',
      onComplete: done
    })
  }

  return { enter, leave }
}

/**
 * Parallax scroll effect
 */
export function useGsapParallax(
  target: Ref<HTMLElement | null>,
  options: { speed?: number; direction?: 'vertical' | 'horizontal' } = {}
) {
  const { speed = 0.5, direction = 'vertical' } = options
  let scrollTrigger: ScrollTrigger | null = null

  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches

  onMounted(async () => {
    if (!target.value || prefersReducedMotion) return

    // Lazy load ScrollTrigger
    const ST = await loadScrollTrigger()
    scrollTrigger = ST.create({
      trigger: target.value,
      start: 'top bottom',
      end: 'bottom top',
      scrub: 1,
      onUpdate: self => {
        const progress = self.progress
        if (direction === 'vertical') {
          gsap.set(target.value, { y: progress * 100 * speed - 50 * speed })
        } else {
          gsap.set(target.value, { x: progress * 100 * speed - 50 * speed })
        }
      }
    })
  })

  onBeforeUnmount(() => {
    scrollTrigger?.kill()
  })
}

/**
 * Text reveal animation (character by character)
 */
export function useTextReveal(
  target: Ref<HTMLElement | null>,
  options: { duration?: number; stagger?: number; delay?: number } = {}
) {
  const { duration = 0.5, stagger = 0.02, delay = 0 } = options
  const isComplete = ref(false)

  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches

  onMounted(async () => {
    if (!target.value) return

    if (prefersReducedMotion) {
      isComplete.value = true
      return
    }

    const text = target.value.textContent || ''
    target.value.innerHTML = text
      .split('')
      .map(char => `<span class="char">${char === ' ' ? '&nbsp;' : char}</span>`)
      .join('')

    const chars = target.value.querySelectorAll('.char')

    // Lazy load ScrollTrigger
    await loadScrollTrigger()
    gsap.from(chars, {
      opacity: 0,
      y: 20,
      duration,
      stagger,
      delay,
      ease: 'power2.out',
      scrollTrigger: {
        trigger: target.value,
        start: 'top 85%',
        once: true
      },
      onComplete: () => {
        isComplete.value = true
      }
    })
  })

  return { isComplete }
}

/**
 * Cleanup all ScrollTriggers (call on route change if needed)
 */
export async function cleanupScrollTriggers() {
  if (ScrollTrigger) {
    ScrollTrigger.getAll().forEach(trigger => trigger.kill())
  }
}

/**
 * Refresh ScrollTrigger (call after dynamic content loads)
 */
export async function refreshScrollTriggers() {
  if (ScrollTrigger) {
    ScrollTrigger.refresh()
  }
}
