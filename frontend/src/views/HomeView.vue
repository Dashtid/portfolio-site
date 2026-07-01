<template>
  <div class="portfolio-home">
    <!-- Navigation Bar -->
    <NavBar />

    <!-- Main content area for accessibility -->
    <main id="main-content" role="main" tabindex="-1">
      <!-- Hero Section. First-pass editorial layout — kept intentionally
           restrained; the v0-driven polish in BACKLOG (HERO-01) will
           replace this with a properly art-directed treatment. -->
      <section
        id="hero"
        class="hero-section relative flex min-h-screen items-center justify-center overflow-hidden bg-white dark:bg-slate-950"
      >
        <ThreeHeroBackground v-if="isDark" />

        <div class="relative z-[2] mx-auto max-w-4xl px-6 text-center">
          <p class="mb-10 font-mono text-xs uppercase tracking-[0.25em] text-slate-500">
            Portfolio — 2026
          </p>

          <h1
            class="custom-hero-title text-balance text-4xl font-semibold leading-[1.05] tracking-tight text-slate-900 sm:text-5xl lg:text-6xl dark:text-white"
          >
            Cybersecurity in medical software development
          </h1>

          <p
            class="custom-hero-lead mx-auto mt-12 max-w-2xl text-base font-light leading-relaxed text-slate-500 sm:text-lg dark:text-slate-400"
          >
            Stockholm, Sweden
          </p>
        </div>
      </section>

      <!-- API Error Banner -->
      <div v-if="portfolioStore.error" class="mx-auto max-w-7xl px-6 pt-6" role="alert">
        <div
          class="rounded-lg border border-amber-300/50 bg-amber-50 px-4 py-3 text-sm text-amber-900 dark:border-amber-500/20 dark:bg-amber-500/10 dark:text-amber-200"
        >
          Unable to load portfolio data. Showing static fallback content.
        </div>
      </div>

      <!-- Experience Section -->
      <section id="experience" class="bg-white py-32 dark:bg-slate-950">
        <div class="mx-auto max-w-7xl px-6 sm:px-8 lg:px-12">
          <header class="mb-12">
            <h2
              class="section-title text-3xl font-semibold tracking-tight text-slate-900 sm:text-4xl dark:text-white"
            >
              Experience
            </h2>
          </header>

          <div class="experience-list grid gap-6 sm:grid-cols-2 xl:grid-cols-3">
            <!-- Dynamic content from backend or static fallback -->
            <template v-if="companies.length">
              <article
                v-for="company in companiesByDate"
                :key="company.id"
                class="experience-card group flex flex-col rounded-2xl border border-slate-200 bg-white p-6 transition-colors hover:border-primary-400/60 dark:border-slate-800 dark:bg-slate-900/50 dark:hover:border-primary-400/40"
              >
                <header class="flex items-start gap-4">
                  <img
                    v-if="company.logo_url"
                    :src="company.logo_url"
                    :alt="`${company.name} Logo`"
                    class="card-logo h-14 w-14 shrink-0 rounded-lg bg-white object-contain p-1.5 ring-1 ring-slate-200 dark:ring-slate-700"
                    width="64"
                    height="64"
                    loading="lazy"
                  />
                  <div class="min-w-0 flex-1">
                    <h3 class="company-name text-lg font-semibold text-slate-900 dark:text-white">
                      {{ company.name }}
                    </h3>
                    <p
                      class="company-dates mt-1 font-mono text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400"
                    >
                      {{ formatDate(company.start_date) }} —
                      {{ company.end_date ? formatDate(company.end_date) : 'Present' }}
                    </p>
                  </div>
                </header>
                <p
                  class="job-title mt-5 text-balance text-sm font-medium text-primary-600 dark:text-primary-400"
                >
                  {{ company.title }}
                </p>
                <p class="company-location mt-0.5 text-sm text-slate-500 dark:text-slate-400">
                  {{ company.location }}
                </p>
                <p
                  class="company-description mt-3 text-sm leading-relaxed text-slate-600 dark:text-slate-300"
                >
                  {{ company.description }}
                </p>

                <router-link
                  :to="{ name: 'experience-detail', params: { id: getDetailLinkId(company) } }"
                  class="mt-auto inline-flex items-center gap-1 pt-6 text-sm font-medium text-primary-600 transition-all hover:gap-2 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-primary-500 dark:text-primary-400"
                >
                  Learn more
                  <svg
                    class="h-3.5 w-3.5"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke-width="2"
                    stroke="currentColor"
                    aria-hidden="true"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      d="M17 8l4 4m0 0l-4 4m4-4H3"
                    />
                  </svg>
                </router-link>
              </article>
            </template>
            <template v-else>
              <!-- Static fallback — rendered when the SSG build fetched no
                   companies from the backend. Kept in sync with seed_data;
                   update both when roles change. -->
              <article
                class="experience-card flex flex-col rounded-2xl border border-slate-200 bg-white p-6 transition-colors hover:border-primary-400/60 dark:border-slate-800 dark:bg-slate-900/50 dark:hover:border-primary-400/40"
              >
                <header>
                  <h3 class="company-name text-lg font-semibold text-slate-900 dark:text-white">
                    Hermes Medical Solutions
                  </h3>
                  <p
                    class="company-dates mt-1 font-mono text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400"
                  >
                    May 2024 — Present
                  </p>
                </header>
                <p
                  class="job-title mt-5 text-balance text-sm font-medium text-primary-600 dark:text-primary-400"
                >
                  QA/RA &amp; Security Specialist
                </p>
                <p class="company-location mt-0.5 text-sm text-slate-500 dark:text-slate-400">
                  Stockholm, Sweden
                </p>
                <p
                  class="company-description mt-3 text-sm leading-relaxed text-slate-600 dark:text-slate-300"
                >
                  QA/RA &amp; Security Specialist at Hermes Medical Solutions, ensuring NIS2/ISO
                  27001 compliance, regulatory clearance, and V&amp;V processes for nuclear medicine
                  software solutions.
                </p>
              </article>
              <article
                class="experience-card flex flex-col rounded-2xl border border-slate-200 bg-white p-6 transition-colors hover:border-primary-400/60 dark:border-slate-800 dark:bg-slate-900/50 dark:hover:border-primary-400/40"
              >
                <header>
                  <h3 class="company-name text-lg font-semibold text-slate-900 dark:text-white">
                    Philips Healthcare
                  </h3>
                  <p
                    class="company-dates mt-1 font-mono text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400"
                  >
                    Mar 2022 — May 2024
                  </p>
                </header>
                <p
                  class="job-title mt-5 text-balance text-sm font-medium text-primary-600 dark:text-primary-400"
                >
                  Incident Support Specialist, Nordics
                </p>
                <p class="company-location mt-0.5 text-sm text-slate-500 dark:text-slate-400">
                  Stockholm, Sweden
                </p>
                <p
                  class="company-description mt-3 text-sm leading-relaxed text-slate-600 dark:text-slate-300"
                >
                  Remote Service Engineer providing Level 1 support for Intellispace Portal (ISP)
                  and Intellispace Cardiovascular (ISCV) systems across the Nordics.
                </p>
              </article>
              <article
                class="experience-card flex flex-col rounded-2xl border border-slate-200 bg-white p-6 transition-colors hover:border-primary-400/60 dark:border-slate-800 dark:bg-slate-900/50 dark:hover:border-primary-400/40"
              >
                <header>
                  <h3 class="company-name text-lg font-semibold text-slate-900 dark:text-white">
                    Karolinska University Hospital
                  </h3>
                  <p
                    class="company-dates mt-1 font-mono text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400"
                  >
                    Jun 2021 — Dec 2021
                  </p>
                </header>
                <p
                  class="job-title mt-5 text-balance text-sm font-medium text-primary-600 dark:text-primary-400"
                >
                  Biomedical Engineer, Medical Imaging and Physiology
                </p>
                <p class="company-location mt-0.5 text-sm text-slate-500 dark:text-slate-400">
                  Stockholm, Sweden
                </p>
                <p
                  class="company-description mt-3 text-sm leading-relaxed text-slate-600 dark:text-slate-300"
                >
                  First-line support for imaging equipment fleet, incident management for RIS/PACS
                  systems, working with GE, Philips, and Siemens solutions.
                </p>
              </article>
            </template>
          </div>
        </div>
      </section>

      <!-- Education Section -->
      <section id="education" class="bg-slate-50 py-32 dark:bg-slate-900/40">
        <div class="mx-auto max-w-7xl px-6 sm:px-8 lg:px-12">
          <header class="mb-12">
            <h2
              class="section-title text-3xl font-semibold tracking-tight text-slate-900 sm:text-4xl dark:text-white"
            >
              Education
            </h2>
          </header>

          <div class="education-grid grid gap-6 sm:grid-cols-2 xl:grid-cols-3">
            <template v-if="education.length">
              <article
                v-for="edu in education"
                :key="edu.id"
                class="education-card group flex flex-col rounded-2xl border border-slate-200 bg-white p-6 transition-colors hover:border-primary-400/60 dark:border-slate-800 dark:bg-slate-900/50 dark:hover:border-primary-400/40"
              >
                <header class="flex items-start gap-4">
                  <img
                    v-if="edu.logo_url"
                    :src="edu.logo_url"
                    :alt="`${edu.institution} Logo`"
                    class="card-logo h-14 w-14 shrink-0 rounded-lg bg-white object-contain p-1.5 ring-1 ring-slate-200 dark:ring-slate-700"
                    width="64"
                    height="64"
                    loading="lazy"
                  />
                  <div class="min-w-0 flex-1">
                    <h3
                      class="education-institution text-lg font-semibold text-slate-900 dark:text-white"
                    >
                      {{ edu.institution }}
                    </h3>
                    <p
                      class="education-degree mt-1 text-sm font-medium text-primary-600 dark:text-primary-400"
                    >
                      {{ edu.degree }}
                    </p>
                  </div>
                </header>
                <p
                  v-if="edu.field_of_study"
                  class="education-field mt-3 text-sm text-slate-500 dark:text-slate-400"
                >
                  {{ edu.field_of_study }}
                </p>
                <p
                  v-if="edu.description"
                  class="education-description mt-3 text-sm leading-relaxed text-slate-600 dark:text-slate-300"
                >
                  {{ edu.description }}
                </p>
                <p
                  class="education-dates mt-4 font-mono text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400"
                >
                  <template v-if="edu.is_certification && edu.end_date">
                    {{ formatDate(edu.end_date) }}
                  </template>
                  <template v-else>
                    {{ formatDate(edu.start_date) }} —
                    {{ edu.end_date ? formatDate(edu.end_date) : 'Present' }}
                  </template>
                </p>
                <a
                  v-if="edu.certificate_url"
                  :href="edu.certificate_url"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="certificate-link mt-auto inline-flex items-center gap-1 pt-6 text-sm font-medium text-primary-600 transition-all hover:gap-2 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-primary-500 dark:text-primary-400"
                  :aria-label="`View certificate for ${edu.degree} from ${edu.institution} (opens in new tab)`"
                >
                  View certificate
                  <svg
                    class="external-icon h-3.5 w-3.5"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                    aria-hidden="true"
                  >
                    <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
                    <polyline points="15 3 21 3 21 9" />
                    <line x1="10" y1="14" x2="21" y2="3" />
                  </svg>
                </a>
              </article>
            </template>
            <template v-else>
              <!-- Static fallback — rendered when the SSG build fetched no
                   education rows. Kept in sync with seed_data. -->
              <article
                class="education-card flex flex-col rounded-2xl border border-slate-200 bg-white p-6 transition-colors hover:border-primary-400/60 dark:border-slate-800 dark:bg-slate-900/50 dark:hover:border-primary-400/40"
              >
                <header>
                  <h3
                    class="education-institution text-lg font-semibold text-slate-900 dark:text-white"
                  >
                    CompTIA
                  </h3>
                  <p
                    class="education-degree mt-1 text-sm font-medium text-primary-600 dark:text-primary-400"
                  >
                    Security+ Certification
                  </p>
                </header>
                <p class="education-field mt-3 text-sm text-slate-500 dark:text-slate-400">
                  Cybersecurity
                </p>
                <p
                  class="education-description mt-3 text-sm leading-relaxed text-slate-600 dark:text-slate-300"
                >
                  Industry-standard certification covering network security, threats,
                  vulnerabilities, and risk management.
                </p>
                <p
                  class="education-dates mt-4 font-mono text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400"
                >
                  Jan 2026
                </p>
                <a
                  href="https://www.credly.com/badges/450d4dcd-e24c-4906-98b9-2ebb792f9462/public_url"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="certificate-link mt-auto inline-flex items-center gap-1 pt-6 text-sm font-medium text-primary-600 transition-all hover:gap-2 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-primary-500 dark:text-primary-400"
                  aria-label="View Security+ certificate from CompTIA (opens in new tab)"
                >
                  View certificate
                  <svg
                    class="external-icon h-3.5 w-3.5"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    stroke-width="2"
                    aria-hidden="true"
                  >
                    <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
                    <polyline points="15 3 21 3 21 9" />
                    <line x1="10" y1="14" x2="21" y2="3" />
                  </svg>
                </a>
              </article>
              <article
                class="education-card flex flex-col rounded-2xl border border-slate-200 bg-white p-6 transition-colors hover:border-primary-400/60 dark:border-slate-800 dark:bg-slate-900/50 dark:hover:border-primary-400/40"
              >
                <header>
                  <h3
                    class="education-institution text-lg font-semibold text-slate-900 dark:text-white"
                  >
                    Microsoft
                  </h3>
                  <p
                    class="education-degree mt-1 text-sm font-medium text-primary-600 dark:text-primary-400"
                  >
                    Azure Security Engineer Associate (AZ-500)
                  </p>
                </header>
                <p class="education-field mt-3 text-sm text-slate-500 dark:text-slate-400">
                  Cloud Security
                </p>
                <p
                  class="education-description mt-3 text-sm leading-relaxed text-slate-600 dark:text-slate-300"
                >
                  Azure security services, identity management, and compliance features.
                </p>
                <p
                  class="education-dates mt-4 font-mono text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400"
                >
                  Jun 2023
                </p>
              </article>
              <article
                class="education-card flex flex-col rounded-2xl border border-slate-200 bg-white p-6 transition-colors hover:border-primary-400/60 dark:border-slate-800 dark:bg-slate-900/50 dark:hover:border-primary-400/40"
              >
                <header>
                  <h3
                    class="education-institution text-lg font-semibold text-slate-900 dark:text-white"
                  >
                    Företagsuniversitetet
                  </h3>
                  <p
                    class="education-degree mt-1 text-sm font-medium text-primary-600 dark:text-primary-400"
                  >
                    Certified ISO 27001 Lead Implementer
                  </p>
                </header>
                <p class="education-field mt-3 text-sm text-slate-500 dark:text-slate-400">
                  Information Security Management
                </p>
                <p
                  class="education-description mt-3 text-sm leading-relaxed text-slate-600 dark:text-slate-300"
                >
                  Intensive certification program for implementing and managing ISO 27001 ISMS.
                </p>
                <p
                  class="education-dates mt-4 font-mono text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400"
                >
                  Mar 2023
                </p>
              </article>
              <article
                class="education-card flex flex-col rounded-2xl border border-slate-200 bg-white p-6 transition-colors hover:border-primary-400/60 dark:border-slate-800 dark:bg-slate-900/50 dark:hover:border-primary-400/40"
              >
                <header>
                  <h3
                    class="education-institution text-lg font-semibold text-slate-900 dark:text-white"
                  >
                    EC-Council
                  </h3>
                  <p
                    class="education-degree mt-1 text-sm font-medium text-primary-600 dark:text-primary-400"
                  >
                    Certified Ethical Hacker (CEH)
                  </p>
                </header>
                <p class="education-field mt-3 text-sm text-slate-500 dark:text-slate-400">
                  Cybersecurity
                </p>
                <p
                  class="education-description mt-3 text-sm leading-relaxed text-slate-600 dark:text-slate-300"
                >
                  Ethical hacking methodologies, penetration testing, and vulnerability assessment.
                </p>
                <p
                  class="education-dates mt-4 font-mono text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400"
                >
                  Oct 2022
                </p>
              </article>
              <article
                class="education-card flex flex-col rounded-2xl border border-slate-200 bg-white p-6 transition-colors hover:border-primary-400/60 dark:border-slate-800 dark:bg-slate-900/50 dark:hover:border-primary-400/40"
              >
                <header>
                  <h3
                    class="education-institution text-lg font-semibold text-slate-900 dark:text-white"
                  >
                    KTH Royal Institute of Technology
                  </h3>
                  <p
                    class="education-degree mt-1 text-sm font-medium text-primary-600 dark:text-primary-400"
                  >
                    M.Sc. Medical Engineering
                  </p>
                </header>
                <p class="education-field mt-3 text-sm text-slate-500 dark:text-slate-400">
                  Medical Technology and Bioengineering
                </p>
                <p
                  class="education-description mt-3 text-sm leading-relaxed text-slate-600 dark:text-slate-300"
                >
                  Specialized in medical imaging, signal processing, and healthcare informatics.
                  Thesis on AI-driven diagnostic systems.
                </p>
                <p
                  class="education-dates mt-4 font-mono text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400"
                >
                  Aug 2017 — Jun 2022
                </p>
              </article>
              <article
                class="education-card flex flex-col rounded-2xl border border-slate-200 bg-white p-6 transition-colors hover:border-primary-400/60 dark:border-slate-800 dark:bg-slate-900/50 dark:hover:border-primary-400/40"
              >
                <header>
                  <h3
                    class="education-institution text-lg font-semibold text-slate-900 dark:text-white"
                  >
                    Lund University (LTH)
                  </h3>
                  <p
                    class="education-degree mt-1 text-sm font-medium text-primary-600 dark:text-primary-400"
                  >
                    B.Sc. Biomedical Engineering (Exchange)
                  </p>
                </header>
                <p class="education-field mt-3 text-sm text-slate-500 dark:text-slate-400">
                  Biomedical Engineering
                </p>
                <p
                  class="education-description mt-3 text-sm leading-relaxed text-slate-600 dark:text-slate-300"
                >
                  Exchange program focusing on medical device development and regulatory affairs.
                </p>
                <p
                  class="education-dates mt-4 font-mono text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400"
                >
                  Jan 2020 — Jun 2021
                </p>
              </article>
            </template>
          </div>
        </div>
      </section>

      <!-- Publications/Research Section -->
      <section id="publications" class="bg-white py-32 dark:bg-slate-950">
        <div class="mx-auto max-w-7xl px-6 sm:px-8 lg:px-12">
          <header class="mb-12">
            <h2
              class="section-title text-3xl font-semibold tracking-tight text-slate-900 sm:text-4xl dark:text-white"
            >
              Academic Work
            </h2>
          </header>
          <div
            v-if="documentsLoading"
            class="rounded-2xl border border-dashed border-slate-200 px-6 py-12 text-center text-sm text-slate-500 dark:border-slate-800 dark:text-slate-400"
            role="status"
            aria-live="polite"
          >
            Loading publications...
          </div>
          <div
            v-else-if="documentsError"
            class="rounded-2xl border border-rose-200 bg-rose-50 px-6 py-6 text-sm text-rose-700 dark:border-rose-500/30 dark:bg-rose-500/10 dark:text-rose-200"
            role="alert"
          >
            {{ documentsError }}
          </div>
          <div v-else class="documents-grid grid gap-6 sm:grid-cols-2 xl:grid-cols-3">
            <DocumentCard v-for="document in documents" :key="document.id" :document="document" />
          </div>
        </div>
      </section>

      <!-- Projects Section -->
      <section id="projects" class="bg-slate-50 py-32 dark:bg-slate-900/40">
        <div class="mx-auto max-w-7xl px-6 sm:px-8 lg:px-12">
          <header class="mb-12">
            <h2
              class="section-title text-3xl font-semibold tracking-tight text-slate-900 sm:text-4xl dark:text-white"
            >
              GitHub
            </h2>
          </header>

          <!-- GitHub Stats with Featured Projects -->
          <GitHubStats username="Dashtid" />
        </div>
      </section>

      <!-- About Section -->
      <section id="about" class="bg-white py-32 dark:bg-slate-950">
        <div class="mx-auto max-w-7xl px-6 sm:px-8 lg:px-12">
          <header class="mb-12">
            <h2
              class="section-title text-3xl font-semibold tracking-tight text-slate-900 sm:text-4xl dark:text-white"
            >
              About Me
            </h2>
          </header>

          <div
            class="about-layout mx-auto grid max-w-5xl items-start gap-12 md:grid-cols-[280px_1fr]"
          >
            <div>
              <picture>
                <source srcset="/images/optimized/cropped.avif" type="image/avif" />
                <source srcset="/images/optimized/cropped.webp" type="image/webp" />
                <!-- FRONTEND-PERF-08: PNG fallback uses the already-optimised
                     cropped.png (343 KB) instead of the unprocessed
                     profile.png (854 KB). >97% of clients hit the AVIF/WebP
                     branches above so the fallback path is rarely walked,
                     but the saving still applies to Lighthouse's total-
                     payload budget and to older browsers/screen readers
                     that fall back. -->
                <img
                  src="/images/optimized/cropped.png"
                  alt="David Dashti - Biomedical Engineer and Cybersecurity Specialist"
                  class="mx-auto h-auto w-[260px] rounded-2xl object-cover ring-1 ring-slate-200 md:mx-0 md:w-full dark:ring-slate-800"
                  width="280"
                  height="326"
                  loading="lazy"
                />
              </picture>
            </div>
            <div class="text-slate-600 dark:text-slate-300">
              <p
                class="text-balance text-lg font-medium leading-relaxed text-slate-800 dark:text-slate-100"
              >
                Medical software security specialist focusing on cybersecurity governance,
                regulatory compliance, and healthcare AI systems. Expert in ISO 27001, NIS2, and MDR
                frameworks.
              </p>
              <p class="mt-10 leading-relaxed">
                I am a biomedical engineer specializing in cybersecurity and regulatory compliance
                for medical software and AI systems. As a QA/RA &amp; Security Specialist at Hermes
                Medical Solutions, I ensure that our software and digital health solutions meet the
                highest standards of security, privacy, and regulatory alignment (NIS2, ISO 27001,
                EU AI Act).
              </p>
              <div class="mt-14">
                <p
                  class="font-mono text-xs uppercase tracking-[0.2em] text-slate-500 dark:text-slate-400"
                >
                  Current focus areas
                </p>
                <ul class="mt-6 space-y-4">
                  <li class="flex gap-3 leading-relaxed">
                    <span
                      class="mt-2.5 h-1.5 w-1.5 shrink-0 rounded-full bg-primary-500"
                      aria-hidden="true"
                    ></span>
                    Cybersecurity governance in medical software development
                  </li>
                  <li class="flex gap-3 leading-relaxed">
                    <span
                      class="mt-2.5 h-1.5 w-1.5 shrink-0 rounded-full bg-primary-500"
                      aria-hidden="true"
                    ></span>
                    Ensuring compliance with NIS2 and ISO 27001
                  </li>
                  <li class="flex gap-3 leading-relaxed">
                    <span
                      class="mt-2.5 h-1.5 w-1.5 shrink-0 rounded-full bg-primary-500"
                      aria-hidden="true"
                    ></span>
                    Supporting market clearance for medical software (MDR, GDPR)
                  </li>
                  <li class="flex gap-3 leading-relaxed">
                    <span
                      class="mt-2.5 h-1.5 w-1.5 shrink-0 rounded-full bg-primary-500"
                      aria-hidden="true"
                    ></span>
                    Preparing frameworks for AI Act compliance in healthcare AI systems
                  </li>
                </ul>
              </div>
              <div class="mt-14">
                <p
                  class="font-mono text-xs uppercase tracking-[0.2em] text-slate-500 dark:text-slate-400"
                >
                  Technical skills
                </p>
                <p class="mt-6 leading-relaxed">
                  Windows Server, Unix/Linux, Docker, Kubernetes, PowerShell, Bash, Python, Rust and
                  Git
                </p>
              </div>
              <p class="mt-14 leading-relaxed">
                I am passionate about making healthcare technology safer and more trustworthy by
                protecting patient data, ensuring system integrity, and helping organizations
                navigate the Cybersecurity &amp; AI regulatory landscape.
              </p>
            </div>
          </div>
        </div>
      </section>
    </main>

    <!-- Footer Section -->
    <FooterSection />

    <!-- Back to Top Button -->
    <BackToTop />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, nextTick, defineAsyncComponent } from 'vue'
