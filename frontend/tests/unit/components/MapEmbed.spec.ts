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

  it('renders the heading as a figcaption when provided', () => {
    const wrapper = mount(MapEmbed, {
      props: {
        url: 'https://www.google.com/maps/embed?pb=abc',
        heading: 'Office Location'
      }
    })
    expect(wrapper.find('figcaption.embed-caption').text()).toBe('Office Location')
    // D3-FE-05: captions are no longer h2s — the page owns its heading levels
    expect(wrapper.find('h2').exists()).toBe(false)
  })

  it('omits the caption element when heading is null', () => {
    const wrapper = mount(MapEmbed, {
      props: { url: 'https://www.google.com/maps/embed?pb=abc' }
    })
    expect(wrapper.find('.embed-caption').exists()).toBe(false)
  })

  it('appends hl=en to the embed URL without duplicating an existing hl param (D3-FE-05)', () => {
    const withQuery = mount(MapEmbed, {
      props: { url: 'https://www.google.com/maps/embed?pb=abc' }
    })
    expect(withQuery.find('iframe').attributes('src')).toBe(
      'https://www.google.com/maps/embed?pb=abc&hl=en'
    )

    const alreadyLocalized = mount(MapEmbed, {
      props: { url: 'https://www.google.com/maps/embed?pb=abc&hl=de' }
    })
    expect(alreadyLocalized.find('iframe').attributes('src')).toBe(
      'https://www.google.com/maps/embed?pb=abc&hl=de'
    )
  })

  it('does not force application mode or an extra tab stop on the iframe (D3-FE-05)', () => {
    const wrapper = mount(MapEmbed, {
      props: { url: 'https://www.google.com/maps/embed?pb=abc' }
    })
    const iframe = wrapper.find('iframe')
    expect(iframe.attributes('role')).toBeUndefined()
    expect(iframe.attributes('tabindex')).toBeUndefined()
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
