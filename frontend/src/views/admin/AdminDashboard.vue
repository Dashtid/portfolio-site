<template>
  <div class="admin-dashboard">
    <!-- Admin Header -->
    <header class="admin-header print:hidden">
      <div class="header-content">
        <div class="header-left">
          <h1 class="dashboard-title">Portfolio Admin</h1>
        </div>
        <div class="header-right">
          <div v-if="authStore.currentUser" class="user-info">
            <!-- Initials, not the GitHub avatar_url: the site's CSP is
                 img-src 'self', so the remote avatar was blocked and rendered
                 as a broken-image circle. This is a private page's decoration
                 and does not justify opening img-src to a third-party host. -->
            <span class="user-avatar" aria-hidden="true">{{ userInitials }}</span>
            <span class="user-name">{{
              authStore.currentUser.name || authStore.currentUser.username
            }}</span>
          </div>
          <button class="logout-button" @click="logout">Sign Out</button>
        </div>
      </div>
    </header>

    <!-- Admin Navigation -->
    <nav class="admin-nav print:hidden" role="navigation" aria-label="Admin navigation">
      <div class="admin-nav-inner">
        <router-link
          to="/admin"
          class="nav-link"
          :class="{ active: $route.name === 'admin-dashboard' }"
        >
          Dashboard
        </router-link>
        <router-link
          to="/admin/companies"
          class="nav-link"
          :class="{ active: $route.path === '/admin/companies' }"
        >
          Experience
        </router-link>
        <router-link
          to="/admin/projects"
          class="nav-link"
          :class="{ active: $route.path === '/admin/projects' }"
        >
          Projects
        </router-link>
        <router-link
          to="/admin/skills"
          class="nav-link"
          :class="{ active: $route.path === '/admin/skills' }"
        >
          Skills
        </router-link>
        <router-link
          to="/admin/education"
          class="nav-link"
          :class="{ active: $route.path === '/admin/education' }"
        >
          Education
        </router-link>
        <router-link
          to="/admin/documents"
          class="nav-link"
          :class="{ active: $route.path === '/admin/documents' }"
        >
          Documents
        </router-link>
        <router-link
          to="/admin/analytics"
          class="nav-link"
          :class="{ active: $route.path === '/admin/analytics' }"
        >
          Analytics
        </router-link>
        <router-link
          to="/admin/metrics"
          class="nav-link"
          :class="{ active: $route.path === '/admin/metrics' }"
        >
          Metrics
        </router-link>
        <router-link
          to="/admin/oss"
          class="nav-link"
          :class="{ active: $route.path === '/admin/oss' }"
        >
          OSS
        </router-link>
        <router-link
          to="/admin/cv"
          class="nav-link"
          :class="{ active: $route.path === '/admin/cv' }"
        >
          CV
        </router-link>
      </div>
    </nav>

    <!-- Admin Content -->
    <main id="main-content" class="admin-content" tabindex="-1">
      <!-- Route NAME, not path string: vue-router resolves '/admin/' (trailing
           slash) to path '/admin/', which failed a path equality check and
           rendered header + nav with a blank main. -->
      <router-view v-if="$route.name !== 'admin-dashboard'" />
      <DashboardOverview
        v-else
        :companies-count="portfolioStore.companies.length"
        :skills-count="portfolioStore.skills.length"
        :projects-count="portfolioStore.projects.length"
        :featured-count="featuredProjects"
        :load-error="loadError"
        @retry="retryLoad"
      />
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { usePortfolioStore } from '../../stores/portfolio'
import { adminLogger } from '../../utils/logger'
import DashboardOverview from '@/components/admin/DashboardOverview.vue'

const router = useRouter()
const authStore = useAuthStore()
const portfolioStore = usePortfolioStore()

// State
const loadError = ref<string | null>(null)

// Computed
const featuredProjects = computed<number>(() => {
  return portfolioStore.projects.filter(p => p.featured).length
})

const userInitials = computed<string>(() => {
  const user = authStore.currentUser
  if (!user) return ''
  const source = user.name || user.username || ''
  const initials = source
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map(part => part[0])
    .join('')
  return initials.toUpperCase()
})

// Methods
const logout = async (): Promise<void> => {
  try {
    await authStore.logout()
  } catch (error) {
    adminLogger.error('Logout failed:', error)
  } finally {
    // Always redirect to login, even if logout API call fails
    router.push('/admin/login')
  }
}

// Retry loading data after error
const retryLoad = async (): Promise<void> => {
  try {
    loadError.value = null
    await portfolioStore.fetchAllData()
  } catch (error) {
    adminLogger.error('Failed to load portfolio data:', error)
    loadError.value = 'Failed to load dashboard data. Please try again.'
  }
}

// Load data on mount with proper error handling
onMounted(async (): Promise<void> => {
  await retryLoad()
})
</script>

<style scoped>
.admin-dashboard {
  /* 80rem = 1280px, matching the public site's max-w-7xl so the gutter does
     not jump when moving between /admin and the site itself. */
  --admin-container-max: 80rem;

  min-height: 100vh;
  background: var(--color-slate-50);
}

