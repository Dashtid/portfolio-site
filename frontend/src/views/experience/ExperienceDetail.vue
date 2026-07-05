<template>
  <div
    class="experience-detail min-h-screen bg-white text-slate-900 dark:bg-slate-950 dark:text-slate-100"
  >
    <NavBar />

    <!-- Main landmark — always present so router focus() and skip link land correctly -->
    <main id="main-content" tabindex="-1" class="pt-24">
      <!-- Loading State -->
      <div v-if="loading" class="mx-auto max-w-3xl px-6 py-20 text-center">
        <div
          class="spinner-border mx-auto h-10 w-10 animate-spin rounded-full border-2 border-slate-200 border-t-primary-500 dark:border-slate-700 dark:border-t-primary-400"
          role="status"
        >
          <span class="sr-only">Loading...</span>
        </div>
        <p class="mt-4 text-sm text-slate-500 dark:text-slate-400">Loading experience details...</p>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="mx-auto max-w-3xl px-6 py-20">
        <div
          class="alert-danger rounded-2xl border border-rose-200 bg-rose-50 p-6 dark:border-rose-500/30 dark:bg-rose-500/10"
          role="alert"
        >
          <h4 class="text-lg font-semibold text-rose-800 dark:text-rose-200">
            Error Loading Experience
          </h4>
          <p class="mt-2 text-sm text-rose-700 dark:text-rose-300">{{ error }}</p>
          <router-link
            to="/"
            class="mt-5 inline-flex items-center gap-1 text-sm font-medium text-primary-600 transition-all hover:gap-2 hover:text-primary-700 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-primary-500 dark:text-primary-400 dark:hover:text-primary-300"
          >
            Return to Home
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
          </router-link>
        </div>
      </div>

      <!-- Company Details -->
      <article v-else-if="company" class="mx-auto max-w-4xl px-6 py-12">
        <!-- Company Information — identity leads: logo, role, and dates
             come before any third-party embed (the media grid used to sit
             first, pushing the h1 below the fold on mobile and putting the
             embed captions ahead of it in the document outline). -->
        <section class="experience-section mb-10">
          <header class="flex items-start gap-5">
            <img
              v-if="company.logo_url && !logoError"
              :src="company.logo_url"
              :alt="`${company.name} logo`"
              class="h-16 w-16 shrink-0 rounded-xl bg-white object-contain p-2 ring-1 ring-slate-200 dark:ring-slate-800"
              @error="logoError = true"
            />
            <div class="min-w-0 flex-1">
              <p
                class="font-mono text-xs uppercase tracking-[0.2em] text-slate-500 dark:text-slate-400"
              >
                {{ company.name }}
              </p>
              <h1
                class="mt-1 text-3xl font-semibold tracking-tight text-slate-900 sm:text-4xl dark:text-white"
              >
                {{ company.title }}
              </h1>
            </div>
          </header>

          <p
            class="mt-5 flex flex-wrap items-center gap-x-6 gap-y-2 text-sm text-slate-500 dark:text-slate-400"
          >
            <!-- FRONTEND-PERF-07: Bootstrap Icons are not bundled in this app
                 (no `bootstrap-icons` import / link in the codebase), so the
                 `<i class="bi bi-*">` tags previously rendered as empty
                 boxes. Inlining the SVG paths fixes the visible bug and
                 removes the need to ever ship the ~120 KB icon font. -->
            <span class="inline-flex items-center gap-1.5">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="14"
                height="14"
                fill="currentColor"
                viewBox="0 0 16 16"
                aria-hidden="true"
              >
                <path
                  d="M12.166 8.94c-.524 1.062-1.234 2.12-1.96 3.07A31.493 31.493 0 0 1 8 14.58a31.481 31.481 0 0 1-2.206-2.57c-.726-.95-1.436-2.008-1.96-3.07C3.304 7.867 3 6.862 3 6a5 5 0 0 1 10 0c0 .862-.305 1.867-.834 2.94zM8 16s6-5.686 6-10A6 6 0 0 0 2 6c0 4.314 6 10 6 10z"
                />
                <path d="M8 8a2 2 0 1 1 0-4 2 2 0 0 1 0 4zm0 1a3 3 0 1 0 0-6 3 3 0 0 0 0 6z" />
              </svg>
              {{ company.location }}
            </span>
            <span v-if="company.start_date" class="inline-flex items-center gap-1.5">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="14"
                height="14"
                fill="currentColor"
                viewBox="0 0 16 16"
                aria-hidden="true"
              >
                <path
                  d="M3.5 0a.5.5 0 0 1 .5.5V1h8V.5a.5.5 0 0 1 1 0V1h1a2 2 0 0 1 2 2v11a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2V3a2 2 0 0 1 2-2h1V.5a.5.5 0 0 1 .5-.5zM1 4v10a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V4H1z"
                />
              </svg>
              {{ formatDate(company.start_date) }} —
              {{ company.end_date ? formatDate(company.end_date) : 'Present' }}
            </span>
          </p>

          <div v-if="company.website" class="mt-6">
            <a
              :href="company.website"
              target="_blank"
              rel="noopener noreferrer"
              class="inline-flex items-center gap-2 rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 transition-colors hover:border-primary-400/60 hover:text-primary-600 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-primary-500 dark:border-slate-800 dark:text-slate-200 dark:hover:border-primary-400/40 dark:hover:text-primary-400"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="14"
                height="14"
                fill="currentColor"
                viewBox="0 0 16 16"
                aria-hidden="true"
              >
                <path
                  d="M0 8a8 8 0 1 1 16 0A8 8 0 0 1 0 8zm7.5-6.923c-.67.204-1.335.82-1.887 1.855A7.97 7.97 0 0 0 5.145 4H7.5V1.077zM4.09 4a9.267 9.267 0 0 1 .64-1.539 6.7 6.7 0 0 1 .597-.933A7.025 7.025 0 0 0 2.255 4H4.09zm-.582 3.5c.03-.877.138-1.718.312-2.5H1.674a6.958 6.958 0 0 0-.656 2.5h2.49zM4.847 5a12.5 12.5 0 0 0-.338 2.5H7.5V5H4.847zM8.5 5v2.5h2.99a12.495 12.495 0 0 0-.337-2.5H8.5zM4.51 8.5a12.5 12.5 0 0 0 .337 2.5H7.5V8.5H4.51zm3.99 0V11h2.653c.187-.765.306-1.608.338-2.5H8.5zM5.145 12c.138.386.295.744.468 1.068.552 1.035 1.218 1.65 1.887 1.855V12H5.145zm.182 2.472a6.696 6.696 0 0 1-.597-.933A9.268 9.268 0 0 1 4.09 12H2.255a7.024 7.024 0 0 0 3.072 2.472zM3.82 11a13.652 13.652 0 0 1-.312-2.5h-2.49c.062.89.291 1.733.656 2.5H3.82zm6.853 3.472A7.024 7.024 0 0 0 13.745 12H11.91a9.27 9.27 0 0 1-.64 1.539 6.688 6.688 0 0 1-.597.933zM8.5 12v2.923c.67-.204 1.335-.82 1.887-1.855.173-.324.33-.682.468-1.068H8.5zm3.68-1h2.146c.365-.767.594-1.61.656-2.5h-2.49a13.65 13.65 0 0 1-.312 2.5zm2.802-3.5a6.959 6.959 0 0 0-.656-2.5H12.18c.174.782.282 1.623.312 2.5h2.49zM11.27 2.461c.247.464.462.98.64 1.539h1.835a7.024 7.024 0 0 0-3.072-2.472c.218.284.418.598.597.933zM10.855 4a7.966 7.966 0 0 0-.468-1.068C9.835 1.897 9.17 1.282 8.5 1.077V4h2.355z"
                />
              </svg>
              Visit Website
            </a>
          </div>
        </section>

        <!-- Media: video and map (side-by-side on desktop). Two columns
             only when BOTH embeds exist; a lone embed gets a centered,
             capped width instead of half the grid sitting empty. -->
        <div
          v-if="company.video_url || company.map_url"
          class="media-section mb-10 grid gap-6"
          :class="
            company.video_url && company.map_url ? 'md:grid-cols-2' : 'md:mx-auto md:max-w-xl'
          "
        >
          <div v-if="company.video_url">
            <VideoEmbed
              :url="company.video_url"
              :heading="company.video_title || `${company.name} Video`"
              :title="company.video_title || `${company.name} Video`"
            />
          </div>

          <div v-if="company.map_url">
            <MapEmbed
              :url="company.map_url"
              :heading="company.map_title || `${company.name} Location`"
              :title="company.map_title || `${company.name} Location Map`"
            />
          </div>
        </div>

        <!-- Description -->
        <section class="experience-section mb-10">
          <h2
            class="font-mono text-xs uppercase tracking-[0.2em] text-slate-500 dark:text-slate-400"
          >
            About {{ company.name }}
          </h2>
          <div
            class="prose-content mt-4 max-w-prose space-y-4 leading-relaxed text-slate-700 dark:text-slate-300"
            v-html="formatDescription(company.description)"
          ></div>
        </section>

        <!-- Detailed Description -->
        <section v-if="company.detailed_description" class="experience-section mb-10">
          <h2
            class="font-mono text-xs uppercase tracking-[0.2em] text-slate-500 dark:text-slate-400"
          >
            Role &amp; Responsibilities
          </h2>
          <div
            class="prose-content mt-4 max-w-prose space-y-4 leading-relaxed text-slate-700 dark:text-slate-300"
            v-html="formatDescription(company.detailed_description)"
          ></div>
        </section>

        <!-- Responsibilities List -->
        <section
          v-if="company.responsibilities && company.responsibilities.length > 0"
          class="experience-section mb-10"
        >
          <h2
            class="font-mono text-xs uppercase tracking-[0.2em] text-slate-500 dark:text-slate-400"
          >
            Key Responsibilities
          </h2>
          <ul class="mt-4 max-w-prose space-y-3">
            <li
              v-for="(responsibility, index) in company.responsibilities"
              :key="`responsibility-${index}-${responsibility.slice(0, 20)}`"
              class="list-group-item flex gap-3 leading-relaxed text-slate-700 dark:text-slate-300"
            >
              <span
                class="mt-2.5 h-1 w-1 shrink-0 rounded-full bg-primary-500"
                aria-hidden="true"
              ></span>
              {{ responsibility }}
            </li>
          </ul>
        </section>

        <!-- Technologies -->
        <section
          v-if="company.technologies && company.technologies.length > 0"
          class="experience-section mb-10"
        >
          <h2
            class="font-mono text-xs uppercase tracking-[0.2em] text-slate-500 dark:text-slate-400"
          >
            Technologies &amp; Tools
          </h2>
          <div class="mt-4 flex flex-wrap gap-2">
            <span
              v-for="tech in company.technologies"
              :key="tech"
              class="badge inline-flex items-center rounded-full bg-primary-50 px-3 py-1 font-mono text-xs uppercase tracking-wider text-primary-700 dark:bg-primary-500/10 dark:text-primary-300"
            >
              {{ tech }}
            </span>
          </div>
        </section>

        <!-- Back Navigation -->
        <div
          class="experience-back-nav border-top mt-12 border-t border-slate-200 pt-8 dark:border-slate-800"
        >
          <router-link
            to="/"
            class="inline-flex items-center gap-1 text-sm font-medium text-primary-600 transition-all hover:gap-2 hover:text-primary-700 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-primary-500 dark:text-primary-400 dark:hover:text-primary-300"
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="14"
              height="14"
              fill="currentColor"
              viewBox="0 0 16 16"
              aria-hidden="true"
            >
              <path
                fill-rule="evenodd"
                d="M15 8a.5.5 0 0 0-.5-.5H2.707l3.147-3.146a.5.5 0 1 0-.708-.708l-4 4a.5.5 0 0 0 0 .708l4 4a.5.5 0 0 0 .708-.708L2.707 8.5H14.5A.5.5 0 0 0 15 8z"
              />
            </svg>
            Back to Portfolio
          </router-link>
        </div>
      </article>
    </main>

    <FooterSection />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { useHead } from '@unhead/vue'
