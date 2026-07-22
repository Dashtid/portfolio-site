<template>
  <div
    class="cv-document cv-page mx-auto max-w-3xl bg-white px-8 py-10 text-slate-900 dark:bg-slate-950 dark:text-slate-100 print:max-w-none print:px-0 print:py-0"
  >
    <!-- Header -->
    <header class="border-b border-slate-200 pb-8 dark:border-slate-800">
      <h1 class="text-title font-semibold text-slate-900 dark:text-white">
        {{ resume.basics.name }}
      </h1>
      <p v-if="resume.basics.label" class="mt-1 text-lg text-slate-600 dark:text-slate-300">
        {{ resume.basics.label }}
      </p>

      <!-- Location + public links -->
      <p
        class="mt-2 font-mono text-xs uppercase tracking-[0.15em] text-slate-500 dark:text-slate-400"
      >
        <template v-if="resume.basics.location?.city">
          {{ resume.basics.location.city
          }}<template v-if="resume.basics.location.countryCode"
            >, {{ resume.basics.location.countryCode }}</template
          >
        </template>
        <template v-for="profile in resume.basics.profiles || []" :key="profile.network">
          &middot;
          <a
            :href="profile.url"
            target="_blank"
            rel="noopener noreferrer"
            class="text-primary-600 hover:text-primary-700 dark:text-primary-400"
            >{{ profile.network }}</a
          >
        </template>
        <template v-if="displayUrl"> &middot; {{ displayUrl }}</template>
      </p>

      <!-- Private contact — only rendered when present. The public site never
           shows these; they exist so the downloaded CV is complete. -->
      <p v-if="hasPrivateContact" class="mt-1 font-mono text-xs text-slate-500 dark:text-slate-400">
        <template v-if="resume.basics.email">{{ resume.basics.email }}</template>
        <template v-if="resume.basics.phone">
          <template v-if="resume.basics.email"> &middot; </template>{{ resume.basics.phone }}
        </template>
        <template v-if="resume.basics.personalNumber">
          <template v-if="resume.basics.email || resume.basics.phone"> &middot; </template
          >{{ resume.basics.personalNumber }}
        </template>
      </p>

      <p
        v-if="resume.basics.summary"
        class="mt-6 max-w-2xl leading-relaxed text-slate-600 dark:text-slate-300"
      >
        {{ resume.basics.summary }}
      </p>

      <div v-if="resume.basics.focus" class="mt-4">
        <p class="font-mono text-xs uppercase tracking-[0.15em] text-slate-500 dark:text-slate-400">
          Current focus
        </p>
        <p class="mt-1 max-w-2xl text-sm leading-relaxed text-slate-600 dark:text-slate-300">
          {{ resume.basics.focus }}
        </p>
      </div>
    </header>

    <!-- Experience -->
    <section v-if="resume.work.length" class="mt-10">
      <h2 class="cv-heading">Experience</h2>
      <div class="mt-5 space-y-8">
        <article v-for="job in resume.work" :key="`${job.name}-${job.startDate}`">
          <div class="flex flex-wrap items-baseline justify-between gap-x-4">
            <h3 class="font-semibold text-slate-900 dark:text-white">{{ job.position }}</h3>
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
    <section v-if="resume.skills.length" class="mt-10">
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
    <section v-if="resume.education.length" class="mt-10">
      <h2 class="cv-heading">Education</h2>
      <div class="mt-5 space-y-6">
        <article v-for="edu in resume.education" :key="`${edu.institution}-${edu.startDate}`">
          <div class="flex flex-wrap items-baseline justify-between gap-x-4">
            <h3 class="font-semibold text-slate-900 dark:text-white">
              {{ edu.studyType }}<template v-if="edu.area">, {{ edu.area }}</template>
            </h3>
            <p class="font-mono text-xs text-slate-500 dark:text-slate-400">
              {{ formatYm(edu.startDate) }} —
              {{ edu.endDate ? formatYm(edu.endDate) : 'Present' }}
            </p>
          </div>
          <p class="mt-0.5 text-sm text-slate-500 dark:text-slate-400">{{ edu.institution }}</p>
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
    <section v-if="resume.certificates.length" class="mt-10">
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
              class="font-medium text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300"
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
    <section v-if="resume.languages.length" class="mt-10">
      <h2 class="cv-heading">Languages</h2>
      <p class="mt-4 text-sm text-slate-600 dark:text-slate-300">
        <template v-for="(lang, index) in resume.languages" :key="lang.language">
          <template v-if="index > 0"> &middot; </template>
          {{ lang.language }} ({{ lang.fluency }})
        </template>
      </p>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted } from 'vue'
import type { CvResume } from '@/types/cv'

const props = defineProps<{ resume: CvResume }>()

// Strip the protocol for a compact printed URL ("dashti.se").
const displayUrl = computed<string>(() =>
  (props.resume.basics.url || '').replace(/^https?:\/\//, '').replace(/\/$/, '')
)

const hasPrivateContact = computed<boolean>(
  () =>
    !!(props.resume.basics.email || props.resume.basics.phone || props.resume.basics.personalNumber)
)

const formatYm = (ym: string): string => {
  if (!ym) return ''
  const [year, month] = ym.split('-')
  if (!month) return year
  const date = new Date(Number(year), Number(month) - 1, 1)
  return date.toLocaleDateString('en-US', { month: 'short', year: 'numeric' })
}

// Printing from dark mode would emit a near-black PDF: the dark: variant keys
// on <html data-theme>, which print media does not reset. Force light around
// the print pass (covers the Print button and Ctrl+P alike), then restore.
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
   (owner prints to PDF from the admin CV page). */
@media print {
  .cv-page {
    font-size: 11px;
    color: #000;
    background: #fff;
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
