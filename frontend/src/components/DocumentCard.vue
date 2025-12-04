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

.card-glass {
  background: rgba(255, 255, 255, 0.08);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 16px;
  padding: 1.75rem;
  transition: all 0.3s ease;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.card-glass:hover {
  transform: translateY(-6px);
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(96, 165, 250, 0.4);
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

.document-title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #f8fafc;
  margin: 0 0 0.75rem 0;
  line-height: 1.4;
}

.document-type {
  display: inline-block;
  padding: 0.375rem 0.875rem;
  background: rgba(96, 165, 250, 0.2);
  color: #93c5fd;
  border-radius: 20px;
  font-size: 0.8125rem;
  font-weight: 500;
  letter-spacing: 0.025em;
}

.document-description {
  color: #cbd5e1;
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
  color: #94a3b8;
  font-size: 0.875rem;
}

.icon {
  stroke-width: 2;
  opacity: 0.8;
  color: #94a3b8;
}

.card-actions {
  display: flex;
  gap: 1rem;
  padding-top: 1.25rem;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  margin-top: auto;
}

.document-link {
  color: #60a5fa;
  text-decoration: none;
  font-weight: 600;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  background: rgba(96, 165, 250, 0.1);
}

.document-link:hover {
  color: #93c5fd;
  background: rgba(96, 165, 250, 0.2);
  transform: translateX(4px);
}

.download-link {
  font-weight: 600;
}
</style>