import axios, { type AxiosError } from 'axios'
import { gsap } from 'gsap'
import type { Company } from '@/types'
import { apiLogger } from '../../utils/logger'
import { useExperienceDetailStore } from '../../stores/experienceDetail'
import VideoEmbed from '@/components/VideoEmbed.vue'
import MapEmbed from '@/components/MapEmbed.vue'
import NavBar from '@/components/NavBar.vue'
import FooterSection from '@/components/FooterSection.vue'
import { formatDescription } from '@/utils/markdown'

// AbortController for cancelling pending requests on route change
let fetchAbortController: AbortController | null = null

// GSAP animation context for cleanup
let gsapContext: gsap.Context | null = null

// Run entrance animations after content loads
const runEntranceAnimations = (): void => {
  // Skip during SSR (no window) and when user prefers reduced motion
  if (typeof window === 'undefined') return
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  if (prefersReducedMotion) return

  // Clean up previous animations
  if (gsapContext) {
    gsapContext.revert()
  }

  gsapContext = gsap.context(() => {
    gsap.from('.media-section', {
      opacity: 0,
      y: 30,
      duration: 0.5,
      ease: 'power2.out'
    })

    gsap.from('.experience-section', {
      opacity: 0,
      y: 25,
      duration: 0.5,
      stagger: 0.1,
      ease: 'power2.out',
      delay: 0.15
    })

    gsap.from('.list-group-item', {
      opacity: 0,
      x: -20,
      duration: 0.4,
      stagger: 0.08,
      ease: 'power2.out',
      delay: 0.4
    })

    gsap.from('.badge', {
      opacity: 0,
      y: 15,
      scale: 0.9,
      duration: 0.3,
      stagger: 0.05,
      ease: 'power2.out',
      delay: 0.5
    })

    gsap.from('.experience-back-nav', {
      opacity: 0,
      y: 20,
      duration: 0.5,
      ease: 'power2.out',
      delay: 0.6
    })
  })
}

