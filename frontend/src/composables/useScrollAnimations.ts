/**
 * Scroll Animations Composable
 * Provides scroll-triggered animations using Intersection Observer
 * Supports fade-in, slide-up, slide-in-left, slide-in-right effects
 */
import { useIntersectionObserver } from '@vueuse/core'
import { ref, onMounted, onBeforeUnmount, type Ref } from 'vue'

interface AnimationStyles {
  opacity: string
  transform: string
}

interface AnimationConfig {
  initial: AnimationStyles
  animate: AnimationStyles
}

type AnimationType = 'fadeIn' | 'slideUp' | 'slideInLeft' | 'slideInRight' | 'scaleIn'

/**
 * Animation configurations
 * Each animation has a CSS class that will be applied when element is visible
 */
const ANIMATIONS: Record<AnimationType, AnimationConfig> = {
  fadeIn: {
    initial: {
      opacity: '0',
      transform: 'none'
    },
    animate: {
      opacity: '1',
      transform: 'none'
    }
  },
  slideUp: {
    initial: {
      opacity: '0',
      transform: 'translateY(30px)'
    },
    animate: {
      opacity: '1',
      transform: 'translateY(0)'
    }
  },
  slideInLeft: {
    initial: {
      opacity: '0',
      transform: 'translateX(-30px)'
    },
    animate: {
      opacity: '1',
      transform: 'translateX(0)'
    }
  },
  slideInRight: {
    initial: {
      opacity: '0',
      transform: 'translateX(30px)'
    },
    animate: {
      opacity: '1',
      transform: 'translateX(0)'
    }
  },
  scaleIn: {
    initial: {
      opacity: '0',
      transform: 'scale(0.9)'
    },
    animate: {
      opacity: '1',
      transform: 'scale(1)'
    }
  }
}

interface ScrollAnimationOptions {
  animation?: AnimationType
  duration?: number
  delay?: number
  easing?: string
  threshold?: number
  once?: boolean
}

interface ScrollAnimationReturn {
  isVisible: Ref<boolean>
  hasAnimated: Ref<boolean>
  /** Stop observing the element (cleanup) */
  stop: () => void
}

/**
 * Apply scroll animation to an element
 * @param target - Element ref to observe
 * @param options - Animation options
 */
export function useScrollAnimation(
  target: Ref<HTMLElement | null>,
  options: ScrollAnimationOptions = {}
): ScrollAnimationReturn {
  const {
    animation = 'fadeIn',
    duration = 600,
    delay = 0,
    easing = 'ease-out',
    threshold = 0.1,
    once = true
  } = options

  const isVisible = ref(false)
  const hasAnimated = ref(false)

  // Get animation config
  const animationConfig = ANIMATIONS[animation] || ANIMATIONS.fadeIn

  // Apply initial styles
  const applyInitialStyles = (): void => {
    if (!target.value) return

    Object.assign(target.value.style, {
      ...animationConfig.initial,
      transition: `all ${duration}ms ${easing} ${delay}ms`
    })
  }

  // Apply animation styles
  const applyAnimationStyles = (): void => {
    if (!target.value) return

    Object.assign(target.value.style, animationConfig.animate)
    hasAnimated.value = true
  }

  // Setup intersection observer
  const { stop } = useIntersectionObserver(
    target,
    ([{ isIntersecting }]) => {
      if (isIntersecting && (!once || !hasAnimated.value)) {
        isVisible.value = true
        applyAnimationStyles()

        if (once) {
          stop()
        }
      } else if (!isIntersecting && !once && hasAnimated.value) {
        // Reset animation if not "once" mode
        isVisible.value = false
        applyInitialStyles()
      }
    },
    {
      threshold
    }
  )

  onMounted(() => {
    applyInitialStyles()
  })

  return {
    isVisible,
    hasAnimated,
    stop
  }
}

interface StaggeredAnimationOptions extends ScrollAnimationOptions {
  stagger?: number
}

/**
 * Apply animations to multiple elements with stagger effect
 * @param targets - Array of element refs
 * @param options - Animation options (same as useScrollAnimation)
 */
