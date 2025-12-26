<template>
  <article class="document-card">
    <div class="card-glass">
      <div class="card-header">
        <div class="document-info">
          <h3 class="document-title">{{ document.title }}</h3>
          <span class="document-type">{{ documentTypeLabel }}</span>
        </div>
      </div>

      <p v-if="document.description" class="document-description">{{ document.description }}</p>

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
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
            <polyline points="14 2 14 8 20 8" />
          </svg>
          <span>{{ formattedFileSize }}</span>
        </div>
        <div v-if="document.published_date" class="meta-item">
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
          <span>{{ formattedDate }}</span>
        </div>
      </div>

      <div class="card-actions">
        <a
          :href="document.file_url"
          target="_blank"
          rel="noopener noreferrer"
          class="document-link download-link"
        >
          Download PDF →
        </a>
      </div>
    </div>
  </article>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Document } from '@/types'

const props = defineProps<{
  document: Document
}>()

const documentTypeLabel = computed(() => {
  const types: Record<string, string> = {
    thesis: 'Thesis',
    paper: 'Research Paper',
    report: 'Technical Report',
    publication: 'Publication'
  }
  return types[props.document.document_type] || props.document.document_type
})

const formattedFileSize = computed(() => {
  const bytes = props.document.file_size
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i]
})

const formattedDate = computed(() => {
  if (!props.document.published_date) return ''
  const date = new Date(props.document.published_date)
  return date.toLocaleDateString('en-US', { year: 'numeric', month: 'long' })
})
</script>

<style scoped>
.document-card {
  width: 100%;
}

/* Light mode - always shown in bg-dark section, so use dark glass effect */
.card-glass {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.18);
  border-radius: 16px;
  padding: 1.75rem;
  transition: all 0.3s ease;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.card-glass:hover {
  transform: translateY(-6px);
  background: rgba(255, 255, 255, 0.15);
  border-color: rgba(96, 165, 250, 0.5);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
}

.document-info {
  flex: 1;
}

/* Text colors - optimized for dark background (bg-dark section) */
.document-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #f8fafc; /* slate-50 - always light for dark bg */
  margin: 0 0 0.75rem 0;
  line-height: 1.4;
}

.document-type {
  display: inline-block;
  padding: 0.375rem 0.875rem;
  background: rgba(96, 165, 250, 0.2);
  color: #93c5fd; /* primary-300 */
  border-radius: 20px;
  font-size: 0.8125rem;
  font-weight: 500;
  letter-spacing: 0.025em;
}

.document-description {
  color: #cbd5e1; /* slate-300 - readable on dark */
  line-height: 1.7;
  margin-bottom: 1.25rem;
  flex: 1;
}

.card-meta {
  display: flex;
  gap: 1.5rem;
  margin-bottom: 1.25rem;
  flex-wrap: wrap;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #94a3b8; /* slate-400 */
  font-size: 0.875rem;
}

.icon {
  stroke-width: 2;
  opacity: 0.8;
  color: #94a3b8; /* slate-400 */
}

.card-actions {
  display: flex;
  gap: 1rem;
  padding-top: 1.25rem;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  margin-top: auto;
}

.document-link {
  color: #93c5fd; /* primary-300 */
  text-decoration: none;
  font-weight: 600;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  background: rgba(96, 165, 250, 0.15);
}

.document-link:hover {
  color: #bfdbfe; /* primary-200 */
  background: rgba(96, 165, 250, 0.25);
  transform: translateX(4px);
}

.document-link:focus-visible {
  outline: 2px solid var(--link-color);
  outline-offset: 2px;
}

.download-link {
  font-weight: 600;
}

/* Dark theme - glass effect for dark backgrounds */
[data-theme='dark'] .card-glass {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.15);
}

[data-theme='dark'] .card-glass:hover {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(96, 165, 250, 0.5);
}

/* Light theme - solid card styling for light bg-dark section */
[data-theme='light'] .card-glass {
  background: rgba(255, 255, 255, 0.9);
  border-color: rgba(0, 0, 0, 0.1);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
}

[data-theme='light'] .card-glass:hover {
  background: rgba(255, 255, 255, 1);
  border-color: rgba(37, 99, 235, 0.3);
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.12);
}

[data-theme='light'] .document-title {
  color: #1e293b; /* slate-800 */
}

[data-theme='light'] .document-type {
  background: rgba(37, 99, 235, 0.1);
  color: #2563eb; /* primary-600 */
}

[data-theme='light'] .document-description {
  color: #475569; /* slate-600 */
}

[data-theme='light'] .meta-item,
[data-theme='light'] .icon {
  color: #64748b; /* slate-500 */
}

[data-theme='light'] .card-actions {
  border-top-color: rgba(0, 0, 0, 0.1);
}

[data-theme='light'] .document-link {
  color: #2563eb; /* primary-600 */
  background: rgba(37, 99, 235, 0.1);
}

[data-theme='light'] .document-link:hover {
  color: #1d4ed8; /* primary-700 */
  background: rgba(37, 99, 235, 0.15);
}
</style>
