import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { defineComponent, h, type App } from 'vue'
import { mount } from '@vue/test-utils'
import { createRouter, createMemoryHistory, Router } from 'vue-router'
import ErrorBoundary from '@/components/ErrorBoundary.vue'
import { initSentry, __resetSentryForTests } from '@/utils/sentry'

vi.mock('@/utils/logger', () => ({
  errorLogger: { error: vi.fn() }
}))

// errorTracker is enabled under Vitest and would post every caught error to
// the API; its own spec covers it. Here only the Sentry path is under test.
vi.mock('@/utils/errorTracking', () => ({
  errorTracker: { handleVueError: vi.fn() }
}))

// The SDK chunk that utils/sentry loads on idle. captureException is the call
// that puts an event on the wire, so it is what the reporting tests count.
const sdk = vi.hoisted(() => ({ init: vi.fn(), captureException: vi.fn() }))
vi.mock('@sentry/vue', () => ({
  init: sdk.init,
  captureException: sdk.captureException,
  browserTracingIntegration: vi.fn(() => ({ name: 'BrowserTracing' })),
  browserApiErrorsIntegration: vi.fn(() => ({ name: 'BrowserApiErrors' })),
  setMeasurement: vi.fn(),
  setContext: vi.fn()
}))
vi.mock('web-vitals', () => ({
  onCLS: vi.fn(),
  onINP: vi.fn(),
  onLCP: vi.fn(),
  onFCP: vi.fn(),
  onTTFB: vi.fn()
}))

