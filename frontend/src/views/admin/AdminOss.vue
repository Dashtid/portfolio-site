<template>
  <div class="admin-oss">
    <header class="page-header">
      <div class="page-header-left">
        <h2 class="section-title">OSS Contributions</h2>
        <p v-if="dashboard" class="page-header-meta">
          Tracking
          <span class="meta-strong">{{ dashboard.trackedRepos.length }}</span>
          upstream repos · last refresh
          <span class="meta-strong">{{ formatLastRefresh(dashboard.lastRefreshAt) }}</span>
        </p>
      </div>
      <div class="page-header-actions">
        <a
          class="pulls-link"
          href="https://github.com/pulls"
          target="_blank"
          rel="noopener"
          title="Open the GitHub global PRs view (your authored + assigned)"
        >
          github.com/pulls ↗
        </a>
        <button
          class="refresh-button"
          type="button"
          :disabled="refreshing || dashboard?.refreshInProgress"
          @click="refresh"
        >
          {{ refreshing || dashboard?.refreshInProgress ? 'Refreshing…' : 'Refresh' }}
        </button>
      </div>
    </header>

    <div v-if="loadError" class="error-alert" role="alert">
      <span>{{ loadError }}</span>
      <button class="retry-button" @click="load">Retry</button>
    </div>

    <div v-if="loading" class="loading-state" aria-live="polite">Loading contributions…</div>

    <div
      v-else-if="lastRefreshTelemetry"
      class="refresh-telemetry"
      role="status"
      aria-live="polite"
    >
      Refresh complete · {{ lastRefreshTelemetry.contributionsCount }} contributions · cost
      {{ lastRefreshTelemetry.rateLimitCost }} pts · remaining
      {{ lastRefreshTelemetry.rateLimitRemaining.toLocaleString() }} / 5,000 per hour.
    </div>

    <template v-if="dashboard && !loading">
      <section
        v-for="bucket in BUCKET_ORDER"
        :key="bucket"
        class="bucket-section"
        :aria-label="BUCKET_LABEL[bucket]"
      >
        <header class="bucket-header" :class="`bucket-${bucket.toLowerCase()}`">
          <h3 class="bucket-title">{{ BUCKET_LABEL[bucket] }}</h3>
          <span class="bucket-count">{{ dashboard.buckets[bucket].length }}</span>
        </header>
        <p class="bucket-description">{{ BUCKET_DESCRIPTION[bucket] }}</p>

        <div v-if="dashboard.buckets[bucket].length === 0" class="empty-state">
          {{ BUCKET_EMPTY_MESSAGE[bucket] }}
        </div>

        <ul v-else class="card-grid" role="list">
          <li
            v-for="row in dashboard.buckets[bucket]"
            :key="row.id"
            class="contrib-card"
            :class="{ 'contrib-card-draft': row.isDraft }"
          >
            <div class="contrib-meta">
              <span class="contrib-repo" :title="row.repoNameWithOwner">
                {{ row.repoNameWithOwner }}
              </span>
              <span v-if="row.number > 0" class="contrib-number">#{{ row.number }}</span>
              <span v-if="row.isDraft" class="contrib-draft-badge">DRAFT</span>
              <span
                v-if="row.kind === 'pr' && row.state === 'MERGED'"
                class="contrib-state-badge contrib-state-merged"
              >
                MERGED
              </span>
            </div>
            <a
              v-if="row.url"
              :href="row.url"
              class="contrib-title"
              target="_blank"
              rel="noopener"
              :title="row.title"
            >
              {{ row.title }}
            </a>
            <span v-else class="contrib-title contrib-title-plain">{{ row.title }}</span>
            <div class="contrib-footer">
              <span class="contrib-activity" :title="row.lastActivityAt">
                {{ daysSince(row.lastActivityAt) }}
              </span>
              <span v-if="row.authorLogin && row.kind !== 'later'" class="contrib-author">
                by {{ row.authorLogin }}
              </span>
            </div>
          </li>
        </ul>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import ossService, {
  BUCKET_DESCRIPTION,
  BUCKET_EMPTY_MESSAGE,
  BUCKET_LABEL,
  BUCKET_ORDER,
  type OssDashboardView,
  type OssRefreshResult
} from '../../services/oss'
import { adminLogger } from '../../utils/logger'

const dashboard = ref<OssDashboardView | null>(null)
const loading = ref<boolean>(true)
const refreshing = ref<boolean>(false)
const loadError = ref<string | null>(null)
const lastRefreshTelemetry = ref<OssRefreshResult | null>(null)

