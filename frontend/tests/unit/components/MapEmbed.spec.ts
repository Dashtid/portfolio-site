import { describe, it, expect, vi, afterEach } from 'vitest'
import { flushPromises, mount } from '@vue/test-utils'
import { createSSRApp } from 'vue'
import { renderToString } from 'vue/server-renderer'
import MapEmbed from '@/components/MapEmbed.vue'

const MAP = 'https://www.google.com/maps/embed?pb=abc123'
const NOTICE =
  'Loads Google Maps, which may store data on your device. ' +
  'Nothing is requested from Google until you press the button.'

// Mounts the component and presses the placeholder's button.
const loadMap = async (props: { url: string; title?: string }) => {
  const wrapper = mount(MapEmbed, { props })
  await wrapper.get('.embed-facade button').trigger('click')
  await flushPromises()
  return wrapper
}

describe('MapEmbed', () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('renders a placeholder and no iframe until the button is pressed', () => {
    const wrapper = mount(MapEmbed, { props: { url: MAP } })
    expect(wrapper.find('iframe').exists()).toBe(false)
    expect(wrapper.find('.embed-facade').exists()).toBe(true)
    expect(wrapper.get('.embed-facade button').attributes('type')).toBe('button')
    expect(wrapper.get('.embed-facade p').text()).toBe(NOTICE)
    // The placeholder links nowhere.
    expect(wrapper.find('a').exists()).toBe(false)
  })

  it('names the button after the map and hides its icon from screen readers', () => {
    const wrapper = mount(MapEmbed, { props: { url: MAP, title: 'Office location' } })
    const button = wrapper.get('.embed-facade button')
    expect(button.attributes('aria-label')).toBe('Show map: Office location')
    // The accessible name starts with the visible label.
    expect(button.text()).toBe('Show map')
    expect(button.get('svg').attributes('aria-hidden')).toBe('true')
  })

  it('describes the button by the notice', () => {
    const wrapper = mount(MapEmbed, { props: { url: MAP } })
    const describedBy = wrapper.get('.embed-facade button').attributes('aria-describedby')
    expect(describedBy).toBeTruthy()
    expect(wrapper.get(`[id="${describedBy}"]`).text()).toBe(NOTICE)
  })

  it('renders the iframe for a valid Google Maps URL after a click', async () => {
    const wrapper = await loadMap({ url: MAP })
    expect(wrapper.find('.embed-facade').exists()).toBe(false)
    expect(wrapper.get('iframe').attributes('src')).toBe(
      'https://www.google.com/maps/embed?pb=abc123&hl=en'
    )
  })

  it('appends hl=en to the embed URL without duplicating an existing hl param (D3-FE-05)', async () => {
    const withQuery = await loadMap({ url: 'https://www.google.com/maps/embed?pb=abc' })
    expect(withQuery.get('iframe').attributes('src')).toBe(
      'https://www.google.com/maps/embed?pb=abc&hl=en'
    )

    const alreadyLocalized = await loadMap({
      url: 'https://www.google.com/maps/embed?pb=abc&hl=de'
    })
    expect(alreadyLocalized.get('iframe').attributes('src')).toBe(
      'https://www.google.com/maps/embed?pb=abc&hl=de'
    )
  })

  it('moves focus to the iframe after the click', async () => {
    // A spy, not document.activeElement: happy-dom logs an error for every
    // iframe connected to its document. visual.spec.ts checks the focus
    // itself in Chromium.
    const focus = vi.spyOn(HTMLElement.prototype, 'focus')
    const wrapper = await loadMap({ url: MAP })
    expect(focus.mock.contexts).toHaveLength(1)
    expect(focus.mock.contexts[0]).toBe(wrapper.get('iframe').element)
  })

  it('gives the iframe its title, the trimmed referrer and no lazy loading', async () => {
    const wrapper = await loadMap({ url: MAP, title: 'Office location' })
    const iframe = wrapper.get('iframe')
    expect(iframe.attributes('title')).toBe('Office location')
    expect(iframe.attributes('referrerpolicy')).toBe('strict-origin-when-cross-origin')
    expect(iframe.attributes('loading')).toBeUndefined()
    expect(iframe.attributes('allowfullscreen')).toBeDefined()
    expect(iframe.attributes('allow')).toBeUndefined()
  })

  it('does not force application mode or an extra tab stop on the iframe (D3-FE-05)', async () => {
    const wrapper = await loadMap({ url: MAP })
    const iframe = wrapper.get('iframe')
    expect(iframe.attributes('role')).toBeUndefined()
    expect(iframe.attributes('tabindex')).toBeUndefined()
  })

  it('renders fallback for invalid URL host', () => {
    const wrapper = mount(MapEmbed, {
      props: { url: 'https://evil.com/maps/embed?pb=abc' }
    })
    expect(wrapper.find('.embed-facade').exists()).toBe(false)
    expect(wrapper.find('iframe').exists()).toBe(false)
    expect(wrapper.find('.map-fallback').exists()).toBe(true)
    expect(wrapper.find('.fallback-text').text()).toBe('Map could not be loaded')
  })

  it('rejects URLs without /maps/embed path', () => {
    const wrapper = mount(MapEmbed, {
      props: { url: 'https://www.google.com/search?q=abc' }
    })
    expect(wrapper.find('.embed-facade').exists()).toBe(false)
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

  it('renders the placeholder, and no iframe, on the server', async () => {
    const html = await renderToString(createSSRApp(MapEmbed, { url: MAP, title: 'Office' }))
    expect(html).not.toMatch(/<iframe/i)
    expect(html).toContain('embed-facade')
    const describedBy = html.match(/aria-describedby="([^"]+)"/)?.[1]
    expect(describedBy).toBeTruthy()
    expect(html).toContain(`id="${describedBy}"`)
  })

  it('hydrates the server markup without a mismatch, then loads on a click', async () => {
    const props = { url: MAP, title: 'Office' }
    const container = document.createElement('div')
    container.innerHTML = await renderToString(createSSRApp(MapEmbed, props))
    const warn = vi.spyOn(console, 'warn')
    const error = vi.spyOn(console, 'error')
    const app = createSSRApp(MapEmbed, props)
    app.mount(container)
    const logged = [...warn.mock.calls, ...error.mock.calls].map(args => args.join(' '))
    expect(logged.filter(line => /hydration/i.test(line))).toEqual([])
    container.querySelector<HTMLButtonElement>('.embed-facade button')!.click()
    await flushPromises()
    expect(container.querySelector('iframe')?.getAttribute('src')).toBe(
      'https://www.google.com/maps/embed?pb=abc123&hl=en'
    )
    app.unmount()
  })
})
