<template>
  <article
    class="document-card group flex flex-col rounded-2xl border border-slate-200 bg-white p-6 transition-colors hover:border-primary-400/60 dark:border-slate-800 dark:bg-slate-900/50 dark:hover:border-primary-400/40"
  >
    <header class="flex items-start justify-between gap-4">
      <div class="min-w-0 flex-1">
        <h3 class="document-title text-lg font-semibold text-slate-900 dark:text-white">
          {{ document.title }}
        </h3>
        <span
          class="document-type mt-2 inline-block rounded-full bg-primary-50 px-2.5 py-0.5 font-mono text-xs uppercase tracking-wider text-primary-700 dark:bg-primary-500/10 dark:text-primary-300"
        >
          {{ documentTypeLabel }}
        </span>
      </div>
    </header>

    <p
      v-if="document.description"
      class="document-description mt-4 text-sm leading-relaxed text-slate-600 dark:text-slate-300"
    >
      {{ document.description }}
    </p>

    <div class="mt-5 flex flex-wrap gap-x-5 gap-y-2 text-xs text-slate-500 dark:text-slate-400">
      <div class="meta-item flex items-center gap-1.5">
        <svg
          class="h-3.5 w-3.5"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          aria-hidden="true"
        >
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
          <polyline points="14 2 14 8 20 8" />
        </svg>
        <span>{{ formattedFileSize }}</span>
      </div>
      <div v-if="document.published_date" class="meta-item flex items-center gap-1.5">
        <svg
          class="h-3.5 w-3.5"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          aria-hidden="true"
        >
          <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
          <line x1="16" y1="2" x2="16" y2="6" />
          <line x1="8" y1="2" x2="8" y2="6" />
          <line x1="3" y1="10" x2="21" y2="10" />
        </svg>
        <span>{{ formattedDate }}</span>
      </div>
    </div>

    <a
      :href="document.file_url"
      target="_blank"
      rel="noopener noreferrer"
      class="download-link mt-6 inline-flex items-center gap-1 text-sm font-medium text-primary-600 transition-all hover:gap-2 hover:text-primary-700 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-primary-500 dark:text-primary-400 dark:hover:text-primary-300"
    >
      Download PDF
      <svg
        class="h-3.5 w-3.5"
        fill="none"
        viewBox="0 0 24 24"
        stroke-width="2"
        stroke="currentColor"
        aria-hidden="true"
      >
        <path stroke-linecap="round" stroke-linejoin="round" d="M17 8l4 4m0 0l-4 4m4-4H3" />
      </svg>
    </a>
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
  // Handle null, undefined, or invalid file sizes
  if (bytes == null || bytes < 0 || !Number.isFinite(bytes)) {
    return 'Unknown size'
  }
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  // Ensure index is within bounds (both lower and upper)
  const safeIndex = Math.max(0, Math.min(i, sizes.length - 1))
  return Math.round((bytes / Math.pow(k, safeIndex)) * 100) / 100 + ' ' + sizes[safeIndex]
})

const formattedDate = computed(() => {
  if (!props.document.published_date) return ''
  const date = new Date(props.document.published_date)
  // Check for Invalid Date (NaN) before formatting
  if (isNaN(date.getTime())) return ''
  return date.toLocaleDateString('en-US', { year: 'numeric', month: 'long' })
})
</script>
