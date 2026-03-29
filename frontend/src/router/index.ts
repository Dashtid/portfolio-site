import { type RouteRecordRaw, type RouterScrollBehavior } from 'vue-router'

// Core views - loaded immediately
import HomeView from '../views/HomeView.vue'

// Detail views - lazy loaded for better performance
const ExperienceDetail = () => import('../views/experience/ExperienceDetail.vue')

// Admin views - lazy loaded (less frequently accessed)
const AdminDashboard = () => import('../views/admin/AdminDashboard.vue')
const AdminLogin = () => import('../views/admin/AdminLogin.vue')
const AdminCompanies = () => import('../views/admin/AdminCompanies.vue')
const AdminEducation = () => import('../views/admin/AdminEducation.vue')
const AdminProjects = () => import('../views/admin/AdminProjects.vue')

export const DEFAULT_TITLE = 'David Dashti | Cybersecurity in Healthcare'

export const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'home',
    component: HomeView,
    meta: { title: DEFAULT_TITLE }
  },
  {
    path: '/experience/:id',
    name: 'experience-detail',
    alias: '/company/:id',
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

export const scrollBehavior: RouterScrollBehavior = (to, _from, savedPosition) => {
  if (savedPosition) return savedPosition
  if (to.hash) return { el: to.hash, behavior: 'smooth' as ScrollBehavior, top: 80 }
  return { top: 0, behavior: 'smooth' as ScrollBehavior }
}
