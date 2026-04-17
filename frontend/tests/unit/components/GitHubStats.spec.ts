import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import axios from 'axios'
import GitHubStats from '@/components/GitHubStats.vue'

vi.mock('axios')
vi.mock('@vueuse/core', () => ({
  useIntersectionObserver: (
    _target: unknown,
    callback: (entries: { isIntersecting: boolean }[]) => void
  ) => {
    // Defer so the returned { stop } is initialized before callback runs
    queueMicrotask(() => callback([{ isIntersecting: true }]))
    return { stop: vi.fn() }
  }
}))

const mockedAxios = vi.mocked(axios, true)

const mockStats = {
  public_repos: 42,
  total_stars: 100,
  followers: 25,
  total_forks: 10,
  top_languages: [
    { name: 'TypeScript', percentage: 60 },
    { name: 'Python', percentage: 30 },
    { name: 'Vue', percentage: 10 }
  ],
  featured_repos: [
    {
      name: 'cool-repo',
      description: 'A cool repo',
      html_url: 'https://github.com/user/cool-repo',
      language: 'TypeScript',
      stars: 50,
      forks: 5
    }
  ]
}

describe('GitHubStats', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('shows loading state initially then renders stats on success', async () => {
    mockedAxios.get.mockResolvedValueOnce({ data: mockStats })
    mockedAxios.isCancel.mockReturnValue(false)

    const wrapper = mount(GitHubStats)
    await flushPromises()

    expect(wrapper.find('.stats-container').exists()).toBe(true)
    expect(wrapper.find('.loading-spinner').exists()).toBe(false)
  })

  it('renders featured repos with name and description', async () => {
    mockedAxios.get.mockResolvedValueOnce({ data: mockStats })
    mockedAxios.isCancel.mockReturnValue(false)

    const wrapper = mount(GitHubStats)
    await flushPromises()

    expect(wrapper.find('.project-title').text()).toBe('cool-repo')
    expect(wrapper.find('.project-description').text()).toBe('A cool repo')
  })

  it('renders top languages with percentages', async () => {
    mockedAxios.get.mockResolvedValueOnce({ data: mockStats })
    mockedAxios.isCancel.mockReturnValue(false)

    const wrapper = mount(GitHubStats)
    await flushPromises()

    const langs = wrapper.findAll('.language-name')
    expect(langs).toHaveLength(3)
    expect(langs[0].text()).toBe('TypeScript')
  })

  it('repo cards use secure rel attributes', async () => {
    mockedAxios.get.mockResolvedValueOnce({ data: mockStats })
    mockedAxios.isCancel.mockReturnValue(false)

    const wrapper = mount(GitHubStats)
    await flushPromises()

    const link = wrapper.find('a.project-card')
    expect(link.attributes('target')).toBe('_blank')
    expect(link.attributes('rel')).toBe('noopener noreferrer')
  })

  it('progress bars have proper ARIA attributes', async () => {
    mockedAxios.get.mockResolvedValueOnce({ data: mockStats })
    mockedAxios.isCancel.mockReturnValue(false)

    const wrapper = mount(GitHubStats)
    await flushPromises()

    const bar = wrapper.find('.progress-bar')
    expect(bar.attributes('role')).toBe('progressbar')
    expect(bar.attributes('aria-valuenow')).toBe('60')
    expect(bar.attributes('aria-valuemin')).toBe('0')
    expect(bar.attributes('aria-valuemax')).toBe('100')
  })

  it('shows error state when API call fails', async () => {
    mockedAxios.get.mockRejectedValueOnce(new Error('Network error'))
    mockedAxios.isCancel.mockReturnValue(false)

    const wrapper = mount(GitHubStats)
    await flushPromises()

    expect(wrapper.find('.error-message').exists()).toBe(true)
    expect(wrapper.find('.retry-button').exists()).toBe(true)
  })

  it('shows empty state when response has no repos or languages', async () => {
    mockedAxios.get.mockResolvedValueOnce({
      data: { ...mockStats, featured_repos: [], top_languages: [] }
    })
    mockedAxios.isCancel.mockReturnValue(false)

    const wrapper = mount(GitHubStats)
    await flushPromises()

    expect(wrapper.find('.empty-state').exists()).toBe(true)
    expect(wrapper.find('.empty-state').text()).toContain('No GitHub repositories found')
  })

  it('retry button refetches data after error', async () => {
    mockedAxios.get
      .mockRejectedValueOnce(new Error('Network error'))
      .mockResolvedValueOnce({ data: mockStats })
    mockedAxios.isCancel.mockReturnValue(false)

    const wrapper = mount(GitHubStats)
    await flushPromises()

    expect(wrapper.find('.error-message').exists()).toBe(true)
    await wrapper.find('.retry-button').trigger('click')
    await flushPromises()

    expect(wrapper.find('.error-message').exists()).toBe(false)
    expect(wrapper.find('.stats-container').exists()).toBe(true)
  })
})
