<template>
  <div class="project-card">
    <div class="project-header">
      <h3 class="project-title">{{ project.title }}</h3>
      <span v-if="project.featured" class="featured-badge">Featured</span>
    </div>

    <p class="project-description">{{ project.description }}</p>

    <div class="project-tech">
      <span
        v-for="(tech, index) in techStack"
        :key="index"
        class="tech-tag"
      >
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
          <path d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/>
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
        <svg class="link-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"/>
        </svg>
        <span>Live Demo</span>
      </a>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  project: {
    type: Object,
    required: true
  }
})

// Parse tech stack from JSON or string
const techStack = computed(() => {
  if (!props.project.tech_stack) return []

  if (typeof props.project.tech_stack === 'string') {
    try {
      return JSON.parse(props.project.tech_stack)
    } catch {
      return props.project.tech_stack.split(',').map(t => t.trim())
    }
  }

  return Array.isArray(props.project.tech_stack)
    ? props.project.tech_stack
    : []
})
</script>

<style scoped>
.project-card {
  background: var(--glass-bg);
  backdrop-filter: blur(var(--glass-blur));
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-xl);
  padding: var(--spacing-6);
  transition: all var(--transition-base) ease;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.project-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
  border-color: var(--color-primary);
}

.project-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--spacing-4);
}

.project-title {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-bold);
  color: var(--color-gray-900);
  margin: 0;
  flex: 1;
}

.featured-badge {
  background: linear-gradient(135deg, var(--color-primary), var(--color-teal));
  color: white;
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  padding: var(--spacing-1) var(--spacing-2);
  border-radius: var(--radius-full);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  flex-shrink: 0;
}

.project-description {
  color: var(--color-gray-600);
  line-height: var(--line-height-relaxed);
  margin-bottom: var(--spacing-4);
  flex: 1;
}

.project-tech {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-2);
  margin-bottom: var(--spacing-4);
}

.tech-tag {
  background: var(--color-gray-100);
  color: var(--color-gray-700);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  padding: var(--spacing-1) var(--spacing-3);
  border-radius: var(--radius-full);
  border: 1px solid var(--color-gray-200);
  transition: all var(--transition-base) ease;
}

.tech-tag:hover {
  background: var(--color-primary);
  color: white;
  border-color: var(--color-primary);
  transform: scale(1.05);
}

.project-links {
  display: flex;
  gap: var(--spacing-3);
  margin-top: auto;
}

.project-link {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-2);
  color: var(--color-gray-600);
  text-decoration: none;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  padding: var(--spacing-2) var(--spacing-3);
  border-radius: var(--radius-base);
  border: 1px solid var(--color-gray-300);
  transition: all var(--transition-base) ease;
  background: white;
}

.project-link:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-sm);
}

.github-link:hover {
  border-color: var(--color-gray-800);
  color: var(--color-gray-900);
  background: var(--color-gray-50);
}

.live-link:hover {
  border-color: var(--color-teal);
  color: var(--color-teal);
  background: rgba(var(--color-teal-rgb), 0.1);
}

.link-icon {
  width: 16px;
  height: 16px;
  flex-shrink: 0;
}

/* Dark mode adjustments */
[data-theme="dark"] .project-title {
  color: var(--color-gray-100);
}

[data-theme="dark"] .project-description {
  color: var(--color-gray-400);
}

[data-theme="dark"] .tech-tag {
  background: var(--color-gray-800);
  color: var(--color-gray-300);
  border-color: var(--color-gray-700);
}

[data-theme="dark"] .tech-tag:hover {
  background: var(--color-primary);
  color: white;
  border-color: var(--color-primary);
}

[data-theme="dark"] .project-link {
  background: var(--color-gray-800);
  color: var(--color-gray-300);
  border-color: var(--color-gray-700);
}

[data-theme="dark"] .github-link:hover {
  background: var(--color-gray-900);
  border-color: var(--color-gray-600);
  color: var(--color-gray-100);
}

/* Responsive design */
@media (max-width: 768px) {
  .project-card {
    padding: var(--spacing-4);
  }

  .project-links {
    flex-direction: column;
  }

  .project-link {
    width: 100%;
    justify-content: center;
  }
}
</style>