<template>
  <div class="github-stats">
    <div v-if="loading" class="loading-spinner">
      <div class="spinner"></div>
      <p>Loading GitHub stats...</p>
    </div>

    <div v-else-if="error" class="error-message">
      <p>Failed to load GitHub stats</p>
      <button @click="fetchGitHubStats" class="retry-button">Retry</button>
    </div>

    <div v-else-if="stats" class="stats-container">
      <div class="stats-grid">
        <div class="stat-card" :style="`animation-delay: ${0 * 100}ms`">
          <div class="stat-icon">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"></path>
              <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"></path>
            </svg>
          </div>
          <div class="stat-value">{{ stats.public_repos }}</div>
          <div class="stat-label">Repositories</div>
        </div>
        <div class="stat-card" :style="`animation-delay: ${1 * 100}ms`">
          <div class="stat-icon">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
            </svg>
          </div>
          <div class="stat-value">{{ stats.total_stars }}</div>
          <div class="stat-label">Stars</div>
        </div>
        <div class="stat-card" :style="`animation-delay: ${2 * 100}ms`">
          <div class="stat-icon">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
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
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
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
          <a v-for="repo in stats.recent_repos"
             :key="repo.name"
             :href="repo.html_url"
             target="_blank"
             rel="noopener noreferrer"
             class="repo-card">
            <h4>{{ repo.name }}</h4>
            <p v-if="repo.description">{{ repo.description }}</p>
            <div class="repo-meta">
              <span v-if="repo.language" class="repo-language">
                <span class="language-dot"></span>
                {{ repo.language }}
              </span>
              <span class="repo-stars">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" width="12" height="12">
                  <polygon points="8 1 10.5 6 16 6.5 12 10.5 13 16 8 13 3 16 4 10.5 0 6.5 5.5 6 8 1"></polygon>
                </svg>
                {{ repo.stars }}
              </span>
              <span class="repo-forks">
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 16 16" fill="currentColor" width="12" height="12">
                  <path d="M5 3.25a.75.75 0 1 1-1.5 0 .75.75 0 0 1 1.5 0zm0 2.122a2.25 2.25 0 1 0-1.5 0v.878A2.25 2.25 0 0 0 5.75 8.5h1.5v2.128a2.251 2.251 0 1 0 1.5 0V8.5h1.5a2.25 2.25 0 0 0 2.25-2.25v-.878a2.25 2.25 0 1 0-1.5 0v.878a.75.75 0 0 1-.75.75h-4.5A.75.75 0 0 1 5 6.25v-.878zm3.75 7.378a.75.75 0 1 1-1.5 0 .75.75 0 0 1 1.5 0zm3-8.75a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5z"></path>
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

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const props = defineProps({
  username: {
    type: String,
    default: 'Dashtid'
  }
})

const stats = ref(null)
const loading = ref(true)
const error = ref(false)

