<template>
  <!-- .project-card is a behavior hook (entrance animation in HomeView +
       the e2e hover test), not a style class — same contract as RepoCard.
       Visuals follow the shared card recipe so the curated projects and the
       live GitHub cards below them read as one system. -->
  <a
    :href="project.github_url ?? project.live_url ?? undefined"
    target="_blank"
    rel="noopener noreferrer"
    class="project-card group flex h-full flex-col rounded-2xl border border-slate-200 bg-white p-6 no-underline transition-colors hover:border-primary-400/60 hover:shadow-md dark:border-slate-800 dark:bg-slate-900/50 dark:hover:border-primary-400/40 dark:hover:bg-slate-900"
    :aria-label="`${project.name} (opens in new tab)`"
    @click="trackOutbound('github', 'projects')"
  >
    <h3 class="text-lg font-semibold text-primary-600 dark:text-primary-400">
      {{ project.name }}
    </h3>

    <p
      v-if="project.description"
      class="mt-3 text-sm leading-relaxed text-slate-600 dark:text-slate-300"
    >
      {{ project.description }}
    </p>

    <div v-if="project.technologies?.length" class="mt-4 flex flex-wrap gap-2">
      <span
        v-for="tech in project.technologies"
        :key="tech"
        class="badge inline-flex items-center rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700 dark:bg-slate-800/60 dark:text-slate-300"
      >
        {{ tech }}
      </span>
    </div>
  </a>
</template>

<script setup lang="ts">
import type { Project } from '@/types'
import { useOutboundTracking } from '@/composables/useOutboundTracking'

defineProps<{ project: Project }>()

const { trackOutbound } = useOutboundTracking()
</script>
