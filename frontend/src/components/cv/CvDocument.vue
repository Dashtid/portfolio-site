<template>
  <!-- The CV is a DOCUMENT, not a page section: it renders as a white A4 sheet
       on screen exactly as it prints, so the admin preview is truthful. That is
       also why no dark: variants appear below — a document does not invert. -->
  <div class="cv-page">
    <!-- Header: name/contact block on the left, headshot on the right. The photo
         is optional; without it the left block simply spans the full width. -->
    <header class="cv-header" :class="{ 'cv-header--with-photo': resume.basics.image }">
      <div class="cv-identity">
        <h1 class="cv-name">{{ resume.basics.name }}</h1>
        <p v-if="resume.basics.label" class="cv-label">{{ resume.basics.label }}</p>

        <dl class="cv-contact">
          <template v-if="resume.basics.phone">
            <dt>Phone</dt>
            <dd>{{ resume.basics.phone }}</dd>
          </template>
          <template v-if="resume.basics.email">
            <dt>Email</dt>
            <dd>{{ resume.basics.email }}</dd>
          </template>
          <template v-if="linkedInUrl">
            <dt>LinkedIn</dt>
            <dd>
              <a :href="linkedInUrl">{{ stripProtocol(linkedInUrl) }}</a>
            </dd>
          </template>
          <template v-if="gitHubUrl">
            <dt>GitHub</dt>
            <dd>
              <a :href="gitHubUrl">{{ stripProtocol(gitHubUrl) }}</a>
            </dd>
          </template>
          <template v-if="resume.basics.url">
            <dt>Web</dt>
            <dd>
              <a :href="resume.basics.url">{{ stripProtocol(resume.basics.url) }}</a>
            </dd>
          </template>
          <template v-if="locationLine">
            <dt>Location</dt>
            <dd>{{ locationLine }}</dd>
          </template>
          <template v-if="resume.basics.personalNumber">
            <dt>Personal no.</dt>
            <dd>{{ resume.basics.personalNumber }}</dd>
          </template>
        </dl>
      </div>

      <img v-if="resume.basics.image" class="cv-photo" :src="resume.basics.image" alt="" />
    </header>

    <!-- Profile -->
    <section v-if="resume.basics.summary || resume.basics.focus" class="cv-section">
      <h2 class="cv-section-title">Profile</h2>
      <p v-if="resume.basics.summary" class="cv-prose">{{ resume.basics.summary }}</p>
      <p v-if="resume.basics.focus" class="cv-prose cv-prose--tight">
        <span class="cv-inline-label">Current focus</span>{{ resume.basics.focus }}
      </p>
    </section>

    <!-- Work experience -->
    <section v-if="resume.work.length" class="cv-section">
      <h2 class="cv-section-title">Work experience</h2>
      <article v-for="job in resume.work" :key="`${job.name}-${job.startDate}`" class="cv-entry">
        <div class="cv-meta">
          <span class="cv-meta-line">{{ dateRange(job.startDate, job.endDate) }}</span>
          <span v-if="job.location" class="cv-meta-line">{{ job.location }}</span>
        </div>
        <div class="cv-body">
          <h3 class="cv-entry-title">{{ job.position }}</h3>
          <p class="cv-entry-org">{{ job.name }}</p>
          <ul v-if="job.highlights?.length" class="cv-bullets">
            <li v-for="(highlight, index) in job.highlights" :key="index">{{ highlight }}</li>
          </ul>
        </div>
      </article>
    </section>

    <!-- Education -->
    <section v-if="resume.education.length" class="cv-section">
      <h2 class="cv-section-title">Education</h2>
      <article
        v-for="edu in resume.education"
        :key="`${edu.institution}-${edu.startDate}`"
        class="cv-entry"
      >
        <div class="cv-meta">
          <span class="cv-meta-line">{{ dateRange(edu.startDate, edu.endDate) }}</span>
          <span v-if="edu.location" class="cv-meta-line">{{ edu.location }}</span>
        </div>
        <div class="cv-body">
          <h3 class="cv-entry-title">
            {{ edu.area || edu.studyType
            }}<template v-if="edu.area && edu.studyType"> | {{ edu.studyType }}</template>
          </h3>
          <p class="cv-entry-org">{{ edu.institution }}</p>
          <p v-for="course in edu.courses ?? []" :key="course" class="cv-prose cv-prose--entry">
            {{ course }}
          </p>
          <p v-if="edu.url" class="cv-prose cv-prose--entry">
            <a :href="edu.url">{{ shortUrl(edu.url) }}</a>
          </p>
        </div>
      </article>
    </section>

    <!-- Certificates -->
    <section v-if="resume.certificates.length" class="cv-section">
      <h2 class="cv-section-title">Certificates</h2>
      <article v-for="cert in resume.certificates" :key="cert.name" class="cv-entry">
        <div class="cv-meta">
          <span class="cv-meta-line">{{ formatYm(cert.date) }}</span>
        </div>
        <div class="cv-body">
          <h3 class="cv-entry-title">{{ cert.name }}</h3>
          <p class="cv-entry-org">{{ cert.issuer }}</p>
          <p v-if="cert.url" class="cv-prose cv-prose--entry">
            <a :href="cert.url">{{ shortUrl(cert.url) }}</a>
          </p>
        </div>
      </article>
    </section>

    <!-- Skills — left-aligned runs rather than a centred grid: ragged phrases
         centred in fixed columns wrap badly and waste most of a page. -->
    <section v-if="resume.skills.length" class="cv-section">
      <h2 class="cv-section-title">Skills</h2>
      <div class="cv-skill-columns">
        <div v-for="group in resume.skills" :key="group.name" class="cv-skill-group">
          <p class="cv-skill-label">{{ group.name }}</p>
          <p class="cv-skill-items">{{ group.keywords.join(' · ') }}</p>
        </div>
        <!-- Languages ride here as one more labelled run rather than owning a
             section: a full centred heading + rule for one short line pushed
             the tail of the CV onto an otherwise empty page. The reference CV
             does the same thing. -->
        <div v-if="resume.languages.length" class="cv-skill-group">
          <p class="cv-skill-label">Languages</p>
          <p class="cv-skill-items">
            <template v-for="(lang, index) in resume.languages" :key="lang.language">
              <template v-if="index > 0"> · </template>
              <span class="cv-lang-name">{{ lang.language }}</span> ({{ lang.fluency }})
            </template>
          </p>
        </div>
      </div>
    </section>

    <!-- Other (Övrigt) — logistics one-liners such as B-körkort. Deliberately
         LAST and structurally separate from Certificates: these are logistics
         facts, not credentials. -->
    <section v-if="resume.other?.length" class="cv-section">
      <h2 class="cv-section-title">Other</h2>
      <div class="cv-skill-group">
        <p class="cv-skill-items">{{ resume.other.join(' · ') }}</p>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { CvResume } from '@/types/cv'

