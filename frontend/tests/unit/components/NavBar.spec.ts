import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import { createRouter, createMemoryHistory, Router } from 'vue-router'
import NavBar from '@/components/NavBar.vue'
import type { ComponentPublicInstance } from 'vue'

interface NavBarInstance extends ComponentPublicInstance {
  scrolled: boolean
}

// Mock ThemeToggle component
vi.mock('@/components/ThemeToggle.vue', () => ({
  default: {
    name: 'ThemeToggle',
    template: '<button class="theme-toggle-mock">Toggle</button>'
  }
}))

describe('NavBar', () => {
  let wrapper: VueWrapper<NavBarInstance>
  let router: Router

  beforeEach(async () => {
    // Create a mock router
    router = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: '/', component: { template: '<div>Home</div>' } }]
    })

    await router.push('/')
    await router.isReady()
  })

  it('renders correctly', () => {
    wrapper = mount(NavBar, {
      global: {
        plugins: [router]
      }
    }) as VueWrapper<NavBarInstance>
    expect(wrapper.exists()).toBe(true)
  })

  it('displays brand logo and name', () => {
    wrapper = mount(NavBar, {
      global: {
        plugins: [router]
      }
    }) as VueWrapper<NavBarInstance>

    const brand = wrapper.find('.navbar-brand')
    expect(brand.exists()).toBe(true)
    expect(brand.text()).toContain('David Dashti')

    const logo = brand.find('img')
    expect(logo.exists()).toBe(true)
    expect(logo.attributes('alt')).toBe('David Dashti Logo')
  })

  it('renders navigation items', () => {
    wrapper = mount(NavBar, {
      global: {
        plugins: [router]
      }
    }) as VueWrapper<NavBarInstance>

    const navItems = wrapper.findAll('.nav-link')
    expect(navItems.length).toBeGreaterThan(0)

    // Check for expected sections
    const navText = wrapper.text()
    expect(navText).toContain('Home')
    expect(navText).toContain('Experience')
    expect(navText).toContain('Education')
    expect(navText).toContain('Projects')
    expect(navText).toContain('About')
    expect(navText).toContain('Contact')
  })

  it('renders theme toggle component', () => {
    wrapper = mount(NavBar, {
      global: {
        plugins: [router]
      }
    }) as VueWrapper<NavBarInstance>

    // Check for mocked ThemeToggle component
    expect(wrapper.find('.theme-toggle-mock').exists()).toBe(true)
  })

  it('has responsive toggle button', () => {
    wrapper = mount(NavBar, {
      global: {
        plugins: [router]
      }
    }) as VueWrapper<NavBarInstance>

    const toggler = wrapper.find('.navbar-toggler')
    expect(toggler.exists()).toBe(true)
    expect(toggler.attributes('aria-label')).toBeDefined()
  })

  it('nav links are accessible', () => {
    wrapper = mount(NavBar, {
      global: {
        plugins: [router]
      }
    }) as VueWrapper<NavBarInstance>

    const navLinks = wrapper.findAll('.nav-link')
    navLinks.forEach(link => {
      expect(link.attributes('href')).toBeDefined()
      expect(link.attributes('aria-label')).toBeDefined()
    })
  })

  it('applies navbar-scrolled class on scroll', async () => {
    wrapper = mount(NavBar, {
      global: {
        plugins: [router]
      }
    }) as VueWrapper<NavBarInstance>

    // Initially not scrolled
    expect(wrapper.vm.scrolled).toBe(false)

    // Simulate scroll
    Object.defineProperty(window, 'scrollY', { value: 100, writable: true })
    window.dispatchEvent(new Event('scroll'))

    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 50))

    // Should update scrolled state
    expect(wrapper.vm.scrolled).toBe(true)
  })

  it('has semantic navigation role', () => {
    wrapper = mount(NavBar, {
      global: {
        plugins: [router]
      }
    }) as VueWrapper<NavBarInstance>

    const nav = wrapper.find('nav')
    expect(nav.attributes('role')).toBe('navigation')
    expect(nav.attributes('aria-label')).toBeDefined()
  })
})
