/**
 * The page-view beacon main.ts wires onto the router: which path a
 * navigation is recorded under, what else goes with it, and which
 * navigations send nothing from here. The routes are the app's own, resolved
 * by a real router, so a renamed or reordered route shows up here.
 */
import { describe, it, expect, vi, beforeAll, beforeEach } from 'vitest'
import { createApp as createVueApp } from 'vue'
import {
  createMemoryHistory,
  createRouter,
  type RouteLocationNormalized,
  type Router
} from 'vue-router'
import { routes } from '@/router'

type SetupContext = {
  app: ReturnType<typeof createVueApp>
  router: Router
  isClient: boolean
  initialState: Record<string, unknown>
}
type AfterEachHook = (to: RouteLocationNormalized) => void

const ssg = vi.hoisted(() => ({
  setup: undefined as ((context: SetupContext) => void) | undefined
}))
const trackPageView = vi.hoisted(() => vi.fn())

// ViteSSG would build and mount the whole app. The mock keeps the setup
// function main.ts hands it, and the tests run that against a bare app.
vi.mock('vite-ssg', () => ({
  ViteSSG: (_app: unknown, _options: unknown, setup: (context: SetupContext) => void) => {
    ssg.setup = setup
    return () => undefined
  }
}))
vi.mock('@/App.vue', () => ({ default: {} }))
vi.mock('@/services/analytics', () => ({ default: { trackPageView } }))
vi.mock('@/utils/sentry', () => ({ initSentry: vi.fn(), captureException: vi.fn() }))
// One article, so that both outcomes of the slug check can be seen.
vi.mock('@/data/writing', () => ({
  writingPosts: [],
  findPost: (slug: string) => (slug === 'an-article' ? { slug } : undefined)
}))

describe('main.ts page-view tracking', () => {
  let router: Router
  let afterEachHook: AfterEachHook

  beforeAll(async () => {
    await import('@/main')
  })

  beforeEach(() => {
    trackPageView.mockClear()
    router = createRouter({ history: createMemoryHistory(), routes })
    const afterEach = vi.spyOn(router, 'afterEach')
    ssg.setup!({ app: createVueApp({}), router, isClient: true, initialState: {} })
    expect(afterEach).toHaveBeenCalledTimes(1)
    afterEachHook = afterEach.mock.calls[0][0] as AfterEachHook
  })

  /** Run the hook as the router does after a navigation to `path`. */
  const navigatedTo = (path: string): void =>
    afterEachHook(router.resolve(path) as RouteLocationNormalized)

  it('records a matched route by its path, and sends nothing else', () => {
    navigatedTo('/colophon?utm_source=feed#stack')
    navigatedTo('/writing')

    expect(trackPageView.mock.calls).toEqual([['/colophon'], ['/writing']])
  })

  it('records a URL that only the catch-all route matches as /404', () => {
    for (const path of ['/no/such/page', '/wp-login.php', '/%3Cscript%3E', '/experience/..']) {
      expect(router.resolve(path).name, path).toBe('not-found-catchall')
      navigatedTo(path)
    }

    expect(trackPageView.mock.calls).toEqual([['/404'], ['/404'], ['/404'], ['/404']])
  })

  it('records the not-found page under its own path', () => {
    navigatedTo('/404')

    expect(trackPageView.mock.calls).toEqual([['/404']])
  })

  it('records an article by its path, and a slug with no article as /404', () => {
    for (const path of ['/writing/an-article', '/writing/no-such-article', '/writing/buy%20now']) {
      expect(router.resolve(path).name, path).toBe('writing-article')
      navigatedTo(path)
    }

    expect(trackPageView.mock.calls).toEqual([['/writing/an-article'], ['/404'], ['/404']])
  })

  it('leaves an experience page to the view, which learns whether it exists', () => {
    for (const path of [
      '/experience/3f2c8a4e-9b1d-4c7e-a5f6-0d8b2e1c4a97',
      '/experience/no-such-id',
      '/company/no-such-id'
    ]) {
      expect(router.resolve(path).name, path).toBe('experience-detail')
      navigatedTo(path)
    }

    expect(trackPageView).not.toHaveBeenCalled()
  })

  it('sends nothing for an admin route, matched or not', () => {
    navigatedTo('/admin/companies')
    navigatedTo('/admin/no-such-page')

    expect(trackPageView).not.toHaveBeenCalled()
  })
})
