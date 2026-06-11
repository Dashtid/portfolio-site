<template>
  <div class="dashboard-overview">
    <h2 class="section-title">Dashboard Overview</h2>

    <div v-if="loadError" class="error-alert" role="alert">
      <svg
        class="error-icon"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
      >
        <circle cx="12" cy="12" r="10" />
        <line x1="12" y1="8" x2="12" y2="12" />
        <line x1="12" y1="16" x2="12.01" y2="16" />
      </svg>
      <span>{{ loadError }}</span>
      <button class="retry-button" @click="emit('retry')">Retry</button>
    </div>

    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-value">{{ companiesCount }}</div>
        <div class="stat-label">Companies</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ skillsCount }}</div>
        <div class="stat-label">Skills</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ projectsCount }}</div>
        <div class="stat-label">Projects</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ featuredCount }}</div>
        <div class="stat-label">Featured</div>
      </div>
    </div>

    <!-- BACKEND-ADMIN-10: Sentry deep-link panel.
         Mounts only after the admin-only sentry-panel endpoint reports
         enabled=true; clicking the CTA opens the operator's configured
         issues view in a new tab. -->
    <div v-if="sentryPanel?.enabled" class="sentry-panel" data-testid="sentry-panel">
      <div class="sentry-panel-header">
        <svg
          class="sentry-icon"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <path d="M12 2L2 22h20L12 2z" />
          <line x1="12" y1="9" x2="12" y2="15" />
          <line x1="12" y1="18" x2="12.01" y2="18" />
        </svg>
        <div class="sentry-panel-text">
          <div class="sentry-panel-title">Error Tracking</div>
          <div class="sentry-panel-subtitle">
            {{
              sentryPanel.issues_url
                ? 'Sentry is wired up. Open the issues view for the last 24h.'
                : 'Sentry is wired up but no issues URL is configured.'
            }}
          </div>
        </div>
        <a
          v-if="sentryPanel.issues_url"
          :href="sentryPanel.issues_url"
          target="_blank"
          rel="noopener noreferrer"
          class="sentry-cta"
        >
          Open Sentry
        </a>
      </div>
    </div>

    <div class="quick-actions">
      <h3 class="subsection-title">Quick Actions</h3>
      <div class="action-buttons">
        <router-link to="/admin/companies" class="action-button">
          <svg
            class="action-icon"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path
              d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
            />
          </svg>
          <span>Add Experience</span>
        </router-link>
        <router-link to="/admin/projects" class="action-button">
          <svg
            class="action-icon"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path d="M12 4v16m8-8H4" />
          </svg>
          <span>New Project</span>
        </router-link>
        <router-link to="/admin/analytics" class="action-button">
          <svg
            class="action-icon"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path d="M3 3v18h18" />
            <path d="M7 14l4-4 4 4 5-5" />
          </svg>
          <span>View Analytics</span>
        </router-link>
        <a href="/" target="_blank" class="action-button">
          <svg
            class="action-icon"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
          >
            <path d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            <path
              d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
            />
          </svg>
          <span>View Site</span>
        </a>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import apiClient from '../../api/client'
import { adminLogger } from '../../utils/logger'

interface Props {
  companiesCount: number
  skillsCount: number
  projectsCount: number
  featuredCount: number
  loadError: string | null
}

interface SentryPanelConfig {
  enabled: boolean
  issues_url: string | null
}

defineProps<Props>()

const emit = defineEmits<{
  retry: []
}>()

// BACKEND-ADMIN-10: fetch the deep-link config. Silently no-ops on
// failure (the panel just stays hidden) — a Sentry-config fetch failure
// shouldn't break the dashboard's primary stats.
const sentryPanel = ref<SentryPanelConfig | null>(null)

onMounted(async () => {
  try {
    const response = await apiClient.get<SentryPanelConfig>('/api/v1/admin/sentry-panel')
    sentryPanel.value = response.data
  } catch (error) {
    adminLogger.error('Failed to load Sentry panel config:', error)
  }
})
</script>

<style scoped>
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

.error-alert {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
  padding: var(--spacing-4);
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: var(--radius-lg);
  color: #991b1b;
  margin-bottom: var(--spacing-6);
}

.sentry-panel {
  background: white;
  border: 1px solid var(--color-gray-200);
  border-radius: var(--radius-lg);
  padding: var(--spacing-4) var(--spacing-6);
  margin-bottom: var(--spacing-6);
}

.sentry-panel-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-4);
}

.sentry-icon {
  width: 28px;
  height: 28px;
  color: #f59e0b;
  flex-shrink: 0;
}

.sentry-panel-text {
  flex: 1;
}

.sentry-panel-title {
  font-weight: var(--font-weight-semibold);
  color: var(--color-gray-900);
  margin-bottom: 2px;
}

.sentry-panel-subtitle {
  font-size: var(--font-size-sm);
  color: var(--color-gray-600);
}

.sentry-cta {
  padding: var(--spacing-2) var(--spacing-4);
  background: #6366f1;
  color: white;
  text-decoration: none;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  border-radius: var(--radius-base);
  transition: background var(--transition-base) ease;
  white-space: nowrap;
}

.sentry-cta:hover {
  background: #4f46e5;
}

.sentry-cta:focus-visible {
  outline: 2px solid var(--color-primary-500, #3b82f6);
  outline-offset: 2px;
}

.error-icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
  color: #dc2626;
}

.retry-button {
  margin-left: auto;
  padding: var(--spacing-2) var(--spacing-4);
  background: #dc2626;
  color: white;
  border: none;
  border-radius: var(--radius-base);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  transition: background var(--transition-base) ease;
}

.retry-button:hover {
  background: #b91c1c;
}

.retry-button:focus-visible {
  outline: 2px solid var(--color-primary-500, #3b82f6);
  outline-offset: 2px;
}

@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: 1fr 1fr;
  }
}

[data-theme='dark'] .section-title {
  color: var(--text-primary, #f8fafc);
}

[data-theme='dark'] .stat-card {
  background: var(--bg-secondary, #1e293b);
  border-color: var(--border-primary, #334155);
}

[data-theme='dark'] .stat-value {
  color: var(--primary-400, #60a5fa);
}

[data-theme='dark'] .stat-label {
  color: var(--text-secondary, #cbd5e1);
}

[data-theme='dark'] .quick-actions {
  background: var(--bg-secondary, #1e293b);
  border-color: var(--border-primary, #334155);
}

[data-theme='dark'] .subsection-title {
  color: var(--text-primary, #f8fafc);
}

[data-theme='dark'] .action-button {
  background: var(--bg-tertiary, #334155);
  color: var(--text-secondary, #cbd5e1);
  border-color: var(--border-primary, #475569);
}

[data-theme='dark'] .action-button:hover {
  background: var(--primary-600, #2563eb);
  color: white;
  border-color: var(--primary-600, #2563eb);
}

[data-theme='dark'] .error-alert {
  background: #450a0a;
  border-color: #7f1d1d;
  color: #fecaca;
}

[data-theme='dark'] .error-icon {
  color: #f87171;
}

[data-theme='dark'] .retry-button {
  background: #dc2626;
}

[data-theme='dark'] .retry-button:hover {
  background: #ef4444;
}

[data-theme='dark'] .sentry-panel {
  background: var(--bg-secondary, #1e293b);
  border-color: var(--border-primary, #334155);
}

[data-theme='dark'] .sentry-panel-title {
  color: var(--text-primary, #f8fafc);
}

[data-theme='dark'] .sentry-panel-subtitle {
  color: var(--text-secondary, #cbd5e1);
}
</style>
