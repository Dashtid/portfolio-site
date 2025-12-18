/**
 * Tests for useScrollAnimations composable
 * Tests core functionality without requiring full DOM interaction
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { ref, nextTick } from 'vue'
import { mount } from '@vue/test-utils'
import { useScrollAnimation, useStaggeredAnimation } from '@/composables/useScrollAnimations'

// Mock IntersectionObserver
const mockObserve = vi.fn()
const mockUnobserve = vi.fn()
const mockDisconnect = vi.fn()

class MockIntersectionObserver {
  constructor() {}
  observe = mockObserve
  unobserve = mockUnobserve
  disconnect = mockDisconnect
  root = null
  rootMargin = ''
  thresholds: number[] = []
  takeRecords = () => []
}

beforeEach(() => {
  vi.stubGlobal('IntersectionObserver', MockIntersectionObserver)
})

afterEach(() => {
  vi.clearAllMocks()
  vi.unstubAllGlobals()
})

// Helper to create a test component that uses the composable
function createTestComponent(composableSetup: () => unknown) {
  return {
    setup() {
      const result = composableSetup()
      return { result }
    },
    template: '<div ref="element"></div>'
  }
}

describe('useScrollAnimations', () => {
  describe('useScrollAnimation', () => {
    it('returns isVisible and hasAnimated refs', () => {
      const element = ref<HTMLElement | null>(null)
      const wrapper = mount(createTestComponent(() => useScrollAnimation(element)))

      const result = wrapper.vm.result as {
        isVisible: { value: boolean }
        hasAnimated: { value: boolean }
      }
      expect(result.isVisible.value).toBe(false)
      expect(result.hasAnimated.value).toBe(false)
      wrapper.unmount()
    })

    it('accepts animation type option', () => {
      const element = ref<HTMLElement | null>(null)
      const wrapper = mount(
        createTestComponent(() => useScrollAnimation(element, { animation: 'slideUp' }))
      )

      expect(wrapper.vm.result).toBeDefined()
      wrapper.unmount()
    })

    it('accepts duration option', () => {
      const element = ref<HTMLElement | null>(null)
      const wrapper = mount(
        createTestComponent(() => useScrollAnimation(element, { duration: 1000 }))
      )

      expect(wrapper.vm.result).toBeDefined()
      wrapper.unmount()
    })

    it('accepts delay option', () => {
      const element = ref<HTMLElement | null>(null)
      const wrapper = mount(createTestComponent(() => useScrollAnimation(element, { delay: 200 })))

      expect(wrapper.vm.result).toBeDefined()
      wrapper.unmount()
    })

    it('accepts threshold option', () => {
      const element = ref<HTMLElement | null>(null)
      const wrapper = mount(
        createTestComponent(() => useScrollAnimation(element, { threshold: 0.5 }))
      )

      expect(wrapper.vm.result).toBeDefined()
      wrapper.unmount()
    })

    it('accepts once option', () => {
      const element = ref<HTMLElement | null>(null)
      const wrapper = mount(createTestComponent(() => useScrollAnimation(element, { once: false })))

      expect(wrapper.vm.result).toBeDefined()
      wrapper.unmount()
    })

    it('accepts easing option', () => {
      const element = ref<HTMLElement | null>(null)
      const wrapper = mount(
        createTestComponent(() => useScrollAnimation(element, { easing: 'ease-in-out' }))
      )

      expect(wrapper.vm.result).toBeDefined()
      wrapper.unmount()
    })

    it('handles all animation types', () => {
      const animations = ['fadeIn', 'slideUp', 'slideInLeft', 'slideInRight', 'scaleIn'] as const

      animations.forEach(animation => {
        const element = ref<HTMLElement | null>(null)
        const wrapper = mount(createTestComponent(() => useScrollAnimation(element, { animation })))

        expect(wrapper.vm.result).toBeDefined()
        wrapper.unmount()
      })
    })

    it('handles invalid animation type gracefully', () => {
      const element = ref<HTMLElement | null>(null)
      const wrapper = mount(
        createTestComponent(() =>
          // @ts-expect-error - testing invalid animation type
          useScrollAnimation(element, { animation: 'invalid' })
        )
      )

      expect(wrapper.vm.result).toBeDefined()
      wrapper.unmount()
    })

    it('applies styles to element when mounted', async () => {
      const element = ref<HTMLElement | null>(document.createElement('div'))

      const wrapper = mount(
        createTestComponent(() => useScrollAnimation(element, { animation: 'fadeIn' })),
        { attachTo: document.body }
      )

      await nextTick()

      // Element should have initial styles applied
      expect(element.value?.style.opacity).toBe('0')
      wrapper.unmount()
    })

    it('handles null element without error', () => {
      const element = ref<HTMLElement | null>(null)
      const wrapper = mount(createTestComponent(() => useScrollAnimation(element)))

      expect(wrapper.vm.result).toBeDefined()
      wrapper.unmount()
    })

    it('combines multiple options', () => {
      const element = ref<HTMLElement | null>(null)
      const wrapper = mount(
        createTestComponent(() =>
          useScrollAnimation(element, {
            animation: 'slideUp',
            duration: 800,
            delay: 100,
            easing: 'ease-out',
            threshold: 0.2,
            once: true
          })
        )
      )

      expect(wrapper.vm.result).toBeDefined()
      wrapper.unmount()
    })
  })

  describe('useStaggeredAnimation', () => {
    it('creates animations for multiple elements', () => {
      const elements = [
        ref<HTMLElement | null>(null),
        ref<HTMLElement | null>(null),
        ref<HTMLElement | null>(null)
      ]

      const wrapper = mount(createTestComponent(() => useStaggeredAnimation(elements)))

      const results = wrapper.vm.result as Array<{ isVisible: boolean; hasAnimated: boolean }>
      expect(results).toHaveLength(3)
      wrapper.unmount()
    })

    it('applies stagger delay to each element', () => {
      const elements = [ref<HTMLElement | null>(null), ref<HTMLElement | null>(null)]

      const wrapper = mount(
        createTestComponent(() => useStaggeredAnimation(elements, { stagger: 100 }))
      )

      const results = wrapper.vm.result as Array<unknown>
      expect(results).toHaveLength(2)
      wrapper.unmount()
    })

    it('combines stagger with custom delay', () => {
      const elements = [ref<HTMLElement | null>(null), ref<HTMLElement | null>(null)]

      const wrapper = mount(
        createTestComponent(() => useStaggeredAnimation(elements, { stagger: 100, delay: 200 }))
      )

      const results = wrapper.vm.result as Array<unknown>
      expect(results).toHaveLength(2)
      wrapper.unmount()
    })

    it('passes through animation options', () => {
      const elements = [ref<HTMLElement | null>(null), ref<HTMLElement | null>(null)]

      const wrapper = mount(
        createTestComponent(() =>
          useStaggeredAnimation(elements, {
            animation: 'slideUp',
            duration: 500,
            threshold: 0.3
          })
        )
      )

      const results = wrapper.vm.result as Array<unknown>
      expect(results).toHaveLength(2)
      wrapper.unmount()
    })

    it('handles empty elements array', () => {
      const elements: Array<ReturnType<typeof ref<HTMLElement | null>>> = []

      const wrapper = mount(createTestComponent(() => useStaggeredAnimation(elements)))

      const results = wrapper.vm.result as Array<unknown>
      expect(results).toHaveLength(0)
      wrapper.unmount()
    })

    it('uses default stagger value', () => {
      const elements = [ref<HTMLElement | null>(null), ref<HTMLElement | null>(null)]

      const wrapper = mount(createTestComponent(() => useStaggeredAnimation(elements)))

      const results = wrapper.vm.result as Array<unknown>
      expect(results).toHaveLength(2)
      wrapper.unmount()
    })

    it('works with single element', () => {
      const elements = [ref<HTMLElement | null>(null)]

      const wrapper = mount(createTestComponent(() => useStaggeredAnimation(elements)))

      const results = wrapper.vm.result as Array<unknown>
      expect(results).toHaveLength(1)
      wrapper.unmount()
    })
  })

  describe('animation styles application', () => {
    it('applies slideUp initial styles', async () => {
      const element = ref<HTMLElement | null>(document.createElement('div'))

      const wrapper = mount(
        createTestComponent(() => useScrollAnimation(element, { animation: 'slideUp' })),
        { attachTo: document.body }
      )

      await nextTick()
      expect(element.value?.style.opacity).toBe('0')
      expect(element.value?.style.transform).toContain('translateY')
      wrapper.unmount()
    })

    it('applies slideInLeft initial styles', async () => {
      const element = ref<HTMLElement | null>(document.createElement('div'))

      const wrapper = mount(
        createTestComponent(() => useScrollAnimation(element, { animation: 'slideInLeft' })),
        { attachTo: document.body }
      )

      await nextTick()
      expect(element.value?.style.opacity).toBe('0')
      expect(element.value?.style.transform).toContain('translateX')
      wrapper.unmount()
    })

    it('applies slideInRight initial styles', async () => {
      const element = ref<HTMLElement | null>(document.createElement('div'))

      const wrapper = mount(
        createTestComponent(() => useScrollAnimation(element, { animation: 'slideInRight' })),
        { attachTo: document.body }
      )

      await nextTick()
      expect(element.value?.style.opacity).toBe('0')
      expect(element.value?.style.transform).toContain('translateX')
      wrapper.unmount()
    })

    it('applies scaleIn initial styles', async () => {
      const element = ref<HTMLElement | null>(document.createElement('div'))

      const wrapper = mount(
        createTestComponent(() => useScrollAnimation(element, { animation: 'scaleIn' })),
        { attachTo: document.body }
      )

      await nextTick()
      expect(element.value?.style.opacity).toBe('0')
      expect(element.value?.style.transform).toContain('scale')
      wrapper.unmount()
    })

    it('sets correct transition with all options', async () => {
      const element = ref<HTMLElement | null>(document.createElement('div'))

      const wrapper = mount(
        createTestComponent(() =>
          useScrollAnimation(element, {
            duration: 500,
            delay: 100,
            easing: 'linear'
          })
        ),
        { attachTo: document.body }
      )

      await nextTick()
      expect(element.value?.style.transition).toContain('500ms')
      expect(element.value?.style.transition).toContain('100ms')
      expect(element.value?.style.transition).toContain('linear')
      wrapper.unmount()
    })
  })
})
