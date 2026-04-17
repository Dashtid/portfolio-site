import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import DocumentCard from '@/components/DocumentCard.vue'
import type { Document } from '@/types'

const baseDoc: Document = {
  id: 'doc-1',
  title: 'Bachelor Thesis',
  description: 'Thesis on applied cryptography',
  document_type: 'thesis',
  file_path: '/docs/thesis.pdf',
  file_size: 2_621_440,
  file_url: 'https://example.com/thesis.pdf',
  published_date: '2024-06-15',
  created_at: '2024-06-20T00:00:00Z'
}

describe('DocumentCard', () => {
  it('renders title and description', () => {
    const wrapper = mount(DocumentCard, { props: { document: baseDoc } })
    expect(wrapper.find('.document-title').text()).toBe('Bachelor Thesis')
    expect(wrapper.find('.document-description').text()).toBe('Thesis on applied cryptography')
  })

  it('maps document_type to human-readable label', () => {
    const wrapper = mount(DocumentCard, { props: { document: baseDoc } })
    expect(wrapper.find('.document-type').text()).toBe('Thesis')
  })

  it('falls back to raw document_type for unknown types', () => {
    const wrapper = mount(DocumentCard, {
      props: { document: { ...baseDoc, document_type: 'custom-type' } }
    })
    expect(wrapper.find('.document-type').text()).toBe('custom-type')
  })

  it('formats file size in MB', () => {
    const wrapper = mount(DocumentCard, { props: { document: baseDoc } })
    expect(wrapper.text()).toContain('2.5 MB')
  })

  it('formats small file size in KB', () => {
    const wrapper = mount(DocumentCard, {
      props: { document: { ...baseDoc, file_size: 512 } }
    })
    expect(wrapper.text()).toContain('512 Bytes')
  })

  it('handles zero file size', () => {
    const wrapper = mount(DocumentCard, {
      props: { document: { ...baseDoc, file_size: 0 } }
    })
    expect(wrapper.text()).toContain('0 Bytes')
  })

  it('shows "Unknown size" for negative file size', () => {
    const wrapper = mount(DocumentCard, {
      props: { document: { ...baseDoc, file_size: -1 } }
    })
    expect(wrapper.text()).toContain('Unknown size')
  })

  it('omits description when not provided', () => {
    const wrapper = mount(DocumentCard, {
      props: { document: { ...baseDoc, description: null } }
    })
    expect(wrapper.find('.document-description').exists()).toBe(false)
  })

  it('omits date when published_date is null', () => {
    const wrapper = mount(DocumentCard, {
      props: { document: { ...baseDoc, published_date: null } }
    })
    const metaItems = wrapper.findAll('.meta-item')
    expect(metaItems).toHaveLength(1)
  })

  it('download link has secure rel attributes', () => {
    const wrapper = mount(DocumentCard, { props: { document: baseDoc } })
    const link = wrapper.find('.download-link')
    expect(link.attributes('target')).toBe('_blank')
    expect(link.attributes('rel')).toBe('noopener noreferrer')
    expect(link.attributes('href')).toBe('https://example.com/thesis.pdf')
  })

  it('formats published date as Month Year', () => {
    const wrapper = mount(DocumentCard, { props: { document: baseDoc } })
    expect(wrapper.text()).toMatch(/June 2024/)
  })
})
