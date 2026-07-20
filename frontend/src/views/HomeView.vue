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
        class="hero-section relative flex min-h-screen items-center justify-center overflow-hidden bg-white pt-20 dark:bg-slate-950"
      >
        <!-- The starfield renders zero visible pixels on the white
             light-mode hero — gate it to dark so light-mode visitors skip
             the ~172KB three.js chunk entirely. -->
        <ThreeHeroBackground v-if="isDark" key="dark" :is-dark="true" />

        <div class="relative z-[2] mx-auto max-w-3xl px-6 text-center">
          <p
            class="mb-6 font-mono text-xs uppercase tracking-[0.2em] text-slate-500 dark:text-slate-400"
          >
            David Dashti — Product Security · QA/RA
          </p>

          <h1
            class="custom-hero-title text-balance text-4xl font-semibold leading-[1.05] tracking-tight text-slate-900 sm:text-5xl lg:text-6xl dark:text-white"
          >
            Cybersecurity in medical software development
          </h1>

          <p
            class="custom-hero-lead mx-auto mt-6 max-w-2xl text-balance text-base font-light leading-relaxed text-slate-500 sm:text-lg dark:text-slate-400"
          >
            Securing medical software from design through market clearance — and, increasingly, the
            AI moving into the devices themselves — at Hermes Medical Solutions, Stockholm.
          </p>

          <div class="mt-8 flex flex-wrap items-center justify-center gap-3">
            <a
              href="https://www.linkedin.com/in/david-dashti/"
              target="_blank"
              rel="noopener noreferrer"
              class="inline-flex items-center gap-2 rounded-lg bg-primary-600 px-5 py-2.5 text-sm font-medium text-white transition-colors hover:bg-primary-700 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-primary-500 dark:bg-primary-500 dark:text-slate-950 dark:hover:bg-primary-400"
            >
              Get in touch
            </a>
            <a
              href="https://github.com/Dashtid"
              target="_blank"
              rel="noopener noreferrer"
              class="inline-flex items-center gap-2 rounded-lg border border-slate-200 px-5 py-2.5 text-sm font-medium text-slate-700 transition-colors hover:border-primary-400/60 hover:text-primary-600 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-primary-500 dark:border-slate-800 dark:text-slate-200 dark:hover:border-primary-400/40 dark:hover:text-primary-400"
            >
              GitHub
            </a>
          </div>
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
      <section id="experience" class="bg-slate-50 py-16 md:py-20 dark:bg-slate-900/40">
        <div class="mx-auto max-w-7xl px-6 sm:px-8 lg:px-12">
          <header class="mb-6 md:mb-8">
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
                class="experience-card group relative flex flex-col rounded-2xl border border-slate-200 bg-white p-6 transition-colors hover:border-primary-400/60 hover:shadow-md dark:border-slate-800 dark:bg-slate-900/50 dark:hover:border-primary-400/40 dark:hover:bg-slate-900"
              >
                <header class="flex items-start gap-4">
                  <img
                    v-if="company.logo_url"
                    :src="company.logo_url"
                    :alt="`${company.name} Logo`"
                    class="card-logo h-16 w-auto min-w-16 max-w-32 shrink-0 rounded-lg bg-white object-contain p-2 ring-1 ring-slate-200 dark:ring-slate-700"
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
                  class="job-title mt-5 text-balance text-sm font-medium text-slate-900 dark:text-slate-100"
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
                  class="mt-auto inline-flex items-center gap-1 pt-8 text-sm font-medium text-primary-600 transition-all after:absolute after:inset-0 hover:gap-2 hover:text-primary-700 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-primary-500 dark:text-primary-400 dark:hover:text-primary-300"
                >
                  <!-- sr-only suffix: distinct link text per card, for screen
                       readers and the Lighthouse link-text audit alike -->
                  Learn more<span class="sr-only"> about {{ company.name }}</span>
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
                class="experience-card flex flex-col rounded-2xl border border-slate-200 bg-white p-6 transition-colors hover:border-primary-400/60 hover:shadow-md dark:border-slate-800 dark:bg-slate-900/50 dark:hover:border-primary-400/40 dark:hover:bg-slate-900"
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
                  class="job-title mt-5 text-balance text-sm font-medium text-slate-900 dark:text-slate-100"
                >
                  QA/RA &amp; Security Specialist
                </p>
                <p class="company-location mt-0.5 text-sm text-slate-500 dark:text-slate-400">
                  Stockholm, Sweden
                </p>
                <p
                  class="company-description mt-3 text-sm leading-relaxed text-slate-600 dark:text-slate-300"
                >
                  QA/RA &amp; Security Specialist at Hermes Medical Solutions, leading product
                  security and premarket cybersecurity — threat modeling, security risk management,
                  and regulatory clearance — for nuclear-medicine imaging software.
                </p>
              </article>
              <article
                class="experience-card flex flex-col rounded-2xl border border-slate-200 bg-white p-6 transition-colors hover:border-primary-400/60 hover:shadow-md dark:border-slate-800 dark:bg-slate-900/50 dark:hover:border-primary-400/40 dark:hover:bg-slate-900"
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
                  class="job-title mt-5 text-balance text-sm font-medium text-slate-900 dark:text-slate-100"
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
                class="experience-card flex flex-col rounded-2xl border border-slate-200 bg-white p-6 transition-colors hover:border-primary-400/60 hover:shadow-md dark:border-slate-800 dark:bg-slate-900/50 dark:hover:border-primary-400/40 dark:hover:bg-slate-900"
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
                  class="job-title mt-5 text-balance text-sm font-medium text-slate-900 dark:text-slate-100"
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
      <section id="education" class="bg-white py-16 md:py-20 dark:bg-slate-950">
        <div class="mx-auto max-w-7xl px-6 sm:px-8 lg:px-12">
          <header class="mb-6 md:mb-8">
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
                class="education-card group flex flex-col rounded-2xl border border-slate-200 bg-white p-6 transition-colors hover:border-primary-400/60 hover:shadow-md dark:border-slate-800 dark:bg-slate-900/50 dark:hover:border-primary-400/40 dark:hover:bg-slate-900"
              >
                <header class="flex items-start gap-4">
                  <img
                    v-if="edu.logo_url"
                    :src="edu.logo_url"
                    :alt="`${edu.institution} Logo`"
                    class="card-logo h-16 w-auto min-w-16 max-w-32 shrink-0 rounded-lg bg-white object-contain p-2 ring-1 ring-slate-200 dark:ring-slate-700"
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
                      class="education-dates mt-1 font-mono text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400"
                    >
                      <template v-if="edu.is_certification && edu.end_date">
                        {{ formatDate(edu.end_date) }}
                      </template>
                      <template v-else>
                        {{ formatDate(edu.start_date) }} —
                        {{ edu.end_date ? formatDate(edu.end_date) : 'Present' }}
                      </template>
                    </p>
                  </div>
                </header>
                <p
                  class="education-degree mt-5 text-balance text-sm font-medium text-slate-900 dark:text-slate-100"
                >
                  {{ edu.degree }}
                </p>
                <p
                  v-if="edu.field_of_study"
                  class="education-field mt-0.5 text-sm text-slate-500 dark:text-slate-400"
                >
                  {{ edu.field_of_study }}
                </p>
                <p
                  v-if="edu.description"
                  class="education-description mt-3 text-sm leading-relaxed text-slate-600 dark:text-slate-300"
                >
                  {{ edu.description }}
                </p>
                <a
                  v-if="edu.certificate_url"
                  :href="edu.certificate_url"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="certificate-link mt-auto pt-8 inline-flex items-center gap-1 text-sm font-medium text-primary-600 transition-all hover:gap-2 hover:text-primary-700 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-primary-500 dark:text-primary-400 dark:hover:text-primary-300"
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
                class="education-card flex flex-col rounded-2xl border border-slate-200 bg-white p-6 transition-colors hover:border-primary-400/60 hover:shadow-md dark:border-slate-800 dark:bg-slate-900/50 dark:hover:border-primary-400/40 dark:hover:bg-slate-900"
              >
                <header>
                  <h3
                    class="education-institution text-lg font-semibold text-slate-900 dark:text-white"
                  >
                    CompTIA
                  </h3>
                  <p
                    class="education-dates mt-1 font-mono text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400"
                  >
                    Jan 2026
                  </p>
                </header>
                <p
                  class="education-degree mt-5 text-balance text-sm font-medium text-slate-900 dark:text-slate-100"
                >
                  Security+ Certification
                </p>
                <p class="education-field mt-0.5 text-sm text-slate-500 dark:text-slate-400">
                  Cybersecurity
                </p>
                <p
                  class="education-description mt-3 text-sm leading-relaxed text-slate-600 dark:text-slate-300"
                >
                  Industry-standard certification covering network security, threats,
                  vulnerabilities, and risk management.
                </p>
                <a
                  href="https://www.credly.com/badges/450d4dcd-e24c-4906-98b9-2ebb792f9462/public_url"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="certificate-link mt-auto pt-8 inline-flex items-center gap-1 text-sm font-medium text-primary-600 transition-all hover:gap-2 hover:text-primary-700 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-primary-500 dark:text-primary-400 dark:hover:text-primary-300"
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
                class="education-card flex flex-col rounded-2xl border border-slate-200 bg-white p-6 transition-colors hover:border-primary-400/60 hover:shadow-md dark:border-slate-800 dark:bg-slate-900/50 dark:hover:border-primary-400/40 dark:hover:bg-slate-900"
              >
                <header>
                  <h3
                    class="education-institution text-lg font-semibold text-slate-900 dark:text-white"
                  >
                    Microsoft
                  </h3>
                  <p
                    class="education-dates mt-1 font-mono text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400"
                  >
                    Jun 2023
                  </p>
                </header>
                <p
                  class="education-degree mt-5 text-balance text-sm font-medium text-slate-900 dark:text-slate-100"
                >
                  Azure Security Engineer Associate (AZ-500)
                </p>
                <p class="education-field mt-0.5 text-sm text-slate-500 dark:text-slate-400">
                  Cloud Security
                </p>
                <p
                  class="education-description mt-3 text-sm leading-relaxed text-slate-600 dark:text-slate-300"
                >
                  Azure security services, identity management, and compliance features.
                </p>
              </article>
              <article
                class="education-card flex flex-col rounded-2xl border border-slate-200 bg-white p-6 transition-colors hover:border-primary-400/60 hover:shadow-md dark:border-slate-800 dark:bg-slate-900/50 dark:hover:border-primary-400/40 dark:hover:bg-slate-900"
              >
                <header>
                  <h3
                    class="education-institution text-lg font-semibold text-slate-900 dark:text-white"
                  >
                    Företagsuniversitetet
                  </h3>
                  <p
                    class="education-dates mt-1 font-mono text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400"
                  >
                    Mar 2023
                  </p>
                </header>
                <p
                  class="education-degree mt-5 text-balance text-sm font-medium text-slate-900 dark:text-slate-100"
                >
                  Certified ISO 27001 Lead Implementer
                </p>
                <p class="education-field mt-0.5 text-sm text-slate-500 dark:text-slate-400">
                  Information Security Management
                </p>
                <p
                  class="education-description mt-3 text-sm leading-relaxed text-slate-600 dark:text-slate-300"
                >
                  Intensive certification program for implementing and managing ISO 27001 ISMS.
                </p>
              </article>
              <article
                class="education-card flex flex-col rounded-2xl border border-slate-200 bg-white p-6 transition-colors hover:border-primary-400/60 hover:shadow-md dark:border-slate-800 dark:bg-slate-900/50 dark:hover:border-primary-400/40 dark:hover:bg-slate-900"
              >
                <header>
                  <h3
                    class="education-institution text-lg font-semibold text-slate-900 dark:text-white"
                  >
                    EC-Council
                  </h3>
                  <p
                    class="education-dates mt-1 font-mono text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400"
                  >
                    Oct 2022
                  </p>
                </header>
                <p
                  class="education-degree mt-5 text-balance text-sm font-medium text-slate-900 dark:text-slate-100"
                >
                  Certified Ethical Hacker (CEH)
                </p>
                <p class="education-field mt-0.5 text-sm text-slate-500 dark:text-slate-400">
                  Cybersecurity
                </p>
                <p
                  class="education-description mt-3 text-sm leading-relaxed text-slate-600 dark:text-slate-300"
                >
                  Ethical hacking methodologies, penetration testing, and vulnerability assessment.
                </p>
              </article>
              <article
                class="education-card flex flex-col rounded-2xl border border-slate-200 bg-white p-6 transition-colors hover:border-primary-400/60 hover:shadow-md dark:border-slate-800 dark:bg-slate-900/50 dark:hover:border-primary-400/40 dark:hover:bg-slate-900"
              >
                <header>
                  <h3
                    class="education-institution text-lg font-semibold text-slate-900 dark:text-white"
                  >
                    KTH Royal Institute of Technology
                  </h3>
                  <p
                    class="education-dates mt-1 font-mono text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400"
                  >
                    Aug 2017 — Jun 2022
                  </p>
                </header>
                <p
                  class="education-degree mt-5 text-balance text-sm font-medium text-slate-900 dark:text-slate-100"
                >
                  M.Sc. Medical Engineering
                </p>
                <p class="education-field mt-0.5 text-sm text-slate-500 dark:text-slate-400">
                  Medical Technology and Bioengineering
                </p>
                <p
                  class="education-description mt-3 text-sm leading-relaxed text-slate-600 dark:text-slate-300"
                >
                  Specialized in medical imaging, signal processing, and healthcare informatics.
                  Thesis on AI-driven diagnostic systems.
                </p>
              </article>
              <article
                class="education-card flex flex-col rounded-2xl border border-slate-200 bg-white p-6 transition-colors hover:border-primary-400/60 hover:shadow-md dark:border-slate-800 dark:bg-slate-900/50 dark:hover:border-primary-400/40 dark:hover:bg-slate-900"
              >
                <header>
                  <h3
                    class="education-institution text-lg font-semibold text-slate-900 dark:text-white"
                  >
                    Lund University (LTH)
                  </h3>
                  <p
                    class="education-dates mt-1 font-mono text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400"
                  >
                    Jan 2020 — Jun 2021
                  </p>
                </header>
                <p
                  class="education-degree mt-5 text-balance text-sm font-medium text-slate-900 dark:text-slate-100"
                >
                  B.Sc. Biomedical Engineering (Exchange)
                </p>
                <p class="education-field mt-0.5 text-sm text-slate-500 dark:text-slate-400">
                  Biomedical Engineering
                </p>
                <p
                  class="education-description mt-3 text-sm leading-relaxed text-slate-600 dark:text-slate-300"
                >
                  Exchange program focusing on medical device development and regulatory affairs.
                </p>
              </article>
            </template>
          </div>
        </div>
      </section>

      <!-- Publications/Research Section -->
      <section id="publications" class="bg-slate-50 py-16 md:py-20 dark:bg-slate-900/40">
        <div class="mx-auto max-w-7xl px-6 sm:px-8 lg:px-12">
          <header class="mb-6 md:mb-8">
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
            v-else-if="documents.length"
            class="documents-grid grid gap-6 sm:grid-cols-2 xl:grid-cols-3"
          >
            <DocumentCard v-for="document in documents" :key="document.id" :document="document" />
          </div>
          <!-- Quiet degradation (D3-UX-02): documents are baked at SSG time,
               so this renders only when the bake AND the client refetch both
               failed — a one-line note, not a raw axios string in a red wall. -->
          <p v-else class="text-sm text-slate-500 dark:text-slate-400">
            Publications are unavailable right now.
          </p>
        </div>
      </section>

      <!-- Projects Section -->
      <section id="projects" class="bg-white py-16 md:py-20 dark:bg-slate-950">
        <div class="mx-auto max-w-7xl px-6 sm:px-8 lg:px-12">
          <header class="mb-6 md:mb-8">
            <h2
              class="section-title text-3xl font-semibold tracking-tight text-slate-900 sm:text-4xl dark:text-white"
            >
              GitHub
            </h2>
          </header>

          <!-- GitHub Stats with Featured Projects -->
          <GitHubStats username="Dashtid" @loaded="projectCardAnimation.refresh()" />
        </div>
      </section>
      <!-- About Section -->
      <section id="about" class="bg-slate-50 py-16 md:py-20 dark:bg-slate-900/40">
        <div class="mx-auto max-w-7xl px-6 sm:px-8 lg:px-12">
          <header class="mb-6 md:mb-8">
            <h2
              class="section-title text-3xl font-semibold tracking-tight text-slate-900 sm:text-4xl dark:text-white"
            >
              About Me
            </h2>
          </header>

          <div class="about-layout grid max-w-6xl items-start gap-10 lg:grid-cols-[280px_1fr]">
            <div class="about-block">
              <picture>
                <source srcset="/images/optimized/cropped.avif" type="image/avif" />
                <source srcset="/images/optimized/cropped.webp" type="image/webp" />
                <!-- FRONTEND-PERF-08 / D3-PRUNE-01: PNG fallback is a
                     640px-wide palette PNG (180 KB, resized from the 851px
                     master in Sprint 4 — the element renders <=500px wide).
                     >97% of clients hit the AVIF/WebP branches above so the
                     fallback path is rarely walked, but the saving still
                     applies to Lighthouse's total-payload budget and to
                     older browsers/screen readers that fall back. -->
                <img
                  src="/images/optimized/cropped.png"
                  alt="David Dashti - product security specialist for medical software"
                  class="mx-auto h-auto w-[260px] rounded-2xl object-cover ring-1 ring-slate-200 lg:mx-0 lg:w-full dark:ring-slate-800"
                  width="280"
                  height="326"
                  loading="lazy"
                />
              </picture>
            </div>
            <div class="about-block max-w-[65ch] text-slate-600 dark:text-slate-300">
              <p
                class="text-balance text-lg font-medium leading-relaxed text-slate-800 dark:text-slate-100"
              >
                Product security specialist for medical software. I build security into medical
                devices from design through premarket submission.
              </p>
              <p class="mt-5 leading-relaxed">
                I'm a biomedical engineer working as a QA/RA &amp; Security Specialist at Hermes
                Medical Solutions, where I secure nuclear-medicine imaging software and help clear
                it for market — premarket cybersecurity, threat modeling, and security risk
                management, grounded in FDA premarket guidance and IEC 81001-5-1. As AI moves into
                these devices, I've started an early gap analysis against the EU AI Act to
                understand what it will ask of us. I also build my own tools — an internal RAG
                system over company data, still a work in progress, and in-house security tooling
                and tests.
              </p>
              <div class="mt-6">
                <p
                  class="font-mono text-xs uppercase tracking-[0.2em] text-slate-500 dark:text-slate-400"
                >
                  Current focus areas
                </p>
                <ul class="mt-4 space-y-3">
                  <li class="flex gap-3 leading-relaxed">
                    <span
                      class="mt-2.5 h-1.5 w-1.5 shrink-0 rounded-full bg-primary-500"
                      aria-hidden="true"
                    ></span>
                    Premarket cybersecurity for medical software (FDA, IEC 81001-5-1)
                  </li>
                  <li class="flex gap-3 leading-relaxed">
                    <span
                      class="mt-2.5 h-1.5 w-1.5 shrink-0 rounded-full bg-primary-500"
                      aria-hidden="true"
                    ></span>
                    Security risk management and threat modeling across the product lifecycle
                  </li>
                  <li class="flex gap-3 leading-relaxed">
                    <span
                      class="mt-2.5 h-1.5 w-1.5 shrink-0 rounded-full bg-primary-500"
                      aria-hidden="true"
                    ></span>
                    Supporting market clearance for medical devices (FDA 510(k), EU MDR)
                  </li>
                  <li class="flex gap-3 leading-relaxed">
                    <span
                      class="mt-2.5 h-1.5 w-1.5 shrink-0 rounded-full bg-primary-500"
                      aria-hidden="true"
                    ></span>
                    Securing the AI now entering medical devices — an early EU AI Act gap analysis,
                    underway
                  </li>
                </ul>
              </div>
              <div class="mt-6">
                <p
                  class="font-mono text-xs uppercase tracking-[0.2em] text-slate-500 dark:text-slate-400"
                >
                  Technical skills
                </p>
                <p class="mt-4 leading-relaxed">
                  Windows Server, Unix/Linux, Docker, Kubernetes, PowerShell, Bash, Python, Rust and
                  Git
                </p>
              </div>
              <p class="mt-6 leading-relaxed">
                I care about making healthcare technology safer and more trustworthy — protecting
                patients by making sure the software, and increasingly the AI, inside their care is
                secure by design.
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
import {
  computed,
  onMounted,
  onServerPrefetch,
  nextTick,
  watch,
  defineAsyncComponent,
  defineComponent,
  type Component
} from 'vue'
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
// Decoration must never take down content (D3-FE-01): the three-* chunk is
// excluded from the SW precache, so an offline dark-mode revisit (or a load
// stalled past the timeout) rejects here — and an unhandled rejection would
// bubble into App.vue's ErrorBoundary and swap the ENTIRE working page for
// "Something went wrong". Render nothing instead.
const NoopBackground = defineComponent({ name: 'NoopBackground', render: () => null })
const ThreeHeroBackground = defineAsyncComponent({
  loader: async (): Promise<Component> => {
    try {
      return (await import('../components/ThreeHeroBackground.vue')).default
    } catch {
      return NoopBackground
    }
  },
  errorComponent: NoopBackground, // covers the timeout path (not routed through loader rejection)
  delay: 0,
  timeout: 10000
})
import { useHead } from '@unhead/vue'
import { logger } from '../utils/logger'

