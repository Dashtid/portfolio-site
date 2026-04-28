<template>
  <div class="admin-analytics">
    <header class="page-header">
      <h2 class="section-title">Analytics</h2>
      <div class="range-tabs" role="tablist" aria-label="Date range">
        <button
          v-for="r in ranges"
          :key="r.days"
          role="tab"
          :aria-selected="days === r.days"
          class="range-tab"
          :class="{ active: days === r.days }"
          @click="setRange(r.days)"
        >
          {{ r.label }}
        </button>
      </div>
    </header>

    <div v-if="loadError" class="error-alert" role="alert">
      <span>{{ loadError }}</span>
      <button class="retry-button" @click="load">Retry</button>
    </div>

    <div v-if="loading" class="loading-state" aria-live="polite">Loading analytics…</div>

    <template v-else-if="summary">
      <section class="stats-grid" aria-label="Summary">
        <div class="stat-card">
          <div class="stat-value">{{ summary.total_views.toLocaleString() }}</div>
          <div class="stat-label">Page views</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ summary.unique_visitors.toLocaleString() }}</div>
          <div class="stat-label">Unique visitors</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ formatDuration(summary.avg_session_duration) }}</div>
          <div class="stat-label">Avg. session</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ formatBounce(visitorStats?.bounce_rate ?? null) }}</div>
          <div class="stat-label">Bounce rate</div>
        </div>
      </section>

      <section class="card chart-card" aria-label="Daily views">
        <div class="card-header">
          <h3 class="card-title">Daily views</h3>
          <span class="card-meta">last {{ summary.period_days }} days</span>
        </div>
        <div v-if="!summary.daily_views.length" class="empty-state">
          No traffic in this range yet.
        </div>
        <svg
          v-else
          :viewBox="`0 0 ${chart.width} ${chart.height}`"
          class="chart"
          role="img"
          :aria-label="`Daily page views over ${summary.period_days} days`"
        >
          <polyline
            class="chart-line"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            :points="chart.points"
          />
          <polygon class="chart-fill" :points="chart.areaPoints" />
          <g class="chart-points">
            <circle
              v-for="(p, i) in chart.coords"
              :key="i"
              :cx="p.x"
              :cy="p.y"
              r="3"
              :aria-label="`${p.date}: ${p.value} views`"
            />
          </g>
          <line
            class="chart-axis"
            x1="0"
            :y1="chart.height - 1"
            :x2="chart.width"
            :y2="chart.height - 1"
          />
        </svg>
        <div v-if="summary.daily_views.length" class="chart-axis-labels">
          <span>{{ formatDate(summary.daily_views[0].date) }}</span>
          <span>{{ formatDate(summary.daily_views[summary.daily_views.length - 1].date) }}</span>
        </div>
      </section>

      <div class="two-col">
        <section class="card" aria-label="Top pages">
          <div class="card-header">
            <h3 class="card-title">Top pages</h3>
          </div>
          <ol v-if="summary.top_pages.length" class="top-list">
            <li v-for="page in summary.top_pages" :key="page.path" class="top-list-item">
              <div class="top-list-text">
                <div class="top-list-primary">{{ page.title || page.path }}</div>
                <div class="top-list-secondary">{{ page.path }}</div>
              </div>
              <div class="top-list-value">{{ page.views.toLocaleString() }}</div>
            </li>
          </ol>
          <div v-else class="empty-state">No pages tracked yet.</div>
        </section>

        <section class="card" aria-label="Top countries">
          <div class="card-header">
            <h3 class="card-title">Top countries</h3>
            <span v-if="visitorStats" class="card-meta">
              last {{ visitorStats.period_days }} days
            </span>
          </div>
          <ol v-if="visitorStats && visitorStats.top_countries.length" class="top-list">
            <li v-for="c in visitorStats.top_countries" :key="c.country" class="top-list-item">
              <div class="top-list-text">
                <div class="top-list-primary">{{ c.country || 'Unknown' }}</div>
              </div>
              <div class="top-list-value">{{ c.count.toLocaleString() }}</div>
            </li>
          </ol>
          <div v-else class="empty-state">
            No country data — geo-IP lookup is not enabled on the backend.
          </div>
        </section>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import analyticsService, {
  type AnalyticsSummary,
  type VisitorStats
} from '../../services/analytics'
import { adminLogger } from '../../utils/logger'

