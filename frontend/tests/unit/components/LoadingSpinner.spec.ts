import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import LoadingSpinner from '@/components/LoadingSpinner.vue'

describe('LoadingSpinner', () => {
  it('renders with default props', () => {
    const wrapper = mount(LoadingSpinner)
    expect(wrapper.find('.loading-container').exists()).toBe(true)
    expect(wrapper.find('.loading-spinner.spinner-medium').exists()).toBe(true)
  })

  it('applies small size class', () => {
    const wrapper = mount(LoadingSpinner, { props: { size: 'small' } })
    expect(wrapper.find('.spinner-small').exists()).toBe(true)
  })

  it('applies large size class', () => {
    const wrapper = mount(LoadingSpinner, { props: { size: 'large' } })
    expect(wrapper.find('.spinner-large').exists()).toBe(true)
  })

  it('renders message when provided', () => {
    const wrapper = mount(LoadingSpinner, { props: { message: 'Please wait' } })
    expect(wrapper.find('.loading-message').text()).toBe('Please wait')
  })

  it('renders sr-only fallback when no message', () => {
    const wrapper = mount(LoadingSpinner)
    expect(wrapper.find('.sr-only').text()).toBe('Loading')
    expect(wrapper.find('.loading-message').exists()).toBe(false)
  })

  it('applies full-screen class when fullScreen is true', () => {
    const wrapper = mount(LoadingSpinner, { props: { fullScreen: true } })
    expect(wrapper.find('.loading-container.full-screen').exists()).toBe(true)
  })

  it('sets aria-label to message when provided', () => {
    const wrapper = mount(LoadingSpinner, { props: { message: 'Fetching data' } })
    expect(wrapper.find('.loading-container').attributes('aria-label')).toBe('Fetching data')
  })

  it('sets aria-label to "Loading" when no message', () => {
    const wrapper = mount(LoadingSpinner)
    expect(wrapper.find('.loading-container').attributes('aria-label')).toBe('Loading')
  })

  it('has role="status" for screen readers', () => {
    const wrapper = mount(LoadingSpinner)
    expect(wrapper.find('.loading-container').attributes('role')).toBe('status')
  })

  it('renders four spinner rings', () => {
    const wrapper = mount(LoadingSpinner)
    expect(wrapper.findAll('.spinner-ring')).toHaveLength(4)
  })
})
