<template>
  <a
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
</template>

<script setup lang="ts">
import { getLanguageColor } from '@/utils/githubLanguageColors'

export interface Repository {
  name: string
  description: string | null
  html_url: string
  language: string | null
  stars: number
  forks: number
}

interface Props {
  repo: Repository
}

defineProps<Props>()
</script>

<style scoped>
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

.project-content {
  padding: var(--space-6, 1.5rem);
}

.project-title {
  font-size: var(--font-size-xl, 1.25rem);
  font-weight: var(--font-weight-semibold, 600);
  color: var(--primary-600, #2563eb);
  margin: 0 0 var(--space-3, 0.75rem) 0;
}

.project-description {
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

[data-theme='dark'] .repo-card-enhanced {
  background: var(--card-bg);
  border-color: var(--border-primary);
}

[data-theme='dark'] .repo-card-enhanced:hover {
  border-color: var(--primary-400);
  box-shadow: var(--card-hover-shadow);
}

[data-theme='dark'] .project-title {
  color: var(--link-color);
}

[data-theme='dark'] .project-description {
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

@media (prefers-reduced-motion: reduce) {
  .repo-card-enhanced {
    transition: none;
  }

  .repo-card-enhanced:hover {
    transform: none;
  }
}
</style>
