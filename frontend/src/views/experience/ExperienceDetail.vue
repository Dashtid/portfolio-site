<template>
  <div class="experience-detail">
    <NavBar />

    <!-- Main landmark — always present so router focus() and skip link land correctly -->
    <main id="main-content" tabindex="-1">
      <!-- Loading State -->
      <div v-if="loading" class="container py-5 text-center">
        <div class="spinner-border text-primary" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
        <p class="mt-3">Loading experience details...</p>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="container py-5">
        <div class="alert alert-danger" role="alert">
          <h4 class="alert-heading">Error Loading Experience</h4>
          <p>{{ error }}</p>
          <hr />
          <router-link to="/" class="btn btn-primary">Return to Home</router-link>
        </div>
      </div>

      <!-- Company Details -->
      <div v-else-if="company" class="container py-5">
        <!-- Media Section: Video and Map (side-by-side on desktop) -->
        <div v-if="company.video_url || company.map_url" class="media-section">
          <!-- YouTube Video -->
          <div v-if="company.video_url" class="media-item">
            <VideoEmbed
              :url="company.video_url"
              :heading="company.video_title || `${company.name} Video`"
              :title="company.video_title || `${company.name} Video`"
            />
          </div>

          <!-- Google Maps -->
          <div v-if="company.map_url" class="media-item">
            <MapEmbed
              :url="company.map_url"
              :heading="company.map_title || `${company.name} Location`"
              :title="company.map_title || `${company.name} Location Map`"
            />
          </div>
        </div>

        <!-- Company Information -->
        <div class="mb-5">
          <div class="d-flex align-items-center mb-3">
            <img
              v-if="company.logo_url && !logoError"
              :src="company.logo_url"
              :alt="`${company.name} logo`"
              class="me-3"
              style="width: 64px; height: 64px; object-fit: contain"
              @error="logoError = true"
            />
            <div>
              <h1 class="mb-1">{{ company.title }}</h1>
              <h3 class="text-muted mb-0">{{ company.name }}</h3>
            </div>
          </div>

          <p class="text-muted">
            <!-- FRONTEND-PERF-07: Bootstrap Icons are not bundled in this app
                 (no `bootstrap-icons` import / link in the codebase), so the
                 `<i class="bi bi-*">` tags previously rendered as empty
                 boxes. Inlining the SVG paths fixes the visible bug and
                 removes the need to ever ship the ~120 KB icon font. -->
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="16"
              height="16"
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
            <span v-if="company.start_date" class="ms-3">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="16"
                height="16"
                fill="currentColor"
                viewBox="0 0 16 16"
                aria-hidden="true"
              >
                <path
                  d="M3.5 0a.5.5 0 0 1 .5.5V1h8V.5a.5.5 0 0 1 1 0V1h1a2 2 0 0 1 2 2v11a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2V3a2 2 0 0 1 2-2h1V.5a.5.5 0 0 1 .5-.5zM1 4v10a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V4H1z"
                />
              </svg>
              {{ formatDate(company.start_date) }} -
              {{ company.end_date ? formatDate(company.end_date) : 'Present' }}
            </span>
          </p>

          <div class="mb-4">
            <a
              v-if="company.website"
              :href="company.website"
              target="_blank"
              rel="noopener noreferrer"
              class="btn btn-outline-primary me-2"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="16"
                height="16"
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
        </div>

        <!-- Description -->
        <div class="mb-5">
          <h3>About {{ company.name }}</h3>
          <!-- eslint-disable-next-line vue/no-v-html -- Input HTML-escaped, only emits strong/em -->
          <div v-html="formatDescription(company.description)"></div>
        </div>

        <!-- Detailed Description -->
        <div v-if="company.detailed_description" class="mb-5">
          <h3>Role & Responsibilities</h3>
          <!-- eslint-disable-next-line vue/no-v-html -- Input HTML-escaped, only emits strong/em -->
          <div v-html="formatDescription(company.detailed_description)"></div>
        </div>

        <!-- Responsibilities List -->
        <div v-if="company.responsibilities && company.responsibilities.length > 0" class="mb-5">
          <h3>Key Responsibilities</h3>
          <ul class="list-group list-group-flush">
            <li
              v-for="(responsibility, index) in company.responsibilities"
              :key="`responsibility-${index}-${responsibility.slice(0, 20)}`"
              class="list-group-item"
            >
              {{ responsibility }}
            </li>
          </ul>
        </div>

        <!-- Technologies -->
        <div v-if="company.technologies && company.technologies.length > 0" class="mb-5">
          <h3>Technologies & Tools</h3>
          <div class="d-flex flex-wrap gap-2">
            <span v-for="tech in company.technologies" :key="tech" class="badge bg-primary">
              {{ tech }}
            </span>
          </div>
        </div>

        <!-- Back Navigation -->
        <div class="mt-5 pt-4 border-top">
          <router-link to="/" class="btn btn-outline-secondary">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="16"
              height="16"
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
      </div>
    </main>
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
    // Media section fade up
    gsap.from('.media-section', {
      opacity: 0,
      y: 30,
      duration: 0.5,
      ease: 'power2.out'
    })

    // Company info section fade up
    gsap.from('.mb-5:not(.media-section)', {
      opacity: 0,
      y: 25,
      duration: 0.5,
      stagger: 0.1,
      ease: 'power2.out',
      delay: 0.15
    })

    // Responsibilities list items stagger
    gsap.from('.list-group-item', {
      opacity: 0,
      x: -20,
      duration: 0.4,
      stagger: 0.08,
      ease: 'power2.out',
      delay: 0.4
    })

    // Technology badges stagger
    gsap.from('.badge', {
      opacity: 0,
      y: 15,
      scale: 0.9,
      duration: 0.3,
      stagger: 0.05,
      ease: 'power2.out',
      delay: 0.5
    })

    // Back navigation fade in
    gsap.from('.border-top', {
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
.experience-detail {
  min-height: 100vh;
  background-color: var(--bg-primary, #ffffff);
  color: var(--text-primary, #1e293b);
}

/* Offset fixed navbar so content doesn't slide under it at scroll top */
.experience-detail > main {
  padding-top: 80px;
}

/* Media Section - Side by side layout for video and map */
.media-section {
  display: flex;
  flex-wrap: wrap;
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.media-item {
  flex: 1 1 400px;
  min-width: 0;
}

@media (max-width: 768px) {
  .media-section {
    flex-direction: column;
  }

  .media-item {
    flex: 1 1 100%;
  }
}

.badge {
  font-size: 0.9rem;
  padding: 0.5rem 0.75rem;
}

.list-group-item {
  border-left: none;
  border-right: none;
  padding-left: 0;
  background-color: transparent;
  color: var(--text-primary, #1e293b);
}

.list-group-item:first-child {
  border-top: none;
}

.ratio iframe {
  border: none;
  border-radius: 0.5rem;
}

h1,
h2,
h3 {
  color: var(--text-primary, #1e293b);
}

.text-muted {
  color: var(--text-secondary, #64748b) !important;
}

main p {
  color: var(--text-primary, #1e293b);
}

main :deep(p) {
  color: var(--text-primary, #1e293b);
}

.border-top {
  border-color: var(--border-color, #e2e8f0) !important;
}

/* Dark mode support */
[data-theme='dark'] .experience-detail {
  background-color: var(--bg-primary, #0f172a);
  color: var(--text-primary, #f1f5f9);
}

[data-theme='dark'] h1,
[data-theme='dark'] h2,
[data-theme='dark'] h3 {
  color: var(--text-primary);
}

[data-theme='dark'] .text-muted {
  color: var(--text-tertiary) !important;
}

[data-theme='dark'] main p,
[data-theme='dark'] main :deep(p) {
  color: var(--text-secondary);
}

[data-theme='dark'] .list-group-item {
  color: var(--text-secondary);
  border-color: var(--border-primary);
}

[data-theme='dark'] .border-top {
  border-color: var(--border-primary) !important;
}

[data-theme='dark'] .btn-outline-primary {
  color: var(--link-color);
  border-color: var(--link-color);
}

[data-theme='dark'] .btn-outline-primary:hover {
  background-color: var(--primary-400);
  color: var(--bg-primary);
}

[data-theme='dark'] .btn-outline-secondary {
  color: var(--text-tertiary);
  border-color: var(--border-secondary);
}

[data-theme='dark'] .btn-outline-secondary:hover {
  background-color: var(--border-secondary);
  color: var(--text-primary);
}

[data-theme='dark'] .badge.bg-primary {
  background-color: rgba(59, 130, 246, 0.3) !important;
  color: var(--primary-300, #93c5fd) !important;
}

[data-theme='dark'] .alert-danger {
  background-color: rgba(239, 68, 68, 0.2);
  border-color: rgba(239, 68, 68, 0.3);
  color: var(--color-error, #fca5a5);
}

[data-theme='dark'] .spinner-border.text-primary {
  color: var(--link-color) !important;
}

[data-theme='dark'] .container p.mt-3 {
  color: var(--text-tertiary);
}

/* Enhanced button hover effects */
.btn-outline-primary,
.btn-outline-secondary {
  transition: all 0.25s cubic-bezier(0.23, 1, 0.32, 1);
}

.btn-outline-primary:hover {
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.25);
}

.btn-outline-secondary:hover {
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 4px 12px rgba(100, 116, 139, 0.2);
}

/* Reduced motion support */
@media (prefers-reduced-motion: reduce) {
  .btn-outline-primary,
  .btn-outline-secondary {
    transition: none;
  }

  .btn-outline-primary:hover,
  .btn-outline-secondary:hover {
    transform: none;
  }
}
</style>
