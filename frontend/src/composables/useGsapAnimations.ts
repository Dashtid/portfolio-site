import { ref, onMounted, onBeforeUnmount } from 'vue'
import gsap from 'gsap'
import type { ScrollTrigger as ScrollTriggerType } from 'gsap/ScrollTrigger'

// Lazy-loaded ScrollTrigger reference — keeps it off the initial bundle.
let ScrollTrigger: typeof ScrollTriggerType | null = null
let scrollTriggerLoaded = false

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
 * GSAP batch animation for multiple elements with stagger.
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

  onMounted(async () => {
    const elements = document.querySelectorAll(selector)
    if (!elements.length) return

    // window is unavailable during SSG pre-render; gate inside onMounted.
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches

    if (prefersReducedMotion) {
      gsap.set(elements, animationStates[animation].to)
      isComplete.value = true
      return
    }

    gsap.set(elements, animationStates[animation].from)

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
