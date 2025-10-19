import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import analytics from '../services/analytics'

// Views
import HomeView from '../views/HomeView.vue'
import AdminDashboard from '../views/admin/AdminDashboard.vue'
import AdminLogin from '../views/admin/AdminLogin.vue'
import AdminCompanies from '../views/admin/AdminCompanies.vue'
import AdminSkills from '../views/admin/AdminSkills.vue'
import AdminProjects from '../views/admin/AdminProjects.vue'

const routes = [
  {
    path: '/',
    name: 'home',
    component: HomeView
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
        path: 'skills',
        name: 'admin-skills',
        component: AdminSkills
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
router.beforeEach(async (to, from, next) => {
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
})

// Track page views after navigation
router.afterEach((to, from) => {
  // Track the page view
  analytics.trackPageView(to.path, to.name)
})

export default router