useHead({
  title: 'David Dashti | Cybersecurity in Healthcare',
  meta: [
    {
      name: 'description',
      content:
        'Product security specialist for medical software — premarket cybersecurity, security risk management, and regulatory clearance for medical devices and healthcare AI.'
    }
  ],
  link: [{ rel: 'canonical', href: 'https://dashti.se/' }]
})

const portfolioStore = usePortfolioStore()

// INFRA-002: fetch portfolio data during the SSG render so vite-ssg
// captures the populated Pinia state into __INITIAL_STATE__ and clients
// see hydrated content immediately. onServerPrefetch is awaited by the
// server renderer before the HTML is captured, and — unlike the previous
// top-level `await` — it keeps setup() compiled as a synchronous
// function.
//
// That distinction is load-bearing: an async setup() under App.vue's
// route <Transition> made Vue discard the entire prerendered DOM on
// every page load and re-render it client-side through the transition
// (a full leave/enter cycle at startup). With a populated
// __INITIAL_STATE__ the swap was near-atomic; with an empty one (SSG
// build couldn't reach the API, or e2e where the API is cross-origin)
// the page went blank until the refetch settled — seconds on slow
// machines, and the source of the CI-only `h1Count = 0` e2e failure.
//
// Failures here MUST NOT throw — a throw would fail the entire SSG
// build over a transient API blip. The static fallback content below
// carries the page when the API is unreachable.
//
// One retry after a short pause: build infrastructure (GitHub runners,
// Vercel) shares egress IPs and intermittently loses 1-4 of the parallel
// fetches against the API — a Vercel build shipped with education and
// skills baked empty while companies and projects succeeded. Since
// hydrated clients trust the baked payload, a partial bake would
// otherwise stick for every visitor until the next deploy.
onServerPrefetch(async () => {
  if (portfolioStore.companies.length === 0) {
    try {
      await portfolioStore.fetchAllData()
      if (portfolioStore.error) {
        await new Promise(resolve => setTimeout(resolve, 2000))
        await portfolioStore.fetchAllData()
      }
    } catch (error) {
      logger.error('Portfolio data fetch failed during SSG render:', error)
    }
  }
})

