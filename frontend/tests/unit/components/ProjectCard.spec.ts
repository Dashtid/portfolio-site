import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import ProjectCard from '@/components/ProjectCard.vue'

vi.mock('@/composables/useMicroInteractions', () => ({
  useTiltEffect: vi.fn()
}))

const baseProject = {
  name: 'Portfolio Site',
  description: 'Personal portfolio built with Vue and FastAPI',
  technologies: ['Vue', 'TypeScript', 'FastAPI'],
  github_url: 'https://github.com/user/portfolio',
  live_url: 'https://example.com',
  featured: false
}

describe('ProjectCard', () => {
  it('renders project name and description', () => {
    const wrapper = mount(ProjectCard, { props: { project: baseProject } })
    expect(wrapper.find('.project-title').text()).toBe('Portfolio Site')
    expect(wrapper.find('.project-description').text()).toBe(
      'Personal portfolio built with Vue and FastAPI'
    )
  })

  it('renders all tech tags', () => {
    const wrapper = mount(ProjectCard, { props: { project: baseProject } })
    const tags = wrapper.findAll('.tech-tag')
    expect(tags).toHaveLength(3)
    expect(tags.map(t => t.text())).toEqual(['Vue', 'TypeScript', 'FastAPI'])
  })

  it('renders empty tech stack when technologies is null', () => {
    const wrapper = mount(ProjectCard, {
      props: { project: { ...baseProject, technologies: [] } }
    })
    expect(wrapper.findAll('.tech-tag')).toHaveLength(0)
  })

  it('shows Featured badge when featured is true', () => {
    const wrapper = mount(ProjectCard, {
      props: { project: { ...baseProject, featured: true } }
    })
    expect(wrapper.find('.featured-badge').exists()).toBe(true)
  })

  it('omits Featured badge when featured is false', () => {
    const wrapper = mount(ProjectCard, { props: { project: baseProject } })
    expect(wrapper.find('.featured-badge').exists()).toBe(false)
  })

  it('renders GitHub link with secure rel', () => {
    const wrapper = mount(ProjectCard, { props: { project: baseProject } })
    const link = wrapper.find('.github-link')
    expect(link.attributes('href')).toBe('https://github.com/user/portfolio')
    expect(link.attributes('target')).toBe('_blank')
    expect(link.attributes('rel')).toBe('noopener noreferrer')
  })

  it('renders Live Demo link when live_url is present', () => {
    const wrapper = mount(ProjectCard, { props: { project: baseProject } })
    expect(wrapper.find('.live-link').exists()).toBe(true)
    expect(wrapper.find('.live-link').attributes('href')).toBe('https://example.com')
  })

  it('omits Live Demo link when live_url is empty', () => {
    const wrapper = mount(ProjectCard, {
      props: { project: { ...baseProject, live_url: '' } }
    })
    expect(wrapper.find('.live-link').exists()).toBe(false)
  })

  it('omits GitHub link when github_url is empty', () => {
    const wrapper = mount(ProjectCard, {
      props: { project: { ...baseProject, github_url: '' } }
    })
    expect(wrapper.find('.github-link').exists()).toBe(false)
  })

  it('sets aria-label with project name for accessibility', () => {
    const wrapper = mount(ProjectCard, { props: { project: baseProject } })
    expect(wrapper.find('.github-link').attributes('aria-label')).toContain('Portfolio Site')
    expect(wrapper.find('.live-link').attributes('aria-label')).toContain('Portfolio Site')
  })
})
