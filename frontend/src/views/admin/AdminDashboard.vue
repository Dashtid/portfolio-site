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
            >
            <span class="user-name">{{ authStore.currentUser.name || authStore.currentUser.username }}</span>
          </div>
          <button @click="logout" class="logout-button">
            Sign Out
          </button>
        </div>
      </div>
    </header>

    <!-- Admin Navigation -->
    <nav class="admin-nav">
      <router-link
        to="/admin"
        class="nav-link"
        :class="{ active: $route.path === '/admin' }"
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
        to="/admin/skills"
        class="nav-link"
        :class="{ active: $route.path === '/admin/skills' }"
      >
        Skills
      </router-link>
      <router-link
        to="/admin/projects"
        class="nav-link"
        :class="{ active: $route.path === '/admin/projects' }"
      >
        Projects
      </router-link>
    </nav>

    <!-- Admin Content -->
    <main class="admin-content">
      <router-view v-if="$route.path !== '/admin'" />

      <!-- Dashboard Overview -->
      <div v-else class="dashboard-overview">
        <h2 class="section-title">Dashboard Overview</h2>

        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-value">{{ portfolioStore.companies.length }}</div>
            <div class="stat-label">Companies</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ portfolioStore.skills.length }}</div>
            <div class="stat-label">Skills</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ portfolioStore.projects.length }}</div>
            <div class="stat-label">Projects</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ featuredProjects }}</div>
            <div class="stat-label">Featured</div>
          </div>
        </div>

        <div class="quick-actions">
          <h3 class="subsection-title">Quick Actions</h3>
          <div class="action-buttons">
            <router-link to="/admin/companies" class="action-button">
              <svg class="action-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>
              </svg>
              <span>Add Experience</span>
            </router-link>
            <router-link to="/admin/projects" class="action-button">
              <svg class="action-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 4v16m8-8H4"/>
              </svg>
              <span>New Project</span>
            </router-link>
            <router-link to="/admin/skills" class="action-button">
              <svg class="action-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
              </svg>
              <span>Update Skills</span>
            </router-link>
            <a href="/" target="_blank" class="action-button">
              <svg class="action-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                <path d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"/>
              </svg>
              <span>View Site</span>
            </a>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../stores/auth'
import { usePortfolioStore } from '../../stores/portfolio'

const router = useRouter()
const authStore = useAuthStore()
const portfolioStore = usePortfolioStore()

// Computed
const featuredProjects = computed<number>(() => {
  return portfolioStore.projects.filter(p => p.featured).length
})

// Methods
const logout = async (): Promise<void> => {
  await authStore.logout()
  router.push('/admin/login')
}

// Load data on mount
onMounted((): void => {
  portfolioStore.fetchAllData()
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

/* Dashboard Overview */
.section-title {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-gray-900);
  margin-bottom: var(--spacing-6);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--spacing-6);
  margin-bottom: var(--spacing-8);
}

.stat-card {
  background: white;
  padding: var(--spacing-6);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-gray-200);
  text-align: center;
}

.stat-value {
  font-size: var(--font-size-4xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-primary);
  margin-bottom: var(--spacing-2);
}

.stat-label {
  font-size: var(--font-size-sm);
  color: var(--color-gray-600);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* Quick Actions */
.quick-actions {
  background: white;
  padding: var(--spacing-6);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-gray-200);
}

.subsection-title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-gray-900);
  margin-bottom: var(--spacing-4);
}

.action-buttons {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--spacing-4);
}

.action-button {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-3) var(--spacing-4);
  background: var(--color-gray-50);
  color: var(--color-gray-700);
  text-decoration: none;
  font-weight: var(--font-weight-medium);
  font-size: var(--font-size-sm);
  border-radius: var(--radius-base);
  border: 1px solid var(--color-gray-200);
  transition: all var(--transition-base) ease;
}

.action-button:hover {
  background: var(--color-primary);
  color: white;
  border-color: var(--color-primary);
  transform: translateY(-2px);
  box-shadow: var(--shadow-sm);
}

.action-icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
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

  .stats-grid {
    grid-template-columns: 1fr 1fr;
  }
}
</style>