// Computed properties for education from API - sorted by end_date (newest first)
const education = computed(() => {
  const items = portfolioStore.education || []
  return [...items].sort((a, b) => {
    const dateA = a.end_date ? new Date(a.end_date).getTime() : Date.now()
    const dateB = b.end_date ? new Date(b.end_date).getTime() : Date.now()
    return dateB - dateA
  })
})

// Documents come from the store (baked into __INITIAL_STATE__ at SSG time,
// D3-UX-02); the skeleton shows only while a live fetch is actually pending
// with nothing baked to show.
const documents = computed(() => portfolioStore.documents || [])
const documentsLoading = computed(() => portfolioStore.loading && documents.value.length === 0)

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

// PERF-03: IntersectionObserver-driven entrance animations replace the
// previous GSAP + ScrollTrigger pass. Stagger is now a per-element CSS
// transition-delay rather than a tween timeline; the animation itself
// is a CSS transition driven by the `[data-anim]` attribute (defined
// in the scoped <style> below). Drops ~45 KB gzipped of gsap from the
// home-page critical path.
//
// These MUST be called here in setup, not inside onMounted: the composable
// registers its own onMounted/onBeforeUnmount hooks, and after an await
// inside an onMounted callback Vue has no active instance to register
// against — the previous call site silently made every entrance animation
// dead code. Document cards render only after the fetch below resolves,
// so that batch is re-scanned via refresh() once the data is in the DOM.
useIntersectionAnimation('.experience-card', { stagger: 0.12 })
useIntersectionAnimation('.education-card', { stagger: 0.12 })
// Repo cards render only after GitHubStats' lazy fetch resolves —
// re-scanned via @loaded on the <GitHubStats> tag, like document cards.
const projectCardAnimation = useIntersectionAnimation('.project-card', { stagger: 0.12 })
const documentCardAnimation = useIntersectionAnimation('.document-card', { stagger: 0.12 })
useIntersectionAnimation('.section-title', { stagger: 0 })
useIntersectionAnimation('.about-block', { stagger: 0.12 })

