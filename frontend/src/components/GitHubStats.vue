<template>
  <div ref="sectionRef" class="github-stats">
    <div v-if="loading" class="loading-spinner">
      <div class="spinner"></div>
      <p>Loading GitHub stats...</p>
    </div>

    <div v-else-if="error" class="error-message">
      <p>Failed to load GitHub stats</p>
      <button
        class="retry-button"
        :disabled="loading"
        :aria-busy="loading"
        @click="fetchGitHubStats"
      >
        {{ loading ? 'Retrying…' : 'Retry' }}
      </button>
    </div>

    <div v-else-if="stats" class="stats-container">
      <div v-if="!hasContent" class="empty-state">
        <p>No GitHub repositories found.</p>
      </div>

      <div v-if="featuredRepos.length" class="featured-repos mt-8">
        <div class="repos-grid grid gap-6 sm:grid-cols-2 xl:grid-cols-3">
          <RepoCard v-for="repo in featuredRepos" :key="repo.name" :repo="repo" />
        </div>
      </div>

      <div
        v-if="topLanguages.length"
        class="languages-section mt-8 rounded-2xl border border-slate-200 bg-white p-6 dark:border-slate-800 dark:bg-slate-900/50"
      >
        <h3>Top Languages</h3>
        <div class="language-bars">
          <LanguageBar
            v-for="lang in topLanguages"
            :key="lang.name"
            :name="lang.name"
            :percentage="lang.percentage"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onUnmounted } from 'vue'
import { useIntersectionObserver } from '@vueuse/core'
import axios from 'axios'
import { apiLogger } from '../utils/logger'
import { config } from '@/config'
import RepoCard, { type Repository } from './RepoCard.vue'
import LanguageBar from './LanguageBar.vue'

interface Language {
  name: string
  percentage: number
}

interface GitHubStatsData {
  public_repos: number
  total_stars: number
  followers: number
  total_forks: number
  top_languages?: Language[]
  featured_repos?: Repository[]
}

interface Props {
  username?: string
}

const props = withDefaults(defineProps<Props>(), {
  username: config.github.username
})

const emit = defineEmits<{ loaded: [] }>()

const stats = ref<GitHubStatsData | null>(null)
const loading = ref<boolean>(true)
const error = ref<boolean>(false)

let isMounted = false
let abortController: AbortController | null = null

const featuredRepos = computed<Repository[]>(() => stats.value?.featured_repos ?? [])
const topLanguages = computed<Language[]>(() => stats.value?.top_languages ?? [])
const hasContent = computed<boolean>(
  () => featuredRepos.value.length > 0 || topLanguages.value.length > 0
)

const fetchGitHubStats = async (): Promise<void> => {
  if (abortController) {
    abortController.abort()
  }
  abortController = new AbortController()

  try {
    loading.value = true
    error.value = false

    const response = await axios.get<GitHubStatsData>(
      `${config.apiUrl}/api/v1/github/stats/${props.username}`,
      { signal: abortController.signal }
    )
    stats.value = response.data
    // Let the parent re-scan entrance animations now the repo cards exist
    // in the DOM (HomeView registers .project-card before this fetch lands).
    await nextTick()
    emit('loaded')
  } catch (err) {
    // Aborted requests on unmount don't count as errors
    if (axios.isCancel(err)) {
      return
    }
    apiLogger.error('Error fetching GitHub stats:', err)
    if (isMounted) {
      error.value = true
    }
  } finally {
    if (isMounted) {
      loading.value = false
    }
  }
}

const sectionRef = ref<HTMLElement | null>(null)

const { stop } = useIntersectionObserver(
  sectionRef,
  ([entry]) => {
    if (entry.isIntersecting) {
      isMounted = true
      fetchGitHubStats()
      stop()
    }
  },
  { rootMargin: '200px' }
)

onUnmounted(() => {
  isMounted = false
  if (abortController) {
    abortController.abort()
    abortController = null
  }
})
</script>

<style scoped>
.github-stats {
  margin: 2rem 0;
}

.loading-spinner {
  text-align: center;
  padding: 2rem;
  color: var(--text-muted);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--color-border);
  border-top: 3px solid var(--link-color);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

.error-message {
  text-align: center;
  color: var(--color-error, #ef4444);
  padding: 2rem;
  background: rgba(239, 68, 68, 0.1);
  border-radius: 12px;
  border: 1px solid rgba(239, 68, 68, 0.2);
}

.empty-state {
  text-align: center;
  padding: 3rem 2rem;
  color: var(--text-muted);
  background: rgba(100, 116, 139, 0.05);
  border-radius: 12px;
  border: 1px dashed var(--color-border);
}

.retry-button {
  margin-top: 1rem;
  padding: 0.625rem 1.5rem;
  background: var(--primary-600, #2563eb);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 600;
  transition: all 0.2s ease;
}

.retry-button:hover {
  background: var(--primary-700, #1d4ed8);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
}

.retry-button:disabled {
  background: var(--primary-400, #60a5fa);
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
  opacity: 0.7;
}

.stats-container {
  animation: fadeIn 0.5s ease-in;
}

.languages-section h3 {
  margin: 0 0 1.25rem 0;
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--text-primary);
}

.featured-repos h3 {
  margin: 0 0 1.25rem 0;
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--text-primary);
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

/* Dark mode overrides. Most surfaces swap via semantic tokens or the
   shared Tailwind card recipe; only the brighter error tint and the
   higher-opacity empty-state border need explicit dark treatment. */

[data-theme='dark'] .error-message {
  color: var(--color-error);
  background: rgba(252, 165, 165, 0.15);
  border-color: rgba(252, 165, 165, 0.25);
}

[data-theme='dark'] .empty-state {
  color: var(--text-tertiary);
  background: rgba(100, 116, 139, 0.1);
  border-color: var(--border-primary);
}
</style>
