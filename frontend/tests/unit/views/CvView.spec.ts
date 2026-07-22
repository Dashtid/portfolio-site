import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import CvView from '@/views/CvView.vue'

vi.mock('@/components/NavBar.vue', () => ({
  default: { name: 'NavBar', template: '<nav data-testid="navbar" />' }
}))
vi.mock('@/components/FooterSection.vue', () => ({
  default: { name: 'FooterSection', template: '<footer data-testid="footer" />' }
}))

const createWrapper = async () => {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', component: { template: '<div />' }, name: 'home' },
      { path: '/cv', component: CvView, name: 'cv' }
    ]
  })
  await router.push('/cv')
  await router.isReady()
  return mount(CvView, { global: { plugins: [router] } })
}

describe('CvView (D3-FEAT-02)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the identity header from resume.json', async () => {
    const wrapper = await createWrapper()
    expect(wrapper.text()).toContain('David Dashti')
    expect(wrapper.text()).toContain('Hermes Medical Solutions')
    expect(wrapper.text()).toContain('QA/RA & Security Specialist')
  })

  it('never renders the scrubbed contact fields (LinkedIn-only contact)', async () => {
    const wrapper = await createWrapper()
    const html = wrapper.html()
    // The repo source carries an email; the public page must not.
    expect(html).not.toContain('dashtid@pm.me')
    expect(html).not.toContain('mailto:')
  })

  it('offers the machine-readable JSON and no redundant PDF-download button', async () => {
    const wrapper = await createWrapper()

    // Owner decision (Campaign 2026-08): the /cv page IS the full CV, so a
    // "Download PDF" button is redundant — and no downloadable file is offered
    // that could carry the personal contact kept off the public variant. The
    // print stylesheet still handles Ctrl+P for anyone who wants a paper copy.
    const downloadBtn = wrapper.findAll('button').find(b => b.text().includes('Download'))
    expect(downloadBtn).toBeUndefined()

    const jsonLink = wrapper.findAll('a').find(a => a.attributes('href') === '/cv.json')
    expect(jsonLink).toBeDefined()
  })

  it('renders every work entry (variant mechanism: no variants field = all shown)', async () => {
    const wrapper = await createWrapper()
    // resume.json carries 8 work entries, none variant-restricted today
    const entries = wrapper.text()
    expect(entries).toContain('Philips')
    expect(entries).toContain('Karolinska')
    expect(entries).toContain('Scania')
  })
})