// Load data on mount. Portfolio data (documents included, D3-UX-02)
// normally arrives via __INITIAL_STATE__ (baked by the onServerPrefetch
// above); the fetch here is the client-side fallback for an empty
// hydration payload — it fills the store after mount without blocking
// hydration, so the prerendered DOM (and its static fallback content)
// stays on screen while it runs.
onMounted(() => {
  // Refetch when the baked payload looks incomplete — not just fully
  // empty. Build-time fetches fail per-collection (a live deploy shipped
  // education/skills empty next to populated companies/projects), and a
  // hydrated client trusts whatever was baked, so a partial bake would
  // otherwise stay partial for every visitor until the next deploy.
  const bakePartial =
    portfolioStore.error !== null ||
    portfolioStore.companies.length === 0 ||
    portfolioStore.skills.length === 0 ||
    portfolioStore.projects.length === 0 ||
    portfolioStore.education.length === 0 ||
    portfolioStore.documents.length === 0
  if (bakePartial) {
    Promise.resolve(portfolioStore.fetchAllData()).catch((error: unknown) => {
      logger.error('Portfolio data fetch failed after mount:', error)
    })
  }
})

// Document cards render whenever the store fills (baked payload or the
// fallback refetch above) — hand the new elements to the observer then.
watch(
  () => documents.value.length,
  async () => {
    await nextTick()
    documentCardAnimation.refresh()
  }
)
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
/* Transition lives on [data-anim] (both states): CSS transitions run from
   the AFTER-change style, so a transition declared only on the hidden
   state makes the reveal snap. border/bg/color are included so cards
   whose transition-colors utility this rule overrides (scoped beats the
   utilities layer) keep their hover feedback. */
:deep([data-anim]) {
  transition:
    opacity 0.5s ease-out,
    transform 0.5s ease-out,
    box-shadow 0.2s ease,
    border-color 0.2s ease,
    background-color 0.2s ease,
    color 0.2s ease;
}

:deep([data-anim='hidden']) {
  opacity: 0;
  transform: translate3d(0, 30px, 0);
  will-change: opacity, transform;
}

:deep([data-anim='visible']) {
  opacity: 1;
  transform: translate3d(0, 0, 0);
  will-change: auto;
}

@media (prefers-reduced-motion: reduce) {
  :deep([data-anim]) {
    transition: none !important;
    transform: none !important;
  }
}

/* No html rule here: scoped selectors can't reach <html>, and the real
   (reduced-motion-aware) scroll-behavior lives in style.css @layer base. */

:deep(.navbar-custom) {
  z-index: 1000;
}
</style>
