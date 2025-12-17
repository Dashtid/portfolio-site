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
          <svg
            class="icon"
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
          >
            <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z" />
            <circle cx="12" cy="10" r="3" />
          </svg>
          <span>{{ company.location }}</span>
        </div>
        <div class="meta-item">
          <svg
            class="icon"
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
          >
            <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
            <line x1="16" y1="2" x2="16" y2="6" />
            <line x1="8" y1="2" x2="8" y2="6" />
            <line x1="3" y1="10" x2="21" y2="10" />
          </svg>
          <span>{{ formatDuration }}</span>
        </div>
      </div>

      <div class="card-actions">
        <router-link :to="`/experience/${company.id}`" class="company-link detail-link">
          View Details →
        </router-link>
        <a
          v-if="company.website"
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

<script setup lang="ts">
import { computed } from 'vue'
import type { Company } from '@/types'

interface Props {
  company: Company
}

const props = defineProps<Props>()

const isCurrent = computed<boolean>(() => {
  return props.company.end_date === null || props.company.end_date === undefined
})

const formatDuration = computed<string>(() => {
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
  margin-bottom: 1.5rem;
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
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(226, 232, 240, 0.8);
  border-radius: 16px;
  padding: 1.5rem;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
  transition: all 0.3s ease;
  position: relative;
  overflow: hidden;
}

.card-glass::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, var(--primary-500, #3b82f6), var(--primary-600, #2563eb));
  transform: scaleX(0);
  transform-origin: left;
  transition: transform 0.3s ease;
}

.experience-card:hover .card-glass::before {
  transform: scaleX(1);
}

.experience-card:hover .card-glass {
  transform: translateY(-6px);
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.12);
  border-color: var(--primary-300, #93c5fd);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 1rem;
  margin-bottom: 1rem;
}

.company-name {
  color: var(--slate-800, #1e293b);
  font-size: 1.25rem;
  font-weight: 700;
  margin: 0 0 0.25rem 0;
  line-height: 1.3;
}

.company-title {
  color: var(--primary-600, #2563eb);
  font-size: 1rem;
  font-weight: 600;
  margin: 0;
}

.current-badge {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.3);
}

.company-description {
  color: var(--slate-600, #475569);
  line-height: 1.6;
  margin: 0 0 1rem 0;
  font-size: 0.95rem;
}

.card-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 1.25rem;
  margin-bottom: 1rem;
  padding-top: 1rem;
  border-top: 1px solid var(--slate-200, #e2e8f0);
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--slate-500, #64748b);
  font-size: 0.875rem;
}

.icon {
  stroke-width: 2;
  color: var(--slate-400, #94a3b8);
}

.card-actions {
  display: flex;
  gap: 1rem;
  padding-top: 1rem;
  flex-wrap: wrap;
}

.company-link {
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
  color: var(--primary-600, #2563eb);
  font-weight: 600;
  font-size: 0.9rem;
  text-decoration: none;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  background: rgba(37, 99, 235, 0.08);
  transition: all 0.2s ease;
}

.company-link:hover {
  background: var(--primary-600, #2563eb);
  color: white;
  transform: translateX(4px);
}

.detail-link {
  background: var(--primary-600, #2563eb);
  color: white;
}

.detail-link:hover {
  background: var(--primary-700, #1d4ed8);
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
}

/* Dark mode adjustments */
[data-theme='dark'] .card-glass {
  background: var(--card-bg);
  border-color: var(--border-primary);
}

[data-theme='dark'] .card-glass::before {
  background: linear-gradient(90deg, var(--primary-500), var(--primary-600));
}

[data-theme='dark'] .experience-card:hover .card-glass {
  border-color: var(--primary-400);
  box-shadow: var(--card-hover-shadow);
}

[data-theme='dark'] .company-name {
  color: var(--text-primary);
}

[data-theme='dark'] .company-title {
  color: var(--link-color);
}

[data-theme='dark'] .company-description {
  color: var(--text-secondary);
}

[data-theme='dark'] .card-meta {
  border-top-color: var(--border-primary);
}

[data-theme='dark'] .meta-item {
  color: var(--text-tertiary);
}

[data-theme='dark'] .icon {
  color: var(--text-tertiary);
}

[data-theme='dark'] .company-link {
  background: rgba(96, 165, 250, 0.15);
  color: var(--link-color);
}

[data-theme='dark'] .company-link:hover {
  background: var(--primary-600);
  color: var(--text-inverse);
}

[data-theme='dark'] .detail-link {
  background: var(--primary-600);
  color: var(--text-inverse);
}

[data-theme='dark'] .detail-link:hover {
  background: var(--primary-500);
}

[data-theme='dark'] .current-badge {
  background: linear-gradient(135deg, #059669 0%, #047857 100%);
  box-shadow: 0 2px 8px rgba(5, 150, 105, 0.4);
}

/* Responsive */
@media (max-width: 768px) {
  .card-glass {
    padding: 1.25rem;
  }

  .card-header {
    flex-direction: column;
    gap: 0.5rem;
  }

  .card-actions {
    flex-direction: column;
  }

  .company-link {
    justify-content: center;
    width: 100%;
  }
}

.experience-link:focus-visible,
.btn:focus-visible {
  outline: 2px solid var(--primary-400, #60a5fa);
  outline-offset: 2px;
}

.experience-card:focus-within {
  outline: 2px solid var(--primary-400, #60a5fa);
  outline-offset: 2px;
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
  .experience-card {
    transition: none;
  }
  .experience-card:hover {
    transform: none;
  }
}
</style>
