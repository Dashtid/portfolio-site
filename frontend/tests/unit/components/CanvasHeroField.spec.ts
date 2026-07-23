import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import CanvasHeroField from '@/components/CanvasHeroField.vue'

/**
 * D3-DSN-03 / D3-TEST-04: unit coverage for the Canvas2D signal field that
 * replaced ThreeHeroBackground (whose spec died with it). happy-dom has no
 * real 2D context, so getContext is stubbed with a call-recording fake —
 * enough to assert the drawing, lifecycle, and reduced-motion contracts.
 */

interface RecordingCtx {
  calls: Record<string, number>
  arcs: Array<[number, number, number]>
  setTransform: (...args: number[]) => void
  clearRect: () => void
  beginPath: () => void
  moveTo: () => void
  lineTo: () => void
  stroke: () => void
  arc: (x: number, y: number, r: number) => void
  fill: () => void
  strokeStyle: string
  fillStyle: string
  lineWidth: number
}

const makeCtx = (): RecordingCtx => {
  const ctx = {
    calls: {},
    arcs: [],
    strokeStyle: '',
    fillStyle: '',
    lineWidth: 0
  } as unknown as RecordingCtx
  for (const m of [
    'setTransform',
    'clearRect',
    'beginPath',
    'moveTo',
    'lineTo',
    'stroke',
    'fill'
  ] as const) {
    ;(ctx as unknown as Record<string, unknown>)[m] = vi.fn(() => {
      ctx.calls[m] = (ctx.calls[m] ?? 0) + 1
    })
  }
  ctx.arc = vi.fn((x: number, y: number, r: number) => {
    ctx.calls.arc = (ctx.calls.arc ?? 0) + 1
    ctx.arcs.push([x, y, r])
  })
  return ctx
}

const setReducedMotion = (matches: boolean): void => {
  vi.spyOn(window, 'matchMedia').mockImplementation(
    (query: string) =>
      ({
        matches: query.includes('prefers-reduced-motion') ? matches : false,
        media: query,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
        addListener: vi.fn(),
        removeListener: vi.fn(),
        onchange: null,
        dispatchEvent: vi.fn()
      }) as unknown as MediaQueryList
  )
}

describe('CanvasHeroField', () => {
  let ctx: RecordingCtx
  let getContextSpy: ReturnType<typeof vi.spyOn>

  beforeEach(() => {
    ctx = makeCtx()
    getContextSpy = vi
      .spyOn(HTMLCanvasElement.prototype, 'getContext')
      .mockReturnValue(ctx as unknown as CanvasRenderingContext2D)
    // clientWidth/Height are 0 in a detached happy-dom mount — give the
    // canvas a fake layout box so DPR sizing and draw math run.
    vi.spyOn(HTMLCanvasElement.prototype, 'clientWidth', 'get').mockReturnValue(800)
    vi.spyOn(HTMLCanvasElement.prototype, 'clientHeight', 'get').mockReturnValue(600)
  })

  afterEach(() => {
    vi.restoreAllMocks()
    vi.unstubAllGlobals()
  })

  it('renders a decorative canvas (aria-hidden, pointer-events handled in CSS)', () => {
    setReducedMotion(true)
    const wrapper = mount(CanvasHeroField)
    const canvas = wrapper.find('canvas')
    expect(canvas.exists()).toBe(true)
    expect(canvas.attributes('aria-hidden')).toBe('true')
    expect(canvas.attributes('data-testid')).toBe('hero-field')
    wrapper.unmount()
  })

  it('draws a static frame under reduced motion without starting a loop', () => {
    setReducedMotion(true)
    const rafSpy = vi.spyOn(window, 'requestAnimationFrame')
    const wrapper = mount(CanvasHeroField)

    // The static t=0 frame rendered: points (arc+fill) and links (stroke)
    expect(ctx.calls.arc).toBeGreaterThan(0)
    expect(ctx.calls.fill).toBeGreaterThan(0)
    // No animation loop was scheduled
    expect(rafSpy).not.toHaveBeenCalled()
    wrapper.unmount()
  })

  it('is deterministic: two mounts draw the identical seeded constellation', () => {
    setReducedMotion(true)
    const w1 = mount(CanvasHeroField)
    const first = [...ctx.arcs]
    w1.unmount()

    ctx.arcs.length = 0
    const w2 = mount(CanvasHeroField)
    expect(ctx.arcs).toEqual(first)
    expect(first.length).toBeGreaterThan(0)
    w2.unmount()
  })

  it('defers the loop to browser idle, then starts it and cancels on unmount', () => {
    setReducedMotion(false)
    // D4-PERF: the loop is gated behind requestIdleCallback so it never
    // competes with hydration on first load. Drive idle synchronously to
    // keep the assertion deterministic.
    const idleCallbacks: Array<() => void> = []
    vi.stubGlobal('requestIdleCallback', (cb: () => void): number => {
      idleCallbacks.push(cb)
      return idleCallbacks.length
    })
    const cancelIdleSpy = vi.fn()
    vi.stubGlobal('cancelIdleCallback', cancelIdleSpy)
    const rafSpy = vi.spyOn(window, 'requestAnimationFrame').mockImplementation(() => 1)
    const cancelSpy = vi.spyOn(window, 'cancelAnimationFrame')

    const wrapper = mount(CanvasHeroField)
    // Nothing scheduled yet — still waiting for the browser to go idle.
    expect(rafSpy).not.toHaveBeenCalled()
    expect(idleCallbacks).toHaveLength(1)

    // Browser goes idle → the loop starts.
    idleCallbacks.forEach(cb => cb())
    expect(rafSpy).toHaveBeenCalled()

    wrapper.unmount()
    expect(cancelSpy).toHaveBeenCalled()
    // The idle handle is released on teardown too.
    expect(cancelIdleSpy).toHaveBeenCalled()
  })

  it('survives a null 2D context without throwing', () => {
    setReducedMotion(true)
    getContextSpy.mockReturnValue(null)
    expect(() => {
      const wrapper = mount(CanvasHeroField)
      wrapper.unmount()
    }).not.toThrow()
  })
})