import { usePortfolioStore } from '../stores/portfolio'
import NavBar from '../components/NavBar.vue'
import FooterSection from '../components/FooterSection.vue'
import BackToTop from '../components/BackToTop.vue'
import DocumentCard from '../components/DocumentCard.vue'
import GitHubStats from '../components/GitHubStats.vue'
import { useIntersectionAnimation } from '../composables/useIntersectionAnimation'
import { useTheme } from '../composables/useTheme'

const { isDark } = useTheme()

// Lazy load Three.js hero background to reduce initial bundle size (~172KB gzipped)
const ThreeHeroBackground = defineAsyncComponent({
  loader: () => import('../components/ThreeHeroBackground.vue'),
  delay: 0,
  timeout: 10000
})
import { useHead } from '@unhead/vue'
import apiClient from '../api/client'
import type { Document } from '@/types'
import { logger } from '../utils/logger'
import { getUserMessage } from '../utils/errorHandler'

useHead({
  title: 'David Dashti | Cybersecurity in Healthcare',
  meta: [
    {
      name: 'description',
      content:
        'Biomedical Engineer and Cybersecurity Specialist specializing in regulatory compliance for medical software and AI systems.'
    }
  ],
  link: [{ rel: 'canonical', href: 'https://dashti.se/' }]
})

