import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, VueWrapper, flushPromises } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import { createRouter, createWebHistory, type Router } from 'vue-router'
import AdminDocuments from '@/views/admin/AdminDocuments.vue'
import api from '@/api/client'

// D3-TEST-02: the Sprint-6 file-upload UI had zero specs and, being
// never-imported, was invisible to coverage. Highest-value paths first:
// the upload contract (FormData POST), the client-side type/size guards,
// and upload-failure surfacing.

// Mock the API client
vi.mock('@/api/client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn()
  }
}))

// Mock useToast composable (component uses toast, not window.alert)
const mockToast = {
  success: vi.fn(),
  error: vi.fn(),
  info: vi.fn(),
  warning: vi.fn()
}
vi.mock('@/composables/useToast', () => ({
  useToast: () => mockToast
}))

// Mock window.confirm
const mockConfirm = vi.fn()
window.confirm = mockConfirm

const createTestRouter = (): Router => {
  return createRouter({
    history: createWebHistory(),
    routes: [
      { path: '/admin/documents', component: { template: '<div>Documents</div>' } },
      { path: '/admin/login', component: { template: '<div>Login</div>' } }
    ]
  })
}

const mockDocuments = [
  {
    id: 'doc-1',
    title: 'Master Thesis',
    description: 'SoftPro Medusa integration',
    document_type: 'thesis',
    file_path: 'documents/thesis.pdf',
    file_size: 2_400_000,
    file_url: 'https://api.dashti.se/static/documents/thesis.pdf',
    published_date: '2022-06-01',
    order_index: 0
  },
  {
    id: 'doc-2',
    title: 'Radiology Paper',
    description: null,
    document_type: 'paper',
    file_path: 'documents/paper.pdf',
    file_size: 800_000,
    file_url: 'https://api.dashti.se/static/documents/paper.pdf',
    published_date: null,
    order_index: 1
  }
]

// Build a File whose reported size we control without allocating the bytes
const makeFile = (name: string, type: string, size: number): File => {
  const file = new File(['x'], name, { type })
  Object.defineProperty(file, 'size', { value: size })
  return file
}

// Fire the file input's change handler with a chosen file. happy-dom keeps
// input.files readonly, so the FileList is defined directly on the element.
const selectFile = async (wrapper: VueWrapper, file: File): Promise<void> => {
  const input = wrapper.find('input[type="file"]')
  Object.defineProperty(input.element, 'files', {
    value: [file],
    configurable: true
  })
  await input.trigger('change')
  await flushPromises()
}

