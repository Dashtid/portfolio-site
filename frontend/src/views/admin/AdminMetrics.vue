<template>
  <div class="admin-metrics">
    <header class="page-header">
      <div>
        <h2 class="page-title">Performance Metrics</h2>
        <p class="page-subtitle">Live from the FastAPI backend's in-process counters.</p>
      </div>
      <div class="header-actions">
        <button class="btn-refresh" :disabled="loading" :aria-busy="loading" @click="load(false)">
          {{ loading ? 'Refreshing…' : 'Refresh' }}
        </button>
        <button
          class="btn-reset"
          :disabled="resetting"
          :aria-busy="resetting"
          @click="confirmReset"
        >
          {{ resetting ? 'Resetting…' : 'Reset Metrics' }}
        </button>
      </div>
    </header>

    <div v-if="loadError" class="error-alert" role="alert">
      <span>{{ loadError }}</span>
      <button class="retry-button" :disabled="loading" @click="load(false)">Retry</button>
    </div>

    <div v-if="initialLoad" class="loading-state" aria-live="polite">Loading metrics…</div>

    <template v-else-if="metrics">
      <section class="summary-grid" aria-label="Summary">
        <div class="summary-card">
          <div class="summary-value">{{ totalRequests.toLocaleString() }}</div>
          <div class="summary-label">Total requests</div>
        </div>
        <div class="summary-card">
          <div class="summary-value">{{ uniqueEndpoints.toLocaleString() }}</div>
          <div class="summary-label">Endpoints</div>
        </div>
        <div class="summary-card">
          <div class="summary-value">{{ errorCount.toLocaleString() }}</div>
          <div class="summary-label">Error responses (4xx + 5xx)</div>
        </div>
        <div class="summary-card">
          <div class="summary-value">
            {{ formatRate(errorRate) }}
          </div>
          <div class="summary-label">Error rate</div>
        </div>
      </section>

      <section class="card" aria-label="Status codes">
        <div class="card-header">
          <h3 class="card-title">HTTP status codes</h3>
        </div>
        <div v-if="!statusEntries.length" class="empty-state">
          No requests recorded since last reset.
        </div>
        <ul v-else class="status-grid">
          <li
            v-for="row in statusEntries"
            :key="row.code"
            class="status-pill"
            :class="statusClass(row.code)"
          >
            <span class="status-code">{{ row.code }}</span>
            <span class="status-count">{{ row.count.toLocaleString() }}</span>
          </li>
        </ul>
      </section>

      <section class="card" aria-label="Business counters">
        <div class="card-header">
          <h3 class="card-title">Business counters</h3>
          <span class="card-meta">
            Bumped via <code>metrics.incr("name")</code> in the backend.
          </span>
        </div>
        <div v-if="!counterEntries.length" class="empty-state">
          No counters recorded since last reset.
        </div>
        <table v-else class="counter-table">
          <thead>
            <tr>
              <th scope="col">Counter</th>
              <th scope="col" class="num-col">Count</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in counterEntries" :key="row.name">
              <td>
                <code>{{ row.name }}</code>
              </td>
              <td class="num-col">{{ row.value.toLocaleString() }}</td>
            </tr>
          </tbody>
        </table>
      </section>

      <section class="card" aria-label="Per-endpoint stats">
        <div class="card-header">
          <h3 class="card-title">Per-endpoint latency</h3>
          <span class="card-meta">Sorted by p99 desc. Keys are templated routes.</span>
        </div>
        <div v-if="!endpointEntries.length" class="empty-state">No endpoint stats yet.</div>
        <div v-else class="endpoint-table-wrap">
          <table class="endpoint-table">
            <thead>
              <tr>
                <th scope="col">Endpoint</th>
                <th scope="col" class="num-col">Count</th>
                <th scope="col" class="num-col">Errors</th>
                <th scope="col" class="num-col">Avg</th>
                <th scope="col" class="num-col">p50</th>
                <th scope="col" class="num-col">p95</th>
                <th scope="col" class="num-col">p99</th>
                <th scope="col" class="num-col">Max</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in endpointEntries" :key="row.endpoint">
                <td class="endpoint-cell">{{ row.endpoint }}</td>
                <td class="num-col">{{ row.stats.count.toLocaleString() }}</td>
                <td class="num-col" :class="{ 'has-errors': row.stats.errors > 0 }">
                  {{ row.stats.errors.toLocaleString() }}
                </td>
                <td class="num-col">{{ formatMs(row.stats.avg_response_time_ms) }}</td>
                <td class="num-col">{{ formatMs(row.stats.p50_response_time_ms) }}</td>
                <td class="num-col">{{ formatMs(row.stats.p95_response_time_ms) }}</td>
                <td class="num-col" :class="latencyClass(row.stats.p99_response_time_ms)">
                  {{ formatMs(row.stats.p99_response_time_ms) }}
                </td>
                <td class="num-col">{{ formatMs(row.stats.max_response_time_ms) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import apiClient from '../../api/client'
import { apiLogger } from '../../utils/logger'
import { useToast } from '@/composables/useToast'

// The /metrics payload mirrors backend/app/schemas/metrics.py::PerformanceMetrics.
// Status codes arrive keyed by numeric HTTP code; JSON forces them to string
// keys on the wire so we re-parse on display.
interface EndpointStats {
  count: number
  avg_response_time_ms: number
  min_response_time_ms: number
  max_response_time_ms: number
  p50_response_time_ms: number
  p95_response_time_ms: number
  p99_response_time_ms: number
  errors: number
}

interface MetricsResponse {
  total_requests: number
  endpoints: Record<string, EndpointStats>
  status_codes: Record<string, number>
  counters: Record<string, number>
  message?: string
}

const toast = useToast()

const metrics = ref<MetricsResponse | null>(null)
const loading = ref<boolean>(false)
const resetting = ref<boolean>(false)
const initialLoad = ref<boolean>(true)
const loadError = ref<string | null>(null)
let refreshTimer: ReturnType<typeof setInterval> | null = null

// 10s auto-refresh is a reasonable trade-off: live enough for on-call to
// notice a spike, slow enough that we don't hammer /metrics ourselves
// (and inflate the very counter we're watching).
const REFRESH_INTERVAL_MS = 10_000

const totalRequests = computed<number>(() => metrics.value?.total_requests ?? 0)

const statusEntries = computed(() =>
  Object.entries(metrics.value?.status_codes ?? {})
    .map(([code, count]) => ({ code: Number(code), count }))
    .sort((a, b) => a.code - b.code)
)

const counterEntries = computed(() =>
  Object.entries(metrics.value?.counters ?? {})
    .map(([name, value]) => ({ name, value }))
    .sort((a, b) => b.value - a.value)
)

const endpointEntries = computed(() =>
  Object.entries(metrics.value?.endpoints ?? {})
    .map(([endpoint, stats]) => ({ endpoint, stats }))
    .sort((a, b) => b.stats.p99_response_time_ms - a.stats.p99_response_time_ms)
)

const uniqueEndpoints = computed<number>(() => endpointEntries.value.length)
const errorCount = computed<number>(() =>
  statusEntries.value.filter(({ code }) => code >= 400).reduce((sum, row) => sum + row.count, 0)
)
const errorRate = computed<number | null>(() => {
  const total = totalRequests.value
  if (!total) return null
  return errorCount.value / total
})

const load = async (silent: boolean): Promise<void> => {
  if (!silent) loading.value = true
  loadError.value = null
  try {
    const response = await apiClient.get<MetricsResponse>('/api/v1/metrics/')
    if (response.data?.message) {
      // Backend returns MetricsDisabled when METRICS_ENABLED=false.
      loadError.value = response.data.message
      metrics.value = null
    } else {
      metrics.value = response.data
    }
  } catch (error) {
    apiLogger.error('Failed to load metrics:', error)
    loadError.value = 'Failed to load metrics.'
  } finally {
    if (!silent) loading.value = false
    initialLoad.value = false
  }
}

const confirmReset = async (): Promise<void> => {
  if (!confirm('Reset all performance metrics? This clears counts and percentile windows.')) return
  resetting.value = true
  try {
    await apiClient.post('/api/v1/metrics/reset')
    toast.success('Metrics reset')
    await load(false)
  } catch (error) {
    apiLogger.error('Failed to reset metrics:', error)
    toast.error('Failed to reset metrics')
  } finally {
    resetting.value = false
  }
}

const formatMs = (ms: number | null | undefined): string => {
  if (ms === null || ms === undefined) return '—'
  if (ms < 10) return `${ms.toFixed(2)} ms`
  if (ms < 1000) return `${Math.round(ms)} ms`
  return `${(ms / 1000).toFixed(2)} s`
}

const formatRate = (rate: number | null): string => {
  if (rate === null) return '—'
  return `${(rate * 100).toFixed(rate < 0.01 ? 2 : 1)}%`
}

const statusClass = (code: number): string => {
  if (code >= 500) return 'status-5xx'
  if (code >= 400) return 'status-4xx'
  if (code >= 300) return 'status-3xx'
  if (code >= 200) return 'status-2xx'
  return ''
}

const latencyClass = (ms: number): string => {
  if (ms >= 1000) return 'latency-slow'
  if (ms >= 500) return 'latency-warn'
  return ''
}

onMounted(async () => {
  await load(false)
  refreshTimer = setInterval(() => load(true), REFRESH_INTERVAL_MS)
})

onUnmounted(() => {
  if (refreshTimer !== null) {
    clearInterval(refreshTimer)
    refreshTimer = null
  }
})
</script>

<style scoped>
.admin-metrics {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-6);
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--spacing-4);
  flex-wrap: wrap;
}

