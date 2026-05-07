import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import DashboardOverview from '@/components/admin/DashboardOverview.vue'

// Minimal router so the <router-link>s in the action buttons resolve.
const makeRouter = () =>
  createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/admin/companies', component: { template: '<div />' } },
      { path: '/admin/projects', component: { template: '<div />' } },
      { path: '/admin/analytics', component: { template: '<div />' } }
    ]
  })

const baseProps = {
  companiesCount: 2,
  skillsCount: 3,
  projectsCount: 4,
  featuredCount: 1,
  loadError: null
}

describe('DashboardOverview', () => {
  it('renders a stat card per metric with the expected counts', () => {
    const wrapper = mount(DashboardOverview, {
      props: baseProps,
      global: { plugins: [makeRouter()] }
    })

    const values = wrapper.findAll('.stat-value').map(el => el.text())
    expect(values).toEqual(['2', '3', '4', '1'])

    const labels = wrapper.findAll('.stat-label').map(el => el.text())
    expect(labels).toEqual(['Companies', 'Skills', 'Projects', 'Featured'])
  })

  it('renders all four quick-action buttons in order', () => {
    const wrapper = mount(DashboardOverview, {
      props: baseProps,
      global: { plugins: [makeRouter()] }
    })

    const labels = wrapper.findAll('.action-button').map(el => el.text())
    expect(labels).toEqual(['Add Experience', 'New Project', 'View Analytics', 'View Site'])
  })

  it('opens the View Site link in a new tab', () => {
    const wrapper = mount(DashboardOverview, {
      props: baseProps,
      global: { plugins: [makeRouter()] }
    })
    const viewSite = wrapper.find('a.action-button[href="/"]')
    expect(viewSite.exists()).toBe(true)
    expect(viewSite.attributes('target')).toBe('_blank')
  })

  it('hides the error alert when loadError is null', () => {
    const wrapper = mount(DashboardOverview, {
      props: baseProps,
      global: { plugins: [makeRouter()] }
    })
    expect(wrapper.find('.error-alert').exists()).toBe(false)
  })

  it('shows the error alert + retry button when loadError is set', () => {
    const wrapper = mount(DashboardOverview, {
      props: { ...baseProps, loadError: 'Backend down' },
      global: { plugins: [makeRouter()] }
    })
    const alert = wrapper.find('.error-alert')
    expect(alert.exists()).toBe(true)
    expect(alert.attributes('role')).toBe('alert')
    expect(alert.text()).toContain('Backend down')
    expect(wrapper.find('.retry-button').exists()).toBe(true)
  })

  it('emits retry when the retry button is clicked', async () => {
    const wrapper = mount(DashboardOverview, {
      props: { ...baseProps, loadError: 'oops' },
      global: { plugins: [makeRouter()] }
    })
    await wrapper.find('.retry-button').trigger('click')
    expect(wrapper.emitted('retry')).toHaveLength(1)
  })

  it('handles zero counts (empty state)', () => {
    const wrapper = mount(DashboardOverview, {
      props: {
        companiesCount: 0,
        skillsCount: 0,
        projectsCount: 0,
        featuredCount: 0,
        loadError: null
      },
      global: { plugins: [makeRouter()] }
    })
    const values = wrapper.findAll('.stat-value').map(el => el.text())
    expect(values).toEqual(['0', '0', '0', '0'])
  })
})
