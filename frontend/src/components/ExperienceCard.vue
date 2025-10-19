<template>
  <article class="experience-card">
    <div class="card-glass">
      <div class="card-header">
        <div class="company-info">
          <h3 class="company-name">{{ company.name }}</h3>
          <p class="company-title">{{ company.title }}</p>
        </div>
        <span v-if="isCurrent" class="current-badge">Current</span>
      </div>

      <p class="company-description">{{ company.description }}</p>

      <div class="card-meta">
        <div class="meta-item">
          <svg class="icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
            <circle cx="12" cy="10" r="3"/>
          </svg>
          <span>{{ company.location }}</span>
        </div>
        <div class="meta-item">
          <svg class="icon" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <rect x="3" y="4" width="18" height="18" rx="2" ry="2"/>
            <line x1="16" y1="2" x2="16" y2="6"/>
            <line x1="8" y1="2" x2="8" y2="6"/>
            <line x1="3" y1="10" x2="21" y2="10"/>
          </svg>
          <span>{{ formatDuration }}</span>
        </div>
      </div>

      <div v-if="company.website" class="card-actions">
        <a
          :href="company.website"
          target="_blank"
          rel="noopener noreferrer"
          class="company-link"
        >
          Visit Website →
        </a>
      </div>
    </div>
  </article>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  company: {
    type: Object,
    required: true
  }
})

const isCurrent = computed(() => {
  return props.company.end_date === null || props.company.end_date === undefined
})

const formatDuration = computed(() => {
  const start = props.company.start_date ? new Date(props.company.start_date) : null
  const end = props.company.end_date ? new Date(props.company.end_date) : new Date()

  if (!start) return 'N/A'

  const startMonth = start.toLocaleDateString('en', { month: 'short', year: 'numeric' })
  const endMonth = isCurrent.value
    ? 'Present'
    : end.toLocaleDateString('en', { month: 'short', year: 'numeric' })

  return `${startMonth} - ${endMonth}`
})
</script>

<style scoped>
.experience-card {
  margin-bottom: var(--spacing-6);
  animation: slideIn 0.5s ease-out;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.card-glass {
  background: var(--glass-bg);
  backdrop-filter: blur(var(--glass-blur));
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-xl);
  padding: var(--spacing-6);
  box-shadow: var(--shadow-lg);
  transition: all var(--transition-base) ease;
}

.experience-card:hover .card-glass {
  transform: translateY(-4px);
  box-shadow: var(--shadow-xl);
  border-color: var(--color-primary);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--spacing-4);
}

.company-name {
  color: var(--color-gray-900);
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-bold);
  margin: 0 0 var(--spacing-1) 0;
}

.company-title {
  color: var(--color-primary);
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-medium);
  margin: 0;
}

.current-badge {
  background: linear-gradient(135deg, var(--color-primary), var(--color-teal));
  color: white;
  padding: var(--spacing-1) var(--spacing-3);
  border-radius: var(--radius-full);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.company-description {
  color: var(--color-gray-600);
  line-height: var(--line-height-relaxed);
  margin: 0 0 var(--spacing-4) 0;
}

.card-meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--spacing-4);
  margin-bottom: var(--spacing-4);
  padding-top: var(--spacing-4);
  border-top: 1px solid var(--glass-border);
}

.meta-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  color: var(--color-gray-500);
  font-size: var(--font-size-sm);
}

.icon {
  stroke-width: 2;
}

.card-actions {
  padding-top: var(--spacing-4);
}

.company-link {
  display: inline-flex;
  align-items: center;
  color: var(--color-primary);
  font-weight: var(--font-weight-medium);
  text-decoration: none;
  transition: color var(--transition-fast);
}

.company-link:hover {
  color: var(--color-primary-dark);
}

/* Dark mode adjustments */
[data-theme="dark"] .company-name {
  color: var(--color-gray-100);
}

[data-theme="dark"] .company-description {
  color: var(--color-gray-400);
}

[data-theme="dark"] .meta-item {
  color: var(--color-gray-500);
}
</style>