export function useStaggeredAnimation(
  targets: Ref<HTMLElement | null>[],
  options: StaggeredAnimationOptions = {}
): ScrollAnimationReturn[] {
  const { stagger = 100, ...animationOptions } = options
  const animations: ScrollAnimationReturn[] = []

  targets.forEach((target, index) => {
    const animation = useScrollAnimation(target, {
      ...animationOptions,
      delay: (animationOptions.delay || 0) + index * stagger
    })
    animations.push(animation)
  })

  return animations
}

interface BatchAnimationReturn {
  elements: Ref<Element[]>
  animations: ScrollAnimationReturn[]
}

/**
 * Batch animate elements with a selector
 * Uses a single IntersectionObserver for all elements to prevent memory issues
 * @param selector - CSS selector for elements to animate
 * @param options - Animation options
 */
export function useBatchAnimation(
  selector: string,
  options: StaggeredAnimationOptions = {}
): BatchAnimationReturn {
  const {
    animation = 'fadeIn',
    duration = 600,
    delay = 0,
    easing = 'ease-out',
    threshold = 0.1,
    stagger = 100
  } = options

  const elements = ref<Element[]>([])
  const animations: ScrollAnimationReturn[] = []
  let observer: IntersectionObserver | null = null
  const animatedElements = new Set<Element>()

  const animationConfig = ANIMATIONS[animation] || ANIMATIONS.fadeIn

  onMounted(() => {
    elements.value = Array.from(document.querySelectorAll(selector))

    if (elements.value.length === 0) return

    // Apply initial styles to all elements
    elements.value.forEach((element, index) => {
      const el = element as HTMLElement
      const elementDelay = delay + index * stagger
      Object.assign(el.style, {
        ...animationConfig.initial,
        transition: `all ${duration}ms ${easing} ${elementDelay}ms`
      })

      // Create animation return object for each element
      animations.push({
        isVisible: ref(false),
        hasAnimated: ref(false),
        stop: () => {
          if (observer) {
            observer.unobserve(element)
          }
        }
      })
    })

    // Create a single shared IntersectionObserver for all elements
    observer = new IntersectionObserver(
      entries => {
        entries.forEach(entry => {
          if (entry.isIntersecting && !animatedElements.has(entry.target)) {
            const el = entry.target as HTMLElement
            Object.assign(el.style, animationConfig.animate)
            animatedElements.add(entry.target)

            // Find and update the animation state
            const index = elements.value.indexOf(entry.target)
            if (index !== -1 && animations[index]) {
              animations[index].isVisible.value = true
              animations[index].hasAnimated.value = true
            }

            // Stop observing this element since animation is complete
            observer?.unobserve(entry.target)
          }
        })
      },
      { threshold }
    )

    // Observe all elements with the single observer
    elements.value.forEach(element => {
      observer?.observe(element)
    })
  })

  // Cleanup observer when component unmounts
  onBeforeUnmount(() => {
    if (observer) {
      observer.disconnect()
      observer = null
    }
    animatedElements.clear()
    animations.length = 0
    elements.value = []
  })

  return {
    elements,
    animations
  }
}

interface ParallaxOptions {
  speed?: number
}

/**
 * Parallax scroll effect
 * @param target - Element ref to apply parallax
 * @param options - Parallax options
 */
export function useParallax(target: Ref<HTMLElement | null>, options: ParallaxOptions = {}): void {
  const { speed = 0.5 } = options

  // Store scroll listener and RAF ID for cleanup
  let scrollListener: (() => void) | null = null
  let rafId: number | null = null

  onMounted(() => {
    const handleScroll = (): void => {
      if (!target.value) return

      const rect = target.value.getBoundingClientRect()
      const scrolled = window.pageYOffset || document.documentElement.scrollTop
      const parallax = (scrolled - rect.top) * speed

      target.value.style.transform = `translateY(${parallax}px)`
    }

    // Throttle scroll events for performance using RAF
    scrollListener = (): void => {
      // Skip if RAF already scheduled
      if (rafId !== null) return

      rafId = window.requestAnimationFrame(() => {
        handleScroll()
        rafId = null
      })
    }

    window.addEventListener('scroll', scrollListener, { passive: true })
  })

  // Properly cleanup scroll listener and pending RAF to prevent memory leaks
  onBeforeUnmount(() => {
    // Cancel any pending animation frame
    if (rafId !== null) {
      window.cancelAnimationFrame(rafId)
      rafId = null
    }
    if (scrollListener) {
      window.removeEventListener('scroll', scrollListener)
      scrollListener = null
    }
  })
}
