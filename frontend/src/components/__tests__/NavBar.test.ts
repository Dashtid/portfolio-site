import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import NavBar from '../NavBar.vue'

describe('NavBar', () => {
  let wrapper: VueWrapper

  beforeEach(() => {
    wrapper = mount(NavBar)
  })

  it('renders navigation menu', () => {
    expect(wrapper.find('nav').exists()).toBe(true)
  })

  it('contains all navigation links', () => {
    const links = wrapper.findAll('a.nav-link')
    const expectedLinks = ['Experience', 'Education', 'Projects', 'About', 'Contact']

    expect(links.length).toBeGreaterThanOrEqual(expectedLinks.length)

    expectedLinks.forEach(linkText => {
      const found = links.some(link => link.text().includes(linkText))
      expect(found).toBe(true)
    })
  })

  it('has theme toggle button', () => {
    const themeButton = wrapper.find('button[aria-label="Toggle theme"]')
    expect(themeButton.exists()).toBe(true)
  })

  it('applies sticky class on scroll', async () => {
    // Simulate scroll event
    Object.defineProperty(window, 'pageYOffset', { value: 100, writable: true })
    window.dispatchEvent(new Event('scroll'))

    await wrapper.vm.$nextTick()

    // Check if sticky class is applied
    const navbar = wrapper.find('.navbar')
    expect(navbar.classes()).toContain('sticky')
  })

  it('handles smooth scrolling on link click', async () => {
    const link = wrapper.find('a[href="#experience"]')

    // Mock scrollIntoView
    const mockScrollIntoView = vi.fn()
    vi.spyOn(document, 'getElementById').mockReturnValue({
      scrollIntoView: mockScrollIntoView
    } as unknown as HTMLElement)

    await link.trigger('click')

    expect(mockScrollIntoView).toHaveBeenCalledWith({ behavior: 'smooth' })
  })

  it('toggles theme when button is clicked', async () => {
    const themeButton = wrapper.find('button[aria-label="Toggle theme"]')
    const initialTheme = document.documentElement.getAttribute('data-theme')

    await themeButton.trigger('click')

    const newTheme = document.documentElement.getAttribute('data-theme')
    expect(newTheme).not.toBe(initialTheme)
  })
})