const props = defineProps<{ resume: CvResume }>()

const stripProtocol = (url: string): string =>
  (url || '').replace(/^https?:\/\//, '').replace(/\/$/, '')

// Long credential URLs (Credly, trueoriginal) wrap to two lines and read as
// noise. Keep the host plus a recognisable stub so the credential is still
// verifiable on paper, and let the anchor carry the full href on screen.
const shortUrl = (url: string): string => {
  const bare = stripProtocol(url).replace(/^www\./, '')
  const [host, ...rest] = bare.split('/')
  const path = rest.join('/').split('?')[0]
  if (!path) return host
  const stub = path.length > 24 ? `${path.slice(0, 24)}…` : path
  return `${host}/${stub}`
}

const profileUrl = (network: string): string =>
  props.resume.basics.profiles?.find(p => p.network?.toLowerCase() === network)?.url || ''

const linkedInUrl = computed<string>(() => profileUrl('linkedin'))
const gitHubUrl = computed<string>(() => profileUrl('github'))

const locationLine = computed<string>(() => {
  const loc = props.resume.basics.location
  if (!loc) return ''
  return [loc.city, loc.countryCode].filter(Boolean).join(', ')
})

// Numeric MM/YYYY throughout — "05/2024 – present" reads as a CV; "May 2024"
// wastes the narrow meta column and wraps.
const formatYm = (ym: string): string => {
  if (!ym) return ''
  const [year, month] = ym.split('-')
  return month ? `${month.padStart(2, '0')}/${year}` : year
}

const dateRange = (start: string, end?: string): string => {
  const from = formatYm(start)
  const to = end ? formatYm(end) : 'present'
  return from ? `${from} – ${to}` : to
}
</script>

<style scoped>
/* ---------------------------------------------------------------------------
   Geometry is taken from the owner's reference CV, measured out of the PDF:
   A4 794x1123px @96dpi, 62px side margins, a 670px content column, a 168px
   meta rail, and a 17px vertical grid. Sizes are px (not rem) because the
   sheet is a fixed-size document and must not inherit the admin shell's scale.

   Two colours only: #000 for structure, #3d3d3d for prose.
--------------------------------------------------------------------------- */
.cv-page {
  --ink: #000;
  --prose: #3d3d3d;
  --rail: 168px;
  --grid: 17px;

  box-sizing: border-box;
  width: 794px;
  margin: 0 auto;
  padding: 37px 62px 27px;
  background: #fff;
  color: var(--prose);
  font-family: 'Roboto', 'Helvetica Neue', Arial, sans-serif;
  font-size: 13px;
  line-height: var(--grid);
  /* A stray line stranded across a page break reads as a printing accident. */
  orphans: 2;
  widows: 2;
}

.cv-page :deep(a) {
  color: inherit;
  text-decoration: none;
}

/* --- Header ------------------------------------------------------------- */
.cv-header {
  display: grid;
  grid-template-columns: 1fr;
}

/* The photo column is 120px wide and bleeds 8px past the text column so its
   right edge lands on the section rules' right edge, as the reference does. */
.cv-header--with-photo {
  grid-template-columns: 1fr 128px;
  column-gap: 24px;
}

.cv-name {
  margin: 0;
  color: var(--ink);
  font-size: 34px;
  font-weight: 700;
  line-height: 1.15;
  letter-spacing: -0.01em;
}

.cv-label {
  margin: 4px 0 0;
  color: var(--ink);
  font-size: 15px;
  font-weight: 700;
}

/* Definition list rather than stacked <p>s: these really are label/value
   pairs, and it gives print and screen readers the same structure. */
.cv-contact {
  display: grid;
  grid-template-columns: max-content 1fr;
  column-gap: 6px;
  margin: 25px 0 0;
  font-size: 13px;
}

.cv-contact dt {
  color: var(--ink);
  font-weight: 700;
}

.cv-contact dd {
  margin: 0;
  color: var(--prose);
}

.cv-photo {
  width: 120px;
  height: 120px;
  margin-left: 8px;
  border-radius: 50%;
  object-fit: cover;
  /* The asset's own backdrop is the grey that shows inside the circle — no
     background is drawn behind it, which would risk a visible seam. */
}

/* --- Sections ----------------------------------------------------------- */
/* 26px rather than the reference's ~40px. At the real print width (670px, not
   the wider on-screen preview) the document came to 2151px against 2118px of
   two-page capacity — it overshot by 33px and emitted a blank third sheet.
   The heading and its rule already separate sections; the extra air was pure
   overflow. Measured headroom after this: ~30px. */
.cv-section {
  margin-top: 26px;
}

.cv-section-title {
  margin: 0 0 10px;
  padding-bottom: 8px;
  /* Bleed the rule 8px past the text column on both sides. */
  width: calc(100% + 16px);
  margin-left: -8px;
  border-bottom: 1px solid var(--ink);
  color: var(--ink);
  font-size: 18px;
  font-weight: 700;
  text-align: center;
}

.cv-prose {
  margin: 0;
  color: var(--prose);
}

.cv-prose--tight {
  margin-top: var(--grid);
}

.cv-prose--entry {
  margin-top: 2px;
}

.cv-inline-label {
  color: var(--ink);
  font-weight: 700;
}

.cv-inline-label::after {
  content: ' – ';
}

/* --- Entries (experience / education / certificates) -------------------- */
.cv-entry {
  display: grid;
  grid-template-columns: var(--rail) 1fr;
  margin-top: 14px;
  /* Keep a whole entry together; the old rule sat on <section>, which can
     never fit one page, so Chrome ignored it and split entries anyway. */
  break-inside: avoid;
}

.cv-entry:first-of-type {
  margin-top: 14px;
}

.cv-meta {
  display: flex;
  flex-direction: column;
  padding-top: 2px;
  color: var(--ink);
  font-size: 11px;
}

.cv-meta-line {
  display: block;
  line-height: var(--grid);
}

.cv-entry-title {
  margin: 0;
  color: var(--ink);
  font-size: 16px;
  font-weight: 700;
  line-height: var(--grid);
}

.cv-entry-org {
  margin: 0;
  color: var(--ink);
  font-size: 15px;
  font-weight: 700;
  line-height: var(--grid);
}

/* --- Bullets ------------------------------------------------------------
   Real list markers, not background-coloured spans: Chrome drops background
   graphics when printing, which is why the previous markers came out white
   (invisible) in the PDF. Foreground ink is never suppressed.
   Item spacing equals wrapped-line spacing — a flat grid, no extra gap. */
.cv-bullets {
  margin: 2px 0 0;
  padding-left: 16px;
  list-style: disc;
}

.cv-bullets li {
  margin: 0;
  color: var(--prose);
}

.cv-bullets li::marker {
  color: var(--prose);
  font-size: 0.7em;
}

/* --- Skills / languages / other ----------------------------------------- */
/* Two columns: the groups are short runs, and stacking six of them pushed
   Languages and Other onto a near-empty final page. */
.cv-skill-columns {
  display: grid;
  grid-template-columns: 1fr 1fr;
  column-gap: 32px;
  margin-top: 14px;
}

.cv-skill-group {
  margin-top: 12px;
  break-inside: avoid;
}

.cv-skill-columns > .cv-skill-group:nth-child(-n + 2) {
  margin-top: 0;
}

.cv-skill-label {
  margin: 0;
  color: var(--ink);
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.cv-skill-items {
  margin: 0;
  color: var(--prose);
}

.cv-lang-name {
  color: var(--ink);
  font-weight: 700;
}

/* --- Screen-only affordance ---------------------------------------------
   On screen the sheet floats on the admin background so it reads as a page;
   in print it IS the page, so the shadow and radius come off. */
@media screen {
  .cv-page {
    border-radius: 2px;
    box-shadow:
      0 1px 3px rgb(15 23 42 / 12%),
      0 8px 24px rgb(15 23 42 / 8%);
  }

  .cv-page :deep(a) {
    text-decoration: underline;
    text-decoration-color: rgb(0 0 0 / 25%);
    text-underline-offset: 2px;
  }
}

@media print {
  .cv-page {
    /* The @page rule owns the sheet margins (element padding would apply to
       the first page only), so the document itself sits flush inside them. */
    width: auto;
    padding: 0;
    box-shadow: none;
  }
}
</style>
