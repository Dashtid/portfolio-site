import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import AdminLogin from '@/views/admin/AdminLogin.vue'
import { useAuthStore } from '@/stores/auth'

// The component reads useRoute().query (the ?oauth=denied cancel notice);
// specs mount without a router, so serve a controllable route stub.
const mockRoute = { query: {} as Record<string, string> }
vi.mock('vue-router', () => ({
  useRoute: () => mockRoute
}))

describe('AdminLogin', () => {
  const createWrapper = (options = {}) => {
    return mount(AdminLogin, {
      global: {
        plugins: [
          createTestingPinia({
            createSpy: vi.fn
          })
        ]
      },
      ...options
    })
  }

  beforeEach(() => {
    vi.clearAllMocks()
    mockRoute.query = {}
  })

  describe('OAuth deny notice', () => {
    it('is hidden without the oauth=denied query param', () => {
      const wrapper = createWrapper()
      expect(wrapper.find('.login-denied').exists()).toBe(false)
    })

    it('shows the cancelled message when oauth=denied is present', () => {
      mockRoute.query = { oauth: 'denied' }
      const wrapper = createWrapper()

      const notice = wrapper.find('.login-denied')
      expect(notice.exists()).toBe(true)
      expect(notice.text()).toContain('cancelled')
    })
  })

  describe('Rendering', () => {
    it('should render the login container', () => {
      const wrapper = createWrapper()

      expect(wrapper.find('.admin-login').exists()).toBe(true)
      expect(wrapper.find('.login-container').exists()).toBe(true)
      expect(wrapper.find('.login-card').exists()).toBe(true)
    })

    it('should display the login title', () => {
      const wrapper = createWrapper()

      const title = wrapper.find('.login-title')
      expect(title.exists()).toBe(true)
      expect(title.text()).toBe('Admin Login')
    })

    it('should display the login subtitle', () => {
      const wrapper = createWrapper()

      const subtitle = wrapper.find('.login-subtitle')
      expect(subtitle.exists()).toBe(true)
      expect(subtitle.text()).toContain('Sign in with your GitHub account')
    })

    it('should render the GitHub login button', () => {
      const wrapper = createWrapper()

      const button = wrapper.find('.github-login-button')
      expect(button.exists()).toBe(true)
      expect(button.text()).toContain('Sign in with GitHub')
    })

    it('should display the login note', () => {
      const wrapper = createWrapper()

      const note = wrapper.find('.note-text')
      expect(note.exists()).toBe(true)
      expect(note.text()).toContain('Only the authorized admin can sign in')
    })

    it('should render the GitHub icon in the button', () => {
      const wrapper = createWrapper()

      const icon = wrapper.find('.github-icon')
      expect(icon.exists()).toBe(true)
    })
  })

  describe('Interactions', () => {
    it('should call loginWithGitHub when button is clicked', async () => {
      const wrapper = createWrapper()
      const authStore = useAuthStore()

      const button = wrapper.find('.github-login-button')
      await button.trigger('click')

      expect(authStore.loginWithGitHub).toHaveBeenCalled()
    })
  })

  describe('Accessibility', () => {
    it('should have proper button element', () => {
      const wrapper = createWrapper()

      const button = wrapper.find('.github-login-button')
      expect(button.element.tagName).toBe('BUTTON')
    })
  })
})
