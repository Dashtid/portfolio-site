<template>
  <div class="min-h-screen bg-white text-slate-900 dark:bg-slate-950 dark:text-slate-100">
    <NavBar class="print:hidden" />

    <main id="main-content" tabindex="-1" class="pt-24 print:pt-0">
      <div class="cv-page mx-auto max-w-3xl px-6 py-12 print:max-w-none print:px-0 print:py-0">
        <!-- Header: contact stays LinkedIn/GitHub-only (openQuestions #4:
             public CV is the medtech variant with contact details scrubbed) -->
        <header class="border-b border-slate-200 pb-8 dark:border-slate-800">
          <div class="flex flex-wrap items-start justify-between gap-4">
            <div>
              <h1 class="text-title font-semibold text-slate-900 dark:text-white">
                {{ resume.basics.name }}
              </h1>
              <p class="mt-1 text-lg text-slate-600 dark:text-slate-300">
                {{ resume.basics.label }}
              </p>
              <p
                class="mt-2 font-mono text-xs uppercase tracking-[0.15em] text-slate-500 dark:text-slate-400"
              >
                {{ resume.basics.location.city }}, {{ resume.basics.location.countryCode }}
                &middot;
                <a
                  href="https://www.linkedin.com/in/david-dashti/"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="text-primary-600 hover:text-primary-700 dark:text-primary-400"
                  >LinkedIn</a
                >
                &middot;
                <a
                  href="https://github.com/Dashtid"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="text-primary-600 hover:text-primary-700 dark:text-primary-400"
                  >GitHub</a
                >
                &middot; dashti.se
              </p>
            </div>
            <div class="flex gap-2 print:hidden">
              <button
                type="button"
                class="inline-flex items-center gap-2 rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-primary-700 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-primary-500 dark:bg-primary-500 dark:text-slate-950 dark:hover:bg-primary-400"
                @click="printCv"
              >
                Download PDF
              </button>
              <a
                href="/cv.json"
                class="inline-flex items-center gap-2 rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 transition-colors hover:border-primary-400/60 hover:text-primary-600 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-primary-500 dark:border-slate-800 dark:text-slate-200 dark:hover:border-primary-400/40 dark:hover:text-primary-400"
              >
                JSON
              </a>
            </div>
          </div>
          <p class="mt-6 max-w-2xl leading-relaxed text-slate-600 dark:text-slate-300">
            {{ resume.basics.summary }}
          </p>
          <!-- Forward-looking defensive-first framing (no offensive-cert
               target): Security+ is the earned credential in Certificates;
               this line states the direction. -->
          <div v-if="resume.basics.focus" class="mt-4">
            <p
              class="font-mono text-xs uppercase tracking-[0.15em] text-slate-500 dark:text-slate-400"
            >
              Current focus
            </p>
            <p class="mt-1 max-w-2xl text-sm leading-relaxed text-slate-600 dark:text-slate-300">
              {{ resume.basics.focus }}
            </p>
          </div>
        </header>

        <!-- Experience -->
        <section class="mt-10">
          <h2 class="cv-heading">Experience</h2>
          <div class="mt-5 space-y-8">
            <article v-for="job in visibleWork" :key="`${job.name}-${job.startDate}`">
              <div class="flex flex-wrap items-baseline justify-between gap-x-4">
                <h3 class="font-semibold text-slate-900 dark:text-white">
                  {{ job.position }}
                </h3>
                <p class="font-mono text-xs text-slate-500 dark:text-slate-400">
                  {{ formatYm(job.startDate) }} —
                  {{ job.endDate ? formatYm(job.endDate) : 'Present' }}
                </p>
              </div>
              <p class="mt-0.5 text-sm text-slate-500 dark:text-slate-400">
                {{ job.name }}<template v-if="job.location"> &middot; {{ job.location }}</template>
              </p>
              <ul v-if="job.highlights && job.highlights.length" class="mt-3 space-y-2">
                <li
                  v-for="(highlight, index) in job.highlights"
                  :key="index"
                  class="flex gap-3 text-sm leading-relaxed text-slate-600 dark:text-slate-300"
                >
                  <span
                    class="mt-2 h-1 w-1 shrink-0 rounded-full bg-primary-500"
                    aria-hidden="true"
                  ></span>
                  {{ highlight }}
                </li>
              </ul>
            </article>
          </div>
        </section>

        <!-- Skills -->
        <section class="mt-10">
          <h2 class="cv-heading">Skills</h2>
          <div class="mt-5 space-y-4">
            <div v-for="group in resume.skills" :key="group.name">
              <p class="text-sm font-medium text-slate-900 dark:text-white">{{ group.name }}</p>
              <div class="mt-2 flex flex-wrap gap-2">
                <span
                  v-for="keyword in group.keywords"
                  :key="keyword"
                  class="inline-flex items-center rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700 dark:bg-slate-800/60 dark:text-slate-300"
                >
                  {{ keyword }}
                </span>
              </div>
            </div>
          </div>
        </section>

        <!-- Education -->
        <section class="mt-10">
          <h2 class="cv-heading">Education</h2>
          <div class="mt-5 space-y-6">
            <article v-for="edu in resume.education" :key="edu.institution">
              <div class="flex flex-wrap items-baseline justify-between gap-x-4">
                <h3 class="font-semibold text-slate-900 dark:text-white">
                  {{ edu.studyType }}, {{ edu.area }}
                </h3>
                <p class="font-mono text-xs text-slate-500 dark:text-slate-400">
                  {{ formatYm(edu.startDate) }} — {{ formatYm(edu.endDate) }}
                </p>
              </div>
              <p class="mt-0.5 text-sm text-slate-500 dark:text-slate-400">
                {{ edu.institution }}
              </p>
              <p
                v-for="course in edu.courses ?? []"
                :key="course"
                class="mt-2 text-sm leading-relaxed text-slate-600 dark:text-slate-300"
              >
                {{ course }}
              </p>
            </article>
          </div>
        </section>

        <!-- Certificates -->
        <section class="mt-10">
          <h2 class="cv-heading">Certificates</h2>
          <ul class="mt-5 space-y-3">
            <li
              v-for="cert in resume.certificates"
              :key="cert.name"
              class="flex flex-wrap items-baseline justify-between gap-x-4"
            >
              <span class="text-sm text-slate-700 dark:text-slate-200">
                <a
                  v-if="cert.url"
                  :href="cert.url"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="font-medium text-primary-600 hover:text-primary-700 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-primary-500 dark:text-primary-400 dark:hover:text-primary-300"
                >
                  {{ cert.name }}
                </a>
                <span v-else class="font-medium">{{ cert.name }}</span>
                &middot; {{ cert.issuer }}
              </span>
              <span class="font-mono text-xs text-slate-500 dark:text-slate-400">
                {{ formatYm(cert.date) }}
              </span>
            </li>
          </ul>
        </section>

        <!-- Languages -->
        <section class="mt-10">
          <h2 class="cv-heading">Languages</h2>
          <p class="mt-4 text-sm text-slate-600 dark:text-slate-300">
            <template v-for="(lang, index) in resume.languages" :key="lang.language">
              <template v-if="index > 0"> &middot; </template>
              {{ lang.language }} ({{ lang.fluency }})
            </template>
          </p>
        </section>

        <footer
          class="mt-12 flex items-center justify-between border-t border-slate-200 pt-8 dark:border-slate-800 print:hidden"
        >
          <router-link
            to="/"
            class="inline-flex items-center gap-1 text-sm font-medium text-primary-600 transition-all hover:gap-2 hover:text-primary-700 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-primary-500 dark:text-primary-400 dark:hover:text-primary-300"
          >
            Back to Portfolio
          </router-link>
          <p class="font-mono text-xs text-slate-400 dark:text-slate-500">
            Also machine-readable at /cv.json
          </p>
        </footer>
      </div>
    </main>

    <FooterSection class="print:hidden" />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted } from 'vue'
