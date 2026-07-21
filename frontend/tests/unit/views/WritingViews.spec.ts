import { describe, it, expect, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createRouter, createMemoryHistory } from 'vue-router'
import { useHead } from '@unhead/vue'
import WritingIndexView from '@/views/writing/WritingIndexView.vue'
import WritingArticleView from '@/views/writing/WritingArticleView.vue'

vi.mock('@/components/NavBar.vue', () => ({
  default: { name: 'NavBar', template: '<nav data-testid="navbar" />' }
}))
vi.mock('@/components/FooterSection.vue', () => ({
  default: { name: 'FooterSection', template: '<footer data-testid="footer" />' }
}))

const mockedUseHead = vi.mocked(useHead)

const mountAt = async (component: unknown, path: string) => {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', component: { template: '<div />' }, name: 'home' },
      { path: '/writing', component: WritingIndexView, name: 'writing' },
      { path: '/writing/:slug', component: WritingArticleView, name: 'writing-article' }
    ]
  })
  await router.push(path)
  await router.isReady()
  return mount(component as never, { global: { plugins: [router] } })
}

describe('Writing surface (D3-FEAT-03)', () => {
  describe('WritingIndexView', () => {
    it('renders the honest empty state while no article is approved', async () => {
      const wrapper = await mountAt(WritingIndexView, '/writing')
      expect(wrapper.text()).toContain('Writing')
      expect(wrapper.text()).toContain('Nothing published yet')
    })

    it('carries noindex while the surface is empty', async () => {
      mockedUseHead.mockClear()
      await mountAt(WritingIndexView, '/writing')

      const headArg = mockedUseHead.mock.calls[0][0] as {
        meta: Array<{ name?: string; content: string }>
      }
      const robots = headArg.meta.find(m => m.name === 'robots')
      expect(robots?.content).toBe('noindex')
    })
  })

  describe('WritingArticleView', () => {
    it('renders the honest 404 for unknown slugs with noindex', async () => {
      mockedUseHead.mockClear()
      const wrapper = await mountAt(WritingArticleView, '/writing/does-not-exist')

      expect(wrapper.text()).toContain('article not found')
      expect(wrapper.text()).toContain('404')

      const headArg = mockedUseHead.mock.calls[0][0] as {
        meta: Array<{ name?: string; content: { value?: string } | string }>
      }
      const robots = headArg.meta.find(m => m.name === 'robots')
      const content = robots?.content as { value?: string }
      expect(content?.value ?? content).toBe('noindex')
    })
  })
})