describe('ErrorBoundary', () => {
  let router: Router

  beforeEach(async () => {
    router = createRouter({
      history: createMemoryHistory(),
      routes: [
        { path: '/', component: { template: '<div>Home</div>' } },
        { path: '/other', component: { template: '<div>Other</div>' } }
      ]
    })
    await router.push('/')
    await router.isReady()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it('renders slot content when no error', () => {
    const wrapper = mount(ErrorBoundary, {
      global: { plugins: [router] },
      slots: { default: '<div class="child">Child content</div>' }
    })
    expect(wrapper.find('.child').exists()).toBe(true)
    expect(wrapper.find('.error-boundary').exists()).toBe(false)
  })

  it('shows error UI when showError is called', async () => {
    const wrapper = mount(ErrorBoundary, {
      global: { plugins: [router] }
    })
    ;(wrapper.vm as unknown as { showError: (e: Error) => void }).showError(new Error('Boom'))
    await wrapper.vm.$nextTick()

    expect(wrapper.find('.error-boundary').exists()).toBe(true)
    expect(wrapper.find('.error-title').text()).toBe('Oops! Something went wrong')
  })

  it('displays custom title and message props', async () => {
    const wrapper = mount(ErrorBoundary, {
      global: { plugins: [router] },
      props: { title: 'Custom Title', message: 'Custom message' }
    })
    ;(wrapper.vm as unknown as { showError: (e: Error) => void }).showError(new Error('Boom'))
    await wrapper.vm.$nextTick()

    expect(wrapper.find('.error-title').text()).toBe('Custom Title')
    expect(wrapper.find('.error-message').text()).toBe('Custom message')
  })

  it('renders Try Again and Go to Homepage buttons', async () => {
    const wrapper = mount(ErrorBoundary, {
      global: { plugins: [router] }
    })
    ;(wrapper.vm as unknown as { showError: (e: Error) => void }).showError(new Error('Boom'))
    await wrapper.vm.$nextTick()

    expect(wrapper.find('.btn-retry').text()).toBe('Try Again')
    expect(wrapper.find('.btn-home').text()).toBe('Go to Homepage')
  })

  it('calls onRetry prop when Try Again is clicked', async () => {
    const onRetry = vi.fn()
    const wrapper = mount(ErrorBoundary, {
      global: { plugins: [router] },
      props: { onRetry }
    })
    ;(wrapper.vm as unknown as { showError: (e: Error) => void }).showError(new Error('Boom'))
    await wrapper.vm.$nextTick()

    await wrapper.find('.btn-retry').trigger('click')
    expect(onRetry).toHaveBeenCalled()
  })

  it('navigates to / when Go to Homepage is clicked', async () => {
    await router.push('/other')
    const wrapper = mount(ErrorBoundary, {
      global: { plugins: [router] }
    })
    ;(wrapper.vm as unknown as { showError: (e: Error) => void }).showError(new Error('Boom'))
    await wrapper.vm.$nextTick()

    await wrapper.find('.btn-home').trigger('click')
    await router.isReady()
    await new Promise(resolve => setTimeout(resolve, 0))
    expect(router.currentRoute.value.path).toBe('/')
  })

  it('resets the fallback on route change instead of latching', async () => {
    // The boundary's fallback replaces the routed tree, so a hasError that
    // survived navigation turned one crashed admin view into "every admin
    // page is broken until refresh" (2026-08-22 admin-bug diagnosis).
    const wrapper = mount(ErrorBoundary, {
      global: { plugins: [router] },
      slots: { default: '<div class="child">Child content</div>' }
    })
    ;(wrapper.vm as unknown as { showError: (e: Error) => void }).showError(new Error('Boom'))
    await wrapper.vm.$nextTick()
    expect(wrapper.find('.error-boundary').exists()).toBe(true)

    await router.push('/other')
    await wrapper.vm.$nextTick()
    expect(wrapper.find('.error-boundary').exists()).toBe(false)
    expect(wrapper.find('.child').exists()).toBe(true)
  })

  it('accepts error info object with message and context', async () => {
    const wrapper = mount(ErrorBoundary, {
      global: { plugins: [router] },
      props: { showDetails: true }
    })
    ;(
      wrapper.vm as unknown as { showError: (e: { message: string; context: string }) => void }
    ).showError({ message: 'Failed', context: 'API call' })
    await wrapper.vm.$nextTick()

    const details = wrapper.find('.error-details')
    expect(details.exists()).toBe(true)
    expect(details.text()).toContain('Failed')
    expect(details.text()).toContain('API call')
  })
})

/**
 * The boundary is the ONLY reporter of what it catches: its `return false`
 * keeps the error away from app.config.errorHandler, where main.ts's handler
 * and, once loaded, the Sentry SDK's own wrapper sit. So every error it
 * catches must reach the SDK exactly once, including one caught in the idle
 * window before the SDK has loaded, which the boundary used to drop.
 */
describe('ErrorBoundary reporting to Sentry', () => {
  const DSN = 'https://publickey@o0.ingest.de.sentry.io/1'
  type AppErrorHandler = NonNullable<App['config']['errorHandler']>
  let router: Router
  let idle: ReturnType<typeof vi.fn>
  let thrown: Error

  // Throws from its own render function, so Vue hands the error to the
  // nearest onErrorCaptured hook above it.
  const ThrowingChild = defineComponent({
    name: 'ThrowingChild',
    setup() {
      return () => {
        throw thrown
      }
    }
  })

  const mountAroundThrowingChild = (appErrorHandler: AppErrorHandler) =>
    mount(ErrorBoundary, {
      global: { plugins: [router], config: { errorHandler: appErrorHandler } },
      slots: { default: () => h(ThrowingChild) }
    })

  /** Run the load initSentry() scheduled for idle, and wait for the SDK's init(). */
  const loadSentry = async (): Promise<void> => {
    expect(idle).toHaveBeenCalledTimes(1)
    ;(idle.mock.calls[0][0] as () => void)()
    await vi.waitFor(() => expect(sdk.init).toHaveBeenCalledTimes(1))
  }

  /** Let timers and promise callbacks queued by the report run, so a late duplicate shows up. */
  const settle = (): Promise<void> => new Promise(resolve => setTimeout(resolve, 0))

  beforeEach(async () => {
    vi.clearAllMocks()
    __resetSentryForTests()
    vi.stubEnv('VITE_SENTRY_DSN', DSN)
    idle = vi.fn()
    vi.stubGlobal('requestIdleCallback', idle)
    thrown = new Error('render failed')
    router = createRouter({
      history: createMemoryHistory(),
      routes: [{ path: '/', component: { template: '<div>Home</div>' } }]
    })
    await router.push('/')
    await router.isReady()
    // As main.ts does: scheduled now, loaded on the first idle slot.
    initSentry({} as unknown as App, router)
  })

  afterEach(() => {
    __resetSentryForTests()
    vi.unstubAllEnvs()
    vi.unstubAllGlobals()
  })

  it('control: an error with no boundary above it does reach app.config.errorHandler', () => {
    // Proves the errorHandler spy below is live, so its "never called"
    // assertions mean the boundary stopped the error, not that nothing
    // listened. Vue Test Utils also rethrows from mount() any error that
    // reached app.config.errorHandler while mounting, so a boundary that let
    // one through would fail the mounts below outright.
    const appErrorHandler = vi.fn<AppErrorHandler>()

    expect(() =>
      mount(ThrowingChild, { global: { config: { errorHandler: appErrorHandler } } })
    ).toThrow(thrown)
    expect(appErrorHandler).toHaveBeenCalledTimes(1)
    expect(appErrorHandler.mock.calls[0][0]).toBe(thrown)
  })

  it('buffers an error caught before Sentry loads and sends it once when Sentry is up', async () => {
    const appErrorHandler = vi.fn<AppErrorHandler>()
    const wrapper = mountAroundThrowingChild(appErrorHandler)
    await wrapper.vm.$nextTick()

    expect(wrapper.find('.error-boundary').exists()).toBe(true)
    // The SDK has not loaded, so nothing can have been sent yet.
    expect(sdk.captureException).not.toHaveBeenCalled()

    await loadSentry()
    await settle()

    expect(sdk.captureException).toHaveBeenCalledTimes(1)
    const [error, hint] = sdk.captureException.mock.calls[0] as [
      Error,
      { extra: Record<string, unknown> }
    ]
    expect(error).toBe(thrown)
    expect(hint.extra).toEqual({
      componentName: 'ThrowingChild',
      errorInfo: expect.any(String),
      buffered_before_sentry_load: true
    })
    expect(appErrorHandler).not.toHaveBeenCalled()
  })

  it('sends an error caught after Sentry has loaded straight through, once', async () => {
    await loadSentry()
    const appErrorHandler = vi.fn<AppErrorHandler>()

    const wrapper = mountAroundThrowingChild(appErrorHandler)
    await wrapper.vm.$nextTick()
    await settle()

    expect(wrapper.find('.error-boundary').exists()).toBe(true)
    expect(sdk.captureException).toHaveBeenCalledTimes(1)
    const [error, hint] = sdk.captureException.mock.calls[0] as [
      Error,
      { extra: Record<string, unknown> }
    ]
    expect(error).toBe(thrown)
    expect(hint.extra).toEqual({ componentName: 'ThrowingChild', errorInfo: expect.any(String) })
    expect(appErrorHandler).not.toHaveBeenCalled()
  })
})