import { useHead } from '@unhead/vue'
import NavBar from '@/components/NavBar.vue'
import FooterSection from '@/components/FooterSection.vue'
// One IP-clean source of truth (FEAT-001): cv/resume.json at the repo
// root, kept consistent with LinkedIn. The public /cv.json emitted at
// build time is the scrubbed machine-readable copy (see vite.config.ts).
import resumeData from '../../../cv/resume.json'

interface WorkEntry {
  name: string
  position: string
  location?: string
  startDate: string
  endDate?: string
  highlights?: string[]
  /** FEAT-001 variant mechanism: absent = all variants */
  variants?: string[]
}

interface Resume {
  basics: {
    name: string
    label: string
    summary: string
    focus?: string
    location: { city: string; countryCode: string }
  }
  work: WorkEntry[]
  education: Array<{
    institution: string
    area: string
    studyType: string
    startDate: string
    endDate: string
    courses?: string[]
  }>
  certificates: Array<{ name: string; date: string; issuer: string; url?: string }>
  skills: Array<{ name: string; keywords: string[] }>
  languages: Array<{ language: string; fluency: string }>
}

const resume = resumeData as unknown as Resume

// FEAT-001 variant mechanism, designed in even though only the medtech
// variant is public (openQuestions #4): entries may carry
// `variants: ["medtech", "fintech"]`; entries without the field appear
// everywhere. The fintech/cloud variant would ship as a second route
// with a different ACTIVE_VARIANT — never published from this repo.
const ACTIVE_VARIANT = 'medtech'
const visibleWork = computed(() =>
  resume.work.filter(job => !job.variants || job.variants.includes(ACTIVE_VARIANT))
)

