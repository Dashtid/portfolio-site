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
      <div class="stats-grid">
        <div class="stat-card" :style="`animation-delay: ${0 * 100}ms`">
          <div class="stat-icon">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"></path>
              <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"></path>
            </svg>
          </div>
          <div class="stat-value">{{ stats.public_repos }}</div>
          <div class="stat-label">Repositories</div>
        </div>
        <div class="stat-card" :style="`animation-delay: ${1 * 100}ms`">
          <div class="stat-icon">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <polygon
                points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"
              ></polygon>
            </svg>
          </div>
          <div class="stat-value">{{ stats.total_stars }}</div>
          <div class="stat-label">Stars</div>
        </div>
        <div class="stat-card" :style="`animation-delay: ${2 * 100}ms`">
          <div class="stat-icon">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
              <circle cx="9" cy="7" r="4"></circle>
              <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
              <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
            </svg>
          </div>
          <div class="stat-value">{{ stats.followers }}</div>
          <div class="stat-label">Followers</div>
        </div>
        <div class="stat-card" :style="`animation-delay: ${3 * 100}ms`">
          <div class="stat-icon">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2"
            >
              <line x1="22" y1="2" x2="11" y2="13"></line>
              <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
            </svg>
          </div>
          <div class="stat-value">{{ stats.total_forks }}</div>
          <div class="stat-label">Forks</div>
        </div>
      </div>

      <div v-if="stats.top_languages && stats.top_languages.length" class="languages-section">
        <h3>Top Languages</h3>
        <div class="language-bars">
          <div v-for="lang in stats.top_languages" :key="lang.name" class="language-bar">
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

      <div v-if="stats.recent_repos && stats.recent_repos.length" class="recent-repos">
        <h3>Recent Projects</h3>
        <div class="repos-grid">
          <a
            v-for="repo in stats.recent_repos"
            :key="repo.name"
            :href="repo.html_url"
            target="_blank"
            rel="noopener noreferrer"
            class="repo-card"
          >
            <h4>{{ repo.name }}</h4>
            <p v-if="repo.description">{{ repo.description }}</p>
            <div class="repo-meta">
              <span v-if="repo.language" class="repo-language">
                <span class="language-dot"></span>
                {{ repo.language }}
              </span>
              <span class="repo-stars">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 16 16"
                  fill="currentColor"
                  width="12"
                  height="12"
                >
                  <polygon
                    points="8 1 10.5 6 16 6.5 12 10.5 13 16 8 13 3 16 4 10.5 0 6.5 5.5 6 8 1"
                  ></polygon>
                </svg>
                {{ repo.stars }}
              </span>
              <span class="repo-forks">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 16 16"
                  fill="currentColor"
                  width="12"
                  height="12"
                >
                  <path
                    d="M5 3.25a.75.75 0 1 1-1.5 0 .75.75 0 0 1 1.5 0zm0 2.122a2.25 2.25 0 1 0-1.5 0v.878A2.25 2.25 0 0 0 5.75 8.5h1.5v2.128a2.251 2.251 0 1 0 1.5 0V8.5h1.5a2.25 2.25 0 0 0 2.25-2.25v-.878a2.25 2.25 0 1 0-1.5 0v.878a.75.75 0 0 1-.75.75h-4.5A.75.75 0 0 1 5 6.25v-.878zm3.75 7.378a.75.75 0 1 1-1.5 0 .75.75 0 0 1 1.5 0zm3-8.75a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5z"
                  ></path>
                </svg>
                {{ repo.forks }}
              </span>
            </div>
          </a>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
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
  recent_repos?: Repository[]
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

const fetchGitHubStats = async (): Promise<void> => {
  try {
    loading.value = true
    error.value = false

    const response = await axios.get<GitHubStatsData>(
      `${API_URL}/api/v1/github/stats/${props.username}`
    )
    stats.value = response.data
  } catch (err) {
    apiLogger.error('Error fetching GitHub stats:', err)
    error.value = true
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchGitHubStats()
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
  color: #ef4444;
  padding: 2rem;
  background: rgba(239, 68, 68, 0.1);
  border-radius: 12px;
  border: 1px solid rgba(239, 68, 68, 0.2);
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

.recent-repos {
  margin-top: 2rem;
}

.recent-repos h3 {
  margin: 0 0 1.25rem 0;
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--slate-800, #1e293b);
}

.repos-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1rem;
}

.repo-card {
  display: block;
  padding: 1.25rem;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(12px);
  border: 1px solid var(--slate-200, #e2e8f0);
  border-radius: 12px;
  text-decoration: none;
  color: inherit;
  transition: all 0.3s ease;
}

.repo-card:hover {
  transform: translateY(-3px);
  border-color: var(--primary-400, #60a5fa);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
}

.repo-card h4 {
  margin: 0 0 0.5rem 0;
  font-size: 1rem;
  font-weight: 700;
  color: var(--primary-600, #2563eb);
}

.repo-card p {
  margin: 0 0 0.75rem 0;
  font-size: 0.875rem;
  color: var(--slate-600, #475569);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.repo-meta {
  display: flex;
  align-items: center;
  gap: 1rem;
  font-size: 0.8rem;
  color: var(--slate-500, #64748b);
}

.repo-meta > span {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.repo-language {
  font-weight: 600;
}

.language-dot {
  display: inline-block;
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--primary-500, #3b82f6);
}

.repo-stars svg,
.repo-forks svg {
  opacity: 0.7;
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
  background: rgba(30, 41, 59, 0.6);
  border-color: rgba(255, 255, 255, 0.1);
}

[data-theme='dark'] .stat-card:hover {
  border-color: rgba(96, 165, 250, 0.4);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.3);
}

[data-theme='dark'] .stat-icon {
  background: linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%);
}

[data-theme='dark'] .stat-value {
  color: #f1f5f9;
}

[data-theme='dark'] .stat-label {
  color: #94a3b8;
}

[data-theme='dark'] .languages-section {
  background: rgba(30, 41, 59, 0.6);
  border-color: rgba(255, 255, 255, 0.1);
}

[data-theme='dark'] .languages-section h3,
[data-theme='dark'] .recent-repos h3 {
  color: #f1f5f9;
}

[data-theme='dark'] .language-name {
  color: #e2e8f0;
}

[data-theme='dark'] .language-percentage {
  color: #94a3b8;
}

[data-theme='dark'] .progress-bar {
  background: rgba(255, 255, 255, 0.1);
}

[data-theme='dark'] .progress-fill {
  background: linear-gradient(90deg, #60a5fa, #3b82f6);
}

[data-theme='dark'] .repo-card {
  background: rgba(30, 41, 59, 0.6);
  border-color: rgba(255, 255, 255, 0.1);
}

[data-theme='dark'] .repo-card:hover {
  border-color: rgba(96, 165, 250, 0.4);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3);
}

[data-theme='dark'] .repo-card h4 {
  color: #60a5fa;
}

[data-theme='dark'] .repo-card p {
  color: #94a3b8;
}

[data-theme='dark'] .repo-meta {
  color: #64748b;
}

[data-theme='dark'] .spinner {
  border-color: rgba(255, 255, 255, 0.1);
  border-top-color: #60a5fa;
}

[data-theme='dark'] .loading-spinner {
  color: #94a3b8;
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
  .repo-card,
  .progress-fill {
    transition: none;
    animation: none;
    opacity: 1;
  }

  .stat-card:hover,
  .repo-card:hover {
    transform: none;
  }
}
</style>
