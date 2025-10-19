<template>
  <div class="github-stats">
    <div v-if="loading" class="loading-spinner">
      <div class="spinner"></div>
      <p>Loading GitHub stats...</p>
    </div>

    <div v-else-if="error" class="error-message">
      <p>Failed to load GitHub stats</p>
    </div>

    <div v-else-if="stats" class="stats-container">
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-value">{{ stats.public_repos }}</div>
          <div class="stat-label">Repositories</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ stats.total_stars }}</div>
          <div class="stat-label">Stars</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ stats.followers }}</div>
          <div class="stat-label">Followers</div>
        </div>
        <div class="stat-card">
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
              <span v-if="repo.language" class="repo-language">{{ repo.language }}</span>
              <span class="repo-stars">[*] {{ repo.stars }}</span>
              <span class="repo-forks">[Y] {{ repo.forks }}</span>
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
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  padding: 1.5rem;
  text-align: center;
  transition: transform 0.3s ease, background 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
  background: rgba(255, 255, 255, 0.08);
}

.stat-value {
  font-size: 2rem;
  font-weight: bold;
  color: var(--primary-color, #007bff);
}

.stat-label {
  font-size: 0.9rem;
  color: #888;
  margin-top: 0.5rem;
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
  gap: 1rem;
  font-size: 0.85rem;
  color: #888;
}

.repo-language {
  font-weight: 500;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

/* Dark theme adjustments */
[data-theme="dark"] .stat-card {
  background: rgba(255, 255, 255, 0.03);
  border-color: rgba(255, 255, 255, 0.05);
}

[data-theme="dark"] .repo-card {
  background: rgba(255, 255, 255, 0.03);
  border-color: rgba(255, 255, 255, 0.05);
}

[data-theme="dark"] .progress-bar {
  background: rgba(255, 255, 255, 0.1);
}
</style>