const portfolioStore = usePortfolioStore()

// INFRA-002: fetch portfolio data in setup (BEFORE component renders) so
// vite-ssg captures the populated Pinia state into __INITIAL_STATE__ and
// clients see hydrated content immediately. The previous onMounted-based
// fetch was fire-and-forget during SSG pre-render — vite-ssg serialized
// the empty store before the fetch resolved, so the rendered HTML
// shipped real content (from the static fallback) but the hydration
// payload was empty.
//
// (Tried onServerPrefetch instead to keep setup sync — vite-ssg's
// renderer doesn't await that hook, so it doesn't populate state.
// Top-level await + the existing App.vue <Suspense> boundary works.)
//
// The guard skips the fetch when the store is already populated, which is
// the normal client-side case after hydration: SSG ships state via
// __INITIAL_STATE__, `main.ts` rehydrates it into Pinia before any
// component runs, and this setup sees a populated store and short-circuits.
//
// Failures here MUST NOT throw, because:
//   - During SSG build, a throw would fail the entire build over a
//     transient API blip.
//   - During client hydration, a throw would bubble to <Suspense> and
//     blank the page rather than gracefully degrade.
// The static fallback below + the documents fetcher in onMounted carry
// the user-facing experience when the API is unreachable.
if (portfolioStore.companies.length === 0) {
  try {
    await portfolioStore.fetchAllData()
  } catch (error) {
    logger.error('Portfolio data fetch failed in setup:', error)
  }
}

