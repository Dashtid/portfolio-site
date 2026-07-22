import { type RouteRecordRaw, type RouterScrollBehavior } from 'vue-router'

// Core views - loaded immediately
import HomeView from '../views/HomeView.vue'

// Detail views - lazy loaded for better performance
const ExperienceDetail = () => import('../views/experience/ExperienceDetail.vue')
const NotFoundView = () => import('../views/NotFoundView.vue')
const WritingIndexView = () => import('../views/writing/WritingIndexView.vue')
const WritingArticleView = () => import('../views/writing/WritingArticleView.vue')

// Admin views - lazy loaded (less frequently accessed)
const AdminDashboard = () => import('../views/admin/AdminDashboard.vue')
const AdminLogin = () => import('../views/admin/AdminLogin.vue')
const AdminCompanies = () => import('../views/admin/AdminCompanies.vue')
const AdminEducation = () => import('../views/admin/AdminEducation.vue')
const AdminProjects = () => import('../views/admin/AdminProjects.vue')
const AdminSkills = () => import('../views/admin/AdminSkills.vue')
const AdminAnalytics = () => import('../views/admin/AdminAnalytics.vue')
const AdminMetrics = () => import('../views/admin/AdminMetrics.vue')
const AdminDocuments = () => import('../views/admin/AdminDocuments.vue')
const AdminOss = () => import('../views/admin/AdminOss.vue')
const AdminCv = () => import('../views/admin/AdminCv.vue')

export const DEFAULT_TITLE = 'David Dashti — Product & Application Security | Medical Devices'

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
    // D3-FEAT-03: writing surface — index + per-article routes. Unlinked
    // from the nav until the first article is owner-approved; the index
    // carries noindex while empty.
    path: '/writing',
    name: 'writing',
    component: WritingIndexView,
    meta: { title: 'Writing | David Dashti' }
  },
  {
    path: '/writing/:slug',
    name: 'writing-article',
    component: WritingArticleView,
    meta: { title: 'Writing | David Dashti' }
  },
  {
    // Static path so vite-ssg prerenders a real dist/404.html; the
    // catch-all below renders the same view client-side (D3-UX-01).
    path: '/404',
    name: 'not-found',
    component: NotFoundView,
    meta: { title: '404 — Page Not Found | David Dashti' }
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
      },
      {
        path: 'skills',
        name: 'admin-skills',
        component: AdminSkills,
        meta: { title: 'Manage Skills | David Dashti' }
      },
      {
        path: 'analytics',
        name: 'admin-analytics',
        component: AdminAnalytics,
        meta: { title: 'Analytics | David Dashti' }
      },
      {
        path: 'metrics',
        name: 'admin-metrics',
        component: AdminMetrics,
        meta: { title: 'Performance Metrics | David Dashti' }
      },
      {
        path: 'documents',
        name: 'admin-documents',
        component: AdminDocuments,
        meta: { title: 'Manage Documents | David Dashti' }
      },
      {
        path: 'oss',
        name: 'admin-oss',
        component: AdminOss,
        meta: { title: 'OSS Contributions | David Dashti' }
      },
      {
        // Admin-only CV export: edit profile prose + private contact and
        // download a CV assembled from the DB (Campaign 2026-08 Sprint 2).
        path: 'cv',
        name: 'admin-cv',
        component: AdminCv,
        meta: { title: 'CV Export | David Dashti' }
      }
    ]
  },
  {
    // Catch-all LAST: unmatched URLs used to hydrate to a completely blank
    // page (no route matched, App.vue renders no chrome outside views) while
    // Vercel's SPA rewrite served them as 200s (D3-UX-01).
    path: '/:pathMatch(.*)*',
    name: 'not-found-catchall',
    component: NotFoundView,
    meta: { title: '404 — Page Not Found | David Dashti' }
  }
]

// Reads --navbar-height (set by NavBar.vue from a one-time scrolled-state
// measurement, refreshed on viewport resize). Falls back to 72 for SSR
// and early boots before the var is written. Section internal padding
// provides any visual breathing room above the title.
const getScrollOffset = (): number => {
  if (typeof window === 'undefined') return 72
  const raw = getComputedStyle(document.documentElement).getPropertyValue('--navbar-height')
  const parsed = parseInt(raw, 10)
  return Number.isFinite(parsed) && parsed > 0 ? parsed : 72
}

// Smooth scrolling is motion — honor prefers-reduced-motion here too
// (SSG guard: matchMedia is absent during the build pass).
const scrollMotion = (): ScrollBehavior =>
  typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches
    ? 'auto'
    : 'smooth'

export const scrollBehavior: RouterScrollBehavior = (to, _from, savedPosition) => {
  if (savedPosition) return savedPosition
  if (to.hash) {
    // On cross-route hash nav (e.g. /experience/:id → /#experience), the home
    // view's section is mounted asynchronously inside <Suspense>, so the hash
    // target may not yet exist when scrollBehavior fires. Poll briefly until
    // the element appears, then scroll. Falls back to top of page if it never
    // shows up (e.g. invalid hash).
    return new Promise(resolve => {
      const start = Date.now()
      const tryResolve = (): void => {
        if (typeof document !== 'undefined' && document.querySelector(to.hash)) {
          resolve({ el: to.hash, behavior: scrollMotion(), top: getScrollOffset() })
        } else if (Date.now() - start < 800) {
          setTimeout(tryResolve, 50)
        } else {
          resolve({ top: 0, behavior: scrollMotion() })
        }
      }
      tryResolve()
    })
  }
  return { top: 0, behavior: scrollMotion() }
}
