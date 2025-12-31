import {
  createRouter,
  createWebHistory,
  type RouteRecordRaw,
  type NavigationGuardNext,
  type RouteLocationNormalized
} from 'vue-router'
import { useAuthStore } from '../stores/auth'
import analytics from '../services/analytics'

// Core views - loaded immediately
import HomeView from '../views/HomeView.vue'

// Detail views - lazy loaded for better performance
const CompanyDetailView = () => import('../views/CompanyDetailView.vue')
const ExperienceDetail = () => import('../views/experience/ExperienceDetail.vue')

// Admin views - lazy loaded (less frequently accessed)
const AdminDashboard = () => import('../views/admin/AdminDashboard.vue')
const AdminLogin = () => import('../views/admin/AdminLogin.vue')
const AdminCompanies = () => import('../views/admin/AdminCompanies.vue')
const AdminEducation = () => import('../views/admin/AdminEducation.vue')
const AdminProjects = () => import('../views/admin/AdminProjects.vue')

// Default page title
const DEFAULT_TITLE = 'David Dashti | Cybersecurity in Healthcare'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'home',
    component: HomeView,
    meta: { title: DEFAULT_TITLE }
  },
  {
    path: '/company/:id',
    name: 'company-detail',
    component: CompanyDetailView,
    props: true,
    meta: { title: 'Experience | David Dashti' }
  },
  {
    path: '/experience/:id',
    name: 'experience-detail',
    component: ExperienceDetail,
    props: true,
    meta: { title: 'Experience | David Dashti' }
  },
  {
    path: '/admin/login',
    name: 'admin-login',
    component: AdminLogin,
    meta: { requiresGuest: true, title: 'Admin Login | David Dashti' }
  },
  {
    path: '/admin',
    name: 'admin-dashboard',
    component: AdminDashboard,
    meta: { requiresAuth: true, title: 'Admin Dashboard | David Dashti' },
    children: [
      {
        path: 'companies',
        name: 'admin-companies',
        component: AdminCompanies,
        meta: { title: 'Manage Companies | David Dashti' }
      },
      {
        path: 'education',
        name: 'admin-education',
        component: AdminEducation,
        meta: { title: 'Manage Education | David Dashti' }
      },
      {
        path: 'projects',
        name: 'admin-projects',
        component: AdminProjects,
        meta: { title: 'Manage Projects | David Dashti' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior(to, _from, savedPosition) {
    // If user navigated back/forward, restore saved position
    if (savedPosition) {
      return savedPosition
    }

    // If navigating to a hash anchor, scroll to it with navbar offset
    if (to.hash) {
      return {
        el: to.hash,
        behavior: 'smooth',
        top: 80 // navbar offset
      }
    }

    // Default: scroll to top smoothly
    return { top: 0, behavior: 'smooth' }
  }
})

// Navigation guards
router.beforeEach(
  async (
    to: RouteLocationNormalized,
    _from: RouteLocationNormalized,
    next: NavigationGuardNext
  ) => {
    const authStore = useAuthStore()

    // Initialize auth state from localStorage if not already done
    // This ensures tokens are loaded before checking authentication
    if (!authStore.isInitialized) {
      await authStore.initializeAuth()
    }

    // Check if route requires authentication
    if (to.matched.some(record => record.meta.requiresAuth)) {
      if (!authStore.isAuthenticated) {
        // Redirect to login if not authenticated
        // Note: Intentionally not passing redirect param to avoid open redirect vulnerabilities
        next({ name: 'admin-login' })
      } else {
        next()
      }
    } else if (to.matched.some(record => record.meta.requiresGuest)) {
      if (authStore.isAuthenticated) {
        // Redirect to dashboard if already authenticated
        next({ name: 'admin-dashboard' })
      } else {
        next()
      }
    } else {
      next()
    }
  }
)

// Update document title and track page views after navigation
router.afterEach((to: RouteLocationNormalized, _from: RouteLocationNormalized) => {
  // Update document title from route meta
  const title = to.meta.title as string | undefined
  document.title = title || DEFAULT_TITLE

  // Track the page view
  analytics.trackPageView(to.path, to.name as string | undefined)
})

export default router
