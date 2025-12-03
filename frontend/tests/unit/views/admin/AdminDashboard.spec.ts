import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, VueWrapper } from '@vue/test-utils'
import { createTestingPinia } from '@pinia/testing'
import { createRouter, createWebHistory, type Router } from 'vue-router'
import AdminDashboard from '@/views/admin/AdminDashboard.vue'
import { useAuthStore } from '@/stores/auth'
import { usePortfolioStore } from '@/stores/portfolio'

// Mock router
const createTestRouter = (): Router => {
  return createRouter({
    history: createWebHistory(),
    routes: [
      { path: '/admin', component: { template: '<div>Dashboard</div>' } },
      { path: '/admin/login', component: { template: '<div>Login</div>' } },
      { path: '/admin/companies', component: { template: '<div>Companies</div>' } },
      { path: '/admin/skills', component: { template: '<div>Skills</div>' } },
      { path: '/admin/projects', component: { template: '<div>Projects</div>' } },
    ],
  })
}

describe('AdminDashboard', () => {
  let router: Router

  const createWrapper = async (options = {}): Promise<VueWrapper> => {
    router = createTestRouter()
    await router.push('/admin')
    await router.isReady()

    return mount(AdminDashboard, {
      global: {
        plugins: [
          createTestingPinia({
            createSpy: vi.fn,
            initialState: {
              auth: {
                user: {
                  id: '1',
                  username: 'testuser',
                  name: 'Test User',
                  avatar_url: 'https://example.com/avatar.jpg',
                },
                accessToken: 'test-token',
                refreshToken: 'test-refresh',
                isLoading: false,
                error: null,
              },
              portfolio: {
                companies: [
                  { id: '1', name: 'Company 1' },
                  { id: '2', name: 'Company 2' },
                ],
                skills: [
                  { id: '1', name: 'Skill 1' },
                  { id: '2', name: 'Skill 2' },
                  { id: '3', name: 'Skill 3' },
                ],
                projects: [
                  { id: '1', name: 'Project 1', featured: true },
                  { id: '2', name: 'Project 2', featured: false },
                  { id: '3', name: 'Project 3', featured: true },
                  { id: '4', name: 'Project 4', featured: false },
                ],
                education: [],
                isLoading: false,
                error: null,
              },
            },
          }),
          router,
        ],
      },
      ...options,
    })
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Rendering', () => {
    it('should render the admin dashboard container', async () => {
      const wrapper = await createWrapper()

      expect(wrapper.find('.admin-dashboard').exists()).toBe(true)
      expect(wrapper.find('.admin-header').exists()).toBe(true)
      expect(wrapper.find('.admin-nav').exists()).toBe(true)
      expect(wrapper.find('.admin-content').exists()).toBe(true)
    })

    it('should display the dashboard title', async () => {
      const wrapper = await createWrapper()

      const title = wrapper.find('.dashboard-title')
      expect(title.exists()).toBe(true)
      expect(title.text()).toBe('Portfolio Admin')
    })

    it('should display user information when logged in', async () => {
      const wrapper = await createWrapper()

      const userInfo = wrapper.find('.user-info')
      expect(userInfo.exists()).toBe(true)

      const avatar = wrapper.find('.user-avatar')
      expect(avatar.exists()).toBe(true)
      expect(avatar.attributes('src')).toBe('https://example.com/avatar.jpg')

      const userName = wrapper.find('.user-name')
      expect(userName.exists()).toBe(true)
      expect(userName.text()).toBe('Test User')
    })

    it('should display username if name is not available', async () => {
      router = createTestRouter()
      await router.push('/admin')
      await router.isReady()

      const wrapper = mount(AdminDashboard, {
        global: {
          plugins: [
            createTestingPinia({
              createSpy: vi.fn,
              initialState: {
                auth: {
                  user: {
                    id: '1',
                    username: 'testuser',
                    name: '',
                    avatar_url: null,
                  },
                  accessToken: 'test-token',
                },
                portfolio: {
                  companies: [],
                  skills: [],
                  projects: [],
                },
              },
            }),
            router,
          ],
        },
      })

      const userName = wrapper.find('.user-name')
      expect(userName.text()).toBe('testuser')
    })

    it('should render logout button', async () => {
      const wrapper = await createWrapper()

      const logoutButton = wrapper.find('.logout-button')
      expect(logoutButton.exists()).toBe(true)
      expect(logoutButton.text()).toBe('Sign Out')
    })
  })

  describe('Navigation', () => {
    it('should render all navigation links', async () => {
      const wrapper = await createWrapper()

      const navLinks = wrapper.findAll('.nav-link')
      expect(navLinks.length).toBe(4)

      const linkTexts = navLinks.map(link => link.text())
      expect(linkTexts).toContain('Dashboard')
      expect(linkTexts).toContain('Experience')
      expect(linkTexts).toContain('Skills')
      expect(linkTexts).toContain('Projects')
    })

    it('should have correct navigation hrefs', async () => {
      const wrapper = await createWrapper()

      const navLinks = wrapper.findAll('.nav-link')
      const hrefs = navLinks.map(link => link.attributes('href'))

      expect(hrefs).toContain('/admin')
      expect(hrefs).toContain('/admin/companies')
      expect(hrefs).toContain('/admin/skills')
      expect(hrefs).toContain('/admin/projects')
    })
  })

  describe('Dashboard Overview', () => {
    it('should display stats grid with correct counts', async () => {
      const wrapper = await createWrapper()

      const statCards = wrapper.findAll('.stat-card')
      expect(statCards.length).toBe(4)

      const statValues = wrapper.findAll('.stat-value')
      const counts = statValues.map(el => el.text())

      // Companies: 2, Skills: 3, Projects: 4, Featured: 2
      expect(counts).toContain('2') // Companies
      expect(counts).toContain('3') // Skills
      expect(counts).toContain('4') // Projects
      expect(counts[3]).toBe('2') // Featured (2 projects with featured: true)
    })

    it('should display correct stat labels', async () => {
      const wrapper = await createWrapper()

      const statLabels = wrapper.findAll('.stat-label')
      const labels = statLabels.map(el => el.text())

      expect(labels).toContain('Companies')
      expect(labels).toContain('Skills')
      expect(labels).toContain('Projects')
      expect(labels).toContain('Featured')
    })

    it('should render quick actions section', async () => {
      const wrapper = await createWrapper()

      expect(wrapper.find('.quick-actions').exists()).toBe(true)
      expect(wrapper.find('.subsection-title').text()).toBe('Quick Actions')
    })

    it('should render action buttons', async () => {
      const wrapper = await createWrapper()

      const actionButtons = wrapper.findAll('.action-button')
      expect(actionButtons.length).toBe(4)

      const buttonTexts = actionButtons.map(btn => btn.text())
      expect(buttonTexts).toContain('Add Experience')
      expect(buttonTexts).toContain('New Project')
      expect(buttonTexts).toContain('Update Skills')
      expect(buttonTexts).toContain('View Site')
    })

    it('should have View Site link opening in new tab', async () => {
      const wrapper = await createWrapper()

      const viewSiteLink = wrapper.find('a.action-button[href="/"]')
      expect(viewSiteLink.exists()).toBe(true)
      expect(viewSiteLink.attributes('target')).toBe('_blank')
    })
  })

  describe('Interactions', () => {
    it('should call logout and redirect when logout button is clicked', async () => {
      const wrapper = await createWrapper()
      const authStore = useAuthStore()

      const logoutButton = wrapper.find('.logout-button')
      await logoutButton.trigger('click')

      expect(authStore.logout).toHaveBeenCalled()
    })

    it('should fetch all data on mount', async () => {
      const wrapper = await createWrapper()
      const portfolioStore = usePortfolioStore()

      expect(portfolioStore.fetchAllData).toHaveBeenCalled()
    })
  })

  describe('Empty State', () => {
    it('should display zero counts when no data', async () => {
      router = createTestRouter()
      await router.push('/admin')
      await router.isReady()

      const wrapper = mount(AdminDashboard, {
        global: {
          plugins: [
            createTestingPinia({
              createSpy: vi.fn,
              initialState: {
                auth: {
                  user: { id: '1', username: 'test' },
                  accessToken: 'test',
                },
                portfolio: {
                  companies: [],
                  skills: [],
                  projects: [],
                },
              },
            }),
            router,
          ],
        },
      })

      const statValues = wrapper.findAll('.stat-value')
      statValues.forEach(stat => {
        expect(stat.text()).toBe('0')
      })
    })
  })
})
