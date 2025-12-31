import { onMounted, onBeforeUnmount, type Ref } from 'vue'
import gsap from 'gsap'

interface TiltOptions {
  maxTilt?: number
  scale?: number
  speed?: number
  glare?: boolean
  glareOpacity?: number
}

interface MagneticOptions {
  strength?: number
  ease?: number
}

interface RippleOptions {
  color?: string
  duration?: number
}

// Check for reduced motion preference
const prefersReducedMotion = () => window.matchMedia('(prefers-reduced-motion: reduce)').matches

/**
 * 3D tilt effect on hover for cards
 */
export function useTiltEffect(cardRef: Ref<HTMLElement | null>, options: TiltOptions = {}) {
  const { maxTilt = 10, scale = 1.02, speed = 400, glare = false, glareOpacity = 0.2 } = options

  let glareElement: HTMLElement | null = null
  let boundingRect: DOMRect | null = null
  let rafId: number | null = null

  const handleMouseMove = (e: MouseEvent) => {
    if (!cardRef.value || prefersReducedMotion()) return

    // Cancel any pending animation frame
    if (rafId) cancelAnimationFrame(rafId)

    rafId = requestAnimationFrame(() => {
      if (!cardRef.value || !boundingRect) return

      const x = e.clientX - boundingRect.left
      const y = e.clientY - boundingRect.top
      const centerX = boundingRect.width / 2
      const centerY = boundingRect.height / 2

      const rotateX = ((y - centerY) / centerY) * -maxTilt
      const rotateY = ((x - centerX) / centerX) * maxTilt

      gsap.to(cardRef.value, {
        rotateX,
        rotateY,
        scale,
        duration: speed / 1000,
        ease: 'power2.out',
        transformPerspective: 1000
      })

      // Update glare position
      if (glare && glareElement) {
        const glareX = (x / boundingRect.width) * 100
        const glareY = (y / boundingRect.height) * 100
        glareElement.style.background = `radial-gradient(circle at ${glareX}% ${glareY}%, rgba(255,255,255,${glareOpacity}), transparent 50%)`
      }
    })
  }

  const handleMouseEnter = () => {
    if (!cardRef.value) return
    boundingRect = cardRef.value.getBoundingClientRect()
  }

  const handleMouseLeave = () => {
    if (!cardRef.value) return

    if (rafId) cancelAnimationFrame(rafId)

    gsap.to(cardRef.value, {
      rotateX: 0,
      rotateY: 0,
      scale: 1,
      duration: 0.5,
      ease: 'power2.out'
    })

    if (glare && glareElement) {
      glareElement.style.background = 'transparent'
    }
  }

  onMounted(() => {
    if (!cardRef.value || prefersReducedMotion()) return

    // Set up card for 3D transforms
    cardRef.value.style.transformStyle = 'preserve-3d'
    cardRef.value.style.willChange = 'transform'

    // Create glare element if enabled
    if (glare) {
      glareElement = document.createElement('div')
      glareElement.className = 'tilt-glare'
      glareElement.style.cssText = `
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        pointer-events: none;
        border-radius: inherit;
        z-index: 1;
      `
      cardRef.value.style.position = 'relative'
      cardRef.value.appendChild(glareElement)
    }

    cardRef.value.addEventListener('mouseenter', handleMouseEnter)
    cardRef.value.addEventListener('mousemove', handleMouseMove)
    cardRef.value.addEventListener('mouseleave', handleMouseLeave)
  })

  onBeforeUnmount(() => {
    if (!cardRef.value) return

    if (rafId) cancelAnimationFrame(rafId)

    cardRef.value.removeEventListener('mouseenter', handleMouseEnter)
    cardRef.value.removeEventListener('mousemove', handleMouseMove)
    cardRef.value.removeEventListener('mouseleave', handleMouseLeave)

    if (glareElement && cardRef.value.contains(glareElement)) {
      cardRef.value.removeChild(glareElement)
    }
  })
}

/**
 * Magnetic button effect - button follows cursor within bounds
 */