const route = useRoute()
const experienceStore = useExperienceDetailStore()

const companyId = computed<string>(() => route.params.id as string)

// Reads from the store, which is populated during SSG and hydrated on the
// client — so the SSG-rendered company is available on first paint without a
// client-side refetch.
const company = computed<Company | null>(() => experienceStore.byId[companyId.value] ?? null)

// Start in the loading state only when the company isn't already available
// (i.e. wasn't hydrated from the SSG payload). This keeps the client's first
// render identical to the server's — no hydration mismatch, no spinner flash.
const loading = ref<boolean>(!company.value)
const error = ref<string | null>(null)
const logoError = ref<boolean>(false)

// Per-route head tags — reactive so SSG renders the correct title/canonical for each page
useHead({
  title: computed(() =>
    company.value
      ? `${company.value.name} | Experience | David Dashti`
      : 'Experience | David Dashti'
  ),
  meta: [
    {
      name: 'description',
      content: computed(() => company.value?.description || 'Experience details')
    }
  ],
  link: [
    {
      rel: 'canonical',
      href: computed(() => `https://dashti.se/experience/${companyId.value}`)
    }
  ]
})

// Format date helper
const formatDate = (dateString: string | null | undefined): string => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' })
}

// Load a company into the store, then settle local UI state. Short-circuits
// the network when the store already has it — which is the common case on the
// client after hydration, since the SSG render already fetched it.
const loadCompany = async (id: string): Promise<void> => {
  // Cancel any pending request before starting a new one
  if (fetchAbortController) {
    fetchAbortController.abort()
  }
  fetchAbortController = new AbortController()

  error.value = null
  logoError.value = false // Reset logo error state for new company

  if (experienceStore.byId[id]) {
    loading.value = false
    nextTick(() => {
      runEntranceAnimations()
    })
    return
  }

  loading.value = true
  try {
    await experienceStore.fetchCompany(id, fetchAbortController.signal)
  } catch (err) {
    // Ignore cancelled requests
    if (axios.isCancel(err)) return
    apiLogger.error('Error fetching company:', err)
    const axiosError = err as AxiosError
    if (axiosError.response?.status === 404) {
      error.value = 'Company not found. It may have been removed or the link is incorrect.'
    } else {
      error.value = 'Failed to load company details. Please try again later.'
    }
  } finally {
    loading.value = false
    // Run entrance animations after DOM updates
    if (!error.value && experienceStore.byId[id]) {
      nextTick(() => {
        runEntranceAnimations()
      })
    }
  }
}

