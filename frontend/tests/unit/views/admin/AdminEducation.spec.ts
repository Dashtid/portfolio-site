import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, VueWrapper, flushPromises } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import { createRouter, createWebHistory, type Router } from 'vue-router'
import AdminEducation from '@/views/admin/AdminEducation.vue'
import api from '@/api/client'

// Mock the API client
vi.mock('@/api/client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn()
  }
}))

// Mock window.alert and window.confirm
const mockAlert = vi.fn()
const mockConfirm = vi.fn()
window.alert = mockAlert
window.confirm = mockConfirm

// Create router
const createTestRouter = (): Router => {
  return createRouter({
    history: createWebHistory(),
    routes: [
      { path: '/admin/education', component: { template: '<div>Education</div>' } },
      { path: '/admin/login', component: { template: '<div>Login</div>' } }
    ]
  })
}

describe('AdminEducation', () => {
  let router: Router

  const mockEducationData = [
    {
      id: '1',
      institution: 'University of Technology',
      degree: 'Master of Science',
      field_of_study: 'Computer Science',
      start_date: '2015-09-01',
      end_date: '2017-06-15',
      location: 'Stockholm, Sweden',
      description: 'Specialized in AI and Machine Learning',
      is_certification: false,
      certificate_number: '',
      order: 1
    },
    {
      id: '2',
      institution: 'AWS',
      degree: 'Solutions Architect Professional',
      field_of_study: '',
      start_date: '',
      end_date: '2023-03-15',
      location: '',
      description: '',
      is_certification: true,
      certificate_number: 'AWS-SAP-123456',
      order: 2
    },
    {
      id: '3',
      institution: 'Tech College',
      degree: 'Bachelor of Engineering',
      field_of_study: 'Software Engineering',
      start_date: '2011-09-01',
      end_date: '2015-06-15',
      location: 'Gothenburg, Sweden',
      description: '',
      is_certification: false,
      certificate_number: '',
      order: 0
    }
  ]

  const createWrapper = async (): Promise<VueWrapper> => {
    router = createTestRouter()
    await router.push('/admin/education')
    await router.isReady()

    return mount(AdminEducation, {
      global: {
        plugins: [
          createTestingPinia({
            createSpy: vi.fn,
            initialState: {
              auth: {
                user: { id: '1', username: 'admin' },
                accessToken: 'test-token',
                refreshToken: 'test-refresh'
              }
            }
          }),
          router
        ],
        stubs: {
          teleport: true
        }
      }
    })
  }

  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(api.get).mockResolvedValue({ data: mockEducationData })
  })

  describe('Rendering', () => {
    it('should render the admin education container', async () => {
      const wrapper = await createWrapper()
      await flushPromises()

      expect(wrapper.find('.admin-education').exists()).toBe(true)
    })

    it('should display the header with title and add button', async () => {
      const wrapper = await createWrapper()
      await flushPromises()

      expect(wrapper.find('.admin-header').exists()).toBe(true)
      expect(wrapper.find('h2').text()).toBe('Manage Education & Certifications')
      expect(wrapper.find('.btn-primary').text()).toContain('Add New Education')
    })

    it('should display degrees table with correct data', async () => {
      const wrapper = await createWrapper()
      await flushPromises()

      // Find degrees table (first table)
      const tables = wrapper.findAll('.table')
      expect(tables.length).toBeGreaterThan(0)

      // Check degrees section header
      expect(wrapper.text()).toContain('Degrees')
    })

    it('should display certifications table separately', async () => {
      const wrapper = await createWrapper()
      await flushPromises()

      expect(wrapper.text()).toContain('Certifications')
      expect(wrapper.text()).toContain('AWS')
      expect(wrapper.text()).toContain('Solutions Architect Professional')
    })

    it('should display empty state for degrees when none exist', async () => {
      vi.mocked(api.get).mockResolvedValue({
        data: mockEducationData.filter(e => e.is_certification)
      })

      const wrapper = await createWrapper()
      await flushPromises()

      expect(wrapper.text()).toContain('No degrees added yet')
    })

    it('should display empty state for certifications when none exist', async () => {
      vi.mocked(api.get).mockResolvedValue({
        data: mockEducationData.filter(e => !e.is_certification)
      })

      const wrapper = await createWrapper()
      await flushPromises()

      expect(wrapper.text()).toContain('No certifications added yet')
    })

    it('should format dates correctly', async () => {
      const wrapper = await createWrapper()
      await flushPromises()

      expect(wrapper.text()).toContain('Sep 2015')
      expect(wrapper.text()).toContain('Jun 2017')
    })

    it('should display "Present" for ongoing education', async () => {
      vi.mocked(api.get).mockResolvedValue({
        data: [
          {
            ...mockEducationData[0],
            end_date: null
          }
        ]
      })

      const wrapper = await createWrapper()
      await flushPromises()

      expect(wrapper.text()).toContain('Present')
    })

    it('should render edit and delete buttons for each entry', async () => {
      const wrapper = await createWrapper()
      await flushPromises()

      const editButtons = wrapper.findAll('.btn-warning')
      const deleteButtons = wrapper.findAll('.btn-danger')

      expect(editButtons.length).toBe(3) // 2 degrees + 1 certification
      expect(deleteButtons.length).toBe(3)
    })
  })

  describe('Add Form', () => {
    it('should show modal when add button is clicked', async () => {
      const wrapper = await createWrapper()
      await flushPromises()

      expect(wrapper.find('.modal-overlay').exists()).toBe(false)

      await wrapper.find('.btn-primary').trigger('click')

      expect(wrapper.find('.modal-overlay').exists()).toBe(true)
      expect(wrapper.find('h3').text()).toContain('Add')
    })

    it('should render all form fields', async () => {
      const wrapper = await createWrapper()
      await flushPromises()
      await wrapper.find('.btn-primary').trigger('click')

      expect(wrapper.find('input[type="text"]').exists()).toBe(true)
      expect(wrapper.findAll('input[type="date"]').length).toBe(2)
      expect(wrapper.find('textarea').exists()).toBe(true)
      expect(wrapper.find('input[type="checkbox"]').exists()).toBe(true)
      expect(wrapper.find('input[type="number"]').exists()).toBe(true)
    })

    it('should show certificate number field when is_certification is checked', async () => {
      const wrapper = await createWrapper()
      await flushPromises()
      await wrapper.find('.btn-primary').trigger('click')

      // Initially certificate number should not be visible
      expect(
        wrapper
          .findAll('input')
          .some(i => i.element.parentElement?.textContent?.includes('Certificate Number'))
      ).toBe(false)

      // Check the certification checkbox
      await wrapper.find('#is_certification').setValue(true)

      // Now certificate number should be visible
      const formGroups = wrapper.findAll('.form-group')
      const hasCertField = formGroups.some(fg => fg.text().includes('Certificate Number'))
      expect(hasCertField).toBe(true)
    })

    it('should close modal when cancel button is clicked', async () => {
      const wrapper = await createWrapper()
      await flushPromises()
      await wrapper.find('.btn-primary').trigger('click')

      expect(wrapper.find('.modal-overlay').exists()).toBe(true)

      await wrapper.find('.btn-secondary').trigger('click')

      expect(wrapper.find('.modal-overlay').exists()).toBe(false)
    })

    it('should close modal when clicking overlay', async () => {
      const wrapper = await createWrapper()
      await flushPromises()
      await wrapper.find('.btn-primary').trigger('click')

      await wrapper.find('.modal-overlay').trigger('click')

      expect(wrapper.find('.modal-overlay').exists()).toBe(false)
    })

    it('should submit new education data', async () => {
      vi.mocked(api.post).mockResolvedValue({ data: { id: '4' } })

      const wrapper = await createWrapper()
      await flushPromises()
      await wrapper.find('.btn-primary').trigger('click')

      // Fill in required fields
      const inputs = wrapper.findAll('.form-control')
      await inputs[0].setValue('New University') // institution
      await inputs[1].setValue('PhD') // degree

      await wrapper.find('form').trigger('submit')
      await flushPromises()

      expect(api.post).toHaveBeenCalledWith(
        '/education/',
        expect.objectContaining({
          institution: 'New University',
          degree: 'PhD'
        })
      )
    })
  })

  describe('Edit Form', () => {
    it('should show modal with populated data when edit button is clicked', async () => {
      const wrapper = await createWrapper()
      await flushPromises()

      // Click first edit button
      const editButtons = wrapper.findAll('.btn-warning')
      await editButtons[0].trigger('click')

      expect(wrapper.find('.modal-overlay').exists()).toBe(true)
      expect(wrapper.find('h3').text()).toContain('Edit')

      const inputs = wrapper.findAll('.form-control')
      expect((inputs[0].element as HTMLInputElement).value).toBeTruthy()
    })

    it('should submit updated education data', async () => {
      vi.mocked(api.put).mockResolvedValue({ data: {} })

      const wrapper = await createWrapper()
      await flushPromises()

      const editButtons = wrapper.findAll('.btn-warning')
      await editButtons[0].trigger('click')

      const inputs = wrapper.findAll('.form-control')
      await inputs[0].setValue('Updated University')

      await wrapper.find('form').trigger('submit')
      await flushPromises()

      expect(api.put).toHaveBeenCalled()
    })
  })

  describe('Delete Education', () => {
    it('should show confirmation dialog before deleting', async () => {
      mockConfirm.mockReturnValue(false)

      const wrapper = await createWrapper()
      await flushPromises()

      const deleteButtons = wrapper.findAll('.btn-danger')
      await deleteButtons[0].trigger('click')

      expect(mockConfirm).toHaveBeenCalledWith(
        'Are you sure you want to delete this education record?'
      )
      expect(api.delete).not.toHaveBeenCalled()
    })

    it('should delete education when confirmed', async () => {
      mockConfirm.mockReturnValue(true)
      vi.mocked(api.delete).mockResolvedValue({})

      const wrapper = await createWrapper()
      await flushPromises()

      const deleteButtons = wrapper.findAll('.btn-danger')
      await deleteButtons[0].trigger('click')
      await flushPromises()

      expect(api.delete).toHaveBeenCalled()
    })
  })

  describe('Error Handling', () => {
    it('should handle fetch error gracefully', async () => {
      vi.mocked(api.get).mockRejectedValue(new Error('Network error'))
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      const wrapper = await createWrapper()
      await flushPromises()

      // Component should still render
      expect(wrapper.find('.admin-education').exists()).toBe(true)
      consoleSpy.mockRestore()
    })

    it('should show error alert when save fails', async () => {
      vi.mocked(api.post).mockRejectedValue(new Error('Save failed'))
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      const wrapper = await createWrapper()
      await flushPromises()
      await wrapper.find('.btn-primary').trigger('click')

      const inputs = wrapper.findAll('.form-control')
      await inputs[0].setValue('Test')
      await inputs[1].setValue('Test')

      await wrapper.find('form').trigger('submit')
      await flushPromises()

      expect(mockAlert).toHaveBeenCalledWith('Failed to save education. Please try again.')
      consoleSpy.mockRestore()
    })

    it('should show error alert when delete fails', async () => {
      mockConfirm.mockReturnValue(true)
      vi.mocked(api.delete).mockRejectedValue(new Error('Delete failed'))
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      const wrapper = await createWrapper()
      await flushPromises()

      const deleteButtons = wrapper.findAll('.btn-danger')
      await deleteButtons[0].trigger('click')
      await flushPromises()

      expect(mockAlert).toHaveBeenCalledWith('Failed to delete education. Please try again.')
      consoleSpy.mockRestore()
    })
  })

  describe('Authentication', () => {
    it('should redirect to login if not authenticated', async () => {
      router = createTestRouter()
      await router.push('/admin/education')
      await router.isReady()

      const wrapper = mount(AdminEducation, {
        global: {
          plugins: [
            createTestingPinia({
              createSpy: vi.fn,
              initialState: {
                auth: {
                  user: null,
                  accessToken: null,
                  refreshToken: null
                }
              }
            }),
            router
          ]
        }
      })

      await flushPromises()

      expect(router.currentRoute.value.path).toBe('/admin/login')
    })
  })

  describe('Lifecycle', () => {
    it('should fetch education data on mount', async () => {
      await createWrapper()
      await flushPromises()

      expect(api.get).toHaveBeenCalledWith('/education/')
    })

    it('should refetch after successful operations', async () => {
      vi.mocked(api.post).mockResolvedValue({ data: { id: '4' } })

      const wrapper = await createWrapper()
      await flushPromises()

      vi.mocked(api.get).mockClear()

      await wrapper.find('.btn-primary').trigger('click')
      const inputs = wrapper.findAll('.form-control')
      await inputs[0].setValue('Test')
      await inputs[1].setValue('Test')
      await wrapper.find('form').trigger('submit')
      await flushPromises()

      expect(api.get).toHaveBeenCalledWith('/education/')
    })
  })
})