// Computed properties for education from API - sorted by end_date (newest first)
const education = computed(() => {
  const items = portfolioStore.education || []
  return [...items].sort((a, b) => {
    const dateA = a.end_date ? new Date(a.end_date).getTime() : Date.now()
    const dateB = b.end_date ? new Date(b.end_date).getTime() : Date.now()
    return dateB - dateA
  })
})

// Documents state
const documents = ref<Document[]>([])
const documentsLoading = ref(false)
const documentsError = ref<string | null>(null)

// Computed properties
const companies = computed(() => portfolioStore.companies || [])
const companiesByDate = computed(() => {
  return [...companies.value].sort((a, b) => {
    if (!a.start_date) return 1
    if (!b.start_date) return -1
    return new Date(b.start_date).getTime() - new Date(a.start_date).getTime()
  })
})

// Methods
const formatDate = (dateString: string | null | undefined): string => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short'
  })
}

// Get the correct company ID for detail links
// For Scania 2012 entry, link to the 2016 entry's detail page
const getDetailLinkId = (company: { id: string; name: string; start_date: string }): string => {
  if (company.name === 'Scania Group' && company.start_date) {
    const startYear = new Date(company.start_date).getFullYear()
    if (startYear === 2012) {
      // Find the 2016 Scania entry and return its ID
      const scania2016 = companies.value.find(
        c =>
          c.name === 'Scania Group' && c.start_date && new Date(c.start_date).getFullYear() === 2016
      )
      if (scania2016) {
        return scania2016.id
      }
    }
  }
  return company.id
}

