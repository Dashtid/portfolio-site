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

  it('offers the print-to-PDF path and the machine-readable JSON', async () => {
    const wrapper = await createWrapper()
    // happy-dom ships no window.print — install a fake to observe the call
    const printSpy = vi.fn()
    window.print = printSpy

    const button = wrapper.findAll('button').find(b => b.text().includes('Download PDF'))
    expect(button).toBeDefined()
    await button?.trigger('click')
    expect(printSpy).toHaveBeenCalledTimes(1)

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
