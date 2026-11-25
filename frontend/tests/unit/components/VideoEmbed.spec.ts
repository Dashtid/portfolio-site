import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import VideoEmbed from '@/components/VideoEmbed.vue'

describe('VideoEmbed', () => {
  it('loads a www.youtube.com URL from the privacy-enhanced host', () => {
    const wrapper = mount(VideoEmbed, {
      props: { url: 'https://www.youtube.com/embed/dQw4w9WgXcQ' }
    })
    const iframe = wrapper.find('iframe')
    expect(iframe.exists()).toBe(true)
    expect(iframe.attributes('src')).toBe('https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ')
  })

  it('drops the si share parameter and keeps the others', () => {
    const wrapper = mount(VideoEmbed, {
      props: { url: 'https://www.youtube.com/embed/abc?si=XyZ123&start=10' }
    })
    expect(wrapper.find('iframe').attributes('src')).toBe(
      'https://www.youtube-nocookie.com/embed/abc?start=10'
    )
  })

  it('still rejects http and the bare youtube.com host', () => {
    for (const url of ['http://www.youtube.com/embed/abc', 'https://youtube.com/embed/abc']) {
      const wrapper = mount(VideoEmbed, { props: { url } })
      expect(wrapper.find('iframe').exists()).toBe(false)
    }
  })

  it('renders fallback for invalid URL host', () => {
    const wrapper = mount(VideoEmbed, {
      props: { url: 'https://evil.com/embed/abc' }
    })
    expect(wrapper.find('iframe').exists()).toBe(false)
    expect(wrapper.find('.video-fallback').exists()).toBe(true)
    expect(wrapper.find('.fallback-text').text()).toBe('Video could not be loaded')
  })

  it('passes youtube-nocookie.com URLs through unchanged', () => {
    const wrapper = mount(VideoEmbed, {
      props: { url: 'https://www.youtube-nocookie.com/embed/abc123' }
    })
    expect(wrapper.find('iframe').attributes('src')).toBe(
      'https://www.youtube-nocookie.com/embed/abc123'
    )
  })

  it('rejects URLs without /embed/ path', () => {
    const wrapper = mount(VideoEmbed, {
      props: { url: 'https://www.youtube.com/watch?v=abc' }
    })
    expect(wrapper.find('iframe').exists()).toBe(false)
  })

  it('renders the heading as a figcaption when provided', () => {
    const wrapper = mount(VideoEmbed, {
      props: {
        url: 'https://www.youtube.com/embed/abc',
        heading: 'Demo Video'
      }
    })
    expect(wrapper.find('figcaption.embed-caption').text()).toBe('Demo Video')
    // D3-FE-05: captions are no longer h2s — the page owns its heading levels
    expect(wrapper.find('h2').exists()).toBe(false)
  })

  it('does not force application mode or an extra tab stop on the iframe (D3-FE-05)', () => {
    const wrapper = mount(VideoEmbed, {
      props: { url: 'https://www.youtube.com/embed/abc' }
    })
    const iframe = wrapper.find('iframe')
    expect(iframe.attributes('role')).toBeUndefined()
    expect(iframe.attributes('tabindex')).toBeUndefined()
  })

  it('sets iframe title from props', () => {
    const wrapper = mount(VideoEmbed, {
      props: {
        url: 'https://www.youtube.com/embed/abc',
        title: 'Product walkthrough'
      }
    })
    expect(wrapper.find('iframe').attributes('title')).toBe('Product walkthrough')
  })

  it('iframe has lazy loading', () => {
    const wrapper = mount(VideoEmbed, {
      props: { url: 'https://www.youtube.com/embed/abc' }
    })
    expect(wrapper.find('iframe').attributes('loading')).toBe('lazy')
  })
})
