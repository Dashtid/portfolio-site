import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, VueWrapper, flushPromises } from '@vue/test-utils'
import AdminCompanies from '@/views/admin/AdminCompanies.vue'
import apiClient from '@/api/client'

// Mock the API client
vi.mock('@/api/client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}))

// Mock window.alert and window.confirm
const mockAlert = vi.fn()
const mockConfirm = vi.fn()
window.alert = mockAlert
window.confirm = mockConfirm

describe('AdminCompanies', () => {
  const mockCompanies = [
    {
      id: '1',
      name: 'Company A',
      title: 'Senior Developer',
      start_date: '2020-01-15',
      end_date: '2022-06-30',
      location: 'Stockholm, Sweden',
      description: 'Worked on various projects',
      technologies: ['Python', 'FastAPI'],
      order_index: 1,
    },
    {
      id: '2',
      name: 'Company B',
      title: 'Tech Lead',
      start_date: '2022-07-01',
      end_date: null,
      location: 'Remote',
      description: 'Leading a team',
      technologies: ['Vue.js', 'TypeScript'],
      order_index: 2,
    },
  ]

  const createWrapper = (): VueWrapper => {
    return mount(AdminCompanies, {
      global: {
        stubs: {
          teleport: true,
        },
      },
    })
  }

  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(apiClient.get).mockResolvedValue({ data: mockCompanies })
  })

  describe('Rendering', () => {
    it('should render the admin companies container', async () => {
      const wrapper = createWrapper()
      await flushPromises()

      expect(wrapper.find('.admin-companies').exists()).toBe(true)
    })

    it('should display the page header with title and add button', async () => {
      const wrapper = createWrapper()
      await flushPromises()

      expect(wrapper.find('.page-header').exists()).toBe(true)
      expect(wrapper.find('.page-title').text()).toBe('Manage Experience')
      expect(wrapper.find('.add-button').exists()).toBe(true)
      expect(wrapper.find('.add-button').text()).toContain('Add Company')
    })

    it('should display loading state while fetching', async () => {
      // Create a promise that never resolves to keep loading state
      vi.mocked(apiClient.get).mockImplementation(
        () => new Promise(() => {})
      )

      const wrapper = createWrapper()
      // Need to wait for nextTick to let Vue render the loading state
      await wrapper.vm.$nextTick()

      expect(wrapper.find('.loading-state').exists()).toBe(true)
      expect(wrapper.find('.loading-state').text()).toContain('Loading companies')
    })

    it('should display empty state when no companies', async () => {
      vi.mocked(apiClient.get).mockResolvedValue({ data: [] })

      const wrapper = createWrapper()
      await flushPromises()

      expect(wrapper.find('.empty-state').exists()).toBe(true)
      expect(wrapper.find('.empty-state').text()).toContain('No companies added yet')
    })

    it('should display company cards when data is loaded', async () => {
      const wrapper = createWrapper()
      await flushPromises()

      const companyCards = wrapper.findAll('.company-card')
      expect(companyCards.length).toBe(2)
    })

    it('should display company information correctly', async () => {
      const wrapper = createWrapper()
      await flushPromises()

      const firstCard = wrapper.findAll('.company-card')[0]
      expect(firstCard.find('.company-name').text()).toBe('Company A')
      expect(firstCard.find('.company-title').text()).toBe('Senior Developer')
      expect(firstCard.find('.company-location').text()).toBe('Stockholm, Sweden')
      expect(firstCard.find('.company-description').text()).toBe('Worked on various projects')
    })

    it('should format dates correctly', async () => {
      const wrapper = createWrapper()
      await flushPromises()

      const firstCard = wrapper.findAll('.company-card')[0]
      const duration = firstCard.find('.company-duration').text()
      expect(duration).toContain('Jan 2020')
      expect(duration).toContain('Jun 2022')
    })

    it('should display "Present" for current positions', async () => {
      const wrapper = createWrapper()
      await flushPromises()

      const secondCard = wrapper.findAll('.company-card')[1]
      const duration = secondCard.find('.company-duration').text()
      expect(duration).toContain('Present')
    })

    it('should render edit and delete buttons for each company', async () => {
      const wrapper = createWrapper()
      await flushPromises()

      const firstCard = wrapper.findAll('.company-card')[0]
      expect(firstCard.find('.edit-btn').exists()).toBe(true)
      expect(firstCard.find('.delete-btn').exists()).toBe(true)
    })
  })

  describe('Add Form', () => {
    it('should show modal when add button is clicked', async () => {
      const wrapper = createWrapper()
      await flushPromises()

      expect(wrapper.find('.modal-overlay').exists()).toBe(false)

      await wrapper.find('.add-button').trigger('click')

      expect(wrapper.find('.modal-overlay').exists()).toBe(true)
      expect(wrapper.find('.modal-title').text()).toBe('Add New Company')
    })

    it('should render all form fields', async () => {
      const wrapper = createWrapper()
      await flushPromises()
      await wrapper.find('.add-button').trigger('click')

      expect(wrapper.find('#name').exists()).toBe(true)
      expect(wrapper.find('#title').exists()).toBe(true)
      expect(wrapper.find('#start_date').exists()).toBe(true)
      expect(wrapper.find('#end_date').exists()).toBe(true)
      expect(wrapper.find('#location').exists()).toBe(true)
      expect(wrapper.find('#description').exists()).toBe(true)
      expect(wrapper.find('#technologies').exists()).toBe(true)
      expect(wrapper.find('#order_index').exists()).toBe(true)
    })

    it('should close modal when cancel button is clicked', async () => {
      const wrapper = createWrapper()
      await flushPromises()
      await wrapper.find('.add-button').trigger('click')

      expect(wrapper.find('.modal-overlay').exists()).toBe(true)

      await wrapper.find('.btn-cancel').trigger('click')

      expect(wrapper.find('.modal-overlay').exists()).toBe(false)
    })

    it('should close modal when clicking overlay', async () => {
      const wrapper = createWrapper()
      await flushPromises()
      await wrapper.find('.add-button').trigger('click')

      await wrapper.find('.modal-overlay').trigger('click')

      expect(wrapper.find('.modal-overlay').exists()).toBe(false)
    })

    it('should submit new company data', async () => {
      vi.mocked(apiClient.post).mockResolvedValue({ data: { id: '3' } })

      const wrapper = createWrapper()
      await flushPromises()
      await wrapper.find('.add-button').trigger('click')

      await wrapper.find('#name').setValue('New Company')
      await wrapper.find('#title').setValue('Developer')
      await wrapper.find('#start_date').setValue('2023-01-01')
      await wrapper.find('#location').setValue('Stockholm')
      await wrapper.find('#description').setValue('Test description')
      await wrapper.find('#technologies').setValue('Python, TypeScript')

      await wrapper.find('.company-form').trigger('submit')
      await flushPromises()

      expect(apiClient.post).toHaveBeenCalledWith(
        '/api/v1/companies',
        expect.objectContaining({
          name: 'New Company',
          title: 'Developer',
          start_date: '2023-01-01',
          location: 'Stockholm',
        })
      )
      expect(mockAlert).toHaveBeenCalledWith('Company added successfully')
    })
  })

  describe('Edit Form', () => {
    it('should show modal with populated data when edit button is clicked', async () => {
      const wrapper = createWrapper()
      await flushPromises()

      const firstCard = wrapper.findAll('.company-card')[0]
      await firstCard.find('.edit-btn').trigger('click')

      expect(wrapper.find('.modal-overlay').exists()).toBe(true)
      expect(wrapper.find('.modal-title').text()).toBe('Edit Company')
      expect((wrapper.find('#name').element as HTMLInputElement).value).toBe('Company A')
      expect((wrapper.find('#title').element as HTMLInputElement).value).toBe('Senior Developer')
    })

    it('should submit updated company data', async () => {
      vi.mocked(apiClient.put).mockResolvedValue({ data: {} })

      const wrapper = createWrapper()
      await flushPromises()

      const firstCard = wrapper.findAll('.company-card')[0]
      await firstCard.find('.edit-btn').trigger('click')

      await wrapper.find('#name').setValue('Updated Company')
      await wrapper.find('.company-form').trigger('submit')
      await flushPromises()

      expect(apiClient.put).toHaveBeenCalledWith(
        '/api/v1/companies/1',
        expect.objectContaining({
          name: 'Updated Company',
        })
      )
      expect(mockAlert).toHaveBeenCalledWith('Company updated successfully')
    })
  })

  describe('Delete Company', () => {
    it('should show confirmation dialog before deleting', async () => {
      mockConfirm.mockReturnValue(false)

      const wrapper = createWrapper()
      await flushPromises()

      const firstCard = wrapper.findAll('.company-card')[0]
      await firstCard.find('.delete-btn').trigger('click')

      expect(mockConfirm).toHaveBeenCalledWith('Are you sure you want to delete this company?')
      expect(apiClient.delete).not.toHaveBeenCalled()
    })

    it('should delete company when confirmed', async () => {
      mockConfirm.mockReturnValue(true)
      vi.mocked(apiClient.delete).mockResolvedValue({})

      const wrapper = createWrapper()
      await flushPromises()

      const firstCard = wrapper.findAll('.company-card')[0]
      await firstCard.find('.delete-btn').trigger('click')
      await flushPromises()

      expect(apiClient.delete).toHaveBeenCalledWith('/api/v1/companies/1')
      expect(mockAlert).toHaveBeenCalledWith('Company deleted successfully')
    })
  })

  describe('Error Handling', () => {
    it('should show error alert when fetch fails', async () => {
      vi.mocked(apiClient.get).mockRejectedValue(new Error('Network error'))
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      const wrapper = createWrapper()
      await flushPromises()

      expect(mockAlert).toHaveBeenCalledWith('Failed to load companies')
      consoleSpy.mockRestore()
    })

    it('should show error alert when save fails', async () => {
      vi.mocked(apiClient.post).mockRejectedValue(new Error('Save failed'))
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      const wrapper = createWrapper()
      await flushPromises()
      await wrapper.find('.add-button').trigger('click')
      await wrapper.find('#name').setValue('Test')
      await wrapper.find('#title').setValue('Test')
      await wrapper.find('#start_date').setValue('2023-01-01')
      await wrapper.find('.company-form').trigger('submit')
      await flushPromises()

      expect(mockAlert).toHaveBeenCalledWith('Failed to save company')
      consoleSpy.mockRestore()
    })

    it('should show error alert when delete fails', async () => {
      mockConfirm.mockReturnValue(true)
      vi.mocked(apiClient.delete).mockRejectedValue(new Error('Delete failed'))
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      const wrapper = createWrapper()
      await flushPromises()

      const firstCard = wrapper.findAll('.company-card')[0]
      await firstCard.find('.delete-btn').trigger('click')
      await flushPromises()

      expect(mockAlert).toHaveBeenCalledWith('Failed to delete company')
      consoleSpy.mockRestore()
    })
  })

  describe('Lifecycle', () => {
    it('should fetch companies on mount', async () => {
      createWrapper()
      await flushPromises()

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/companies')
    })

    it('should refetch companies after successful operations', async () => {
      mockConfirm.mockReturnValue(true)
      vi.mocked(apiClient.delete).mockResolvedValue({})

      const wrapper = createWrapper()
      await flushPromises()

      // Clear the initial call count
      vi.mocked(apiClient.get).mockClear()

      const firstCard = wrapper.findAll('.company-card')[0]
      await firstCard.find('.delete-btn').trigger('click')
      await flushPromises()

      // Should refetch after delete
      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/companies')
    })
  })
})
