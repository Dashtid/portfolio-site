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

  it('renders container with aria attributes', async () => {
    const wrapper = mount(ToastContainer, { attachTo: document.body })
    // The Teleport is client-only (v-if on a post-mount flag) so the first
    // render matches the prerendered HTML — the container therefore appears
    // one tick after mount, not synchronously with it.
    await wrapper.vm.$nextTick()
    const container = document.querySelector('.toast-container')
    expect(container).not.toBeNull()
    expect(container?.getAttribute('role')).toBe('region')
    expect(container?.getAttribute('aria-live')).toBe('polite')
    wrapper.unmount()
  })

  it('renders nothing on the first (pre-mount-flag) render', () => {
    // Regression guard for the hydration mismatch: vite-ssg never serializes
    // Teleport payloads, so the server HTML has an empty teleport anchor. If
    // the Teleport ever renders during the FIRST client render again, Vue
    // reports "Hydration completed but contains mismatches." on every page
    // load. Asserting the synchronous-mount DOM is empty is what makes the
    // v-if load-bearing — without this, deleting it still passes every other
    // test in this file.
    const wrapper = mount(ToastContainer, { attachTo: document.body })
    expect(document.querySelector('.toast-container')).toBeNull()
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