const fetchGitHubStats = async () => {
  try {
    loading.value = true
    error.value = false

    const response = await axios.get(`http://localhost:8001/api/v1/github/stats/${props.username}`)
    stats.value = response.data
  } catch (err) {
    console.error('Error fetching GitHub stats:', err)
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
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid var(--primary-color, #007bff);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-message {
  text-align: center;
  color: #dc3545;
  padding: 2rem;
}

.retry-button {
  margin-top: 1rem;
  padding: 0.5rem 1.5rem;
  background: var(--color-primary, #2563eb);
  color: white;
  border: none;
  border-radius: 0.5rem;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.3s ease;
}

.retry-button:hover {
  background: var(--color-primary-dark, #1d4ed8);
  transform: translateY(-2px);
}

.stats-container {
  animation: fadeIn 0.5s ease-in;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: var(--card-bg, #ffffff);
  border: 2px solid var(--color-border, #e2e8f0);
  border-radius: 12px;
  padding: 1.5rem;
  text-align: center;
  transition: all 0.3s ease;
  animation: slideUp 0.5s ease-out forwards;
  opacity: 0;
  box-shadow: var(--shadow-sm, 0 1px 2px rgba(0, 0, 0, 0.05));
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
  transform: translateY(-5px);
  border-color: var(--color-primary, #2563eb);
  box-shadow: var(--card-hover-shadow, 0 10px 15px rgba(0, 0, 0, 0.1));
}

.stat-icon {
  width: 40px;
  height: 40px;
  margin: 0 auto 1rem;
  color: var(--color-primary, #2563eb);
  transition: all 0.3s ease;
}

.stat-card:hover .stat-icon {
  transform: scale(1.1);
  color: var(--color-primary-dark, #1d4ed8);
}

.stat-icon svg {
  width: 100%;
  height: 100%;
}

.stat-value {
  font-size: 2rem;
  font-weight: bold;
  color: var(--text-primary, #0f172a);
  margin-bottom: 0.5rem;
}

.stat-label {
  font-size: 0.9rem;
  color: var(--text-secondary, #64748b);
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.languages-section {
  margin: 2rem 0;
}

.languages-section h3 {
  margin-bottom: 1rem;
  color: var(--text-color, #333);
}

.language-bars {
  space-y: 0.75rem;
}

.language-bar {
  margin-bottom: 1rem;
}

.language-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.25rem;
  font-size: 0.9rem;
}

.language-name {
  font-weight: 500;
}

.language-percentage {
  color: #666;
}

.progress-bar {
  height: 8px;
  background: rgba(0, 0, 0, 0.1);
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #007bff, #00a8ff);
  border-radius: 4px;
  transition: width 0.5s ease;
}

.recent-repos {
  margin-top: 2rem;
}

.recent-repos h3 {
  margin-bottom: 1rem;
}

.repos-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1rem;
}

.repo-card {
  display: block;
  padding: 1rem;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  text-decoration: none;
  color: inherit;
  transition: transform 0.3s ease, background 0.3s ease;
}

.repo-card:hover {
  transform: translateY(-2px);
  background: rgba(255, 255, 255, 0.08);
}

.repo-card h4 {
  margin: 0 0 0.5rem 0;
  color: var(--primary-color, #007bff);
}

.repo-card p {
  margin: 0 0 0.75rem 0;
  font-size: 0.9rem;
  color: #666;
}

.repo-meta {
  display: flex;
  align-items: center;
  gap: 1rem;
  font-size: 0.85rem;
  color: var(--text-tertiary, #94a3b8);
}

.repo-meta > span {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.repo-language {
  font-weight: 500;
}

.language-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--color-primary, #2563eb);
}

.repo-stars svg,
.repo-forks svg {
  opacity: 0.7;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* Dark theme adjustments */
:global(html[data-theme="dark"]) .stat-card {
  background: var(--card-bg, #1e293b);
  border-color: var(--color-border-dark, #334155);
}

:global(html[data-theme="dark"]) .stat-card:hover {
  border-color: var(--color-teal, #14b8a6);
}

:global(html[data-theme="dark"]) .stat-icon {
  color: var(--color-teal, #14b8a6);
}

:global(html[data-theme="dark"]) .stat-card:hover .stat-icon {
  color: var(--color-teal-light, #5eead4);
}

:global(html[data-theme="dark"]) .repo-card {
  background: var(--card-bg, #1e293b);
  border-color: var(--color-border-dark, #334155);
}

:global(html[data-theme="dark"]) .repo-card:hover {
  border-color: var(--color-teal, #14b8a6);
}

:global(html[data-theme="dark"]) .progress-bar {
  background: rgba(255, 255, 255, 0.1);
}

:global(html[data-theme="dark"]) .progress-fill {
  background: linear-gradient(90deg, var(--color-teal, #14b8a6), var(--color-teal-light, #5eead4));
}

/* Responsive improvements */
@media (max-width: 768px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .stat-card {
    padding: 1rem;
  }

  .stat-icon {
    width: 32px;
    height: 32px;
  }

  .stat-value {
    font-size: 1.5rem;
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
  }

  .stat-card:hover,
  .repo-card:hover {
    transform: none;
  }
}
</style>