.page-title {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-gray-900);
  margin: 0;
}

.page-subtitle {
  margin: 0;
  color: var(--color-gray-600);
  font-size: var(--font-size-sm);
}

.header-actions {
  display: flex;
  gap: var(--spacing-2);
}

.btn-refresh,
.btn-reset {
  padding: var(--spacing-2) var(--spacing-4);
  border-radius: var(--radius-base);
  font-weight: var(--font-weight-medium);
  font-size: var(--font-size-sm);
  cursor: pointer;
  border: 1px solid var(--color-gray-300);
  background: white;
  color: var(--color-gray-700);
  transition: all var(--transition-base) ease;
}

.btn-refresh:hover:not(:disabled),
.btn-reset:hover:not(:disabled) {
  background: var(--color-gray-100);
}

.btn-reset {
  border-color: #dc2626;
  color: #dc2626;
}

.btn-reset:hover:not(:disabled) {
  background: rgba(220, 38, 38, 0.08);
}

.btn-refresh:disabled,
.btn-reset:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--spacing-4);
}

.summary-card {
  background: white;
  padding: var(--spacing-5);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-gray-200);
  text-align: center;
}

.summary-value {
  font-size: var(--font-size-3xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-primary);
  margin-bottom: var(--spacing-1);
  font-variant-numeric: tabular-nums;
}