const CV_DESCRIPTION =
  'CV of David Dashti — product security for regulated medical software: threat modeling, FDA premarket cybersecurity, IEC 81001-5-1, SBOM and vulnerability management.'

useHead({
  title: 'CV — David Dashti | Product Security for Medical Software',
  meta: [
    { name: 'description', content: CV_DESCRIPTION },
    // Full og/twitter override set: any key left unset here keeps the
    // homepage values hardcoded in index.html — shares of /cv would card
    // as the homepage (the exact regression D3-CNT-02 fixed for the
    // experience pages).
    { property: 'og:title', content: 'CV — David Dashti' },
    { property: 'og:description', content: CV_DESCRIPTION },
    { property: 'og:url', content: 'https://dashti.se/cv' },
    { property: 'og:type', content: 'profile' },
    { name: 'twitter:title', content: 'CV — David Dashti' },
    { name: 'twitter:description', content: CV_DESCRIPTION }
  ],
  link: [{ rel: 'canonical', href: 'https://dashti.se/cv' }]
})

// Printing from dark mode would emit a near-black PDF: the dark: variant
// keys on <html data-theme>, which print media does not reset. Force the
// light theme around the print pass (covers both the button and Ctrl+P
// via the beforeprint/afterprint events).
let themeBeforePrint: string | null = null
const forceLightForPrint = (): void => {
  themeBeforePrint = document.documentElement.getAttribute('data-theme')
  document.documentElement.setAttribute('data-theme', 'light')
}
const restoreThemeAfterPrint = (): void => {
  if (themeBeforePrint) {
    document.documentElement.setAttribute('data-theme', themeBeforePrint)
  }
  themeBeforePrint = null
}

onMounted(() => {
  window.addEventListener('beforeprint', forceLightForPrint)
  window.addEventListener('afterprint', restoreThemeAfterPrint)
})

onUnmounted(() => {
  window.removeEventListener('beforeprint', forceLightForPrint)
  window.removeEventListener('afterprint', restoreThemeAfterPrint)
})

const printCv = (): void => {
  window.print()
}

const formatYm = (ym: string): string => {
  const [year, month] = ym.split('-')
  if (!month) return year
  const date = new Date(Number(year), Number(month) - 1, 1)
  return date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' })
}
</script>

<style scoped>
.cv-heading {
  font-family: var(--font-mono, monospace);
  font-size: 0.75rem;
  font-weight: 400;
  text-transform: uppercase;
  letter-spacing: 0.2em;
  color: var(--text-secondary);
}

/* Print: compact black-on-white single column — this IS the PDF path
   (FEAT-001: "a print stylesheet producing the PDF"). */
@media print {
  .cv-page {
    font-size: 11px;
    color: #000;
  }

  .cv-page :deep(a) {
    color: #000;
    text-decoration: none;
  }

  section {
    break-inside: avoid;
  }
}
</style>
