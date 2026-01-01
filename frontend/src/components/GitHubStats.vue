<template>
  <div class="github-stats">
    <div v-if="loading" class="loading-spinner">
      <div class="spinner"></div>
      <p>Loading GitHub stats...</p>
    </div>

    <div v-else-if="error" class="error-message">
      <p>Failed to load GitHub stats</p>
      <button class="retry-button" @click="fetchGitHubStats">Retry</button>
    </div>

    <div v-else-if="stats" class="stats-container">
      <!-- Empty state when no repos found -->
      <div v-if="!hasContent" class="empty-state">
        <p>No GitHub repositories found.</p>
      </div>

      <div v-if="featuredRepos.length" class="featured-repos">
        <div class="repos-grid">
          <a
            v-for="repo in featuredRepos"
            :key="repo.name"
            :href="repo.html_url"
            target="_blank"
            rel="noopener noreferrer"
            class="project-card repo-card-enhanced"
            :aria-label="`${repo.name} repository on GitHub (opens in new tab)`"
          >
            <div class="project-content">
              <h3 class="project-title">{{ repo.name }}</h3>
              <p v-if="repo.description" class="project-description">
                {{ repo.description }}
              </p>

              <div class="repo-meta-enhanced">
                <span v-if="repo.language" class="repo-language">
                  <span
                    class="language-dot"
                    :style="{ background: getLanguageColor(repo.language) }"
                  ></span>
                  {{ repo.language }}
                </span>
                <span class="repo-stats">
                  <span class="repo-stat">
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 16 16"
                      fill="currentColor"
                      aria-hidden="true"
                    >
                      <polygon
                        points="8 1 10.5 6 16 6.5 12 10.5 13 16 8 13 3 16 4 10.5 0 6.5 5.5 6 8 1"
                      ></polygon>
                    </svg>
                    {{ repo.stars }}
                  </span>
                  <span class="repo-stat">
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 16 16"
                      fill="currentColor"
                      aria-hidden="true"
                    >
                      <path
                        d="M5 3.25a.75.75 0 1 1-1.5 0 .75.75 0 0 1 1.5 0zm0 2.122a2.25 2.25 0 1 0-1.5 0v.878A2.25 2.25 0 0 0 5.75 8.5h1.5v2.128a2.251 2.251 0 1 0 1.5 0V8.5h1.5a2.25 2.25 0 0 0 2.25-2.25v-.878a2.25 2.25 0 1 0-1.5 0v.878a.75.75 0 0 1-.75.75h-4.5A.75.75 0 0 1 5 6.25v-.878zm3.75 7.378a.75.75 0 1 1-1.5 0 .75.75 0 0 1 1.5 0zm3-8.75a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5z"
                      ></path>
                    </svg>
                    {{ repo.forks }}
                  </span>
                </span>
              </div>

              <div class="project-links">
                <span class="project-link">View on GitHub</span>
              </div>
            </div>
          </a>
        </div>
      </div>

      <div v-if="topLanguages.length" class="languages-section">
        <h3>Top Languages</h3>
        <div class="language-bars">
          <div v-for="lang in topLanguages" :key="lang.name" class="language-bar">
            <div class="language-info">
              <span class="language-name">{{ lang.name }}</span>
              <span class="language-percentage">{{ lang.percentage }}%</span>
            </div>
            <div class="progress-bar">
              <div class="progress-fill" :style="`width: ${lang.percentage}%`"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import { apiLogger } from '../utils/logger'

interface Language {
  name: string
  percentage: number
}

