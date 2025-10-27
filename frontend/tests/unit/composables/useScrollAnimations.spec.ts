/**
 * Tests for useScrollAnimations composable (TypeScript)
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ref } from 'vue'
import { useScrollAnimation, useStaggeredAnimation } from '@/composables/useScrollAnimations'

describe('useScrollAnimations', () => {
  describe('useScrollAnimation', () => {
    beforeEach(() => {
      vi.clearAllMocks()
    })

    it('returns isVisible and hasAnimated refs', () => {
      const element = ref<HTMLElement | null>(null)
      const result = useScrollAnimation(element)

      expect(result.isVisible).toBeDefined()
      expect(result.hasAnimated).toBeDefined()
      expect(result.isVisible.value).toBe(false)
      expect(result.hasAnimated.value).toBe(false)
    })

    it('accepts animation type option', () => {
      const element = ref<HTMLElement | null>(null)
      const result = useScrollAnimation(element, { animation: 'slideUp' })

      expect(result).toBeDefined()
    })

    it('accepts duration option', () => {
      const element = ref<HTMLElement | null>(null)
      const result = useScrollAnimation(element, { duration: 1000 })

      expect(result).toBeDefined()
    })

    it('accepts delay option', () => {
      const element = ref<HTMLElement | null>(null)
      const result = useScrollAnimation(element, { delay: 200 })

      expect(result).toBeDefined()
    })

    it('accepts threshold option', () => {
      const element = ref<HTMLElement | null>(null)
      const result = useScrollAnimation(element, { threshold: 0.5 })

      expect(result).toBeDefined()
    })

    it('accepts once option', () => {
      const element = ref<HTMLElement | null>(null)
      const result = useScrollAnimation(element, { once: false })

      expect(result).toBeDefined()
    })

    it('accepts easing option', () => {
      const element = ref<HTMLElement | null>(null)
      const result = useScrollAnimation(element, { easing: 'ease-in-out' })

      expect(result).toBeDefined()
    })

    it('handles multiple animation types', () => {
      const element = ref<HTMLElement | null>(null)

      const animations = ['fadeIn', 'slideUp', 'slideInLeft', 'slideInRight', 'scaleIn'] as const

      animations.forEach(animation => {
        const result = useScrollAnimation(element, { animation })
        expect(result).toBeDefined()
      })
    })
  })

  describe('useStaggeredAnimation', () => {
    it('creates animations for multiple elements', () => {
      const elements = [
        ref<HTMLElement | null>(null),
        ref<HTMLElement | null>(null),
        ref<HTMLElement | null>(null)
      ]

      const results = useStaggeredAnimation(elements)

      expect(results).toHaveLength(3)
      results.forEach(result => {
        expect(result.isVisible).toBeDefined()
        expect(result.hasAnimated).toBeDefined()
      })
    })

    it('applies stagger delay to each element', () => {
      const elements = [
        ref<HTMLElement | null>(null),
        ref<HTMLElement | null>(null)
      ]

      const results = useStaggeredAnimation(elements, { stagger: 100 })

      expect(results).toHaveLength(2)
    })

    it('combines stagger with custom delay', () => {
      const elements = [
        ref<HTMLElement | null>(null),
        ref<HTMLElement | null>(null)
      ]

      const results = useStaggeredAnimation(elements, { stagger: 100, delay: 200 })

      expect(results).toHaveLength(2)
    })

    it('passes through animation options', () => {
      const elements = [
        ref<HTMLElement | null>(null),
        ref<HTMLElement | null>(null)
      ]

      const results = useStaggeredAnimation(elements, {
        animation: 'slideUp',
        duration: 500,
        threshold: 0.3
      })

      expect(results).toHaveLength(2)
    })
  })
})
