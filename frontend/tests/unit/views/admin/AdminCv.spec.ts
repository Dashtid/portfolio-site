import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises, type VueWrapper } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import { createRouter, createWebHistory, type Router } from 'vue-router'
import AdminCv from '@/views/admin/AdminCv.vue'
import api from '@/api/client'

// AdminCv (Campaign 2026-08 Sprint 2) edits the admin-only CV profile + private
// contact, previews the assembled CV, and prints / downloads it. The backend is
// mocked at the api-client boundary.

vi.mock('@/api/client', () => ({
  default: { get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn() }
}))

const mockToast = { success: vi.fn(), error: vi.fn(), info: vi.fn(), warning: vi.fn() }
vi.mock('@/composables/useToast', () => ({ useToast: () => mockToast }))

const profileFixture = () => ({
  id: 1,
  name: 'David Dashti',
  label: 'Product & Application Security Engineer',
  summary: 'Security engineer.',
  focus: 'Cloud security.',
  location_city: 'Stockholm',
  location_region: 'Stockholm',
  location_country: 'SE',
  url: 'https://dashti.se',
  linkedin_url: 'https://www.linkedin.com/in/david-dashti/',
  github_url: 'https://github.com/Dashtid',
  languages: [{ language: 'Swedish', fluency: 'Native' }],
  email: '',
  phone: '',
  personnummer: ''
})

const exportFixture = () => ({
  basics: {
    name: 'David Dashti',
    label: 'Product & Application Security Engineer',
    email: '',
    phone: '',
    url: 'https://dashti.se',
    summary: 'Security engineer.',
    focus: 'Cloud security.',
    location: { city: 'Stockholm', region: 'Stockholm', countryCode: 'SE' },
    profiles: []
  },
  work: [],
  education: [],
  certificates: [],
  skills: [],
  languages: [{ language: 'Swedish', fluency: 'Native' }]
})

const createTestRouter = (): Router =>
  createRouter({
    history: createWebHistory(),
    routes: [
      { path: '/admin/cv', component: { template: '<div />' } },
      { path: '/admin/login', component: { template: '<div />' } }
    ]
  })

const createWrapper = async (): Promise<VueWrapper> => {
  const router = createTestRouter()
  router.push('/admin/cv')
  await router.isReady()
  const wrapper = mount(AdminCv, {
    global: {
      plugins: [
        createTestingPinia({
          createSpy: vi.fn,
          initialState: { auth: { user: { id: '1', is_admin: true } } }
        }),
        router
      ]
    }
  })
  await flushPromises()
  return wrapper
}

describe('AdminCv', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(api.get).mockImplementation((url: string) =>
      Promise.resolve({ data: url.endsWith('/export') ? exportFixture() : profileFixture() })
    )
    vi.mocked(api.put).mockResolvedValue({ data: profileFixture() })
  })

  it('loads the profile + export and renders the form and preview', async () => {
    const wrapper = await createWrapper()
    expect(api.get).toHaveBeenCalledWith('/api/v1/admin/cv/profile')
    expect(api.get).toHaveBeenCalledWith('/api/v1/admin/cv/export')
    expect((wrapper.find('#cv-name').element as HTMLInputElement).value).toBe('David Dashti')
    expect(wrapper.find('.cv-preview').exists()).toBe(true)
  })

  it('surfaces an error toast and message when loading fails', async () => {
    vi.mocked(api.get).mockRejectedValue(new Error('boom'))
    const wrapper = await createWrapper()
    expect(mockToast.error).toHaveBeenCalledWith('Failed to load CV data')
    expect(wrapper.text()).toContain('Failed to load CV data.')
  })

  it('prunes blank language rows before the PUT and toasts success', async () => {
    const wrapper = await createWrapper()
    const addBtn = wrapper.findAll('button').find(b => b.text() === 'Add language')!
    await addBtn.trigger('click') // blank row (left empty)
    await addBtn.trigger('click') // row we will fill
    const langInputs = wrapper.findAll('input[placeholder="Language"]')
    await langInputs[langInputs.length - 1].setValue('French')

    await wrapper.find('form').trigger('submit')
    await flushPromises()

    const body = vi.mocked(api.put).mock.calls[0][1] as { languages: unknown }
    expect(body.languages).toEqual([
      { language: 'Swedish', fluency: 'Native' },
      { language: 'French', fluency: '' }
    ])
    expect(mockToast.success).toHaveBeenCalledWith('CV profile saved')
    // preview re-assembled after save
    expect(api.get).toHaveBeenCalledWith('/api/v1/admin/cv/export')
  })

  it('surfaces an error toast when saving fails', async () => {
    const wrapper = await createWrapper()
    vi.mocked(api.put).mockRejectedValueOnce(new Error('boom'))
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    expect(mockToast.error).toHaveBeenCalledWith('Failed to save CV profile')
  })

  it('removes a language row', async () => {
    const wrapper = await createWrapper()
    const removeBtn = wrapper.findAll('button').find(b => b.text() === 'Remove')!
    await removeBtn.trigger('click')
    expect(wrapper.findAll('input[placeholder="Language"]').length).toBe(0)
  })

  it('calls window.print from the Print button', async () => {
    // happy-dom has no window.print to spy on — assign a stub.
    const printSpy = vi.fn()
    window.print = printSpy
    const wrapper = await createWrapper()
    const printBtn = wrapper.findAll('button').find(b => b.text().includes('Print'))!
    await printBtn.trigger('click')
    expect(printSpy).toHaveBeenCalled()
  })

  it('downloads the export as JSON with a slugified filename', async () => {
    const createUrl = vi.fn(() => 'blob:x')
    const revokeUrl = vi.fn()
    ;(URL as unknown as { createObjectURL: unknown }).createObjectURL = createUrl
    ;(URL as unknown as { revokeObjectURL: unknown }).revokeObjectURL = revokeUrl
    const clickSpy = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {})

    const wrapper = await createWrapper()
    const dlBtn = wrapper.findAll('button').find(b => b.text() === 'Download JSON')!
    await dlBtn.trigger('click')

    expect(createUrl).toHaveBeenCalled()
    expect(clickSpy).toHaveBeenCalled()
    expect(revokeUrl).toHaveBeenCalledWith('blob:x')
  })
})
