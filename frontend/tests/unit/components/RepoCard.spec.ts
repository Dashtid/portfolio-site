import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import RepoCard from '@/components/RepoCard.vue'

const sampleRepo = {
  name: 'cool-repo',
  description: 'A cool repo',
  html_url: 'https://github.com/user/cool-repo',
  language: 'TypeScript',
  stars: 50,
  forks: 5
}

// Queries are semantic (elements, text, aria) rather than styling-class
// hooks — the card was migrated from scoped CSS to Tailwind utilities in
// S3 and class names no longer describe structure.
describe('RepoCard', () => {
  it('renders the repo name and description', () => {
    const wrapper = mount(RepoCard, { props: { repo: sampleRepo } })
    expect(wrapper.find('h3').text()).toBe('cool-repo')
    expect(wrapper.find('p').text()).toBe('A cool repo')
  })

  it('renders stars and forks counts', () => {
    const text = mount(RepoCard, { props: { repo: sampleRepo } }).text()
    expect(text).toContain('50')
    expect(text).toContain('5')
  })

  it('opens GitHub in a new tab with secure rel attributes', () => {
    const wrapper = mount(RepoCard, { props: { repo: sampleRepo } })
    const link = wrapper.find('a')
    expect(link.attributes('href')).toBe('https://github.com/user/cool-repo')
    expect(link.attributes('target')).toBe('_blank')
    expect(link.attributes('rel')).toBe('noopener noreferrer')
  })

  it('keeps the project-card hook class for entrance animation and e2e', () => {
    const wrapper = mount(RepoCard, { props: { repo: sampleRepo } })
    expect(wrapper.find('a').classes()).toContain('project-card')
  })

  it('exposes an aria-label that names the repo', () => {
    const wrapper = mount(RepoCard, { props: { repo: sampleRepo } })
    expect(wrapper.find('a').attributes('aria-label')).toBe(
      'cool-repo repository on GitHub (opens in new tab)'
    )
  })

  it('paints the language dot with the linguist color for known languages', () => {
    const wrapper = mount(RepoCard, { props: { repo: sampleRepo } })
    const dot = wrapper.find('span[style]')
    // TypeScript -> #3178c6
    expect(dot.attributes('style')).toContain('#3178c6')
  })

  it('falls back to default blue for an unknown language', () => {
    const wrapper = mount(RepoCard, {
      props: { repo: { ...sampleRepo, language: 'MadeUpLang' } }
    })
    const dot = wrapper.find('span[style]')
    expect(dot.attributes('style')).toContain('#3b82f6')
  })

  it('omits the description when null', () => {
    const wrapper = mount(RepoCard, {
      props: { repo: { ...sampleRepo, description: null } }
    })
    expect(wrapper.find('p').exists()).toBe(false)
  })

  it('omits the language pill when language is null', () => {
    const wrapper = mount(RepoCard, {
      props: { repo: { ...sampleRepo, language: null } }
    })
    expect(wrapper.find('span[style]').exists()).toBe(false)
    expect(wrapper.text()).not.toContain('TypeScript')
  })
})