export function useMagneticButton(
  buttonRef: Ref<HTMLElement | null>,
  options: MagneticOptions = {}
) {
  const { ease = 0.3 } = options

  let boundingRect: DOMRect | null = null
  let rafId: number | null = null

  const handleMouseMove = (e: MouseEvent) => {
    if (!buttonRef.value || !boundingRect || prefersReducedMotion()) return

    if (rafId) cancelAnimationFrame(rafId)

    rafId = requestAnimationFrame(() => {
      if (!buttonRef.value || !boundingRect) return

      const x = e.clientX - boundingRect.left - boundingRect.width / 2
      const y = e.clientY - boundingRect.top - boundingRect.height / 2

      gsap.to(buttonRef.value, {
        x: x * ease,
        y: y * ease,
        duration: 0.3,
        ease: 'power2.out'
      })
    })
  }

  const handleMouseEnter = () => {
    if (!buttonRef.value) return
    boundingRect = buttonRef.value.getBoundingClientRect()
  }

  const handleMouseLeave = () => {
    if (!buttonRef.value) return

    if (rafId) cancelAnimationFrame(rafId)

    gsap.to(buttonRef.value, {
      x: 0,
      y: 0,
      duration: 0.5,
      ease: 'elastic.out(1, 0.3)'
    })
  }

  onMounted(() => {
    if (!buttonRef.value || prefersReducedMotion()) return

    buttonRef.value.addEventListener('mouseenter', handleMouseEnter)
    buttonRef.value.addEventListener('mousemove', handleMouseMove)
    buttonRef.value.addEventListener('mouseleave', handleMouseLeave)
  })

  onBeforeUnmount(() => {
    if (!buttonRef.value) return

    if (rafId) cancelAnimationFrame(rafId)

    buttonRef.value.removeEventListener('mouseenter', handleMouseEnter)
    buttonRef.value.removeEventListener('mousemove', handleMouseMove)
    buttonRef.value.removeEventListener('mouseleave', handleMouseLeave)
  })
}

/**
 * Ripple effect on click
 */
export function useRippleEffect(
  containerRef: Ref<HTMLElement | null>,
  options: RippleOptions = {}
) {
  const { color = 'rgba(59, 130, 246, 0.3)', duration = 0.6 } = options

  const createRipple = (e: MouseEvent) => {
    if (!containerRef.value || prefersReducedMotion()) return

    const rect = containerRef.value.getBoundingClientRect()
    const ripple = document.createElement('span')

    ripple.className = 'ripple-effect'
    ripple.style.cssText = `
      position: absolute;
      width: 50px;
      height: 50px;
      background: ${color};
      border-radius: 50%;
      transform: translate(-50%, -50%) scale(0);
      pointer-events: none;
      left: ${e.clientX - rect.left}px;
      top: ${e.clientY - rect.top}px;
    `

    containerRef.value.style.position = 'relative'
    containerRef.value.style.overflow = 'hidden'
    containerRef.value.appendChild(ripple)

    gsap.to(ripple, {
      scale: 4,
      opacity: 0,
      duration,
      ease: 'power2.out',
      onComplete: () => ripple.remove()
    })
  }

  onMounted(() => {
    if (!containerRef.value) return
    containerRef.value.addEventListener('click', createRipple)
  })

  onBeforeUnmount(() => {
    if (!containerRef.value) return
    containerRef.value.removeEventListener('click', createRipple)
  })
}

/**
 * Hover scale effect
 */
export function useHoverScale(
  elementRef: Ref<HTMLElement | null>,
  options: { scale?: number; duration?: number } = {}
) {
  const { scale = 1.05, duration = 0.3 } = options

  const handleMouseEnter = () => {
    if (!elementRef.value || prefersReducedMotion()) return

    gsap.to(elementRef.value, {
      scale,
      duration,
      ease: 'power2.out'
    })
  }

  const handleMouseLeave = () => {
    if (!elementRef.value) return

    gsap.to(elementRef.value, {
      scale: 1,
      duration,
      ease: 'power2.out'
    })
  }

  onMounted(() => {
    if (!elementRef.value) return

    elementRef.value.addEventListener('mouseenter', handleMouseEnter)
    elementRef.value.addEventListener('mouseleave', handleMouseLeave)
  })

  onBeforeUnmount(() => {
    if (!elementRef.value) return

    elementRef.value.removeEventListener('mouseenter', handleMouseEnter)
    elementRef.value.removeEventListener('mouseleave', handleMouseLeave)
  })
}

/**
 * Button press effect
 */
export function useButtonPress(
  buttonRef: Ref<HTMLElement | null>,
  options: { scale?: number } = {}
) {
  const { scale = 0.95 } = options

  const handleMouseDown = () => {
    if (!buttonRef.value || prefersReducedMotion()) return

    gsap.to(buttonRef.value, {
      scale,
      duration: 0.1,
      ease: 'power2.out'
    })
  }

  const handleMouseUp = () => {
    if (!buttonRef.value) return

    gsap.to(buttonRef.value, {
      scale: 1,
      duration: 0.2,
      ease: 'elastic.out(1, 0.5)'
    })
  }

  onMounted(() => {
    if (!buttonRef.value) return

    buttonRef.value.addEventListener('mousedown', handleMouseDown)
    buttonRef.value.addEventListener('mouseup', handleMouseUp)
    buttonRef.value.addEventListener('mouseleave', handleMouseUp)
  })

  onBeforeUnmount(() => {
    if (!buttonRef.value) return

    buttonRef.value.removeEventListener('mousedown', handleMouseDown)
    buttonRef.value.removeEventListener('mouseup', handleMouseUp)
    buttonRef.value.removeEventListener('mouseleave', handleMouseUp)
  })
}
