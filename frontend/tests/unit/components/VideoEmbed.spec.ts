import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import VideoEmbed from '@/components/VideoEmbed.vue'

describe('VideoEmbed', () => {
  it('renders iframe for valid YouTube URL', () => {
    const wrapper = mount(VideoEmbed, {
      props: { url: 'https://www.youtube.com/embed/dQw4w9WgXcQ' }
    })
    const iframe = wrapper.find('iframe')
    expect(iframe.exists()).toBe(true)
    expect(iframe.attributes('src')).toBe('https://www.youtube.com/embed/dQw4w9WgXcQ')
  })

  it('renders fallback for invalid URL host', () => {
    const wrapper = mount(VideoEmbed, {
      props: { url: 'https://evil.com/embed/abc' }
    })
    expect(wrapper.find('iframe').exists()).toBe(false)
    expect(wrapper.find('.video-fallback').exists()).toBe(true)
    expect(wrapper.find('.fallback-text').text()).toBe('Video could not be loaded')
  })

  it('accepts youtube-nocookie.com URLs', () => {
    const wrapper = mount(VideoEmbed, {
      props: { url: 'https://www.youtube-nocookie.com/embed/abc123' }
    })
    expect(wrapper.find('iframe').exists()).toBe(true)
  })

  it('rejects URLs without /embed/ path', () => {
    const wrapper = mount(VideoEmbed, {
      props: { url: 'https://www.youtube.com/watch?v=abc' }
    })
    expect(wrapper.find('iframe').exists()).toBe(false)
  })

  it('renders heading when provided', () => {
    const wrapper = mount(VideoEmbed, {
      props: {
        url: 'https://www.youtube.com/embed/abc',
        heading: 'Demo Video'
      }
    })
    expect(wrapper.find('.video-heading').text()).toBe('Demo Video')
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