// Load data on mount. Portfolio data is fetched in setup() above
// (INFRA-002); only the documents fetch lives here, because documents are a
// component-local ref that doesn't need to flow through __INITIAL_STATE__.
onMounted(async () => {
  documentsLoading.value = true

  try {
    const response = await apiClient.get<Document[]>('/api/v1/documents')
    documents.value = response.data
  } catch (error) {
    logger.error('Error loading documents:', error)
    documentsError.value = getUserMessage(error as Error)
  } finally {
    documentsLoading.value = false
  }

  // Wait for DOM to update before applying animations
  // This ensures elements are rendered before IntersectionObserver setup
  await nextTick()

  // PERF-03: IntersectionObserver-driven entrance animations replace the
  // previous GSAP + ScrollTrigger pass. Stagger is now a per-element CSS
  // transition-delay rather than a tween timeline; the animation itself
  // is a CSS transition driven by the `[data-anim]` attribute (defined
  // in the scoped <style> below). Drops ~45 KB gzipped of gsap from the
  // home-page critical path.
  useIntersectionAnimation('.experience-card', { stagger: 0.12 })
  useIntersectionAnimation('.education-card', { stagger: 0.12 })
  useIntersectionAnimation('.project-card', { stagger: 0.12 })
  useIntersectionAnimation('.document-card', { stagger: 0.12 })
  useIntersectionAnimation('.section-title', { stagger: 0 })
})
</script>

<style scoped>
.portfolio-home {
  padding-top: 0;
}

/*
 * PERF-03: entrance animations driven by useIntersectionAnimation.
 * `[data-anim="hidden"]` is set on mount; the observer flips elements
 * to `[data-anim="visible"]` as they scroll into view. Transitions are
 * GPU-friendly (transform + opacity only), so the same look the GSAP
 * pass produced — slide-up + fade — runs without the GSAP runtime.
 *
 * `:deep` because `scoped` doesn't rewrite the attribute selector
 * across element boundaries (the data attribute lives on cards rendered
 * by child components).
 */
:deep([data-anim='hidden']) {
  opacity: 0;
  transform: translate3d(0, 30px, 0);
  transition:
    opacity 0.5s ease-out,
    transform 0.5s ease-out;
  will-change: opacity, transform;
}

:deep([data-anim='visible']) {
  opacity: 1;
  transform: translate3d(0, 0, 0);
  will-change: auto;
}

@media (prefers-reduced-motion: reduce) {
  :deep([data-anim='hidden']),
  :deep([data-anim='visible']) {
    transition: none !important;
    transform: none !important;
  }
}

html {
  scroll-behavior: smooth;
}

:deep(.navbar-custom) {
  z-index: 1000;
}
</style>