// SSG: fetch the company synchronously during server-side render so the
// useHead computed above resolves to the per-route title/description before
// vite-ssg captures the rendered HTML and head tags. The store state is then
// serialized into the page (see main.ts) and hydrated on the client. Branch is
// tree-shaken from the client bundle when import.meta.env.SSR is statically false.
if (import.meta.env.SSR && companyId.value) {
  await loadCompany(companyId.value)
}

// Watch for route changes
watch(
  () => route.params.id,
  newId => {
    if (newId) {
      loadCompany(newId as string)
    }
  }
)

// Initial load
onMounted(async (): Promise<void> => {
  if (companyId.value) {
    await loadCompany(companyId.value)
  }
})

// Cleanup: cancel pending requests and animations on unmount
onUnmounted(() => {
  if (fetchAbortController) {
    fetchAbortController.abort()
    fetchAbortController = null
  }
  if (gsapContext) {
    gsapContext.revert()
  }
})
</script>

<style scoped>
/* The prose-content block renders v-html output from formatDescription.
   Scoped <p> styling here is :deep so it reaches the injected paragraphs. */
.prose-content :deep(p) {
  margin: 0;
}
.prose-content :deep(p + p) {
  margin-top: 1rem;
}
.prose-content :deep(strong) {
  font-weight: 600;
  color: inherit;
}
.prose-content :deep(em) {
  font-style: italic;
}
</style>