.summary-label {
  font-size: var(--font-size-xs);
  color: var(--color-gray-600);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.card {
  background: white;
  border: 1px solid var(--color-gray-200);
  border-radius: var(--radius-lg);
  padding: var(--spacing-5);
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

.empty-state {
  padding: var(--spacing-4);
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

.retry-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.status-grid {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: var(--spacing-2);
}

.status-pill {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-2) var(--spacing-3);
  background: var(--color-gray-50);
  border: 1px solid var(--color-gray-200);
  border-radius: var(--radius-base);
}

.status-code {
  font-weight: var(--font-weight-semibold);
  font-variant-numeric: tabular-nums;
}

.status-count {
  color: var(--color-gray-600);
  font-variant-numeric: tabular-nums;
}

.status-2xx {
  border-left: 3px solid #16a34a;
}

.status-3xx {
  border-left: 3px solid #2563eb;
}

.status-4xx {
  border-left: 3px solid #f59e0b;
}

.status-5xx {
  border-left: 3px solid #dc2626;
}

.counter-table,
.endpoint-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--font-size-sm);
}

.counter-table th,
.counter-table td,
.endpoint-table th,
.endpoint-table td {
  text-align: left;
  padding: var(--spacing-2) var(--spacing-3);
  border-bottom: 1px solid var(--color-gray-200);
}

