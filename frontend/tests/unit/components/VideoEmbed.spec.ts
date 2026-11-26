import { describe, it, expect, vi, afterEach } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createSSRApp, h } from 'vue'
import { renderToString } from 'vue/server-renderer'
import VideoEmbed from '@/components/VideoEmbed.vue'

const VIDEO = 'https://www.youtube.com/embed/dQw4w9WgXcQ'
const NOTICE =
  'Plays from YouTube, run by Google, which may store data on your device. ' +
  'Nothing is requested from YouTube until you press play.'

// Mounts the component and presses the placeholder's button.
const loadVideo = async (props: { url: string; title?: string }) => {
  const wrapper = mount(VideoEmbed, { props })
  await wrapper.get('.embed-facade button').trigger('click')
  await flushPromises()
  return wrapper
}

describe('VideoEmbed', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('renders a placeholder and no iframe until the button is pressed', () => {
    const wrapper = mount(VideoEmbed, { props: { url: VIDEO } })
    expect(wrapper.find('iframe').exists()).toBe(false)
    expect(wrapper.find('.embed-facade').exists()).toBe(true)
    expect(wrapper.get('.embed-facade button').attributes('type')).toBe('button')
    expect(wrapper.get('.embed-facade p').text()).toBe(NOTICE)
  })

  it('names the button after the video and hides its icon from screen readers', () => {
    const wrapper = mount(VideoEmbed, {
      props: { url: VIDEO, title: 'Product walkthrough' }
    })
    const button = wrapper.get('.embed-facade button')
    expect(button.attributes('aria-label')).toBe('Play video: Product walkthrough')
    // The accessible name starts with the visible label.
    expect(button.text()).toBe('Play video')
    expect(button.get('svg').attributes('aria-hidden')).toBe('true')
  })

  it('describes the button by the notice', () => {
    const wrapper = mount(VideoEmbed, { props: { url: VIDEO } })
    const describedBy = wrapper.get('.embed-facade button').attributes('aria-describedby')
    expect(describedBy).toBeTruthy()
    expect(wrapper.get(`[id="${describedBy}"]`).text()).toBe(NOTICE)
  })

  it('gives each placeholder its own notice id', () => {
    const wrapper = mount({
      render: () => h('div', [h(VideoEmbed, { url: VIDEO }), h(VideoEmbed, { url: VIDEO })])
    })
    const ids = wrapper.findAll('.embed-facade p').map(p => p.attributes('id'))
    expect(ids).toHaveLength(2)
    expect(new Set(ids).size).toBe(2)
  })

  it('links to the video on youtube.com, in a new tab', () => {
    const wrapper = mount(VideoEmbed, { props: { url: VIDEO } })
    const link = wrapper.get('.embed-facade a')
    expect(link.attributes('href')).toBe('https://www.youtube.com/watch?v=dQw4w9WgXcQ')
    expect(link.attributes('target')).toBe('_blank')
    expect(link.attributes('rel')).toBe('noopener noreferrer')
    expect(link.text()).toBe('Watch on YouTube (opens in a new tab)')
  })

  it('builds the watch link only from an 11-character video id', () => {
    for (const url of [
      'https://www.youtube.com/embed/abc',
      'https://www.youtube.com/embed/dQw4w9WgXcQ/extra',
      'https://www.youtube.com/embed/videoseries?list=PL0123456789',
      'https://www.youtube.com/embed/live_stream?channel=UC0123456789abcdefghijkl'
    ]) {
      const wrapper = mount(VideoEmbed, { props: { url } })
      expect(wrapper.find('.embed-facade').exists()).toBe(true)
      expect(wrapper.find('.embed-facade a').exists()).toBe(false)
    }
  })

  it('loads a www.youtube.com URL from the privacy-enhanced host, playing, after a click', async () => {
    const wrapper = await loadVideo({ url: VIDEO })
    expect(wrapper.find('.embed-facade').exists()).toBe(false)
    expect(wrapper.get('iframe').attributes('src')).toBe(
      'https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ?autoplay=1'
    )
  })

  it('drops the si share parameter and keeps the others', async () => {
    const wrapper = await loadVideo({ url: 'https://www.youtube.com/embed/abc?si=XyZ123&start=10' })
    expect(wrapper.get('iframe').attributes('src')).toBe(
      'https://www.youtube-nocookie.com/embed/abc?start=10&autoplay=1'
    )
  })

  it('passes youtube-nocookie.com URLs through, adding autoplay', async () => {
    const wrapper = await loadVideo({ url: 'https://www.youtube-nocookie.com/embed/abc123' })
    expect(wrapper.get('iframe').attributes('src')).toBe(
      'https://www.youtube-nocookie.com/embed/abc123?autoplay=1'
    )
  })

  it('moves focus to the iframe after the click', async () => {
    // A spy, not document.activeElement: happy-dom logs an error for every
    // iframe connected to its document. visual.spec.ts checks the focus
    // itself in Chromium.
    const focus = vi.spyOn(HTMLElement.prototype, 'focus')
    const wrapper = await loadVideo({ url: VIDEO })
    expect(focus.mock.contexts).toHaveLength(1)
    expect(focus.mock.contexts[0]).toBe(wrapper.get('iframe').element)
  })

  it('gives the iframe its title, the trimmed referrer and no lazy loading', async () => {
    const wrapper = await loadVideo({ url: VIDEO, title: 'Product walkthrough' })
    const iframe = wrapper.get('iframe')
    expect(iframe.attributes('title')).toBe('Product walkthrough')
    expect(iframe.attributes('referrerpolicy')).toBe('strict-origin-when-cross-origin')
    expect(iframe.attributes('loading')).toBeUndefined()
    expect(iframe.attributes('allowfullscreen')).toBeDefined()
    expect(iframe.attributes('allow')).toBe('autoplay; encrypted-media; picture-in-picture')
  })

  it('does not force application mode or an extra tab stop on the iframe (D3-FE-05)', async () => {
    const wrapper = await loadVideo({ url: VIDEO })
    const iframe = wrapper.get('iframe')
    expect(iframe.attributes('role')).toBeUndefined()
    expect(iframe.attributes('tabindex')).toBeUndefined()
  })

  it('still rejects http and the bare youtube.com host', () => {
    for (const url of ['http://www.youtube.com/embed/abc', 'https://youtube.com/embed/abc']) {
      const wrapper = mount(VideoEmbed, { props: { url } })
      expect(wrapper.find('.embed-facade').exists()).toBe(false)
      expect(wrapper.find('iframe').exists()).toBe(false)
    }
  })

  it('renders fallback for invalid URL host', () => {
    const wrapper = mount(VideoEmbed, {
      props: { url: 'https://evil.com/embed/abc' }
    })
    expect(wrapper.find('.embed-facade').exists()).toBe(false)
    expect(wrapper.find('iframe').exists()).toBe(false)
    expect(wrapper.find('.video-fallback').exists()).toBe(true)
    expect(wrapper.find('.fallback-text').text()).toBe('Video could not be loaded')
  })

  it('rejects URLs without /embed/ path', () => {
    const wrapper = mount(VideoEmbed, {
      props: { url: 'https://www.youtube.com/watch?v=abc' }
    })
    expect(wrapper.find('.embed-facade').exists()).toBe(false)
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

  it('renders the placeholder, and no iframe, on the server', async () => {
    const html = await renderToString(createSSRApp(VideoEmbed, { url: VIDEO, title: 'Demo' }))
    expect(html).not.toMatch(/<iframe/i)
    expect(html).toContain('embed-facade')
    const describedBy = html.match(/aria-describedby="([^"]+)"/)?.[1]
    expect(describedBy).toBeTruthy()
    expect(html).toContain(`id="${describedBy}"`)
  })

  it('hydrates the server markup without a mismatch, then loads on a click', async () => {
    const props = { url: VIDEO, title: 'Demo' }
    const container = document.createElement('div')
    container.innerHTML = await renderToString(createSSRApp(VideoEmbed, props))
    const warn = vi.spyOn(console, 'warn')
    const error = vi.spyOn(console, 'error')
    const app = createSSRApp(VideoEmbed, props)
    app.mount(container)
    const logged = [...warn.mock.calls, ...error.mock.calls].map(args => args.join(' '))
    expect(logged.filter(line => /hydration/i.test(line))).toEqual([])
    container.querySelector<HTMLButtonElement>('.embed-facade button')!.click()
    await flushPromises()
    expect(container.querySelector('iframe')?.getAttribute('src')).toBe(
      'https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ?autoplay=1'
    )
    app.unmount()
  })
})
