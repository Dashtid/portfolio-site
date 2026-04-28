import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import AdminProjects from '@/views/admin/AdminProjects.vue'

describe('AdminProjects', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Rendering', () => {
    it('should render the admin projects container', () => {
      const wrapper = mount(AdminProjects)

      expect(wrapper.find('.admin-projects').exists()).toBe(true)
    })

    it('should display the page title', () => {
      const wrapper = mount(AdminProjects)

      expect(wrapper.find('h2').text()).toBe('Projects')
    })

    it('should display the placeholder message', () => {
      const wrapper = mount(AdminProjects)

      expect(wrapper.text()).toContain('Projects management is not wired up yet')
    })
  })
})
