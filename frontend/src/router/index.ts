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

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'home',
    component: HomeView
  },
  {
    path: '/company/:id',
    name: 'company-detail',
    component: CompanyDetailView,
    props: true
  },
  {
    path: '/experience/:id',
    name: 'experience-detail',
    component: ExperienceDetail,
    props: true
  },
  {
    path: '/admin/login',
    name: 'admin-login',
    component: AdminLogin,
    meta: { requiresGuest: true }
  },
  {
    path: '/admin',
    name: 'admin-dashboard',
    component: AdminDashboard,
    meta: { requiresAuth: true },
    children: [
      {
        path: 'companies',
        name: 'admin-companies',
        component: AdminCompanies
      },
      {
        path: 'education',
        name: 'admin-education',
        component: AdminEducation
      },
      {
        path: 'projects',
        name: 'admin-projects',
        component: AdminProjects
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

// Navigation guards
router.beforeEach(
  async (
    to: RouteLocationNormalized,
    _from: RouteLocationNormalized,
    next: NavigationGuardNext
  ) => {
    const authStore = useAuthStore()

    // Check if route requires authentication
    if (to.matched.some(record => record.meta.requiresAuth)) {
      if (!authStore.isAuthenticated) {
        // Redirect to login if not authenticated
        next({ name: 'admin-login', query: { redirect: to.fullPath } })
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

// Track page views after navigation
router.afterEach((to: RouteLocationNormalized, _from: RouteLocationNormalized) => {
  // Track the page view
  analytics.trackPageView(to.path, to.name as string | undefined)
})

export default router