interface Repository {
  name: string
  description: string | null
  html_url: string
  language: string | null
  stars: number
  forks: number
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

// Get API URL from environment variables
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const props = withDefaults(defineProps<Props>(), {
  username: 'Dashtid'
})

const stats = ref<GitHubStatsData | null>(null)
const loading = ref<boolean>(true)
const error = ref<boolean>(false)

// Track mounted state to prevent updates after unmount
let isMounted = false

// AbortController for request cancellation on unmount
let abortController: AbortController | null = null

// Computed properties with null safety for API data
const featuredRepos = computed<Repository[]>(() => {
  return stats.value?.featured_repos ?? []
})

const topLanguages = computed<Language[]>(() => {
  return stats.value?.top_languages ?? []
})

const hasContent = computed<boolean>(() => {
  return featuredRepos.value.length > 0 || topLanguages.value.length > 0
})

// GitHub language colors (from linguist)
const languageColors: Record<string, string> = {
  TypeScript: '#3178c6',
  JavaScript: '#f1e05a',
  Python: '#3572A5',
  Vue: '#41b883',
  HTML: '#e34c26',
  CSS: '#563d7c',
  SCSS: '#c6538c',
  Shell: '#89e051',
  Go: '#00ADD8',
  Rust: '#dea584',
  Java: '#b07219',
  'C++': '#f34b7d',
  C: '#555555',
  'C#': '#239120',
  Ruby: '#701516',
  PHP: '#4F5D95',
  Swift: '#F05138',
  Kotlin: '#A97BFF',
  Dart: '#00B4AB'
}

const getLanguageColor = (lang: string): string => {
  return languageColors[lang] || '#3b82f6'
}

const fetchGitHubStats = async (): Promise<void> => {
  // Cancel any pending request
  if (abortController) {
    abortController.abort()
  }
  abortController = new AbortController()

  try {
    loading.value = true
    error.value = false

    const response = await axios.get<GitHubStatsData>(
      `${API_URL}/api/v1/github/stats/${props.username}`,
      { signal: abortController.signal }
    )
    stats.value = response.data
  } catch (err) {
    // Don't set error state if request was intentionally aborted (on unmount)
    if (axios.isCancel(err)) {
      return
    }
    apiLogger.error('Error fetching GitHub stats:', err)
    // Only update error state if component is still mounted
    if (isMounted) {
      error.value = true
    }
  } finally {
    // Only update loading state if component is still mounted
    if (isMounted) {
      loading.value = false
    }
  }
}

onMounted(() => {
  isMounted = true
  fetchGitHubStats()
})

onUnmounted(() => {
  isMounted = false
  // Cancel any pending request on unmount
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
  color: var(--slate-500, #64748b);
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--slate-200, #e2e8f0);
  border-top: 3px solid var(--primary-600, #2563eb);
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
  color: var(--slate-500, #64748b);
  background: rgba(100, 116, 139, 0.05);
  border-radius: 12px;
  border: 1px dashed var(--slate-300, #cbd5e1);
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

.stats-container {
  animation: fadeIn 0.5s ease-in;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid var(--slate-200, #e2e8f0);
  border-radius: 16px;
  padding: 1.5rem;
  text-align: center;
  transition: all 0.3s ease;
  animation: slideUp 0.5s ease-out forwards;
  opacity: 0;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.stat-card:hover {
  transform: translateY(-4px);
  border-color: var(--primary-400, #60a5fa);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.1);
}

.stat-icon {
  width: 44px;
  height: 44px;
  margin: 0 auto 0.75rem;
  padding: 10px;
  background: linear-gradient(
    135deg,
    var(--primary-500, #3b82f6) 0%,
    var(--primary-600, #2563eb) 100%
  );
  border-radius: 12px;
  color: white;
  transition: all 0.3s ease;
}

.stat-card:hover .stat-icon {
  transform: scale(1.1);
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.4);
}

.stat-icon svg {
  width: 100%;
  height: 100%;
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  color: var(--slate-800, #1e293b);
  margin-bottom: 0.25rem;
  line-height: 1.2;
}

.stat-label {
  font-size: 0.8rem;
  color: var(--slate-500, #64748b);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.languages-section {
  margin: 2rem 0;
  padding: 1.5rem;
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(12px);
  border-radius: 16px;
  border: 1px solid var(--slate-200, #e2e8f0);
}

.languages-section h3 {
  margin: 0 0 1.25rem 0;
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--slate-800, #1e293b);
}

.language-bar {
  margin-bottom: 1rem;
}

.language-bar:last-child {
  margin-bottom: 0;
}

.language-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.375rem;
  font-size: 0.875rem;
}

.language-name {
  font-weight: 600;
  color: var(--slate-700, #334155);
}

.language-percentage {
  color: var(--slate-500, #64748b);
  font-weight: 500;
}

.progress-bar {
  height: 8px;
  background: var(--slate-200, #e2e8f0);
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--primary-500, #3b82f6), var(--primary-600, #2563eb));
  border-radius: 4px;
  transition: width 0.8s ease;
}

.featured-repos {
  margin-top: 2rem;
}

.featured-repos h3 {
  margin: 0 0 1.25rem 0;
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--slate-800, #1e293b);
}

.repos-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 2rem;
}

/* Enhanced repo card - matches project-card shape */
.repo-card-enhanced {
  display: block;
  background: var(--bg-secondary, #ffffff);
  border: 1px solid var(--border-primary, #e2e8f0);
  border-radius: var(--radius-lg, 12px);
  overflow: hidden;
  box-shadow: var(--shadow-md, 0 4px 6px -1px rgba(0, 0, 0, 0.1));
  transition: all 0.3s ease;
  text-decoration: none;
  color: inherit;
}

.repo-card-enhanced:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-xl, 0 20px 25px -5px rgba(0, 0, 0, 0.1));
  border-color: var(--primary-400, #60a5fa);
}

.repo-card-enhanced .project-content {
  padding: var(--space-6, 1.5rem);
}

.repo-card-enhanced .project-title {
  font-size: var(--font-size-xl, 1.25rem);
  font-weight: var(--font-weight-semibold, 600);
  color: var(--primary-600, #2563eb);
  margin: 0 0 var(--space-3, 0.75rem) 0;
}

.repo-card-enhanced .project-description {
  color: var(--text-secondary, #475569);
  line-height: 1.6;
  margin: 0 0 var(--space-4, 1rem) 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  font-size: 0.9375rem;
}

.repo-meta-enhanced {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-4, 1rem);
  font-size: 0.875rem;
  color: var(--text-tertiary, #64748b);
}

.repo-language {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  font-weight: 600;
}

.language-dot {
  display: inline-block;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  flex-shrink: 0;
}

.repo-stats {
  display: flex;
  gap: 1rem;
}

.repo-stat {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.repo-stat svg {
  width: 14px;
  height: 14px;
  opacity: 0.7;
}

.project-links {
  display: flex;
  gap: var(--space-4, 1rem);
}

.project-link {
  color: var(--primary-600, #2563eb);
  font-weight: var(--font-weight-medium, 500);
  font-size: 0.875rem;
  transition: color 0.2s ease;
}

.repo-card-enhanced:hover .project-link {
  color: var(--primary-700, #1d4ed8);
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

/* Dark theme adjustments */
[data-theme='dark'] .stat-card {
  background: var(--card-bg);
  border-color: var(--border-primary);
}

[data-theme='dark'] .stat-card:hover {
  border-color: var(--primary-400);
  box-shadow: var(--card-hover-shadow);
}

[data-theme='dark'] .stat-icon {
  background: linear-gradient(135deg, var(--primary-600) 0%, var(--primary-500) 100%);
}

[data-theme='dark'] .stat-value {
  color: var(--text-primary);
}

[data-theme='dark'] .stat-label {
  color: var(--text-tertiary);
}

[data-theme='dark'] .languages-section {
  background: var(--card-bg);
  border-color: var(--border-primary);
}

[data-theme='dark'] .languages-section h3,
[data-theme='dark'] .featured-repos h3 {
  color: var(--text-primary);
}

[data-theme='dark'] .language-name {
  color: var(--text-secondary);
}

[data-theme='dark'] .language-percentage {
  color: var(--text-tertiary);
}

[data-theme='dark'] .progress-bar {
  background: var(--bg-tertiary);
}

[data-theme='dark'] .progress-fill {
  background: linear-gradient(90deg, var(--primary-500), var(--primary-600));
}

[data-theme='dark'] .repo-card-enhanced {
  background: var(--card-bg);
  border-color: var(--border-primary);
}

[data-theme='dark'] .repo-card-enhanced:hover {
  border-color: var(--primary-400);
  box-shadow: var(--card-hover-shadow);
}

[data-theme='dark'] .repo-card-enhanced .project-title {
  color: var(--link-color);
}

[data-theme='dark'] .repo-card-enhanced .project-description {
  color: var(--text-secondary);
}

[data-theme='dark'] .repo-meta-enhanced {
  color: var(--text-tertiary);
}

[data-theme='dark'] .repo-language {
  color: var(--text-secondary);
}

[data-theme='dark'] .project-link {
  color: var(--link-color);
}

[data-theme='dark'] .repo-card-enhanced:hover .project-link {
  color: var(--primary-400);
}

[data-theme='dark'] .spinner {
  border-color: var(--border-primary);
  border-top-color: var(--link-color);
}

[data-theme='dark'] .loading-spinner {
  color: var(--text-tertiary);
}

[data-theme='dark'] .error-message {
  color: var(--color-error, #fca5a5);
  background: rgba(252, 165, 165, 0.15);
  border-color: rgba(252, 165, 165, 0.25);
}

[data-theme='dark'] .empty-state {
  color: var(--text-tertiary);
  background: rgba(100, 116, 139, 0.1);
  border-color: var(--border-primary);
}

/* Responsive improvements */
@media (max-width: 992px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .stat-card {
    padding: 1.25rem;
  }

  .stat-icon {
    width: 40px;
    height: 40px;
  }

  .stat-value {
    font-size: 1.75rem;
  }

  .repos-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 480px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
}

/* Reduced motion preference */
@media (prefers-reduced-motion: reduce) {
  .stat-card,
  .stat-icon,
  .repo-card-enhanced,
  .progress-fill {
    transition: none;
    animation: none;
    opacity: 1;
  }

  .stat-card:hover,
  .repo-card-enhanced:hover {
    transform: none;
  }
}
</style>
