import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import MapEmbed from '@/components/MapEmbed.vue'

describe('MapEmbed', () => {
  it('renders iframe for valid Google Maps URL', () => {
    const wrapper = mount(MapEmbed, {
      props: { url: 'https://www.google.com/maps/embed?pb=abc123' }
    })
    const iframe = wrapper.find('iframe')
    expect(iframe.exists()).toBe(true)
    expect(iframe.attributes('src')).toContain('google.com/maps/embed')
  })

  it('renders fallback for invalid URL host', () => {
    const wrapper = mount(MapEmbed, {
      props: { url: 'https://evil.com/maps/embed?pb=abc' }
    })
    expect(wrapper.find('iframe').exists()).toBe(false)
    expect(wrapper.find('.map-fallback').exists()).toBe(true)
    expect(wrapper.find('.fallback-text').text()).toBe('Map could not be loaded')
  })

  it('rejects URLs without /maps/embed path', () => {
    const wrapper = mount(MapEmbed, {
      props: { url: 'https://www.google.com/search?q=abc' }
    })
    expect(wrapper.find('iframe').exists()).toBe(false)
  })

  it('renders heading when provided', () => {
    const wrapper = mount(MapEmbed, {
      props: {
        url: 'https://www.google.com/maps/embed?pb=abc',
        heading: 'Office Location'
      }
    })
    expect(wrapper.find('.map-heading').text()).toBe('Office Location')
  })

  it('omits heading element when heading is null', () => {
    const wrapper = mount(MapEmbed, {
      props: { url: 'https://www.google.com/maps/embed?pb=abc' }
    })
    expect(wrapper.find('.map-heading').exists()).toBe(false)
  })

  it('iframe has lazy loading and no-referrer policy', () => {
    const wrapper = mount(MapEmbed, {
      props: { url: 'https://www.google.com/maps/embed?pb=abc' }
    })
    const iframe = wrapper.find('iframe')
    expect(iframe.attributes('loading')).toBe('lazy')
    expect(iframe.attributes('referrerpolicy')).toBe('no-referrer-when-downgrade')
  })
})
