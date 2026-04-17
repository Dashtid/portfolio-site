import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import { createRouter, createMemoryHistory, Router } from 'vue-router'
import ErrorBoundary from '@/components/ErrorBoundary.vue'

vi.mock('@/utils/logger', () => ({
  errorLogger: { error: vi.fn() }
}))

describe('ErrorBoundary', () => {
  let router: Router

  beforeEach(async () => {
    router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: '/', component: { template: '<div>Home</div>' } },
        { path: '/other', component: { template: '<div>Other</div>' } }
      ]
    })
    await router.push('/')
    await router.isReady()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('renders slot content when no error', () => {
    const wrapper = mount(ErrorBoundary, {
      global: { plugins: [router] },
      slots: { default: '<div class="child">Child content</div>' }
    })
    expect(wrapper.find('.child').exists()).toBe(true)
    expect(wrapper.find('.error-boundary').exists()).toBe(false)
  })

  it('shows error UI when showError is called', async () => {
    const wrapper = mount(ErrorBoundary, {
      global: { plugins: [router] }
    })
    ;(wrapper.vm as unknown as { showError: (e: Error) => void }).showError(new Error('Boom'))
    await wrapper.vm.$nextTick()

    expect(wrapper.find('.error-boundary').exists()).toBe(true)
    expect(wrapper.find('.error-title').text()).toBe('Oops! Something went wrong')
  })

  it('displays custom title and message props', async () => {
    const wrapper = mount(ErrorBoundary, {
      global: { plugins: [router] },
      props: { title: 'Custom Title', message: 'Custom message' }
    })
    ;(wrapper.vm as unknown as { showError: (e: Error) => void }).showError(new Error('Boom'))
    await wrapper.vm.$nextTick()

    expect(wrapper.find('.error-title').text()).toBe('Custom Title')
    expect(wrapper.find('.error-message').text()).toBe('Custom message')
  })

  it('renders Try Again and Go to Homepage buttons', async () => {
    const wrapper = mount(ErrorBoundary, {
      global: { plugins: [router] }
    })
    ;(wrapper.vm as unknown as { showError: (e: Error) => void }).showError(new Error('Boom'))
    await wrapper.vm.$nextTick()

    expect(wrapper.find('.btn-retry').text()).toBe('Try Again')
    expect(wrapper.find('.btn-home').text()).toBe('Go to Homepage')
  })

  it('calls onRetry prop when Try Again is clicked', async () => {
    const onRetry = vi.fn()
    const wrapper = mount(ErrorBoundary, {
      global: { plugins: [router] },
      props: { onRetry }
    })
    ;(wrapper.vm as unknown as { showError: (e: Error) => void }).showError(new Error('Boom'))
    await wrapper.vm.$nextTick()

    await wrapper.find('.btn-retry').trigger('click')
    expect(onRetry).toHaveBeenCalled()
  })

  it('navigates to / when Go to Homepage is clicked', async () => {
    await router.push('/other')
    const wrapper = mount(ErrorBoundary, {
      global: { plugins: [router] }
    })
    ;(wrapper.vm as unknown as { showError: (e: Error) => void }).showError(new Error('Boom'))
    await wrapper.vm.$nextTick()

    await wrapper.find('.btn-home').trigger('click')
    await router.isReady()
    await new Promise(resolve => setTimeout(resolve, 0))
    expect(router.currentRoute.value.path).toBe('/')
  })

  it('accepts error info object with message and context', async () => {
    const wrapper = mount(ErrorBoundary, {
      global: { plugins: [router] },
      props: { showDetails: true }
    })
    ;(
      wrapper.vm as unknown as { showError: (e: { message: string; context: string }) => void }
    ).showError({ message: 'Failed', context: 'API call' })
    await wrapper.vm.$nextTick()

    const details = wrapper.find('.error-details')
    expect(details.exists()).toBe(true)
    expect(details.text()).toContain('Failed')
    expect(details.text()).toContain('API call')
  })
})
