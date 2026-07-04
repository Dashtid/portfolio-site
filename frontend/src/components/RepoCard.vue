<template>
  <!-- .project-card is a behavior hook (entrance animation in HomeView +
       e2e hover test), not a style class. Visuals follow the same Tailwind
       recipe as the experience/education cards so all card systems match. -->
  <a
    :href="repo.html_url"
    target="_blank"
    rel="noopener noreferrer"
    class="project-card group flex h-full flex-col rounded-2xl border border-slate-200 bg-white p-6 no-underline transition-colors hover:border-primary-400/60 dark:border-slate-800 dark:bg-slate-900/50 dark:hover:border-primary-400/40"
    :aria-label="`${repo.name} repository on GitHub (opens in new tab)`"
  >
    <h3 class="text-lg font-semibold text-primary-600 dark:text-primary-400">
      {{ repo.name }}
    </h3>

    <p
      v-if="repo.description"
      class="mt-3 line-clamp-2 text-sm leading-relaxed text-slate-600 dark:text-slate-300"
    >
      {{ repo.description }}
    </p>

    <div
      class="mt-4 flex items-center justify-between font-mono text-xs text-slate-500 dark:text-slate-400"
    >
      <span v-if="repo.language" class="flex items-center gap-1.5 font-semibold">
        <span
          class="inline-block h-3 w-3 shrink-0 rounded-full"
          :style="{ background: getLanguageColor(repo.language) }"
        ></span>
        {{ repo.language }}
      </span>
      <span class="flex gap-4">
        <span class="flex items-center gap-1">
          <svg
            class="h-3.5 w-3.5 opacity-70"
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 16 16"
            fill="currentColor"
            aria-hidden="true"
          >
            <polygon
              points="8 1 10.5 6 16 6.5 12 10.5 13 16 8 13 3 16 4 10.5 0 6.5 5.5 6 8 1"
            ></polygon>
          </svg>
          {{ repo.stars }}<span class="sr-only"> stars</span>
        </span>
        <span class="flex items-center gap-1">
          <svg
            class="h-3.5 w-3.5 opacity-70"
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 16 16"
            fill="currentColor"
            aria-hidden="true"
          >
            <path
              d="M5 3.25a.75.75 0 1 1-1.5 0 .75.75 0 0 1 1.5 0zm0 2.122a2.25 2.25 0 1 0-1.5 0v.878A2.25 2.25 0 0 0 5.75 8.5h1.5v2.128a2.251 2.251 0 1 0 1.5 0V8.5h1.5a2.25 2.25 0 0 0 2.25-2.25v-.878a2.25 2.25 0 1 0-1.5 0v.878a.75.75 0 0 1-.75.75h-4.5A.75.75 0 0 1 5 6.25v-.878zm3.75 7.378a.75.75 0 1 1-1.5 0 .75.75 0 0 1 1.5 0zm3-8.75a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5z"
            ></path>
          </svg>
          {{ repo.forks }}<span class="sr-only"> forks</span>
        </span>
      </span>
    </div>

    <div
      class="mt-auto pt-4 text-sm font-medium text-primary-600 group-hover:text-primary-700 dark:text-primary-400 dark:group-hover:text-primary-300"
    >
      View on GitHub
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