interface Range {
  label: string
  days: number
}

const ranges: Range[] = [
  { label: '7d', days: 7 },
  { label: '30d', days: 30 },
  { label: '90d', days: 90 },
  { label: '1y', days: 365 }
]

const days = ref<number>(30)
const summary = ref<AnalyticsSummary | null>(null)
const visitorStats = ref<VisitorStats | null>(null)
const loading = ref<boolean>(true)
const loadError = ref<string | null>(null)

// Chart dimensions in SVG user units. The viewBox preserves aspect ratio
// while CSS scales the rendered size.
const CHART_WIDTH = 800
const CHART_HEIGHT = 220
const CHART_PADDING_X = 8
const CHART_PADDING_Y = 12

const chart = computed(() => {
  const data = summary.value?.daily_views ?? []
  if (!data.length) {
    return { width: CHART_WIDTH, height: CHART_HEIGHT, points: '', areaPoints: '', coords: [] }
  }
  const max = Math.max(...data.map(d => d.views), 1)
  const stepX = data.length > 1 ? (CHART_WIDTH - CHART_PADDING_X * 2) / (data.length - 1) : 0
  const usableHeight = CHART_HEIGHT - CHART_PADDING_Y * 2

  const coords = data.map((d, i) => ({
    x: CHART_PADDING_X + i * stepX,
    y: CHART_PADDING_Y + usableHeight - (d.views / max) * usableHeight,
    value: d.views,
    date: d.date
  }))

  const points = coords.map(p => `${p.x},${p.y}`).join(' ')
  // Close the polygon back along the X axis so we can fill under the line.
  const areaPoints = [
    `${coords[0].x},${CHART_HEIGHT - CHART_PADDING_Y}`,
    ...coords.map(p => `${p.x},${p.y}`),
    `${coords[coords.length - 1].x},${CHART_HEIGHT - CHART_PADDING_Y}`
  ].join(' ')

  return { width: CHART_WIDTH, height: CHART_HEIGHT, points, areaPoints, coords }
})

const setRange = (newDays: number): void => {
  if (newDays === days.value) return
  days.value = newDays
  void load()
}

const load = async (): Promise<void> => {
  loading.value = true
  loadError.value = null
  try {
    const [s, v] = await Promise.all([
      analyticsService.getAnalyticsSummary(days.value),
      analyticsService.getVisitorStats(Math.min(days.value, 90))
    ])
    summary.value = s
    visitorStats.value = v
    if (!s) loadError.value = 'Could not load analytics summary.'
  } catch (err) {
    adminLogger.error('Analytics load failed:', err)
    loadError.value = 'Failed to load analytics.'
  } finally {
    loading.value = false
  }
}

const formatDuration = (seconds: number | null | undefined): string => {
  if (!seconds || seconds < 1) return '—'
  const mins = Math.floor(seconds / 60)
  const secs = Math.round(seconds % 60)
  return mins ? `${mins}m ${secs}s` : `${secs}s`
}

const formatBounce = (rate: number | null): string => {
  if (rate === null || rate === undefined) return '—'
  return `${Math.round(rate * 100)}%`
}

const formatDate = (iso: string): string => {
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return iso
  return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}

onMounted(load)
</script>

<style scoped>
.admin-analytics {
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

.section-title {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-gray-900);
  margin: 0;
}

.range-tabs {
  display: inline-flex;
  background: var(--color-gray-100);
  border: 1px solid var(--color-gray-200);
  border-radius: var(--radius-base);
  padding: 2px;
  gap: 2px;
}

.range-tab {
  padding: var(--spacing-2) var(--spacing-3);
  background: transparent;
  border: none;
  border-radius: calc(var(--radius-base) - 2px);
  cursor: pointer;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-gray-600);
  transition: all var(--transition-base) ease;
}