describe('AdminDocuments', () => {
  let router: Router

  const createWrapper = async (): Promise<VueWrapper> => {
    router = createTestRouter()
    await router.push('/admin/documents')
    await router.isReady()

    const wrapper = mount(AdminDocuments, {
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
    await flushPromises()
    return wrapper
  }

  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(api.get).mockResolvedValue({ data: mockDocuments })
  })

  describe('listing', () => {
    it('renders a table row per document from the API', async () => {
      const wrapper = await createWrapper()

      expect(api.get).toHaveBeenCalledWith('/api/v1/documents/')
      const rows = wrapper.findAll('tbody tr')
      expect(rows).toHaveLength(2)
      expect(rows[0].text()).toContain('Master Thesis')
      expect(rows[0].text()).toContain('2.3 MB')
      expect(rows[1].text()).toContain('Radiology Paper')
    })

    it('shows the empty state when there are no documents', async () => {
      vi.mocked(api.get).mockResolvedValue({ data: [] })
      const wrapper = await createWrapper()

      expect(wrapper.find('.empty-state').exists()).toBe(true)
    })

    it('surfaces a toast when the list fails to load', async () => {
      vi.mocked(api.get).mockRejectedValue(new Error('boom'))
      await createWrapper()

      expect(mockToast.error).toHaveBeenCalledWith('Failed to load documents.')
    })
  })

  describe('file upload', () => {
    it('POSTs the selected PDF as multipart FormData and stores the response', async () => {
      vi.mocked(api.post).mockResolvedValue({
        data: {
          file_path: 'documents/uuid_new.pdf',
          file_size: 1_000_000,
          file_url: 'https://api.dashti.se/static/documents/uuid_new.pdf',
          original_filename: 'new.pdf'
        }
      })
      const wrapper = await createWrapper()
      await wrapper.find('.add-button').trigger('click')

      await selectFile(wrapper, makeFile('new.pdf', 'application/pdf', 1_000_000))

      expect(api.post).toHaveBeenCalledWith(
        '/api/v1/documents/upload',
        expect.any(FormData),
        expect.objectContaining({
          headers: { 'Content-Type': 'multipart/form-data' }
        })
      )
      expect(wrapper.find('.upload-status-ok').exists()).toBe(true)
      expect(mockToast.success).toHaveBeenCalledWith('File uploaded.')
    })

    it('rejects non-PDF files client-side without calling the API', async () => {
      const wrapper = await createWrapper()
      await wrapper.find('.add-button').trigger('click')

      await selectFile(wrapper, makeFile('evil.exe', 'application/x-msdownload', 1_000))

      expect(api.post).not.toHaveBeenCalled()
      expect(wrapper.text()).toContain('PDF files only.')
    })

    it('rejects files over 25 MB client-side without calling the API', async () => {
      const wrapper = await createWrapper()
      await wrapper.find('.add-button').trigger('click')

      await selectFile(wrapper, makeFile('huge.pdf', 'application/pdf', 26 * 1024 * 1024))

      expect(api.post).not.toHaveBeenCalled()
      expect(wrapper.text()).toContain('File exceeds 25 MB limit.')
    })

    it('surfaces an inline error and toast when the upload fails (413/415 path)', async () => {
      vi.mocked(api.post).mockRejectedValue({ response: { status: 413 } })
      const wrapper = await createWrapper()
      await wrapper.find('.add-button').trigger('click')

      await selectFile(wrapper, makeFile('big.pdf', 'application/pdf', 1_000_000))

      expect(wrapper.text()).toContain('Upload failed. Try again.')
      expect(mockToast.error).toHaveBeenCalledWith('Upload failed.')
    })
  })

  describe('create', () => {
    it('blocks save until a file has been uploaded', async () => {
      const wrapper = await createWrapper()
      await wrapper.find('.add-button').trigger('click')

      await wrapper.find('#doc-title').setValue('New Doc')
      await wrapper.find('#doc-type').setValue('paper')
      await wrapper.find('form').trigger('submit.prevent')
      await flushPromises()

      // No POST to the collection endpoint — only validation errors
      expect(api.post).not.toHaveBeenCalledWith('/api/v1/documents/', expect.anything())
      expect(wrapper.text()).toContain('Upload a file first.')
    })

    it('POSTs the document after a successful upload', async () => {
      vi.mocked(api.post)
        .mockResolvedValueOnce({
          data: {
            file_path: 'documents/uuid_new.pdf',
            file_size: 1_000_000,
            file_url: 'https://api.dashti.se/static/documents/uuid_new.pdf',
            original_filename: 'new.pdf'
          }
        })
        .mockResolvedValueOnce({ data: {} })
      const wrapper = await createWrapper()
      await wrapper.find('.add-button').trigger('click')

      await wrapper.find('#doc-title').setValue('New Doc')
      await wrapper.find('#doc-type').setValue('paper')
      await selectFile(wrapper, makeFile('new.pdf', 'application/pdf', 1_000_000))
      await wrapper.find('form').trigger('submit.prevent')
      await flushPromises()

      expect(api.post).toHaveBeenCalledWith(
        '/api/v1/documents/',
        expect.objectContaining({
          title: 'New Doc',
          document_type: 'paper',
          file_url: 'https://api.dashti.se/static/documents/uuid_new.pdf'
        })
      )
      expect(mockToast.success).toHaveBeenCalledWith('Document added.')
    })
  })

  describe('delete', () => {
    it('DELETEs after confirm', async () => {
      mockConfirm.mockReturnValue(true)
      vi.mocked(api.delete).mockResolvedValue({ data: {} })
      const wrapper = await createWrapper()

      await wrapper
        .find('tbody tr .delete-button, tbody tr [aria-label*="Delete"]')
        .trigger('click')
      await flushPromises()

      expect(api.delete).toHaveBeenCalledWith('/api/v1/documents/doc-1')
    })

    it('does not DELETE when confirm is dismissed', async () => {
      mockConfirm.mockReturnValue(false)
      const wrapper = await createWrapper()

      await wrapper
        .find('tbody tr .delete-button, tbody tr [aria-label*="Delete"]')
        .trigger('click')
      await flushPromises()

      expect(api.delete).not.toHaveBeenCalled()
    })
  })
})