.counter-table th,
.endpoint-table th {
  font-weight: var(--font-weight-semibold);
  color: var(--color-gray-700);
  text-transform: uppercase;
  letter-spacing: 0.04em;
  font-size: var(--font-size-xs);
}

.num-col {
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.has-errors {
  color: #dc2626;
  font-weight: var(--font-weight-medium);
}

.latency-slow {
  color: #dc2626;
  font-weight: var(--font-weight-semibold);
}

.latency-warn {
  color: #f59e0b;
}

.endpoint-cell {
  font-family: var(--font-mono, ui-monospace, SFMono-Regular, monospace);
  font-size: var(--font-size-xs);
  word-break: break-all;
}

.endpoint-table-wrap {
  overflow-x: auto;
}

[data-theme='dark'] .page-title {
  color: var(--text-primary, #f8fafc);
}

[data-theme='dark'] .page-subtitle,
[data-theme='dark'] .summary-label,
[data-theme='dark'] .empty-state,
[data-theme='dark'] .loading-state,
[data-theme='dark'] .card-meta {
  color: var(--text-tertiary, #94a3b8);
}

[data-theme='dark'] .summary-card,
[data-theme='dark'] .card {
  background: var(--bg-secondary, #1e293b);
  border-color: var(--border-primary, #334155);
}

[data-theme='dark'] .summary-value {
  color: var(--primary-400, #60a5fa);
}

[data-theme='dark'] .card-title {
  color: var(--text-primary, #f8fafc);
}

[data-theme='dark'] .btn-refresh,
[data-theme='dark'] .btn-reset {
  background: var(--bg-tertiary, #334155);
  color: var(--text-secondary, #cbd5e1);
  border-color: var(--border-primary, #475569);
}

[data-theme='dark'] .btn-refresh:hover:not(:disabled),
[data-theme='dark'] .btn-reset:hover:not(:disabled) {
  background: var(--bg-secondary, #1e293b);
}

[data-theme='dark'] .btn-reset {
  border-color: #f87171;
  color: #f87171;
}

[data-theme='dark'] .status-pill {
  background: var(--bg-tertiary, #334155);
  border-color: var(--border-primary, #475569);
}

[data-theme='dark'] .status-count {
  color: var(--text-tertiary, #94a3b8);
}

[data-theme='dark'] .counter-table th,
[data-theme='dark'] .endpoint-table th {
  color: var(--text-tertiary, #94a3b8);
}

[data-theme='dark'] .counter-table th,
[data-theme='dark'] .counter-table td,
[data-theme='dark'] .endpoint-table th,
[data-theme='dark'] .endpoint-table td {
  border-bottom-color: var(--border-primary, #334155);
}

[data-theme='dark'] .has-errors {
  color: #f87171;
}

[data-theme='dark'] .latency-slow {
  color: #f87171;
}

[data-theme='dark'] .latency-warn {
  color: #fbbf24;
}

[data-theme='dark'] .error-alert {
  background: #450a0a;
  border-color: #7f1d1d;
  color: #fecaca;
}
</style>
