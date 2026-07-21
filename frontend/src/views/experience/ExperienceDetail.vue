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

      <!-- Not-found State (D3-UX-01): a real 404, distinct from a transient
           API failure — mirrors NotFoundView's treatment, noindex via the
           reactive useHead below. -->
      <div v-else-if="notFound" class="mx-auto max-w-3xl px-6 py-20 text-center">
        <p class="font-mono text-xs uppercase tracking-[0.2em] text-slate-500 dark:text-slate-400">
          HTTP 404 — experience not found
        </p>
        <h1
          class="mt-6 font-mono text-8xl font-semibold tracking-tight text-slate-900 dark:text-white"
        >
          404
        </h1>
        <p
          class="mx-auto mt-6 max-w-md text-balance text-base font-light leading-relaxed text-slate-500 sm:text-lg dark:text-slate-400"
        >
          This experience doesn't exist — it may have been removed, or the link is stale.
        </p>
        <div class="mt-8 flex flex-wrap items-center justify-center gap-3">
          <router-link
            to="/"
            class="inline-flex items-center gap-2 rounded-lg bg-primary-600 px-5 py-2.5 text-sm font-medium text-white transition-colors hover:bg-primary-700 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-primary-500 dark:bg-primary-500 dark:text-slate-950 dark:hover:bg-primary-400"
          >
            Back to home
          </router-link>
          <router-link
            to="/#experience"
            class="inline-flex items-center gap-2 rounded-lg border border-slate-200 px-5 py-2.5 text-sm font-medium text-slate-700 transition-colors hover:border-primary-400/60 hover:text-primary-600 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-primary-500 dark:border-slate-800 dark:text-slate-200 dark:hover:border-primary-400/40 dark:hover:text-primary-400"
          >
            View experience
          </router-link>
        </div>
      </div>

      <!-- Transient error state: the API was unreachable — retry copy, not a
           dead end (and not a red wall; amber = degraded, matching HomeView's
           API banner). -->
      <div v-else-if="error" class="mx-auto max-w-3xl px-6 py-20">
        <div
          class="rounded-2xl border border-amber-300/50 bg-amber-50 p-6 dark:border-amber-500/20 dark:bg-amber-500/10"
          role="alert"
        >
          <h1 class="text-lg font-semibold text-amber-900 dark:text-amber-200">
            Couldn't load this experience
          </h1>
          <p class="mt-2 text-sm text-amber-800 dark:text-amber-300">{{ error }}</p>
          <div class="mt-5 flex flex-wrap items-center gap-4">
            <button
              type="button"
              class="inline-flex items-center gap-2 rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-primary-700 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-primary-500 dark:bg-primary-500 dark:text-slate-950 dark:hover:bg-primary-400"
              @click="retry"
            >
              Try again
            </button>
            <router-link
              to="/"
              class="inline-flex items-center gap-1 text-sm font-medium text-primary-600 transition-all hover:gap-2 hover:text-primary-700 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-primary-500 dark:text-primary-400 dark:hover:text-primary-300"
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
      </div>

      <!-- Company Details — case-study layout (D3-FE-05): a main content
           column plus a sticky meta rail on lg. The rail (dates, location,
           website, tags, back-link) fills what used to be a dead right
           third; on mobile it renders as a details card directly under the
           header (source order drives the stack). -->
      <article
        v-else-if="company"
        class="mx-auto max-w-6xl px-6 py-12 lg:grid lg:grid-cols-[minmax(0,1fr)_300px] lg:gap-x-12"
      >
        <!-- Identity header: kicker + h1. Dates/location/website moved to
             the meta rail — the h1 block stays lean. -->
        <header class="experience-section flex items-start gap-5 lg:col-start-1">
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

        <!-- Meta rail: sticky on lg, a details card under the header on
             mobile. Interactive elements (links) keep primary blue; the
             tag chips are deliberately neutral sentence-case slate. -->
        <aside class="mt-10 lg:col-start-2 lg:row-span-2 lg:row-start-1 lg:mt-0">
          <div
            class="rounded-2xl border border-slate-200 p-6 lg:sticky lg:top-24 dark:border-slate-800"
          >
            <dl class="grid grid-cols-1 gap-x-6 gap-y-5 sm:grid-cols-2 lg:grid-cols-1">
              <div v-if="company.start_date">
                <dt
                  class="font-mono text-xs uppercase tracking-[0.2em] text-slate-500 dark:text-slate-400"
                >
                  Period
                </dt>
                <dd class="mt-1.5 text-sm text-slate-700 dark:text-slate-300">
                  {{ formatDate(company.start_date) }} —
                  {{ company.end_date ? formatDate(company.end_date) : 'Present' }}
                </dd>
              </div>
              <div v-if="company.location">
                <dt
                  class="font-mono text-xs uppercase tracking-[0.2em] text-slate-500 dark:text-slate-400"
                >
                  Location
                </dt>
                <dd class="mt-1.5 text-sm text-slate-700 dark:text-slate-300">
                  {{ company.location }}
                </dd>
              </div>
              <div v-if="company.website">
                <dt
                  class="font-mono text-xs uppercase tracking-[0.2em] text-slate-500 dark:text-slate-400"
                >
                  Website
                </dt>
                <dd class="mt-1.5 text-sm">
                  <a
                    :href="company.website"
                    target="_blank"
                    rel="noopener noreferrer"
                    class="inline-flex items-center gap-1.5 font-medium text-primary-600 transition-colors hover:text-primary-700 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-primary-500 dark:text-primary-400 dark:hover:text-primary-300"
                  >
                    {{ websiteHost }}
                    <svg
                      class="h-3 w-3"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke-width="2"
                      stroke="currentColor"
                      aria-hidden="true"
                    >
                      <path
                        stroke-linecap="round"
                        stroke-linejoin="round"
                        d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25"
                      />
                    </svg>
                  </a>
                </dd>
              </div>
              <div v-if="company.technologies && company.technologies.length > 0">
                <dt
                  class="font-mono text-xs uppercase tracking-[0.2em] text-slate-500 dark:text-slate-400"
                >
                  {{ techHeading }}
                </dt>
                <dd class="mt-2.5 flex flex-wrap gap-2">
                  <span
                    v-for="tech in company.technologies"
                    :key="tech"
                    class="badge inline-flex items-center rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700 dark:bg-slate-800/60 dark:text-slate-300"
                  >
                    {{ tech }}
                  </span>
                </dd>
              </div>
            </dl>
            <div class="mt-6 border-t border-slate-200 pt-5 dark:border-slate-800">
              <router-link
                to="/#experience"
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
                Back to portfolio
              </router-link>
            </div>
          </div>
        </aside>

        <!-- Main content column. Outcomes lead (the recruiter-facing
             evidence, D3-UX-03); employer marketing media is demoted to the
             bottom, below all role content. -->
        <div class="mt-12 lg:col-start-1 lg:row-start-2 lg:mt-14">
          <!-- Outcomes -->
          <section
            v-if="company.outcomes && company.outcomes.length > 0"
            class="experience-section mb-12"
          >
            <div
              class="rounded-2xl border border-slate-200 bg-slate-50/80 p-6 sm:p-7 dark:border-slate-800 dark:bg-slate-900/60"
            >
              <h2 class="text-lg font-semibold tracking-tight text-slate-900 dark:text-white">
                Outcomes
              </h2>
              <ul class="mt-4 space-y-3">
                <li
                  v-for="(outcome, index) in company.outcomes"
                  :key="`outcome-${index}-${outcome.slice(0, 20)}`"
                  class="flex gap-3 leading-relaxed text-slate-700 dark:text-slate-300"
                >
                  <span
                    class="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-primary-500"
                    aria-hidden="true"
                  ></span>
                  {{ outcome }}
                </li>
              </ul>
            </div>
          </section>

          <!-- Description -->
          <section class="experience-section mb-12">
            <h2 class="text-lg font-semibold tracking-tight text-slate-900 dark:text-white">
              About {{ company.name }}
            </h2>
            <div
              class="prose-content mt-4 max-w-prose space-y-4 leading-relaxed text-slate-700 dark:text-slate-300"
              v-html="formatDescription(company.description)"
            ></div>
          </section>

          <!-- Detailed Description -->
          <section v-if="company.detailed_description" class="experience-section mb-12">
            <h2 class="text-lg font-semibold tracking-tight text-slate-900 dark:text-white">
              The role
            </h2>
            <div
              class="prose-content mt-4 max-w-prose space-y-4 leading-relaxed text-slate-700 dark:text-slate-300"
              v-html="formatDescription(company.detailed_description)"
            ></div>
          </section>

          <!-- Responsibilities List — two-column card list on sm+ -->
          <section
            v-if="company.responsibilities && company.responsibilities.length > 0"
            class="experience-section mb-12"
          >
            <h2 class="text-lg font-semibold tracking-tight text-slate-900 dark:text-white">
              Key responsibilities
            </h2>
            <ul class="mt-4 grid gap-3 sm:grid-cols-2">
              <li
                v-for="(responsibility, index) in company.responsibilities"
                :key="`responsibility-${index}-${responsibility.slice(0, 20)}`"
                class="list-group-item rounded-xl border border-slate-200 p-4 text-sm leading-relaxed text-slate-700 dark:border-slate-800 dark:text-slate-300"
              >
                {{ responsibility }}
              </li>
            </ul>
          </section>

          <!-- Media — demoted below all role content (D3-UX-03): employer
               marketing video and office map are context, not evidence. -->
          <section v-if="company.video_url || company.map_url" class="experience-section mb-12">
            <h2 class="text-lg font-semibold tracking-tight text-slate-900 dark:text-white">
              Media
            </h2>
            <div
              class="mt-4 grid gap-6"
              :class="company.video_url && company.map_url ? 'md:grid-cols-2' : 'md:max-w-xl'"
            >
              <VideoEmbed
                v-if="company.video_url"
                :url="company.video_url"
                :heading="company.video_title || `${company.name} Video`"
                :title="company.video_title || `${company.name} Video`"
              />
              <MapEmbed
                v-if="company.map_url"
                :url="company.map_url"
                :heading="company.map_title || `${company.name} Location`"
                :title="company.map_title || `${company.name} Location Map`"
              />
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
        </div>
      </article>
    </main>

    <FooterSection />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onServerPrefetch, onUnmounted, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { useHead } from '@unhead/vue'
