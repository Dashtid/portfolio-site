import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import ToastContainer from '@/components/ToastContainer.vue'
import { useToast } from '@/composables/useToast'

describe('ToastContainer', () => {
  beforeEach(() => {
    useToast().clear()
    vi.useFakeTimers()
  })

  afterEach(() => {
    useToast().clear()
    vi.useRealTimers()
  })

  it('renders container with aria attributes', () => {
    const wrapper = mount(ToastContainer, { attachTo: document.body })
    const container = document.querySelector('.toast-container')
    expect(container).not.toBeNull()
    expect(container?.getAttribute('role')).toBe('region')
    expect(container?.getAttribute('aria-live')).toBe('polite')
    wrapper.unmount()
  })

  it('displays a success toast', async () => {
    const wrapper = mount(ToastContainer, { attachTo: document.body })
    useToast().success('Saved!')
    await wrapper.vm.$nextTick()

    const toast = document.querySelector('.toast--success')
    expect(toast).not.toBeNull()
    expect(toast?.querySelector('.toast__message')?.textContent).toBe('Saved!')
    wrapper.unmount()
  })

  it('displays an error toast', async () => {
    const wrapper = mount(ToastContainer, { attachTo: document.body })
    useToast().error('Failed!')
    await wrapper.vm.$nextTick()

    const toast = document.querySelector('.toast--error')
    expect(toast).not.toBeNull()
    expect(toast?.querySelector('.toast__message')?.textContent).toBe('Failed!')
    wrapper.unmount()
  })

  it('displays a warning toast', async () => {
    const wrapper = mount(ToastContainer, { attachTo: document.body })
    useToast().warning('Careful!')
    await wrapper.vm.$nextTick()

    expect(document.querySelector('.toast--warning')).not.toBeNull()
    wrapper.unmount()
  })

  it('displays an info toast', async () => {
    const wrapper = mount(ToastContainer, { attachTo: document.body })
    useToast().info('FYI')
    await wrapper.vm.$nextTick()

    expect(document.querySelector('.toast--info')).not.toBeNull()
    wrapper.unmount()
  })

  it('removes toast when close button is clicked', async () => {
    const wrapper = mount(ToastContainer, { attachTo: document.body })
    useToast().info('Message')
    await wrapper.vm.$nextTick()

    const closeBtn = document.querySelector<HTMLButtonElement>('.toast__close')
    expect(closeBtn).not.toBeNull()
    closeBtn!.click()
    await wrapper.vm.$nextTick()

    expect(document.querySelector('.toast')).toBeNull()
    wrapper.unmount()
  })

  it('close button has aria-label', async () => {
    const wrapper = mount(ToastContainer, { attachTo: document.body })
    useToast().info('Message')
    await wrapper.vm.$nextTick()

    const closeBtn = document.querySelector('.toast__close')
    expect(closeBtn?.getAttribute('aria-label')).toBe('Dismiss notification')
    wrapper.unmount()
  })
})
