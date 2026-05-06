import { describe, it, expect, vi } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import AdminFormModal from '@/components/admin/AdminFormModal.vue'

describe('AdminFormModal', () => {
  it('renders nothing when open is false', () => {
    const wrapper = mount(AdminFormModal, {
      props: { open: false, title: 'Add Thing' }
    })
    expect(wrapper.find('.modal-overlay').exists()).toBe(false)
  })

  it('renders the dialog with role + aria-modal when open', () => {
    const wrapper = mount(AdminFormModal, {
      props: { open: true, title: 'Add Thing' }
    })
    const overlay = wrapper.find('.modal-overlay')
    expect(overlay.exists()).toBe(true)
    expect(overlay.attributes('role')).toBe('dialog')
    expect(overlay.attributes('aria-modal')).toBe('true')
  })

  it('renders the title and links it via aria-labelledby', () => {
    const wrapper = mount(AdminFormModal, {
      props: { open: true, title: 'Add Company', titleId: 'co-modal-title' }
    })
    expect(wrapper.find('.modal-title').text()).toBe('Add Company')
    expect(wrapper.find('.modal-title').attributes('id')).toBe('co-modal-title')
    expect(wrapper.find('.modal-overlay').attributes('aria-labelledby')).toBe('co-modal-title')
  })

  it('renders default slot content', () => {
    const wrapper = mount(AdminFormModal, {
      props: { open: true, title: 'X' },
      slots: { default: '<form data-test="form"><input id="name" /></form>' }
    })
    expect(wrapper.find('[data-test="form"]').exists()).toBe(true)
  })

  it('emits close when the overlay is clicked', async () => {
    const wrapper = mount(AdminFormModal, { props: { open: true, title: 'X' } })
    await wrapper.find('.modal-overlay').trigger('click')
    expect(wrapper.emitted('close')).toHaveLength(1)
  })

  it('does NOT emit close when clicking inside the modal content', async () => {
    const wrapper = mount(AdminFormModal, {
      props: { open: true, title: 'X' },
      slots: { default: '<button data-test="inner">inside</button>' }
    })
    await wrapper.find('[data-test="inner"]').trigger('click')
    expect(wrapper.emitted('close')).toBeUndefined()
  })

  it('emits close on Escape', async () => {
    const wrapper = mount(AdminFormModal, { props: { open: true, title: 'X' } })
    await wrapper.find('.modal-overlay').trigger('keydown.escape')
    expect(wrapper.emitted('close')).toHaveLength(1)
  })

  it('applies the maxWidth prop as inline style', () => {
    const wrapper = mount(AdminFormModal, {
      props: { open: true, title: 'X', maxWidth: '720px' }
    })
    const content = wrapper.find('.modal-content')
    expect(content.attributes('style')).toContain('max-width: 720px')
  })

  it('activates focus trap when transitioning open=false -> true', async () => {
    const addSpy = vi.spyOn(document, 'addEventListener')

    const wrapper = mount(AdminFormModal, {
      props: { open: false, title: 'X' },
      slots: { default: '<input id="x" />' }
    })

    await wrapper.setProps({ open: true })
    await flushPromises()

    // useFocusTrap registers a 'keydown' listener on the document on activate
    expect(addSpy).toHaveBeenCalledWith('keydown', expect.any(Function))
    addSpy.mockRestore()
  })
})
