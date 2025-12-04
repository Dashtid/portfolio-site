<template>
  <div class="project-card">
    <div class="project-header">
      <h3 class="project-title">{{ project.title }}</h3>
      <span v-if="project.featured" class="featured-badge">Featured</span>
    </div>

    <p class="project-description">{{ project.description }}</p>

    <div class="project-tech">
      <span v-for="(tech, index) in techStack" :key="index" class="tech-tag">
        {{ tech }}
      </span>
    </div>

    <div class="project-links">
      <a
        v-if="project.github_url"
        :href="project.github_url"
        target="_blank"
        rel="noopener noreferrer"
        class="project-link github-link"
      >
        <svg class="link-icon" viewBox="0 0 16 16" fill="currentColor">
          <path
            d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"
          />
        </svg>
        <span>View Code</span>
      </a>

      <a
        v-if="project.live_url"
        :href="project.live_url"
        target="_blank"
        rel="noopener noreferrer"
        class="project-link live-link"
      >
        <svg
          class="link-icon"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
        >
          <path d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
        </svg>
        <span>Live Demo</span>
      </a>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface ProjectData {
  title: string
  description: string
  featured?: boolean
  github_url?: string | null
  live_url?: string | null
  tech_stack?: string | string[] | null
}

interface Props {
  project: ProjectData
}

const props = defineProps<Props>()

// Parse tech stack from JSON or string
const techStack = computed<string[]>(() => {
  if (!props.project.tech_stack) return []

  if (typeof props.project.tech_stack === 'string') {
    try {
      return JSON.parse(props.project.tech_stack) as string[]
    } catch {
      return props.project.tech_stack.split(',').map((t: string) => t.trim())
    }
  }

  return Array.isArray(props.project.tech_stack) ? props.project.tech_stack : []
})
</script>

<style scoped>
.project-card {
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(226, 232, 240, 0.8);
  border-radius: 16px;
  padding: 1.5rem;
  transition: all 0.3s ease;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.project-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
  border-color: var(--primary-400, #60a5fa);
}

.project-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 1rem;
}

.project-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--slate-800, #1e293b);
  margin: 0;
  flex: 1;
  line-height: 1.3;
}

.featured-badge {
  background: linear-gradient(135deg, #2563eb 0%, #0891b2 100%);
  color: white;
  font-size: 0.7rem;
  font-weight: 600;
  padding: 0.25rem 0.625rem;
  border-radius: 20px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.3);
}

.project-description {
  color: var(--slate-600, #475569);
  line-height: 1.6;
  margin-bottom: 1rem;
  flex: 1;
  font-size: 0.95rem;
}

.project-tech {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1.25rem;
}

.tech-tag {
  background: var(--slate-100, #f1f5f9);
  color: var(--slate-700, #334155);
  font-size: 0.8rem;
  font-weight: 500;
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  border: 1px solid var(--slate-200, #e2e8f0);
  transition: all 0.2s ease;
}

.tech-tag:hover {
  background: var(--primary-600, #2563eb);
  color: white;
  border-color: var(--primary-600, #2563eb);
  transform: translateY(-1px);
}

.project-links {
  display: flex;
  gap: 0.75rem;
  margin-top: auto;
}

.project-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  color: var(--slate-600, #475569);
  text-decoration: none;
  font-size: 0.875rem;
  font-weight: 600;
  padding: 0.625rem 1rem;
  border-radius: 10px;
  border: none;
  transition: all 0.2s ease;
  flex: 1;
}

.github-link {
  background: var(--slate-800, #1e293b);
  color: white;
}

.github-link:hover {
  background: var(--slate-900, #0f172a);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.3);
}

.live-link {
  background: linear-gradient(135deg, #0891b2 0%, #0d9488 100%);
  color: white;
}

.live-link:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(8, 145, 178, 0.4);
}

.link-icon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

/* Dark mode adjustments */
[data-theme='dark'] .project-card {
  background: rgba(30, 41, 59, 0.6);
  border-color: rgba(255, 255, 255, 0.1);
}

[data-theme='dark'] .project-card:hover {
  border-color: rgba(96, 165, 250, 0.4);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
}

[data-theme='dark'] .project-title {
  color: #f1f5f9;
}

[data-theme='dark'] .project-description {
  color: #94a3b8;
}

[data-theme='dark'] .tech-tag {
  background: rgba(255, 255, 255, 0.08);
  color: #cbd5e1;
  border-color: rgba(255, 255, 255, 0.1);
}

[data-theme='dark'] .tech-tag:hover {
  background: #3b82f6;
  color: white;
  border-color: #3b82f6;
}

[data-theme='dark'] .github-link {
  background: rgba(255, 255, 255, 0.1);
  color: #f1f5f9;
}

[data-theme='dark'] .github-link:hover {
  background: rgba(255, 255, 255, 0.15);
}

/* Responsive design */
@media (max-width: 768px) {
  .project-card {
    padding: 1.25rem;
  }

  .project-header {
    flex-direction: column;
    gap: 0.5rem;
  }

  .project-links {
    flex-direction: column;
  }

  .project-link {
    width: 100%;
  }
}
</style>
