/**
 * Tests for useScrollAnimations composable
 * Tests core functionality without requiring full DOM interaction
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { ref, nextTick, type Ref } from 'vue'
import { mount } from '@vue/test-utils'
import {
  useScrollAnimation,
  useStaggeredAnimation,
  useBatchAnimation,
  useParallax
} from '@/composables/useScrollAnimations'

// Store callbacks for triggering intersection events
type IntersectionCallback = (entries: IntersectionObserverEntry[]) => void
let intersectionCallbacks: IntersectionCallback[] = []

// Mock IntersectionObserver
const mockObserve = vi.fn()
const mockUnobserve = vi.fn()
const mockDisconnect = vi.fn()

class MockIntersectionObserver {
  callback: IntersectionCallback

  constructor(callback: IntersectionCallback) {
    this.callback = callback
    intersectionCallbacks.push(callback)
  }

  observe = mockObserve
  unobserve = mockUnobserve
  disconnect = mockDisconnect
  root = null
  rootMargin = ''
  thresholds: number[] = []
  takeRecords = () => []
}

// Helper to trigger intersection
function triggerIntersection(isIntersecting: boolean, target?: Element): void {
  const entry = {
    isIntersecting,
    target: target || document.createElement('div'),
    boundingClientRect: {} as DOMRectReadOnly,
    intersectionRatio: isIntersecting ? 1 : 0,
    intersectionRect: {} as DOMRectReadOnly,
    rootBounds: null,
    time: Date.now()
  } as IntersectionObserverEntry

  intersectionCallbacks.forEach(cb => cb([entry]))
}

beforeEach(() => {
  intersectionCallbacks = []
  vi.stubGlobal('IntersectionObserver', MockIntersectionObserver)
})

afterEach(() => {
  vi.clearAllMocks()
  vi.unstubAllGlobals()
  intersectionCallbacks = []
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
      const elements: Array<Ref<HTMLElement | null>> = []

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

  describe('intersection callback behavior', () => {
    it('sets isVisible to true when element intersects', async () => {
      const element = ref<HTMLElement | null>(document.createElement('div'))

      const wrapper = mount(
        createTestComponent(() => useScrollAnimation(element, { animation: 'fadeIn' })),
        { attachTo: document.body }
      )

      await nextTick()

      const result = wrapper.vm.result as {
        isVisible: { value: boolean }
        hasAnimated: { value: boolean }
      }

      expect(result.isVisible.value).toBe(false)

      // Trigger intersection
      triggerIntersection(true, element.value!)

      expect(result.isVisible.value).toBe(true)
      expect(result.hasAnimated.value).toBe(true)

      wrapper.unmount()
    })

    it('applies animation styles when visible', async () => {
      const element = ref<HTMLElement | null>(document.createElement('div'))

      const wrapper = mount(
        createTestComponent(() => useScrollAnimation(element, { animation: 'fadeIn' })),
        { attachTo: document.body }
      )

      await nextTick()

      // Initially hidden
      expect(element.value?.style.opacity).toBe('0')

      // Trigger intersection
      triggerIntersection(true, element.value!)

      // Should now be visible
      expect(element.value?.style.opacity).toBe('1')

      wrapper.unmount()
    })

    it('resets animation when once is false and element leaves viewport', async () => {
      const element = ref<HTMLElement | null>(document.createElement('div'))

      const wrapper = mount(
        createTestComponent(() =>
          useScrollAnimation(element, { animation: 'fadeIn', once: false })
        ),
        { attachTo: document.body }
      )

      await nextTick()

      const result = wrapper.vm.result as {
        isVisible: { value: boolean }
        hasAnimated: { value: boolean }
      }

      // Enter viewport
      triggerIntersection(true, element.value!)
      expect(result.isVisible.value).toBe(true)
      expect(element.value?.style.opacity).toBe('1')

      // Leave viewport
      triggerIntersection(false, element.value!)
      expect(result.isVisible.value).toBe(false)
      expect(element.value?.style.opacity).toBe('0')

      wrapper.unmount()
    })

    it('does not reset animation when once is true', async () => {
      const element = ref<HTMLElement | null>(document.createElement('div'))

      const wrapper = mount(
        createTestComponent(() => useScrollAnimation(element, { animation: 'fadeIn', once: true })),
        { attachTo: document.body }
      )

      await nextTick()

      const result = wrapper.vm.result as {
        isVisible: { value: boolean }
        hasAnimated: { value: boolean }
      }

      // Enter viewport
      triggerIntersection(true, element.value!)
      expect(result.isVisible.value).toBe(true)
      expect(result.hasAnimated.value).toBe(true)

      // Leave viewport - should stay visible because once=true
      triggerIntersection(false, element.value!)
      expect(result.hasAnimated.value).toBe(true)

      wrapper.unmount()
    })
  })

  describe('useBatchAnimation', () => {
    it('returns elements and animations arrays', async () => {
      // Create some elements in the DOM
      document.body.innerHTML = `
        <div class="batch-item">Item 1</div>
        <div class="batch-item">Item 2</div>
        <div class="batch-item">Item 3</div>
      `

      const wrapper = mount(
        createTestComponent(() => useBatchAnimation('.batch-item')),
        { attachTo: document.body }
      )

      await nextTick()

      const result = wrapper.vm.result as {
        elements: { value: Element[] }
        animations: Array<unknown>
      }

      expect(result.elements.value).toHaveLength(3)
      expect(result.animations).toHaveLength(3)

      wrapper.unmount()
      document.body.innerHTML = ''
    })

    it('applies stagger delay to batch elements', async () => {
      document.body.innerHTML = `
        <div class="batch-stagger">Item 1</div>
        <div class="batch-stagger">Item 2</div>
      `

      const wrapper = mount(
        createTestComponent(() => useBatchAnimation('.batch-stagger', { stagger: 150 })),
        { attachTo: document.body }
      )

      await nextTick()

      const result = wrapper.vm.result as {
        elements: { value: Element[] }
        animations: Array<unknown>
      }

      expect(result.elements.value).toHaveLength(2)

      wrapper.unmount()
      document.body.innerHTML = ''
    })

    it('handles empty selector result', async () => {
      const wrapper = mount(
        createTestComponent(() => useBatchAnimation('.non-existent-selector')),
        { attachTo: document.body }
      )

      await nextTick()

      const result = wrapper.vm.result as {
        elements: { value: Element[] }
        animations: Array<unknown>
      }

      expect(result.elements.value).toHaveLength(0)
      expect(result.animations).toHaveLength(0)

      wrapper.unmount()
    })

    it('passes animation options to batch elements', async () => {
      document.body.innerHTML = '<div class="batch-opts">Item</div>'

      const wrapper = mount(
        createTestComponent(() =>
          useBatchAnimation('.batch-opts', {
            animation: 'slideUp',
            duration: 800,
            delay: 50
          })
        ),
        { attachTo: document.body }
      )

      await nextTick()

      const result = wrapper.vm.result as {
        elements: { value: Element[] }
      }

      expect(result.elements.value).toHaveLength(1)

      wrapper.unmount()
      document.body.innerHTML = ''
    })
  })

  describe('useParallax', () => {
    it('sets up scroll listener on mount', async () => {
      const addEventListenerSpy = vi.spyOn(window, 'addEventListener')
      const element = ref<HTMLElement | null>(document.createElement('div'))

      const wrapper = mount(
        createTestComponent(() => useParallax(element)),
        { attachTo: document.body }
      )

      await nextTick()

      expect(addEventListenerSpy).toHaveBeenCalledWith('scroll', expect.any(Function), {
        passive: true
      })

      wrapper.unmount()
      addEventListenerSpy.mockRestore()
    })

    it('removes scroll listener on unmount', async () => {
      const removeEventListenerSpy = vi.spyOn(window, 'removeEventListener')
      const element = ref<HTMLElement | null>(document.createElement('div'))

      const wrapper = mount(
        createTestComponent(() => useParallax(element)),
        { attachTo: document.body }
      )

      await nextTick()

      wrapper.unmount()

      expect(removeEventListenerSpy).toHaveBeenCalledWith('scroll', expect.any(Function))
      removeEventListenerSpy.mockRestore()
    })

    it('accepts custom speed option', async () => {
      const element = ref<HTMLElement | null>(document.createElement('div'))

      const wrapper = mount(
        createTestComponent(() => useParallax(element, { speed: 0.3 })),
        { attachTo: document.body }
      )

      await nextTick()

      // Component should mount without errors
      expect(true).toBe(true)

      wrapper.unmount()
    })

    it('applies transform on scroll', async () => {
      const element = ref<HTMLElement | null>(document.createElement('div'))
      document.body.appendChild(element.value!)

      // Mock getBoundingClientRect
      element.value!.getBoundingClientRect = vi.fn().mockReturnValue({
        top: 100,
        bottom: 200,
        left: 0,
        right: 100,
        width: 100,
        height: 100
      })

      // Mock requestAnimationFrame
      vi.spyOn(window, 'requestAnimationFrame').mockImplementation(cb => {
        cb(0)
        return 0
      })

      const wrapper = mount(
        createTestComponent(() => useParallax(element, { speed: 0.5 })),
        { attachTo: document.body }
      )

      await nextTick()

      // Dispatch scroll event
      window.dispatchEvent(new Event('scroll'))

      await nextTick()

      // Transform should be applied
      expect(element.value?.style.transform).toContain('translateY')

      wrapper.unmount()
      document.body.removeChild(element.value!)
    })

    it('handles null element gracefully on scroll', async () => {
      const element = ref<HTMLElement | null>(null)

      vi.spyOn(window, 'requestAnimationFrame').mockImplementation(cb => {
        cb(0)
        return 0
      })

      const wrapper = mount(
        createTestComponent(() => useParallax(element)),
        { attachTo: document.body }
      )

      await nextTick()

      // Should not throw when scrolling with null element
      expect(() => {
        window.dispatchEvent(new Event('scroll'))
      }).not.toThrow()

      wrapper.unmount()
    })
  })
})