/* Admin Header */
.admin-header {
  background: white;
  border-bottom: 1px solid var(--color-slate-200);
  padding: var(--spacing-4) 0;
}

.header-content {
  max-width: var(--admin-container-max);
  margin: 0 auto;
  padding: 0 var(--spacing-6);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--spacing-4);
}

.dashboard-title {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-slate-900);
  margin: 0;
}

.header-right {
  display: flex;
  align-items: center;
  gap: var(--spacing-4);
}

.user-info {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
}

.user-avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: var(--radius-full);
  border: 2px solid var(--color-slate-200);
  background: var(--color-slate-100);
  color: var(--color-slate-700);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-bold);
  line-height: 1;
  user-select: none;
}

.user-name {
  font-size: var(--font-size-sm);
  color: var(--color-slate-700);
  font-weight: var(--font-weight-medium);
}

.logout-button {
  padding: var(--spacing-2) var(--spacing-4);
  background: transparent;
  color: var(--color-slate-600);
  border: 1px solid var(--color-slate-300);
  border-radius: var(--radius-base);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  transition: all var(--transition-base) ease;
}

.logout-button:hover {
  background: var(--color-slate-100);
  color: var(--color-slate-900);
}

.logout-button:focus-visible {
  outline: 2px solid var(--color-primary-500, #3b82f6);
  outline-offset: 2px;
}

/* Admin Navigation
   The band (background + border) is full-bleed on .admin-nav so it lines up
   with the full-bleed .admin-header above it; the width constraint lives on
   the inner element, mirroring .admin-header/.header-content. Keeping both on
   one element painted the nav as a centred 1200px island under a full-bleed
   header — a notch of page background down each side at wide viewports.
   overflow-x is unconditional: the ten links need ~900px, so the tab strip
   was unreachable (and the whole document scrolled sideways) between 769px
   and ~911px, where the old max-width:768px media query no longer applied. */
.admin-nav {
  background: white;
  border-bottom: 1px solid var(--color-slate-200);
  overflow-x: auto;
  scrollbar-width: thin;
}

.admin-nav-inner {
  display: flex;
  gap: var(--spacing-1);
  min-width: max-content;
  max-width: var(--admin-container-max);
  margin: 0 auto;
  padding: 0 var(--spacing-6);
}

.nav-link {
  padding: var(--spacing-3) var(--spacing-4);
  color: var(--color-slate-600);
  text-decoration: none;
  font-weight: var(--font-weight-medium);
  font-size: var(--font-size-sm);
  white-space: nowrap;
  flex-shrink: 0;
  border-bottom: 2px solid transparent;
  transition: all var(--transition-base) ease;
}

.nav-link:hover {
  color: var(--color-slate-900);
}

.nav-link.active {
  color: var(--color-primary);
  border-bottom-color: var(--color-primary);
}

/* Admin Content */
.admin-content {
  max-width: var(--admin-container-max);
  margin: 0 auto;
  padding: var(--spacing-8) var(--spacing-6);
}

/* Responsive Design */
@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    gap: var(--spacing-4);
    align-items: flex-start;
  }

  .admin-nav-inner {
    padding: 0 var(--spacing-4);
  }
}

/* Print: the admin shell is chrome, not content. Its header and nav are
   already print:hidden, but .admin-content's gutter still offset the printed
   CV by 24px per side and 32px on top, so the page margins came out wrong. */
@media print {
  .admin-content {
    max-width: none;
    padding: 0;
    margin: 0;
  }

  .admin-dashboard {
    min-height: 0;
    background: none;
  }
}

/* Dark Mode */
[data-theme='dark'] .admin-dashboard {
  background: var(--bg-primary, #0f172a);
}

[data-theme='dark'] .admin-header {
  background: var(--bg-secondary, #1e293b);
  border-bottom-color: var(--border-primary, #334155);
}

[data-theme='dark'] .dashboard-title {
  color: var(--text-primary, #f8fafc);
}

[data-theme='dark'] .user-name {
  color: var(--text-secondary, #cbd5e1);
}

[data-theme='dark'] .user-avatar {
  border-color: var(--border-primary, #334155);
  background: var(--bg-tertiary, #334155);
  color: var(--text-primary, #f8fafc);
}

[data-theme='dark'] .logout-button {
  color: var(--text-secondary, #cbd5e1);
  border-color: var(--border-primary, #334155);
}

[data-theme='dark'] .logout-button:hover {
  background: var(--bg-tertiary, #334155);
  color: var(--text-primary, #f8fafc);
}

[data-theme='dark'] .admin-nav {
  background: var(--bg-secondary, #1e293b);
  border-bottom-color: var(--border-primary, #334155);
}

[data-theme='dark'] .nav-link {
  color: var(--text-secondary, #cbd5e1);
}

[data-theme='dark'] .nav-link:hover {
  color: var(--text-primary, #f8fafc);
}

[data-theme='dark'] .nav-link.active {
  color: var(--primary-400, #60a5fa);
  border-bottom-color: var(--primary-400, #60a5fa);
}
</style>