const load = async (): Promise<void> => {
  loading.value = true
  loadError.value = null
  try {
    const view = await ossService.getOssDashboard()
    dashboard.value = view
    if (!view) {
      loadError.value = 'Could not load OSS contributions.'
    }
  } catch (err) {
    adminLogger.error('OSS dashboard load failed:', err)
    loadError.value = 'Failed to load OSS contributions.'
  } finally {
    loading.value = false
  }
}

const refresh = async (): Promise<void> => {
  if (refreshing.value) return
  refreshing.value = true
  loadError.value = null
  try {
    const result = await ossService.refreshOssDashboard()
    if (result) {
      lastRefreshTelemetry.value = result
      // Refetch the dashboard so the freshly-classified rows render. The
      // backend POST returns telemetry but not the bucketed rows.
      await load()
    } else {
      loadError.value =
        'Refresh failed. Either the GitHub PAT is unconfigured ' +
        '(operator must set GITHUB_OSS_DASHBOARD_PAT) or the upstream API call errored.'
    }
  } finally {
    refreshing.value = false
  }
}

const daysSince = (iso: string): string => {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  const now = Date.now()
  const diffMs = now - d.getTime()
  const days = Math.floor(diffMs / (1000 * 60 * 60 * 24))
  if (days <= 0) return 'today'
  if (days === 1) return '1 day ago'
  if (days < 30) return `${days} days ago`
  if (days < 60) return '1 month ago'
  return `${Math.floor(days / 30)} months ago`
}

const formatLastRefresh = (iso: string | null): string => {
  if (!iso) return 'never'
  return daysSince(iso)
}

onMounted(load)
</script>

<style scoped>
.admin-oss {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-6);
}

.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-4);
  flex-wrap: wrap;
}

.page-header-left {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-1);
}

.section-title {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-slate-900);
  margin: 0;
}

.page-header-meta {
  font-size: var(--font-size-sm);
  color: var(--color-slate-600);
  margin: 0;
}

.meta-strong {
  color: var(--color-slate-900);
  font-weight: var(--font-weight-semibold);
}

.page-header-actions {
  display: flex;
  align-items: center;
  gap: var(--spacing-3);
}

.pulls-link {
  color: var(--color-primary);
  text-decoration: none;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  padding: var(--spacing-2) var(--spacing-3);
  border-radius: var(--radius-base);
  border: 1px solid var(--color-slate-200);
}

.pulls-link:hover {
  background: var(--color-slate-50);
}

.pulls-link:focus-visible {
  outline: 2px solid var(--color-primary-500, #3b82f6);
  outline-offset: 2px;
}

.refresh-button {
  padding: var(--spacing-2) var(--spacing-4);
  background: var(--color-primary);
  color: white;
  border: none;
  border-radius: var(--radius-base);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  transition: background var(--transition-base) ease;
}

.refresh-button:hover:not(:disabled) {
  background: var(--color-primary-700, #1e40af);
}

.refresh-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.refresh-button:focus-visible {
  outline: 2px solid var(--color-primary-500, #3b82f6);
  outline-offset: 2px;
}

.refresh-telemetry {
  padding: var(--spacing-3) var(--spacing-4);
  background: #ecfdf5;
  border: 1px solid #a7f3d0;
  border-radius: var(--radius-base);
  color: #065f46;
  font-size: var(--font-size-sm);
}

.bucket-section {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3);
}

.bucket-header {
  display: flex;
  align-items: baseline;
  gap: var(--spacing-3);
  padding-bottom: var(--spacing-2);
  border-bottom: 2px solid var(--color-slate-200);
}

.bucket-title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-bold);
  color: var(--color-slate-900);
  margin: 0;
  letter-spacing: 0.02em;
}

.bucket-count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 1.5rem;
  padding: 0 var(--spacing-2);
  background: var(--color-slate-100);
  border-radius: var(--radius-full, 999px);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-slate-700);
}

/* Per-bucket accent colors so the visual triage is faster than reading. */
.bucket-now {
  border-bottom-color: #ef4444;
}
.bucket-now .bucket-count {
  background: #fee2e2;
  color: #991b1b;
}

.bucket-waiting {
  border-bottom-color: #f59e0b;
}
.bucket-waiting .bucket-count {
  background: #fef3c7;
  color: #92400e;
}

.bucket-watching {
  border-bottom-color: #3b82f6;
}
.bucket-watching .bucket-count {
  background: #dbeafe;
  color: #1e40af;
}

