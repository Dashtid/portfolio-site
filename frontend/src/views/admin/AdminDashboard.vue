<template>
  <div class="admin-dashboard">
    <!-- Admin Header -->
    <header class="admin-header">
      <div class="header-content">
        <div class="header-left">
          <h1 class="dashboard-title">Portfolio Admin</h1>
        </div>
        <div class="header-right">
          <div v-if="authStore.currentUser" class="user-info">
            <img
              v-if="authStore.currentUser.avatar_url"
              :src="authStore.currentUser.avatar_url"
              :alt="authStore.currentUser.name"
              class="user-avatar"
            />
            <span class="user-name">{{
              authStore.currentUser.name || authStore.currentUser.username
            }}</span>
          </div>
          <button class="logout-button" @click="logout">Sign Out</button>
        </div>
      </div>
    </header>

    <!-- Admin Navigation -->
    <nav class="admin-nav" role="navigation" aria-label="Admin navigation">
      <router-link to="/admin" class="nav-link" :class="{ active: $route.path === '/admin' }">
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
    </nav>

    <!-- Admin Content -->
    <main id="main-content" class="admin-content" tabindex="-1">
      <router-view v-if="$route.path !== '/admin'" />
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
  min-height: 100vh;
  background: var(--color-gray-50);
}

/* Admin Header */
.admin-header {
  background: white;
  border-bottom: 1px solid var(--color-gray-200);
  padding: var(--spacing-4) 0;
}

.header-content {
  max-width: 1200px;
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
  color: var(--color-gray-900);
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
  width: 32px;
  height: 32px;
  border-radius: var(--radius-full);
  border: 2px solid var(--color-gray-200);
}

.user-name {
  font-size: var(--font-size-sm);
  color: var(--color-gray-700);
  font-weight: var(--font-weight-medium);
}

.logout-button {
  padding: var(--spacing-2) var(--spacing-4);
  background: transparent;
  color: var(--color-gray-600);
  border: 1px solid var(--color-gray-300);
  border-radius: var(--radius-base);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  transition: all var(--transition-base) ease;
}

.logout-button:hover {
  background: var(--color-gray-100);
  color: var(--color-gray-900);
}

.logout-button:focus-visible {
  outline: 2px solid var(--color-primary-500, #3b82f6);
  outline-offset: 2px;
}

/* Admin Navigation */
.admin-nav {
  background: white;
  border-bottom: 1px solid var(--color-gray-200);
  padding: 0;
  display: flex;
  gap: var(--spacing-1);
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 var(--spacing-6);
}

.nav-link {
  padding: var(--spacing-3) var(--spacing-4);
  color: var(--color-gray-600);
  text-decoration: none;
  font-weight: var(--font-weight-medium);
  font-size: var(--font-size-sm);
  border-bottom: 2px solid transparent;
  transition: all var(--transition-base) ease;
}

.nav-link:hover {
  color: var(--color-gray-900);
}

.nav-link.active {
  color: var(--color-primary);
  border-bottom-color: var(--color-primary);
}

/* Admin Content */
.admin-content {
  max-width: 1200px;
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

  .admin-nav {
    overflow-x: auto;
    padding: 0 var(--spacing-4);
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
