import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import LanguageBar from '@/components/LanguageBar.vue'

describe('LanguageBar', () => {
  it('renders the language name and percentage', () => {
    const wrapper = mount(LanguageBar, { props: { name: 'TypeScript', percentage: 60 } })
    expect(wrapper.find('.language-name').text()).toBe('TypeScript')
    expect(wrapper.find('.language-percentage').text()).toBe('60%')
  })

  it('exposes the right ARIA progressbar attributes', () => {
    const wrapper = mount(LanguageBar, { props: { name: 'Python', percentage: 30 } })
    const bar = wrapper.find('.progress-bar')
    expect(bar.attributes('role')).toBe('progressbar')
    expect(bar.attributes('aria-valuenow')).toBe('30')
    expect(bar.attributes('aria-valuemin')).toBe('0')
    expect(bar.attributes('aria-valuemax')).toBe('100')
    expect(bar.attributes('aria-label')).toBe('Python language usage')
  })

  it('paints the fill width to match the percentage', () => {
    const wrapper = mount(LanguageBar, { props: { name: 'Vue', percentage: 75 } })
    const fill = wrapper.find('.progress-fill')
    expect(fill.attributes('style')).toContain('width: 75%')
  })

  it('handles 0 and 100 boundary values', () => {
    const zero = mount(LanguageBar, { props: { name: 'Rust', percentage: 0 } })
    expect(zero.find('.progress-bar').attributes('aria-valuenow')).toBe('0')
    expect(zero.find('.progress-fill').attributes('style')).toContain('width: 0%')

    const full = mount(LanguageBar, { props: { name: 'Go', percentage: 100 } })
    expect(full.find('.progress-bar').attributes('aria-valuenow')).toBe('100')
    expect(full.find('.progress-fill').attributes('style')).toContain('width: 100%')
  })
})
