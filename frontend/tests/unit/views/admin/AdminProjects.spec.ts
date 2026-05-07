import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, VueWrapper, flushPromises } from '@vue/test-utils'
import AdminProjects from '@/views/admin/AdminProjects.vue'
import apiClient from '@/api/client'

vi.mock('@/api/client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn()
  }
}))

const mockToast = {
  success: vi.fn(),
  error: vi.fn(),
  info: vi.fn(),
  warning: vi.fn()
}
vi.mock('@/composables/useToast', () => ({
  useToast: () => mockToast
}))

const mockConfirm = vi.fn()
window.confirm = mockConfirm

describe('AdminProjects', () => {
  const mockCompanies = [
    { id: 'co-1', name: 'Acme Corp', title: 'Engineer', start_date: '2020-01-01' },
    { id: 'co-2', name: 'Initech', title: 'Lead', start_date: '2022-01-01' }
  ]

  const mockProjects = [
    {
      id: 'p-1',
      name: 'Project Alpha',
      description: 'First project',
      detailed_description: null,
      technologies: ['Python', 'FastAPI'],
      github_url: 'https://github.com/x/alpha',
      live_url: null,
      image_url: null,
      company_id: 'co-1',
      featured: true,
      order_index: 1,
      video_url: null,
      video_title: null,
      map_url: null,
      map_title: null,
      responsibilities: null
    },
    {
      id: 'p-2',
      name: 'Project Beta',
      description: 'Second project',
      detailed_description: null,
      technologies: ['Vue', 'TypeScript'],
      github_url: null,
      live_url: null,
      image_url: null,
      company_id: null,
      featured: false,
      order_index: 2,
      video_url: null,
      video_title: null,
      map_url: null,
      map_title: null,
      responsibilities: null
    }
  ]

  // /api/v1/projects -> projects, /api/v1/companies -> companies
  const stubGet = (
    overrides: { projects?: unknown; companies?: unknown; rejectAll?: boolean } = {}
  ): void => {
    vi.mocked(apiClient.get).mockImplementation((url: string) => {
      if (overrides.rejectAll) return Promise.reject(new Error('Network error'))
      if (url.includes('/projects')) {
        return Promise.resolve({ data: overrides.projects ?? mockProjects } as never)
      }
      if (url.includes('/companies')) {
        return Promise.resolve({ data: overrides.companies ?? mockCompanies } as never)
      }
      return Promise.resolve({ data: [] } as never)
    })
  }

  const createWrapper = (): VueWrapper => mount(AdminProjects)

  beforeEach(() => {
    vi.clearAllMocks()
    mockToast.success.mockClear()
    mockToast.error.mockClear()
    stubGet()
  })

  describe('Rendering', () => {
    it('renders the admin projects container', async () => {
      const wrapper = createWrapper()
      await flushPromises()
      expect(wrapper.find('.admin-projects').exists()).toBe(true)
    })

    it('shows the page header with title and add button', async () => {
      const wrapper = createWrapper()
      await flushPromises()
      expect(wrapper.find('.page-title').text()).toBe('Manage Projects')
      expect(wrapper.find('.add-button').text()).toContain('Add Project')
    })

    it('shows loading state while fetching', async () => {
      vi.mocked(apiClient.get).mockImplementation(() => new Promise(() => {}))
      const wrapper = createWrapper()
      await wrapper.vm.$nextTick()
      expect(wrapper.find('.loading-state').exists()).toBe(true)
      expect(wrapper.find('.loading-state').text()).toContain('Loading projects')
    })

    it('shows empty state when no projects', async () => {
      stubGet({ projects: [] })
      const wrapper = createWrapper()
      await flushPromises()
      expect(wrapper.find('.empty-state').exists()).toBe(true)
      expect(wrapper.find('.empty-state').text()).toContain('No projects added yet')
    })

    it('renders one card per project', async () => {
      const wrapper = createWrapper()
      await flushPromises()
      expect(wrapper.findAll('.project-card')).toHaveLength(2)
    })

    it('resolves company name on cards via the companies fetch', async () => {
      const wrapper = createWrapper()
      await flushPromises()
      const firstCard = wrapper.findAll('.project-card')[0]
      expect(firstCard.find('.project-company').text()).toBe('Acme Corp')
    })

    it('marks featured projects with a badge', async () => {
      const wrapper = createWrapper()
      await flushPromises()
      const cards = wrapper.findAll('.project-card')
      expect(cards[0].find('.featured-badge').exists()).toBe(true)
      expect(cards[1].find('.featured-badge').exists()).toBe(false)
    })

    it('renders technologies as pills', async () => {
      const wrapper = createWrapper()
      await flushPromises()
      const firstCard = wrapper.findAll('.project-card')[0]
      const pills = firstCard.findAll('.tech-pill')
      expect(pills).toHaveLength(2)
      expect(pills[0].text()).toBe('Python')
    })
  })

  describe('Add form', () => {
    it('opens the modal with empty fields when Add is clicked', async () => {
      const wrapper = createWrapper()
      await flushPromises()
      expect(wrapper.find('.modal-overlay').exists()).toBe(false)

      await wrapper.find('.add-button').trigger('click')

      expect(wrapper.find('.modal-overlay').exists()).toBe(true)
      expect(wrapper.find('.modal-title').text()).toBe('Add New Project')
      expect((wrapper.find('#name').element as HTMLInputElement).value).toBe('')
    })

    it('closes the modal on cancel', async () => {
      const wrapper = createWrapper()
      await flushPromises()
      await wrapper.find('.add-button').trigger('click')
      await wrapper.find('.btn-cancel').trigger('click')
      expect(wrapper.find('.modal-overlay').exists()).toBe(false)
    })

    it('closes the modal on Escape', async () => {
      const wrapper = createWrapper()
      await flushPromises()
      await wrapper.find('.add-button').trigger('click')
      expect(wrapper.find('.modal-overlay').exists()).toBe(true)

      await wrapper.find('.modal-overlay').trigger('keydown.escape')

      expect(wrapper.find('.modal-overlay').exists()).toBe(false)
    })

    it('does NOT close when clicking inside the form', async () => {
      const wrapper = createWrapper()
      await flushPromises()
      await wrapper.find('.add-button').trigger('click')

      await wrapper.find('.project-form').trigger('click')

      expect(wrapper.find('.modal-overlay').exists()).toBe(true)
    })

    it('populates the company dropdown from the companies fetch', async () => {
      const wrapper = createWrapper()
      await flushPromises()
      await wrapper.find('.add-button').trigger('click')
      const options = wrapper.find('#company_id').findAll('option')
      // 1 placeholder + 2 companies
      expect(options).toHaveLength(3)
      expect(options[1].text()).toBe('Acme Corp')
    })

    it('submits new project payload with normalised lists and blanks-as-null', async () => {
      vi.mocked(apiClient.post).mockResolvedValue({ data: { id: 'p-3' } })
      const wrapper = createWrapper()
      await flushPromises()
      await wrapper.find('.add-button').trigger('click')

      await wrapper.find('#name').setValue('New Project')
      await wrapper.find('#description').setValue('A description')
      await wrapper.find('#technologies').setValue('Rust, WASM')
      await wrapper.find('#responsibilities').setValue('design, ship')
      // Leave github_url blank to verify blank-to-null normalisation
      await wrapper.find('.project-form').trigger('submit')
      await flushPromises()

      expect(apiClient.post).toHaveBeenCalledWith(
        '/api/v1/projects',
        expect.objectContaining({
          name: 'New Project',
          description: 'A description',
          technologies: ['Rust', 'WASM'],
          responsibilities: ['design', 'ship'],
          github_url: null
        })
      )
      expect(mockToast.success).toHaveBeenCalledWith('Project added successfully')
    })
  })

  describe('Edit form', () => {
    it('pre-fills form with project data', async () => {
      const wrapper = createWrapper()
      await flushPromises()
      const firstCard = wrapper.findAll('.project-card')[0]
      await firstCard.find('.edit-btn').trigger('click')

      expect(wrapper.find('.modal-title').text()).toBe('Edit Project')
      expect((wrapper.find('#name').element as HTMLInputElement).value).toBe('Project Alpha')
      expect((wrapper.find('#technologies').element as HTMLInputElement).value).toBe(
        'Python, FastAPI'
      )
      expect((wrapper.find('#featured').element as HTMLInputElement).checked).toBe(true)
    })

    it('submits updated project via PUT', async () => {
      vi.mocked(apiClient.put).mockResolvedValue({ data: {} })
      const wrapper = createWrapper()
      await flushPromises()

      const firstCard = wrapper.findAll('.project-card')[0]
      await firstCard.find('.edit-btn').trigger('click')
      await wrapper.find('#name').setValue('Project Alpha v2')
      await wrapper.find('.project-form').trigger('submit')
      await flushPromises()

      expect(apiClient.put).toHaveBeenCalledWith(
        '/api/v1/projects/p-1',
        expect.objectContaining({ name: 'Project Alpha v2' })
      )
      expect(mockToast.success).toHaveBeenCalledWith('Project updated successfully')
    })
  })

  describe('Delete', () => {
    it('does nothing when the user cancels the confirm dialog', async () => {
      mockConfirm.mockReturnValue(false)
      const wrapper = createWrapper()
      await flushPromises()
      await wrapper.findAll('.project-card')[0].find('.delete-btn').trigger('click')
      expect(mockConfirm).toHaveBeenCalledWith('Are you sure you want to delete this project?')
      expect(apiClient.delete).not.toHaveBeenCalled()
    })

    it('calls DELETE and refetches when confirmed', async () => {
      mockConfirm.mockReturnValue(true)
      vi.mocked(apiClient.delete).mockResolvedValue({})
      const wrapper = createWrapper()
      await flushPromises()
      vi.mocked(apiClient.get).mockClear()

      await wrapper.findAll('.project-card')[0].find('.delete-btn').trigger('click')
      await flushPromises()

      expect(apiClient.delete).toHaveBeenCalledWith('/api/v1/projects/p-1')
      expect(mockToast.success).toHaveBeenCalledWith('Project deleted successfully')
      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/projects')
    })
  })

  describe('Validation', () => {
    it('blocks submit when name is empty', async () => {
      const wrapper = createWrapper()
      await flushPromises()
      await wrapper.find('.add-button').trigger('click')
      await wrapper.find('.project-form').trigger('submit')

      expect(apiClient.post).not.toHaveBeenCalled()
    })
  })

  describe('Error handling', () => {
    it('toasts an error when the initial load fails', async () => {
      stubGet({ rejectAll: true })
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
      createWrapper()
      await flushPromises()
      expect(mockToast.error).toHaveBeenCalledWith('Failed to load projects')
      consoleSpy.mockRestore()
    })

    it('toasts an error when save fails', async () => {
      vi.mocked(apiClient.post).mockRejectedValue(new Error('boom'))
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      const wrapper = createWrapper()
      await flushPromises()
      await wrapper.find('.add-button').trigger('click')
      await wrapper.find('#name').setValue('X')
      await wrapper.find('.project-form').trigger('submit')
      await flushPromises()

      expect(mockToast.error).toHaveBeenCalledWith('Failed to save project')
      consoleSpy.mockRestore()
    })
  })

  describe('Lifecycle', () => {
    it('fetches projects and companies in parallel on mount', async () => {
      createWrapper()
      await flushPromises()
      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/projects')
      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/companies')
    })
  })
})