.bucket-later {
  border-bottom-color: #6b7280;
}
.bucket-later .bucket-count {
  background: #f3f4f6;
  color: #4b5563;
}

.bucket-done {
  border-bottom-color: #10b981;
}
.bucket-done .bucket-count {
  background: #d1fae5;
  color: #065f46;
}

.bucket-description {
  font-size: var(--font-size-sm);
  color: var(--color-slate-500);
  margin: 0;
  font-style: italic;
}

.card-grid {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: var(--spacing-4);
}

.contrib-card {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
  padding: var(--spacing-4);
  background: white;
  border: 1px solid var(--color-slate-200);
  border-radius: var(--radius-base);
  transition: box-shadow var(--transition-base) ease;
}

.contrib-card:hover {
  box-shadow: var(--elevation-sm);
}

.contrib-card-draft {
  background: #fef9c3;
  border-color: #fde68a;
}

.contrib-meta {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  font-size: var(--font-size-xs);
  color: var(--color-slate-500);
  font-variant-numeric: tabular-nums;
}

.contrib-repo {
  color: var(--color-slate-700);
  font-weight: var(--font-weight-medium);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 50%;
}

.contrib-number {
  color: var(--color-slate-500);
}

.contrib-draft-badge,
.contrib-state-badge {
  margin-left: auto;
  padding: 1px var(--spacing-2);
  border-radius: var(--radius-base);
  font-size: 10px;
  font-weight: var(--font-weight-bold);
  letter-spacing: 0.05em;
}

.contrib-draft-badge {
  background: #fde68a;
  color: #78350f;
}

.contrib-state-merged {
  background: #c4b5fd;
  color: #5b21b6;
}

.contrib-title {
  /* Clamp long titles to two lines so cards stay even-height. */
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  color: var(--color-slate-900);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  text-decoration: none;
  line-height: 1.35;
}

.contrib-title:hover:not(.contrib-title-plain) {
  text-decoration: underline;
}

.contrib-title-plain {
  color: var(--color-slate-700);
}

.contrib-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-2);
  font-size: var(--font-size-xs);
  color: var(--color-slate-500);
}

.contrib-author {
  font-style: italic;
}

.empty-state {
  padding: var(--spacing-6);
  text-align: center;
  color: var(--color-slate-500);
  font-size: var(--font-size-sm);
  background: var(--color-slate-50);
  border: 1px dashed var(--color-slate-200);
  border-radius: var(--radius-base);
}

.loading-state {
  padding: var(--spacing-8);
  text-align: center;
  color: var(--color-slate-500);
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
}

.retry-button:hover {
  background: #b91c1c;
}

[data-theme='dark'] .section-title,
[data-theme='dark'] .bucket-title,
[data-theme='dark'] .meta-strong {
  color: var(--text-primary, #f8fafc);
}

[data-theme='dark'] .contrib-card {
  background: var(--bg-secondary, #1e293b);
  border-color: var(--border-primary, #334155);
}

[data-theme='dark'] .contrib-card-draft {
  background: #422006;
  border-color: #854d0e;
}

[data-theme='dark'] .contrib-title {
  color: var(--text-primary, #f8fafc);
}

[data-theme='dark'] .contrib-repo {
  color: var(--text-secondary, #cbd5e1);
}

[data-theme='dark'] .page-header-meta,
[data-theme='dark'] .bucket-description,
[data-theme='dark'] .contrib-meta,
[data-theme='dark'] .contrib-footer,
[data-theme='dark'] .empty-state,
[data-theme='dark'] .loading-state {
  color: var(--text-tertiary, #94a3b8);
}

[data-theme='dark'] .empty-state {
  background: var(--bg-tertiary, #334155);
  border-color: var(--border-primary, #475569);
}

[data-theme='dark'] .bucket-count {
  background: var(--bg-tertiary, #334155);
  color: var(--text-secondary, #cbd5e1);
}

[data-theme='dark'] .pulls-link {
  border-color: var(--border-primary, #334155);
  color: var(--primary-400, #60a5fa);
}

[data-theme='dark'] .pulls-link:hover {
  background: var(--bg-tertiary, #334155);
}

[data-theme='dark'] .refresh-telemetry {
  background: #052e21;
  border-color: #047857;
  color: #6ee7b7;
}

[data-theme='dark'] .error-alert {
  background: #450a0a;
  border-color: #7f1d1d;
  color: #fecaca;
}

@media (max-width: 640px) {
  .card-grid {
    grid-template-columns: 1fr;
  }
}
</style>
