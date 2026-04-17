import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import FooterSection from '@/components/FooterSection.vue'

describe('FooterSection', () => {
  it('renders the footer element', () => {
    const wrapper = mount(FooterSection)
    expect(wrapper.find('footer.footer-section').exists()).toBe(true)
  })

  it('displays the brand name', () => {
    const wrapper = mount(FooterSection)
    expect(wrapper.find('.footer-name').text()).toBe('David Dashti')
  })

  it('displays the tagline', () => {
    const wrapper = mount(FooterSection)
    expect(wrapper.find('.footer-tagline').text()).toBe(
      'Cybersecurity Engineer & Medical Software Specialist'
    )
  })

  it('displays the current year in copyright', () => {
    const wrapper = mount(FooterSection)
    const currentYear = new Date().getFullYear()
    expect(wrapper.find('.footer-copyright').text()).toContain(currentYear.toString())
  })

  it('renders LinkedIn and GitHub social links', () => {
    const wrapper = mount(FooterSection)
    const links = wrapper.findAll('.social-link')
    expect(links).toHaveLength(2)
    expect(links[0].attributes('href')).toBe('https://www.linkedin.com/in/david-dashti/')
    expect(links[1].attributes('href')).toBe('https://github.com/Dashtid')
  })

  it('social links open in new tab with secure rel', () => {
    const wrapper = mount(FooterSection)
    wrapper.findAll('.social-link').forEach(link => {
      expect(link.attributes('target')).toBe('_blank')
      expect(link.attributes('rel')).toBe('noopener noreferrer')
    })
  })

  it('social links have descriptive aria-labels', () => {
    const wrapper = mount(FooterSection)
    const links = wrapper.findAll('.social-link')
    expect(links[0].attributes('aria-label')).toContain('LinkedIn')
    expect(links[1].attributes('aria-label')).toContain('GitHub')
  })
})
