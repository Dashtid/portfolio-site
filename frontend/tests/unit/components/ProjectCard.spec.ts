import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import ProjectCard from '@/components/ProjectCard.vue'
import type { Project } from '@/types'

vi.mock('@/composables/useOutboundTracking', () => ({
  useOutboundTracking: () => ({ trackOutbound: vi.fn() })
}))

const project = (overrides: Partial<Project> = {}): Project =>
  ({
    id: 'p1',
    name: 'subvectors',
    description: 'Cited, versioned conformance vectors for CI/CD OIDC trust decisions.',
    technologies: ['Python', 'OIDC', 'GitHub Actions'],
    github_url: 'https://github.com/Dashtid/subvectors',
    live_url: null,
    featured: true,
    order_index: 1,
    ...overrides
  }) as Project

describe('ProjectCard', () => {
  it('renders the curated name, description and technologies', () => {
    const wrapper = mount(ProjectCard, { props: { project: project() } })
    expect(wrapper.text()).toContain('subvectors')
    expect(wrapper.text()).toContain('conformance vectors')
    const chips = wrapper.findAll('.badge').map(c => c.text())
    expect(chips).toEqual(['Python', 'OIDC', 'GitHub Actions'])
  })

  it('links to the repository and opens it safely', () => {
    const wrapper = mount(ProjectCard, { props: { project: project() } })
    const link = wrapper.find('a')
    expect(link.attributes('href')).toBe('https://github.com/Dashtid/subvectors')
    expect(link.attributes('target')).toBe('_blank')
    expect(link.attributes('rel')).toBe('noopener noreferrer')
    expect(link.attributes('aria-label')).toContain('opens in new tab')
  })

  it('falls back to live_url when there is no repository link', () => {
    const wrapper = mount(ProjectCard, {
      props: { project: project({ github_url: null, live_url: 'https://example.com' }) }
    })
    expect(wrapper.find('a').attributes('href')).toBe('https://example.com')
  })

  it('carries the .project-card behavior hook the animation and e2e rely on', () => {
    // Shared contract with RepoCard: HomeView's entrance animation and the
    // hover e2e test both select on this class.
    const wrapper = mount(ProjectCard, { props: { project: project() } })
    expect(wrapper.find('a').classes()).toContain('project-card')
  })

  it('omits the technology row entirely when there are no technologies', () => {
    const wrapper = mount(ProjectCard, { props: { project: project({ technologies: [] }) } })
    expect(wrapper.findAll('.badge')).toHaveLength(0)
  })
})
