import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { mount, type VueWrapper } from '@vue/test-utils'
import CvDocument from '@/components/cv/CvDocument.vue'
import type { CvResume } from '@/types/cv'

// CvDocument is the presentational, print-ready CV used by the admin export
// page (Campaign 2026-08 Sprint 2). It is pure — a `resume` prop in, DOM out —
// so it is exercised directly here.

const fullResume = (): CvResume => ({
  basics: {
    name: 'David Dashti',
    label: 'Product & Application Security Engineer',
    email: 'me@example.com',
    phone: '+46 70 000 00 00',
    url: 'https://dashti.se',
    summary: 'Security engineer for regulated medical software.',
    focus: 'Cloud & CI/CD security.',
    personalNumber: '900101-0000',
    location: { city: 'Stockholm', region: 'Stockholm', countryCode: 'SE' },
    profiles: [
      { network: 'LinkedIn', url: 'https://www.linkedin.com/in/david-dashti/' },
      { network: 'GitHub', url: 'https://github.com/Dashtid' }
    ]
  },
  work: [
    {
      name: 'Hermes Medical Solutions',
      position: 'QA/RA & Security Specialist',
      location: 'Stockholm',
      startDate: '2024-05',
      endDate: '',
      highlights: ['Threat modeling', 'SBOM-based SCA']
    }
  ],
  education: [
    {
      institution: 'KTH',
      studyType: 'M.Sc.',
      area: 'Biomedical Engineering',
      startDate: '2018-08',
      endDate: '',
      courses: ['Thesis: process modelling']
    }
  ],
  certificates: [
    { name: 'Security+', issuer: 'CompTIA', date: '2026-01', url: 'https://www.credly.com/x' },
    { name: 'Cybersecurity Fundamentals', issuer: 'Företagsuniversitetet', date: '2024-12' }
  ],
  skills: [{ name: 'Security Engineering', keywords: ['AppSec', 'Threat Modeling'] }],
  languages: [
    { language: 'Swedish', fluency: 'Native' },
    { language: 'English', fluency: 'Fluent' }
  ]
})

const emptyResume = (): CvResume => ({
  basics: {
    name: 'David Dashti',
    label: '',
    email: '',
    phone: '',
    url: '',
    summary: '',
    location: { city: '', region: '', countryCode: '' },
    profiles: []
  },
  work: [],
  education: [],
  certificates: [],
  skills: [],
  languages: []
})

describe('CvDocument', () => {
  // Track and unmount every wrapper: CvDocument attaches window
  // beforeprint/afterprint listeners in onMounted and removes them in
  // onUnmounted. Leaving instances mounted would leak listeners across tests
  // and corrupt the theme-force assertions.
  let wrappers: VueWrapper[] = []
  const make = (resume: CvResume): VueWrapper => {
    const wrapper = mount(CvDocument, { props: { resume } })
    wrappers.push(wrapper)
    return wrapper
  }

  beforeEach(() => {
    document.documentElement.removeAttribute('data-theme')
  })

  afterEach(() => {
    wrappers.forEach(w => w.unmount())
    wrappers = []
  })

  it('renders identity, summary, focus and location', () => {
    const wrapper = make(fullResume())
    const text = wrapper.text()
    expect(text).toContain('David Dashti')
    expect(text).toContain('Product & Application Security Engineer')
    expect(text).toContain('Security engineer for regulated medical software.')
    expect(text).toContain('Current focus')
    expect(text).toContain('Cloud & CI/CD security.')
    expect(text).toContain('Stockholm, SE')
  })

  it('strips the protocol from the displayed URL', () => {
    const wrapper = make(fullResume())
    expect(wrapper.text()).toContain('dashti.se')
    expect(wrapper.text()).not.toContain('https://dashti.se')
  })

  it('renders profile links and private contact when present', () => {
    const wrapper = make(fullResume())
    const hrefs = wrapper.findAll('a').map(a => a.attributes('href'))
    expect(hrefs).toContain('https://www.linkedin.com/in/david-dashti/')
    expect(hrefs).toContain('https://github.com/Dashtid')
    const text = wrapper.text()
    expect(text).toContain('me@example.com')
    expect(text).toContain('+46 70 000 00 00')
    expect(text).toContain('900101-0000')
  })

  it('omits the private-contact line when email/phone/personnummer are all blank', () => {
    const wrapper = make(emptyResume())
    expect(wrapper.text()).not.toContain('@')
  })

  it('shows Present for an open-ended role and an in-progress degree', () => {
    const wrapper = make(fullResume())
    // Experience and Education both fall back to "Present" on a blank end date.
    expect(wrapper.text().match(/Present/g)?.length).toBe(2)
  })

  it('formats year-only dates without a month', () => {
    const resume = fullResume()
    resume.work[0].startDate = '2024'
    const wrapper = make(resume)
    expect(wrapper.text()).toContain('2024')
  })

  it('renders skills, education courses, certificates (linked + plain) and languages', () => {
    const wrapper = make(fullResume())
    const text = wrapper.text()
    expect(text).toContain('AppSec')
    expect(text).toContain('Thesis: process modelling')
    expect(text).toContain('Security+')
    expect(text).toContain('Cybersecurity Fundamentals')
    expect(text).toContain('Swedish (Native)')
    expect(text).toContain('English (Fluent)')
    // Security+ is linked, the plain course is not.
    const certLink = wrapper.findAll('a').find(a => a.text().includes('Security+'))
    expect(certLink?.attributes('href')).toBe('https://www.credly.com/x')
  })

  it('hides every empty section without error', () => {
    const wrapper = make(emptyResume())
    const headings = wrapper.findAll('h2').map(h => h.text())
    expect(headings).not.toContain('Experience')
    expect(headings).not.toContain('Skills')
    expect(headings).not.toContain('Education')
    expect(headings).not.toContain('Certificates')
    expect(headings).not.toContain('Languages')
  })

  it('forces light theme around print and restores it afterward', async () => {
    document.documentElement.setAttribute('data-theme', 'dark')
    make(fullResume())

    window.dispatchEvent(new Event('beforeprint'))
    expect(document.documentElement.getAttribute('data-theme')).toBe('light')

    window.dispatchEvent(new Event('afterprint'))
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark')
  })

  it('afterprint without a prior beforeprint leaves the theme untouched', () => {
    document.documentElement.setAttribute('data-theme', 'dark')
    make(fullResume())
    window.dispatchEvent(new Event('afterprint'))
    expect(document.documentElement.getAttribute('data-theme')).toBe('dark')
  })
})
