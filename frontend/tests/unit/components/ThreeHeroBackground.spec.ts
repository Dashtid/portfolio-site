import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import ThreeHeroBackground from '@/components/ThreeHeroBackground.vue'

// Mock three so the component doesn't actually try to load WebGL
vi.mock('three', () => ({
  Scene: vi.fn(() => ({ add: vi.fn(), remove: vi.fn() })),
  PerspectiveCamera: vi.fn(() => ({
    position: { z: 0 },
    aspect: 1,
    updateProjectionMatrix: vi.fn()
  })),
  WebGLRenderer: vi.fn(() => ({
    setSize: vi.fn(),
    setPixelRatio: vi.fn(),
    render: vi.fn(),
    dispose: vi.fn(),
    domElement: document.createElement('canvas')
  })),
  BufferGeometry: vi.fn(() => ({ setAttribute: vi.fn(), dispose: vi.fn() })),
  BufferAttribute: vi.fn(),
  PointsMaterial: vi.fn(() => ({ dispose: vi.fn() })),
  Points: vi.fn(() => ({
    rotation: { x: 0, y: 0 },
    geometry: { dispose: vi.fn() },
    material: { dispose: vi.fn() }
  }))
}))

describe('ThreeHeroBackground', () => {
  beforeEach(() => {
    // Mock matchMedia
    window.matchMedia = vi.fn().mockImplementation(() => ({
      matches: false,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn()
    }))
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('renders a canvas element', () => {
    const wrapper = mount(ThreeHeroBackground)
    expect(wrapper.find('canvas.hero-canvas').exists()).toBe(true)
  })

  it('canvas is marked as decorative with aria-hidden', () => {
    const wrapper = mount(ThreeHeroBackground)
    expect(wrapper.find('canvas').attributes('aria-hidden')).toBe('true')
  })

  it('gracefully handles WebGL unavailability', () => {
    // happy-dom does not provide WebGL context, so getContext returns null.
    // The component logs a warning and early-returns without crashing.
    const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})
    const wrapper = mount(ThreeHeroBackground)

    // Component mounted without throwing
    expect(wrapper.exists()).toBe(true)
    warnSpy.mockRestore()
  })

  it('unmounts cleanly', () => {
    const wrapper = mount(ThreeHeroBackground)
    expect(() => wrapper.unmount()).not.toThrow()
  })
})
