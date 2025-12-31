import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import { createRouter, createMemoryHistory, Router } from 'vue-router'
import { nextTick } from 'vue'
import NavBar from '@/components/NavBar.vue'
import type { ComponentPublicInstance } from 'vue'

interface NavBarInstance extends ComponentPublicInstance {
  scrolled: boolean
  activeSection: string
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

    // Reset window.scrollY
    Object.defineProperty(window, 'scrollY', { value: 0, writable: true })
    Object.defineProperty(window, 'pageYOffset', { value: 0, writable: true })
  })

  afterEach(() => {
    if (wrapper) {
      wrapper.unmount()
    }
    vi.clearAllMocks()
  })

  it('renders correctly', () => {
    wrapper = mount(NavBar, {
      global: {
        plugins: [router]
      }
    }) as VueWrapper<NavBarInstance>
    expect(wrapper.exists()).toBe(true)
  })

  it('displays brand name', () => {
    wrapper = mount(NavBar, {
      global: {
        plugins: [router]
      }
    }) as VueWrapper<NavBarInstance>

    const brand = wrapper.find('.navbar-brand')
    expect(brand.exists()).toBe(true)
    expect(brand.text()).toContain('David Dashti')
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

  it('does not apply navbar-scrolled when scroll is less than 50', async () => {
    wrapper = mount(NavBar, {
      global: {
        plugins: [router]
      }
    }) as VueWrapper<NavBarInstance>

    // Simulate small scroll
    Object.defineProperty(window, 'scrollY', { value: 30, writable: true })
    window.dispatchEvent(new Event('scroll'))

    await wrapper.vm.$nextTick()
    await new Promise(resolve => setTimeout(resolve, 50))

    // Should not update scrolled state
    expect(wrapper.vm.scrolled).toBe(false)
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

  describe('scrollToSection', () => {
    it('scrolls to section when nav link is clicked', async () => {
      // Create mock element
      const mockElement = document.createElement('div')
      mockElement.id = 'experience'
      mockElement.getBoundingClientRect = vi.fn().mockReturnValue({ top: 500 })
      document.body.appendChild(mockElement)

      // Mock window.scrollTo
      const scrollToSpy = vi.spyOn(window, 'scrollTo').mockImplementation(() => {})

      wrapper = mount(NavBar, {
        global: {
          plugins: [router]
        },
        attachTo: document.body
      }) as VueWrapper<NavBarInstance>

      // Click on experience link
      const experienceLink = wrapper.find('[data-testid="nav-link-experience"]')
      await experienceLink.trigger('click')

      expect(scrollToSpy).toHaveBeenCalledWith({
        top: expect.any(Number),
        behavior: 'smooth'
      })

      // Cleanup
      document.body.removeChild(mockElement)
      scrollToSpy.mockRestore()
    })

    it('updates activeSection when nav link is clicked', async () => {
      // Create mock element
      const mockElement = document.createElement('div')
      mockElement.id = 'projects'
      mockElement.getBoundingClientRect = vi.fn().mockReturnValue({ top: 800 })
      document.body.appendChild(mockElement)

      vi.spyOn(window, 'scrollTo').mockImplementation(() => {})

      wrapper = mount(NavBar, {
        global: {
          plugins: [router]
        },
        attachTo: document.body
      }) as VueWrapper<NavBarInstance>

      // Click on projects link
      const projectsLink = wrapper.find('[data-testid="nav-link-projects"]')
      await projectsLink.trigger('click')

      expect(wrapper.vm.activeSection).toBe('projects')

      // Cleanup
      document.body.removeChild(mockElement)
    })

    it('does not scroll when element does not exist', async () => {
      const scrollToSpy = vi.spyOn(window, 'scrollTo').mockImplementation(() => {})

      wrapper = mount(NavBar, {
        global: {
          plugins: [router]
        }
      }) as VueWrapper<NavBarInstance>

      // Click on link for non-existent section
      const heroLink = wrapper.find('[data-testid="nav-link-hero"]')
      await heroLink.trigger('click')

      // scrollTo should not be called if element doesn't exist
      // Note: The test env doesn't have the actual sections, so this tests the guard clause
      expect(scrollToSpy).not.toHaveBeenCalled()

      scrollToSpy.mockRestore()
    })

    it('closes mobile menu when link is clicked', async () => {
      // Create section element
      const mockSection = document.createElement('div')
      mockSection.id = 'education'
      mockSection.getBoundingClientRect = vi.fn().mockReturnValue({ top: 600 })
      document.body.appendChild(mockSection)

      // Create navbar-collapse element with 'show' class (simulating open mobile menu)
      const mockNavbarCollapse = document.createElement('div')
      mockNavbarCollapse.className = 'navbar-collapse show'
      document.body.appendChild(mockNavbarCollapse)

      vi.spyOn(window, 'scrollTo').mockImplementation(() => {})

      wrapper = mount(NavBar, {
        global: {
          plugins: [router]
        },
        attachTo: document.body
      }) as VueWrapper<NavBarInstance>

      // Click on education link
      const educationLink = wrapper.find('[data-testid="nav-link-education"]')
      await educationLink.trigger('click')

      // The 'show' class should be removed
      expect(mockNavbarCollapse.classList.contains('show')).toBe(false)

      // Cleanup
      document.body.removeChild(mockSection)
      document.body.removeChild(mockNavbarCollapse)
    })
  })

  describe('handleScroll - active section detection', () => {
    it('updates activeSection based on scroll position', async () => {
      // Create mock sections
      const sections = ['hero', 'experience', 'education', 'projects', 'about']
      const mockElements: HTMLElement[] = []

      sections.forEach((id, index) => {
        const el = document.createElement('div')
        el.id = id
        Object.defineProperty(el, 'offsetTop', { value: index * 500 })
        Object.defineProperty(el, 'offsetHeight', { value: 400 })
        document.body.appendChild(el)
        mockElements.push(el)
      })

      wrapper = mount(NavBar, {
        global: {
          plugins: [router]
        },
        attachTo: document.body
      }) as VueWrapper<NavBarInstance>

      // Simulate scroll to experience section
      Object.defineProperty(window, 'scrollY', { value: 550, writable: true })
      window.dispatchEvent(new Event('scroll'))

      await nextTick()
      await new Promise(resolve => setTimeout(resolve, 50))

      expect(wrapper.vm.activeSection).toBe('experience')

      // Cleanup
      mockElements.forEach(el => document.body.removeChild(el))
    })

    it('handles missing section elements gracefully', async () => {
      wrapper = mount(NavBar, {
        global: {
          plugins: [router]
        }
      }) as VueWrapper<NavBarInstance>

      // Simulate scroll when no sections exist
      Object.defineProperty(window, 'scrollY', { value: 200, writable: true })
      window.dispatchEvent(new Event('scroll'))

      await nextTick()
      await new Promise(resolve => setTimeout(resolve, 50))

      // Should not throw and activeSection should remain at default
      expect(wrapper.vm.activeSection).toBe('hero')
    })
  })

  describe('active state styling', () => {
    it('applies active class to current section link', async () => {
      wrapper = mount(NavBar, {
        global: {
          plugins: [router]
        }
      }) as VueWrapper<NavBarInstance>

      // Default active section is 'hero'
      const heroLink = wrapper.find('[data-testid="nav-link-hero"]')
      expect(heroLink.classes()).toContain('active')
    })

    it('sets aria-current on active link', async () => {
      wrapper = mount(NavBar, {
        global: {
          plugins: [router]
        }
      }) as VueWrapper<NavBarInstance>

      const heroLink = wrapper.find('[data-testid="nav-link-hero"]')
      expect(heroLink.attributes('aria-current')).toBe('page')
    })

    it('does not set aria-current on inactive links', async () => {
      wrapper = mount(NavBar, {
        global: {
          plugins: [router]
        }
      }) as VueWrapper<NavBarInstance>

      const experienceLink = wrapper.find('[data-testid="nav-link-experience"]')
      expect(experienceLink.attributes('aria-current')).toBeUndefined()
    })
  })

  describe('mobile menu toggle', () => {
    it('has correct aria attributes on mobile toggle', () => {
      wrapper = mount(NavBar, {
        global: {
          plugins: [router]
        }
      }) as VueWrapper<NavBarInstance>

      const toggleButton = wrapper.find('[data-testid="mobile-menu-toggle"]')
      expect(toggleButton.attributes('aria-controls')).toBe('navbarNav')
      expect(toggleButton.attributes('aria-expanded')).toBe('false')
      expect(toggleButton.attributes('aria-label')).toBe('Toggle navigation menu')
    })
  })

  describe('brand link', () => {
    it('scrolls to hero section when brand is clicked', async () => {
      const mockElement = document.createElement('div')
      mockElement.id = 'hero'
      mockElement.getBoundingClientRect = vi.fn().mockReturnValue({ top: 0 })
      document.body.appendChild(mockElement)

      const scrollToSpy = vi.spyOn(window, 'scrollTo').mockImplementation(() => {})

      wrapper = mount(NavBar, {
        global: {
          plugins: [router]
        },
        attachTo: document.body
      }) as VueWrapper<NavBarInstance>

      const brand = wrapper.find('.navbar-brand')
      await brand.trigger('click')

      expect(scrollToSpy).toHaveBeenCalled()

      document.body.removeChild(mockElement)
      scrollToSpy.mockRestore()
    })
  })

  describe('cleanup', () => {
    it('removes scroll listener on unmount', async () => {
      const removeEventListenerSpy = vi.spyOn(window, 'removeEventListener')

      wrapper = mount(NavBar, {
        global: {
          plugins: [router]
        }
      }) as VueWrapper<NavBarInstance>

      wrapper.unmount()

      expect(removeEventListenerSpy).toHaveBeenCalledWith('scroll', expect.any(Function))

      removeEventListenerSpy.mockRestore()
    })
  })
})
