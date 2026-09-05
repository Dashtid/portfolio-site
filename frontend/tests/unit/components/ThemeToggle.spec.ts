import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import ThemeToggle from '@/components/ThemeToggle.vue'
import type { ComponentPublicInstance } from 'vue'

describe('ThemeToggle', () => {
  let wrapper: VueWrapper<ComponentPublicInstance>

  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear()

    // Reset DOM theme attribute
    document.documentElement.removeAttribute('data-theme')
  })

  it('renders correctly', () => {
    wrapper = mount(ThemeToggle)
    expect(wrapper.exists()).toBe(true)
    expect(wrapper.find('button').exists()).toBe(true)
  })

  it('renders BOTH icons regardless of theme — the hydration-safety contract', async () => {
    // The SSG pass bakes the light page; a dark-preference client must
    // hydrate against identical markup. That only holds if neither icon is
    // behind a v-if on isDark: CSS ([data-theme] rules) picks the visible
    // one instead. If this test starts failing because an icon left the
    // DOM, the "Hydration completed but contains mismatches" console error
    // is back for every dark-mode visitor.
    wrapper = mount(ThemeToggle)
    expect(wrapper.find('svg.icon-sun').exists()).toBe(true)
    expect(wrapper.find('svg.icon-moon').exists()).toBe(true)

    await wrapper.find('button').trigger('click')
    await wrapper.vm.$nextTick()
    expect(wrapper.find('svg.icon-sun').exists()).toBe(true)
    expect(wrapper.find('svg.icon-moon').exists()).toBe(true)
  })

  it('icons are decorative — hidden from assistive tech behind the button label', () => {
    wrapper = mount(ThemeToggle)
    wrapper.findAll('svg').forEach(svg => {
      expect(svg.attributes('aria-hidden')).toBe('true')
    })
  })

  it('has proper ARIA label', () => {
    wrapper = mount(ThemeToggle)
    const button = wrapper.find('button')
    expect(button.attributes('aria-label')).toBeDefined()
    expect(button.attributes('title')).toBeDefined()
  })

  it('toggles theme on click', async () => {
    wrapper = mount(ThemeToggle)
    const button = wrapper.find('button')

    // Click to toggle
    await button.trigger('click')
    await wrapper.vm.$nextTick()

    // Check localStorage was updated
    expect(localStorage.getItem('portfolio-theme')).toBeTruthy()
  })

  it('applies theme to html element', async () => {
    wrapper = mount(ThemeToggle)
    const button = wrapper.find('button')

    await button.trigger('click')
    await wrapper.vm.$nextTick()

    // HTML element should have data-theme attribute
    const htmlElement = document.documentElement
    expect(htmlElement.hasAttribute('data-theme')).toBe(true)
  })

  it('has hover state', () => {
    wrapper = mount(ThemeToggle)
    const button = wrapper.find('button')

    // Check that button has the theme-toggle class for hover styles
    expect(button.classes()).toContain('theme-toggle')
  })

  it('is keyboard accessible', () => {
    wrapper = mount(ThemeToggle)
    const button = wrapper.find('button')

    // Button should be focusable
    expect(button.element.tagName).toBe('BUTTON')
    expect(button.attributes('type')).toBeUndefined() // Default button type
  })

  it('dispatches custom event on theme change', async () => {
    const dispatchEventSpy = vi.spyOn(window, 'dispatchEvent')

    wrapper = mount(ThemeToggle)
    const button = wrapper.find('button')

    await button.trigger('click')
    await wrapper.vm.$nextTick()

    // Should dispatch theme-changed event
    expect(dispatchEventSpy).toHaveBeenCalled()

    dispatchEventSpy.mockRestore()
  })
})
