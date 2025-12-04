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

  it('shows moon icon in light mode', () => {
    wrapper = mount(ThemeToggle)
    const svg = wrapper.find('svg')
    expect(svg.exists()).toBe(true)
    // Moon icon has a path element with specific d attribute
    expect(svg.find('path').exists()).toBe(true)
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