import axios, { type AxiosError } from 'axios'
import type { Company } from '@/types'
import { apiLogger } from '../../utils/logger'
import { useExperienceDetailStore } from '../../stores/experienceDetail'
import { useIntersectionAnimation } from '@/composables/useIntersectionAnimation'
import VideoEmbed from '@/components/VideoEmbed.vue'
import MapEmbed from '@/components/MapEmbed.vue'
import NavBar from '@/components/NavBar.vue'
import FooterSection from '@/components/FooterSection.vue'
import { formatDescription } from '@/utils/markdown'

// AbortController for cancelling pending requests on route change
let fetchAbortController: AbortController | null = null

// D3-PERF-01: entrance animations are the same IntersectionObserver +
// CSS-transition pattern as HomeView (PERF-03 there) — this page was the
// last gsap consumer, and 27KB gzip for five fade-ups on the site's SEO
// entry pages wasn't paying rent. Must be called in synchronous setup:
// the composable registers its own lifecycle hooks (see its NOTE).
const sectionAnimation = useIntersectionAnimation('.experience-section', { stagger: 0.1 })
const itemAnimation = useIntersectionAnimation('.list-group-item', { stagger: 0.06 })

// Hand freshly rendered sections to the observer after content settles
// (route change or async load — mount-time content is caught by the
// composables' own onMounted scan).
const refreshAnimations = (): void => {
  void nextTick(() => {
    sectionAnimation.refresh()
    itemAnimation.refresh()
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
const notFound = ref<boolean>(false)
const logoError = ref<boolean>(false)

// Per-route head tags — reactive so SSG renders the correct title/canonical
// for each page. D3-CNT-02: titles carry the position + start year (the year
// also de-dupes the two Scania stints), and every detail page gets its own
// og/twitter tags — before this, shares of any detail URL scraped the
// homepage's card and og:url pointed the share back at dashti.se.
const truncateAtWord = (text: string, max = 155): string => {
  if (text.length <= max) return text
  const cut = text.slice(0, max)
  return `${cut.slice(0, cut.lastIndexOf(' '))}…`
}

const pageTitle = computed(() =>
  notFound.value
    ? '404 — Experience Not Found | David Dashti'
    : company.value
      ? `${company.value.title} at ${company.value.name} (${new Date(
          company.value.start_date
        ).getFullYear()}) | David Dashti`
      : 'Experience | David Dashti'
)
const metaDescription = computed(() =>
  truncateAtWord(company.value?.description || 'Experience details')
)
const SOFT_SKILL_CHIPS = new Set([
  'leadership',
  'strategic planning',
  'team management',
  'crisis management',
  'training development',
  'communication',
  'mentoring'
])
// D3-CNT-01: non-technical roles (FDF) list soft skills under a heading
// that used to claim they were technologies. Data-aware: the heading
// flips when every chip is a known soft skill.
const techHeading = computed(() => {
  const techs = company.value?.technologies ?? []
  const allSoft = techs.length > 0 && techs.every(t => SOFT_SKILL_CHIPS.has(t.toLowerCase()))
  return allSoft ? 'Skills applied' : 'Technologies'
})

// Rail website link shows the bare host — "hermesmedical.com" reads better
// in a 300px column than a generic "Visit Website" button.
const websiteHost = computed(() => {
  if (!company.value?.website) return null
  try {
    return new URL(company.value.website).hostname.replace(/^www\./, '')
  } catch {
    return 'Website'
  }
})

const canonicalUrl = computed(() => `https://dashti.se/experience/${companyId.value}`)

useHead({
  title: pageTitle,
  meta: [
    {
      name: 'description',
      content: metaDescription
    },
    { property: 'og:title', content: pageTitle },
    { property: 'og:description', content: metaDescription },
    { property: 'og:url', content: canonicalUrl },
    { property: 'og:type', content: 'article' },
    { name: 'twitter:title', content: pageTitle },
    { name: 'twitter:description', content: metaDescription },
    // Unknown IDs are served 200 by the SPA rewrite — noindex is the honest
    // crawler signal for the not-found state (D3-UX-01).
    {
      name: 'robots',
      content: computed(() => (notFound.value ? 'noindex' : 'index, follow'))
    }
  ],
  link: [
    {
      rel: 'canonical',
      href: canonicalUrl
    }
  ],
  script: [
    {
      type: 'application/ld+json',
      // D3-SEO-02: breadcrumb trail for the detail pages (SERP context)
      innerHTML: computed(() =>
        JSON.stringify({
          '@context': 'https://schema.org',
          '@type': 'BreadcrumbList',
          itemListElement: [
            { '@type': 'ListItem', position: 1, name: 'Home', item: 'https://dashti.se/' },
            {
              '@type': 'ListItem',
              position: 2,
              name: 'Experience',
              item: 'https://dashti.se/#experience'
            },
            {
              '@type': 'ListItem',
              position: 3,
              name: company.value?.name ?? 'Experience detail',
              item: canonicalUrl.value
            }
          ]
        })
      )
    }
  ]
})

// Format date helper
const formatDate = (dateString: string | null | undefined): string => {
  if (!dateString) return ''
  const date = new Date(dateString)
  // timeZone UTC: date-only strings parse as UTC midnight (see HomeView)
  return date.toLocaleDateString('en-US', { month: 'short', year: 'numeric', timeZone: 'UTC' })
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
  notFound.value = false
  logoError.value = false // Reset logo error state for new company

  if (experienceStore.byId[id]) {
    loading.value = false
    refreshAnimations()
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
      // Definitive: the ID doesn't exist — a 404 state, not an error banner
      notFound.value = true
    } else {
      error.value = "The server couldn't be reached. Check your connection and try again."
    }
  } finally {
    loading.value = false
    // Observe the freshly rendered sections after DOM updates
    if (!error.value && experienceStore.byId[id]) {
      refreshAnimations()
    }
  }
}

// Retry after a transient failure (the "Try again" button in the error state)
const retry = (): void => {
  if (companyId.value) {
    void loadCompany(companyId.value)
  }
}

// SSG: fetch the company during server-side render so the useHead computed
// above resolves to the per-route title/description before vite-ssg captures
// the rendered HTML and head tags. The store state is then serialized into
// the page (see main.ts) and hydrated on the client. onServerPrefetch (not a
// top-level `await` in an SSR-only branch) is deliberate: any top-level
// await compiles setup() to an async function even when the branch is dead
// on the client, and an async setup() under App.vue's route <Transition>
// makes Vue throw away the prerendered DOM on direct page loads and
// re-render client-side — blanking the page until data arrives.
onServerPrefetch(async () => {
  if (companyId.value) {
    await loadCompany(companyId.value)
  }
})

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

// Cleanup: cancel pending requests on unmount (the animation composables
// disconnect their own observers in onBeforeUnmount)
onUnmounted(() => {
  if (fetchAbortController) {
    fetchAbortController.abort()
    fetchAbortController = null
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

/*
 * D3-PERF-01: entrance animations driven by useIntersectionAnimation —
 * same recipe as HomeView's PERF-03 block. `[data-anim="hidden"]` is set
 * on mount; the observer flips elements to `[data-anim="visible"]` as
 * they enter the viewport. Transition lives on [data-anim] (both states)
 * so the reveal doesn't snap, and border/bg/color are included so cards
 * whose transition-colors utility this rule overrides keep hover
 * feedback.
 */
[data-anim] {
  transition:
    opacity 0.5s ease-out,
    transform 0.5s ease-out,
    border-color 0.2s ease,
    background-color 0.2s ease,
    color 0.2s ease;
}

[data-anim='hidden'] {
  opacity: 0;
  transform: translate3d(0, 24px, 0);
  will-change: opacity, transform;
}

[data-anim='visible'] {
  opacity: 1;
  transform: translate3d(0, 0, 0);
  will-change: auto;
}

@media (prefers-reduced-motion: reduce) {
  [data-anim] {
    transition: none !important;
    transform: none !important;
  }
}
</style>
