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
          <!-- Bare text, no anchors: recruiters need the LinkedIn/GitHub/site
               identity lines, but a printed document has nothing to click and
               link styling only adds noise (owner call, 2026-08-22). -->
          <template v-if="linkedInUrl">
            <dt>LinkedIn</dt>
            <dd>{{ stripProtocol(linkedInUrl) }}</dd>
          </template>
          <template v-if="gitHubUrl">
            <dt>GitHub</dt>
            <dd>{{ stripProtocol(gitHubUrl) }}</dd>
          </template>
          <template v-if="resume.basics.url">
            <dt>Web</dt>
            <dd>{{ stripProtocol(resume.basics.url) }}</dd>
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
          <!-- Name and issuer share the line (no verification URL either):
               a certificate is one fact, and a two-line entry under a
               full-dress section heading read as a starved template block. -->
          <h3 class="cv-entry-title">
            {{ cert.name
            }}<span v-if="cert.issuer" class="cv-cert-issuer"> — {{ cert.issuer }}</span>
          </h3>
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
          <!-- Each keyword is an unbreakable run ("Software Supply-Chain /
               Security (SBOM)" split across lines reads as two skills), and
               the separator RIDES ITS KEYWORD so a wrapped line never opens
               with a stray "·". -->
          <p class="cv-skill-items">
            <template v-for="(keyword, index) in group.keywords" :key="keyword"
              ><span class="cv-skill-item"
                >{{ keyword }}<template v-if="index < group.keywords.length - 1"> ·</template></span
              >{{ index < group.keywords.length - 1 ? ' ' : '' }}</template
            >
          </p>
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
// The reference CV is set in Roboto (identified from its embedded glyph
// metrics); without these imports the 'Roboto' declaration below silently
// fell through to Arial, whose ~12% wider spacing changed every line break
// against the reference. Self-hosted via fontsource (CSP font-src 'self'),
// and only this lazy admin chunk pays the ~32KB.
import '@fontsource/roboto/latin-400.css'
import '@fontsource/roboto/latin-700.css'
import { computed } from 'vue'
import type { CvResume } from '@/types/cv'

const props = defineProps<{ resume: CvResume }>()

const stripProtocol = (url: string): string =>
  (url || '')
    .replace(/^https?:\/\//, '')
    .replace(/^www\./, '')
    .replace(/\/$/, '')

const profileUrl = (network: string): string =>
  props.resume.basics.profiles?.find(p => p.network?.toLowerCase() === network)?.url || ''

const linkedInUrl = computed<string>(() => profileUrl('linkedin'))
const gitHubUrl = computed<string>(() => profileUrl('github'))

// "Stockholm, Sweden" — not "Stockholm, SE". Intl.DisplayNames turns the
// stored ISO code into the English country name; the code is the fallback if
// the runtime cannot resolve it.
const countryName = (code: string): string => {
  try {
    return new Intl.DisplayNames(['en'], { type: 'region' }).of(code.toUpperCase()) || code
  } catch {
    return code
  }
}

const locationLine = computed<string>(() => {
  const loc = props.resume.basics.location
  if (!loc) return ''
  const country = loc.countryCode ? countryName(loc.countryCode) : ''
  return [loc.city, country].filter(Boolean).join(', ')
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
  font-family: 'Roboto', Arial, sans-serif;
  font-size: 13px;
  line-height: var(--grid);
  /* A stray line stranded across a page break reads as a printing accident. */
  orphans: 2;
  widows: 2;
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

/* Regular weight so the name stands alone; the headline is a subtitle, not a
   second heading shouting at the first. */
.cv-label {
  margin: 5px 0 0;
  color: var(--ink);
  font-size: 14px;
  font-weight: 400;
  letter-spacing: 0.01em;
}

/* Definition list rather than stacked <p>s: these really are label/value
   pairs, and it gives print and screen readers the same structure. */
.cv-contact {
  display: grid;
  grid-template-columns: max-content 1fr;
  column-gap: 8px;
  /* One grid line of air, not an off-rhythm 25px hole. */
  margin: 17px 0 0;
  font-size: 12px;
}

/* Micro-label voice (matches .cv-skill-label) rather than six bold-black
   words stacking into a second heavy edge that competed with the name. */
.cv-contact dt {
  padding-top: 2px;
  color: var(--ink);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.cv-contact dd {
  margin: 0;
  color: var(--prose);
}

.cv-photo {
  width: 120px;
  height: 120px;
  /* A true bleed: -8px pushes the circle's right edge onto the section
     rules' right terminus (margin-left only reached the CONTENT edge, which
     left the circle hanging 8px inboard of every rule). Centered against
     the six-row identity block so the header's right side carries no void. */
  align-self: center;
  margin-right: -8px;
  border-radius: 50%;
  object-fit: cover;
  /* The asset's own backdrop is the grey that shows inside the circle — no
     background is drawn behind it, which would risk a visible seam. */
}

/* --- Sections ----------------------------------------------------------- */
/* Space above a section is 2x the space under its rule, so a heading binds to
   its own content instead of floating between neighbours. (Both distances are
   re-measured against the 670px print width — the sheet must stay 2 pages.) */
.cv-section {
  margin-top: 28px;
}

.cv-section-title {
  margin: 0 0 12px;
  padding-bottom: 6px;
  /* Bleed the rule 8px past the text column on both sides. */
  width: calc(100% + 16px);
  margin-left: -8px;
  border-bottom: 1px solid var(--ink);
  color: var(--ink);
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-align: center;
  text-transform: uppercase;
  /* A heading stranded at a page bottom is the one break worse than a split
     entry. */
  break-after: avoid;
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

/* The first entry sits close under its section rule — the rule already
   separates; 12px (title margin) + 14px opened every section with a hole
   twice the inter-entry gap. */
.cv-entry:first-of-type {
  margin-top: 2px;
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

/* Role owns the line; employer recedes. Two bold near-identical lines per
   entry was the loudest "template CV" tell — one voice each now. 15px also
   keeps every degree line to a single line at the 502px body width. */
.cv-entry-title {
  margin: 0;
  color: var(--ink);
  font-size: 15px;
  font-weight: 700;
  line-height: var(--grid);
}

.cv-entry-org {
  margin: 1px 0 0;
  color: var(--prose);
  font-size: 13px;
  font-weight: 400;
  line-height: var(--grid);
}

/* --- Bullets ------------------------------------------------------------
   Real list markers, not background-coloured spans: Chrome drops background
   graphics when printing, which is why the previous markers came out white
   (invisible) in the PDF. Foreground ink is never suppressed.
   Item spacing equals wrapped-line spacing — a flat grid, no extra gap. */
.cv-bullets {
  margin: 2px 0 0;
  /* Committed to the fine 0.7em dot: 13px closes the gap so the marker
     reads as structure, not a stray mark adrift in a 16px indent. */
  padding-left: 13px;
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
  /* Same rule-to-first-content rhythm as the entry sections. */
  margin-top: 2px;
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

.cv-skill-item {
  white-space: nowrap;
}

.cv-cert-issuer {
  color: var(--prose);
  font-size: 13px;
  font-weight: 400;
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