.range-tab:hover {
  color: var(--color-gray-900);
}

.range-tab.active {
  background: white;
  color: var(--color-gray-900);
  box-shadow: var(--shadow-sm);
}

.range-tab:focus-visible {
  outline: 2px solid var(--color-primary-500, #3b82f6);
  outline-offset: 2px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--spacing-6);
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

.card {
  background: white;
  border: 1px solid var(--color-gray-200);
  border-radius: var(--radius-lg);
  padding: var(--spacing-6);
}

.card-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--spacing-3);
  margin-bottom: var(--spacing-4);
}

.card-title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--color-gray-900);
  margin: 0;
}

.card-meta {
  font-size: var(--font-size-sm);
  color: var(--color-gray-500);
}

.chart {
  width: 100%;
  height: auto;
  display: block;
  color: var(--color-primary);
}

.chart-fill {
  fill: var(--color-primary);
  fill-opacity: 0.12;
}

.chart-points circle {
  fill: var(--color-primary);
}

.chart-axis {
  stroke: var(--color-gray-200);
  stroke-width: 1;
}

.chart-axis-labels {
  display: flex;
  justify-content: space-between;
  font-size: var(--font-size-xs);
  color: var(--color-gray-500);
  margin-top: var(--spacing-2);
}

.two-col {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: var(--spacing-6);
}

.top-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3);
}

.top-list-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--spacing-3);
  padding: var(--spacing-2) 0;
  border-bottom: 1px solid var(--color-gray-100);
}

.top-list-item:last-child {
  border-bottom: none;
}

.top-list-text {
  min-width: 0;
}

.top-list-primary {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--color-gray-900);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.top-list-secondary {
  font-size: var(--font-size-xs);
  color: var(--color-gray-500);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.top-list-value {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--color-gray-700);
  flex-shrink: 0;
  font-variant-numeric: tabular-nums;
}

.empty-state {
  padding: var(--spacing-6);
  text-align: center;
  color: var(--color-gray-500);
  font-size: var(--font-size-sm);
}

.loading-state {
  padding: var(--spacing-8);
  text-align: center;
  color: var(--color-gray-500);
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
[data-theme='dark'] .card-title,
[data-theme='dark'] .top-list-primary {
  color: var(--text-primary, #f8fafc);
}

[data-theme='dark'] .stat-card,
[data-theme='dark'] .card {
  background: var(--bg-secondary, #1e293b);
  border-color: var(--border-primary, #334155);
}

[data-theme='dark'] .stat-value {
  color: var(--primary-400, #60a5fa);
}

[data-theme='dark'] .stat-label,
[data-theme='dark'] .card-meta,
[data-theme='dark'] .top-list-secondary,
[data-theme='dark'] .empty-state,
[data-theme='dark'] .loading-state {
  color: var(--text-tertiary, #94a3b8);
}

[data-theme='dark'] .top-list-value {
  color: var(--text-secondary, #cbd5e1);
}

[data-theme='dark'] .top-list-item {
  border-bottom-color: var(--border-primary, #334155);
}

[data-theme='dark'] .range-tabs {
  background: var(--bg-tertiary, #334155);
  border-color: var(--border-primary, #475569);
}

[data-theme='dark'] .range-tab {
  color: var(--text-secondary, #cbd5e1);
}

[data-theme='dark'] .range-tab.active {
  background: var(--bg-secondary, #1e293b);
  color: var(--text-primary, #f8fafc);
}

[data-theme='dark'] .chart-axis {
  stroke: var(--border-primary, #334155);
}

[data-theme='dark'] .chart {
  color: var(--primary-400, #60a5fa);
}

[data-theme='dark'] .chart-fill {
  fill: var(--primary-400, #60a5fa);
}

[data-theme='dark'] .chart-points circle {
  fill: var(--primary-400, #60a5fa);
}

[data-theme='dark'] .error-alert {
  background: #450a0a;
  border-color: #7f1d1d;
  color: #fecaca;
}

@media (max-width: 640px) {
  .stats-grid {
    grid-template-columns: 1fr 1fr;
  }
}
</style>
