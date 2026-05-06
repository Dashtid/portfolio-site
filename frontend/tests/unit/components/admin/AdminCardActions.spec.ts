import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import AdminCardActions from '@/components/admin/AdminCardActions.vue'

describe('AdminCardActions', () => {
  it('renders both edit and delete buttons', () => {
    const wrapper = mount(AdminCardActions, { props: { itemName: 'Acme' } })
    expect(wrapper.find('.edit-btn').exists()).toBe(true)
    expect(wrapper.find('.delete-btn').exists()).toBe(true)
  })

  it('exposes aria-labels that include the item name', () => {
    const wrapper = mount(AdminCardActions, { props: { itemName: 'Acme' } })
    expect(wrapper.find('.edit-btn').attributes('aria-label')).toBe('Edit Acme')
    expect(wrapper.find('.delete-btn').attributes('aria-label')).toBe('Delete Acme')
  })

  it('emits edit when the edit button is clicked', async () => {
    const wrapper = mount(AdminCardActions, { props: { itemName: 'X' } })
    await wrapper.find('.edit-btn').trigger('click')
    expect(wrapper.emitted('edit')).toHaveLength(1)
    expect(wrapper.emitted('delete')).toBeUndefined()
  })

  it('emits delete when the delete button is clicked', async () => {
    const wrapper = mount(AdminCardActions, { props: { itemName: 'X' } })
    await wrapper.find('.delete-btn').trigger('click')
    expect(wrapper.emitted('delete')).toHaveLength(1)
    expect(wrapper.emitted('edit')).toBeUndefined()
  })

  it('renders SVG icons inside each button', () => {
    const wrapper = mount(AdminCardActions, { props: { itemName: 'X' } })
    expect(wrapper.find('.edit-btn svg').exists()).toBe(true)
    expect(wrapper.find('.delete-btn svg').exists()).toBe(true)
  })
})
