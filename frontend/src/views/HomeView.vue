<template>
  <div class="portfolio-home">
    <!-- Navigation Bar -->
    <NavBar />

    <!-- Main content area for accessibility -->
    <main id="main-content" role="main" tabindex="-1">
      <!-- Hero Section (D3-DSN-03): typography-led, left-aligned on a
           12-col grid. Light mode = engineering-paper dot grid + a
           self-drawing signal trace through labeled lifecycle gates;
           dark mode = seeded Canvas2D signal field + a CSS radial glow
           behind the headline (present at SSG first paint, so the page
           is never flat black before hydration). -->
      <section
        id="hero"
        class="hero-section relative flex min-h-screen items-center overflow-hidden bg-white pb-24 pt-20 dark:bg-slate-950"
      >
        <!-- Light: dot grid, radially masked so it reads as paper, not
             wallpaper. Pure CSS — no JS required for first paint. -->
        <div
          class="pointer-events-none absolute inset-0 z-0 opacity-60 [background-image:radial-gradient(circle,#cbd5e1_1px,transparent_1px)] [background-size:26px_26px] [mask-image:radial-gradient(ellipse_75%_65%_at_55%_42%,black,transparent)] dark:hidden"
          aria-hidden="true"
        ></div>

        <!-- Dark: radial glow behind the headline (CSS, SSG-safe) -->
        <div
          class="pointer-events-none absolute -left-32 top-1/4 z-0 hidden h-[36rem] w-[64rem] [background-image:radial-gradient(closest-side,rgba(47,136,232,0.16),transparent)] dark:block"
          aria-hidden="true"
        ></div>
        <!-- Dark: seeded Canvas2D field (~2KB) — replaced the 122KB gzip
             three.js starfield whose output measured below perceptual
             threshold. Renders a static frame under reduced motion. -->
        <CanvasHeroField v-if="isDark" key="dark" />

        <div
          class="relative z-[2] mx-auto grid w-full max-w-7xl items-center gap-12 px-6 sm:px-8 lg:grid-cols-12 lg:gap-8 lg:px-12"
        >
          <div class="lg:col-span-7">
            <p
              class="font-mono text-xs uppercase tracking-[0.2em] text-slate-500 dark:text-slate-400"
            >
              David Dashti · Product Security
            </p>

            <h1
              class="custom-hero-title mt-5 max-w-[16ch] text-balance text-hero font-semibold text-slate-900 dark:text-white"
            >
              Product security for medical software<span
                class="text-primary-600 dark:text-primary-400"
                >.</span
              >
            </h1>

            <p
              class="custom-hero-lead mt-6 max-w-xl text-balance text-base font-light leading-relaxed text-slate-600 sm:text-lg dark:text-slate-400"
            >
              Securing medical software from design through market clearance — and, increasingly,
              the AI moving into the devices themselves — at Hermes Medical Solutions, Stockholm.
            </p>

            <div class="mt-8 flex flex-wrap items-center gap-3">
              <a
                href="https://www.linkedin.com/in/david-dashti/"
                target="_blank"
                rel="noopener noreferrer"
                class="inline-flex items-center gap-2 rounded-lg bg-primary-600 px-5 py-2.5 text-sm font-medium text-white transition-colors hover:bg-primary-700 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-primary-500 dark:bg-primary-500 dark:text-slate-950 dark:hover:bg-primary-400"
              >
                Connect on LinkedIn
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

            <!-- D3-CNT-03 proof row, retyped into the HERO-01 layout -->
            <p
              class="mt-10 font-mono text-[11px] uppercase tracking-[0.18em] text-slate-400 dark:text-slate-500"
            >
              FDA Premarket &middot; IEC 81001-5-1 &middot; EU MDR &middot; Security+
            </p>
          </div>

          <!-- Light-mode motif: self-drawing signal trace through labeled
               lifecycle gates (audit-approved direction). CSS animates the
               draw once on load; fully drawn under reduced motion. lg-only
               — mobile and dark mode each keep a single quiet backdrop. -->
          <div class="relative hidden lg:col-span-5 lg:block dark:lg:hidden" aria-hidden="true">
            <svg
              class="signal-trace w-full text-slate-300"
              viewBox="0 0 520 400"
              fill="none"
              role="presentation"
            >
              <!-- staircase trace: each gate one step up — design to clearance -->
              <path
                class="trace-path"
                d="M8 330 H74 L138 275 H204 L268 220 H334 L398 165 H464 L512 124"
                stroke="currentColor"
                stroke-width="1.5"
                pathLength="1"
              />
              <g class="trace-nodes">
                <g class="trace-node" style="--node-i: 0">
                  <rect x="36" y="325" width="10" height="10" rx="2" class="node-box" />
                  <text x="41" y="352" text-anchor="middle" class="node-label">Threat model</text>
                </g>
                <g class="trace-node" style="--node-i: 1">
                  <rect x="166" y="270" width="10" height="10" rx="2" class="node-box" />
                  <text x="171" y="297" text-anchor="middle" class="node-label">Secure SDLC</text>
                </g>
                <g class="trace-node" style="--node-i: 2">
                  <rect x="296" y="215" width="10" height="10" rx="2" class="node-box" />
                  <text x="301" y="242" text-anchor="middle" class="node-label">Fuzzing</text>
                </g>
                <g class="trace-node" style="--node-i: 3">
                  <rect x="426" y="160" width="10" height="10" rx="2" class="node-box" />
                  <text x="431" y="187" text-anchor="middle" class="node-label">SBOM</text>
                </g>
                <g class="trace-node" style="--node-i: 4">
                  <circle cx="512" cy="124" r="5" class="node-end" />
                  <text x="518" y="106" text-anchor="end" class="node-label node-label-end">
                    Clearance
                  </text>
                </g>
              </g>
            </svg>
          </div>
        </div>

        <a
          href="#experience"
          class="absolute bottom-8 left-1/2 z-[2] -translate-x-1/2 text-slate-400 transition-colors hover:text-primary-600 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-primary-500 dark:text-slate-500 dark:hover:text-primary-400 [@media(max-height:640px)]:hidden"
          aria-label="Scroll to experience"
        >
          <svg
            class="h-5 w-5"
            fill="none"
            viewBox="0 0 24 24"
            stroke-width="2"
            stroke="currentColor"
            aria-hidden="true"
          >
            <path stroke-linecap="round" stroke-linejoin="round" d="M19 14l-7 7m0 0l-7-7m7 7V3" />
          </svg>
        </a>
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
      <section id="experience" class="bg-slate-50 py-16 md:py-20 dark:bg-surface-1">
        <div class="mx-auto max-w-7xl px-6 sm:px-8 lg:px-12">
          <header class="mb-6 md:mb-8">
            <h2 class="section-title text-title font-semibold text-slate-900 dark:text-white">
              Experience
            </h2>
          </header>

          <div class="experience-list grid gap-6 sm:grid-cols-2 xl:grid-cols-3">
            <!-- Dynamic content from backend or static fallback.
                 D3-DSN-04: hierarchy swapped — the hiring-relevant role
                 title leads at full weight, the company name supports.
                 Logo chips are normalized 56px squares (wordmarks used to
                 balloon to 128px tiles); description clamps at 3 lines so
                 card bottoms align. Pre-2020 roles collapse into the
                 compact 'Earlier' list below the grid. -->
            <template v-if="companies.length">
              <article
                v-for="company in recentCompanies"
                :key="company.id"
                class="experience-card group relative flex flex-col rounded-2xl border border-slate-200 bg-white p-6 transition-colors hover:border-primary-400/60 hover:shadow-md dark:border-slate-800 dark:bg-surface-2 dark:hover:border-primary-400/40 dark:hover:bg-surface-3"
              >
                <header class="flex items-start gap-4">
                  <img
                    v-if="company.logo_url"
                    :src="company.logo_url"
                    :alt="`${company.name} Logo`"
                    class="card-logo h-14 w-14 shrink-0 rounded-lg bg-white object-contain p-2 ring-1 ring-slate-200 dark:bg-slate-100 dark:ring-slate-600"
                    width="56"
                    height="56"
                    loading="lazy"
                  />
                  <div class="min-w-0 flex-1">
                    <h3
                      class="job-title text-balance text-base font-semibold leading-snug text-slate-900 dark:text-white"
                    >
                      {{ company.title }}
                    </h3>
                    <p class="company-name mt-1 text-sm text-slate-500 dark:text-slate-400">
                      {{ company.name }}
                    </p>
                  </div>
                </header>
                <p
                  class="company-dates mt-4 font-mono text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400"
                >
                  {{ formatDate(company.start_date) }} —
                  {{ company.end_date ? formatDate(company.end_date) : 'Present' }}
                  <template v-if="company.location"> &middot; {{ company.location }}</template>
                </p>
                <p
                  class="company-description mt-3 line-clamp-3 text-sm leading-relaxed text-slate-600 dark:text-slate-300"
                >
                  {{ company.description }}
                </p>

                <router-link
                  :to="{ name: 'experience-detail', params: { id: company.id } }"
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
                class="experience-card flex flex-col rounded-2xl border border-slate-200 bg-white p-6 transition-colors hover:border-primary-400/60 hover:shadow-md dark:border-slate-800 dark:bg-surface-2 dark:hover:border-primary-400/40 dark:hover:bg-surface-3"
              >
                <header>
                  <h3
                    class="job-title text-balance text-base font-semibold leading-snug text-slate-900 dark:text-white"
                  >
                    QA/RA &amp; Security Specialist
                  </h3>
                  <p class="company-name mt-1 text-sm text-slate-500 dark:text-slate-400">
                    Hermes Medical Solutions
                  </p>
                </header>
                <p
                  class="company-dates mt-4 font-mono text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400"
                >
                  May 2024 — Present &middot; Stockholm, Sweden
                </p>
                <p
                  class="company-description mt-3 line-clamp-3 text-sm leading-relaxed text-slate-600 dark:text-slate-300"
                >
                  QA/RA &amp; Security Specialist at Hermes Medical Solutions, leading product
                  security and premarket cybersecurity — threat modeling, security risk management,
                  and regulatory clearance — for nuclear-medicine imaging software.
                </p>
              </article>
              <article
                class="experience-card flex flex-col rounded-2xl border border-slate-200 bg-white p-6 transition-colors hover:border-primary-400/60 hover:shadow-md dark:border-slate-800 dark:bg-surface-2 dark:hover:border-primary-400/40 dark:hover:bg-surface-3"
              >
                <header>
                  <h3
                    class="job-title text-balance text-base font-semibold leading-snug text-slate-900 dark:text-white"
                  >
                    Incident Support Specialist, Nordics
                  </h3>
                  <p class="company-name mt-1 text-sm text-slate-500 dark:text-slate-400">
                    Philips Healthcare
                  </p>
                </header>
                <p
                  class="company-dates mt-4 font-mono text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400"
                >
                  Mar 2022 — May 2024 &middot; Stockholm, Sweden
                </p>
                <p
                  class="company-description mt-3 line-clamp-3 text-sm leading-relaxed text-slate-600 dark:text-slate-300"
                >
                  Remote Service Engineer providing Level 1 support for Intellispace Portal (ISP)
                  and Intellispace Cardiovascular (ISCV) systems across the Nordics.
                </p>
              </article>
              <article
                class="experience-card flex flex-col rounded-2xl border border-slate-200 bg-white p-6 transition-colors hover:border-primary-400/60 hover:shadow-md dark:border-slate-800 dark:bg-surface-2 dark:hover:border-primary-400/40 dark:hover:bg-surface-3"
              >
                <header>
                  <h3
                    class="job-title text-balance text-base font-semibold leading-snug text-slate-900 dark:text-white"
                  >
                    Biomedical Engineer, Medical Imaging and Physiology
                  </h3>
                  <p class="company-name mt-1 text-sm text-slate-500 dark:text-slate-400">
                    Karolinska University Hospital
                  </p>
                </header>
                <p
                  class="company-dates mt-4 font-mono text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400"
                >
                  Jun 2021 — Dec 2021 &middot; Stockholm, Sweden
                </p>
                <p
                  class="company-description mt-3 line-clamp-3 text-sm leading-relaxed text-slate-600 dark:text-slate-300"
                >
                  First-line support for imaging equipment fleet, incident management for RIS/PACS
                  systems, working with GE, Philips, and Siemens solutions.
                </p>
              </article>
            </template>
          </div>

          <!-- D3-DSN-04: pre-2020 roles as a compact list — eight equal
               cards gave summer jobs the same billing as the flagship
               role. Every entry keeps a real link to its detail page, so
               nothing falls out of the crawl. -->
          <div v-if="earlierCompanies.length" class="mt-10">
            <h3
              class="font-mono text-xs uppercase tracking-[0.2em] text-slate-500 dark:text-slate-400"
            >
              Earlier
            </h3>
            <ul
              class="mt-3 divide-y divide-slate-200 rounded-2xl border border-slate-200 bg-white dark:divide-slate-800 dark:border-slate-800 dark:bg-surface-2"
            >
              <li v-for="company in earlierCompanies" :key="company.id">
                <router-link
                  :to="{ name: 'experience-detail', params: { id: company.id } }"
                  class="group flex items-center gap-4 px-5 py-3.5 transition-colors first:rounded-t-2xl last:rounded-b-2xl hover:bg-slate-50 focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-primary-500 dark:hover:bg-surface-3"
                >
                  <img
                    v-if="company.logo_url"
                    :src="company.logo_url"
                    :alt="`${company.name} Logo`"
                    class="h-9 w-9 shrink-0 rounded-md bg-white object-contain p-1 ring-1 ring-slate-200 dark:bg-slate-100 dark:ring-slate-600"
                    width="36"
                    height="36"
                    loading="lazy"
                  />
                  <span class="flex min-w-0 flex-1 flex-col sm:flex-row sm:items-baseline sm:gap-2">
                    <span class="truncate text-sm font-medium text-slate-900 dark:text-white">
                      {{ company.title }}
                    </span>
                    <span class="truncate text-sm text-slate-500 dark:text-slate-400">
                      {{ company.name }}
                    </span>
                  </span>
                  <span class="shrink-0 font-mono text-xs text-slate-500 dark:text-slate-400">
                    {{ yearRange(company) }}
                  </span>
                  <svg
                    class="h-3.5 w-3.5 shrink-0 text-slate-400 transition-transform group-hover:translate-x-0.5 dark:text-slate-500"
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
              </li>
            </ul>
          </div>
        </div>
      </section>

      <!-- Education Section -->
      <section id="education" class="bg-white py-16 md:py-20 dark:bg-slate-950">
        <div class="mx-auto max-w-7xl px-6 sm:px-8 lg:px-12">
          <header class="mb-6 md:mb-8">
            <h2 class="section-title text-title font-semibold text-slate-900 dark:text-white">
              Education
            </h2>
          </header>

          <div class="education-grid grid gap-6 sm:grid-cols-2 xl:grid-cols-3">
            <template v-if="education.length">
              <article
                v-for="edu in education"
                :key="edu.id"
                class="education-card group flex flex-col rounded-2xl border border-slate-200 bg-white p-6 transition-colors hover:border-primary-400/60 hover:shadow-md dark:border-slate-800 dark:bg-surface-1 dark:hover:border-primary-400/40 dark:hover:bg-surface-2"
              >
                <header class="flex items-start gap-4">
                  <img
                    v-if="edu.logo_url"
                    :src="edu.logo_url"
                    :alt="`${edu.institution} Logo`"
                    class="card-logo h-14 w-14 shrink-0 rounded-lg bg-white object-contain p-2 ring-1 ring-slate-200 dark:bg-slate-100 dark:ring-slate-600"
                    width="56"
                    height="56"
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
                class="education-card flex flex-col rounded-2xl border border-slate-200 bg-white p-6 transition-colors hover:border-primary-400/60 hover:shadow-md dark:border-slate-800 dark:bg-surface-1 dark:hover:border-primary-400/40 dark:hover:bg-surface-2"
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
                class="education-card flex flex-col rounded-2xl border border-slate-200 bg-white p-6 transition-colors hover:border-primary-400/60 hover:shadow-md dark:border-slate-800 dark:bg-surface-1 dark:hover:border-primary-400/40 dark:hover:bg-surface-2"
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
                class="education-card flex flex-col rounded-2xl border border-slate-200 bg-white p-6 transition-colors hover:border-primary-400/60 hover:shadow-md dark:border-slate-800 dark:bg-surface-1 dark:hover:border-primary-400/40 dark:hover:bg-surface-2"
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
                class="education-card flex flex-col rounded-2xl border border-slate-200 bg-white p-6 transition-colors hover:border-primary-400/60 hover:shadow-md dark:border-slate-800 dark:bg-surface-1 dark:hover:border-primary-400/40 dark:hover:bg-surface-2"
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
                class="education-card flex flex-col rounded-2xl border border-slate-200 bg-white p-6 transition-colors hover:border-primary-400/60 hover:shadow-md dark:border-slate-800 dark:bg-surface-1 dark:hover:border-primary-400/40 dark:hover:bg-surface-2"
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
                class="education-card flex flex-col rounded-2xl border border-slate-200 bg-white p-6 transition-colors hover:border-primary-400/60 hover:shadow-md dark:border-slate-800 dark:bg-surface-1 dark:hover:border-primary-400/40 dark:hover:bg-surface-2"
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
      <section id="publications" class="bg-slate-50 py-16 md:py-20 dark:bg-surface-1">
        <div class="mx-auto max-w-7xl px-6 sm:px-8 lg:px-12">
          <header class="mb-6 md:mb-8">
            <h2 class="section-title text-title font-semibold text-slate-900 dark:text-white">
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
            <h2 class="section-title text-title font-semibold text-slate-900 dark:text-white">
              Projects
            </h2>
          </header>

          <!-- GitHub Stats with Featured Projects -->
          <GitHubStats username="Dashtid" @loaded="projectCardAnimation.refresh()" />
        </div>
      </section>
      <!-- About Section -->
      <section id="about" class="bg-slate-50 py-16 md:py-20 dark:bg-surface-1">
        <div class="mx-auto max-w-7xl px-6 sm:px-8 lg:px-12">
          <header class="mb-6 md:mb-8">
            <h2 class="section-title text-title font-semibold text-slate-900 dark:text-white">
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

      <!-- D3-CNT-03: closing CTA band — the page ended on About with no ask -->
      <section class="bg-white py-16 dark:bg-slate-950">
        <div class="mx-auto max-w-3xl px-6 text-center">
          <h2
            class="text-2xl font-semibold tracking-tight text-slate-900 sm:text-3xl dark:text-white"
          >
            Working on premarket security for medical software?
          </h2>
          <p class="mt-3 text-slate-600 dark:text-slate-300">
            Let's talk — threat modeling, submissions, secure lifecycle, or all three.
          </p>
          <a
            href="https://www.linkedin.com/in/david-dashti/"
            target="_blank"
            rel="noopener noreferrer"
            class="mt-6 inline-flex items-center gap-2 rounded-lg bg-primary-600 px-5 py-2.5 text-sm font-medium text-white transition-colors hover:bg-primary-700 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-primary-500 dark:bg-primary-500 dark:text-slate-950 dark:hover:bg-primary-400"
          >
            Connect on LinkedIn
          </a>
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
import { computed, onMounted, onServerPrefetch, nextTick, watch } from 'vue'
import { usePortfolioStore } from '../stores/portfolio'
import type { Company } from '../types'
import NavBar from '../components/NavBar.vue'
import FooterSection from '../components/FooterSection.vue'
import BackToTop from '../components/BackToTop.vue'
import DocumentCard from '../components/DocumentCard.vue'
import GitHubStats from '../components/GitHubStats.vue'
// D3-DSN-03: the Canvas2D field is ~2KB and dependency-free, so it ships
// in the home chunk directly — no async-component/error-boundary
// scaffolding needed (that machinery existed for the 122KB three.js
// chunk this replaced). It renders a static frame under reduced motion,
// so the only gate left is the theme.
import CanvasHeroField from '../components/CanvasHeroField.vue'
import { useIntersectionAnimation } from '../composables/useIntersectionAnimation'
import { useTheme } from '../composables/useTheme'

const { isDark } = useTheme()
import { useHead } from '@unhead/vue'
import { logger } from '../utils/logger'

useHead({
  title: 'David Dashti | Product Security for Medical Software',
  script: [
    {
      type: 'application/ld+json',
      // D3-SEO-02: ProfilePage lives on the home route only — in the shared
      // index.html template it claimed every experience page WAS the profile
      // page, with dateModified frozen at 2026-04-09. Stamped at SSG time.
      innerHTML: JSON.stringify({
        '@context': 'https://schema.org',
        '@type': 'ProfilePage',
        '@id': 'https://dashti.se/#profilepage',
        name: 'David Dashti - Professional Profile',
        url: 'https://dashti.se',
        mainEntity: { '@id': 'https://dashti.se/#person' },
        dateModified: new Date().toISOString().slice(0, 10),
        isPartOf: { '@id': 'https://dashti.se/#website' }
      })
    }
  ],
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

// D3-DSN-04: the grid shows the healthcare-era roles; pre-2020 stints
// (Scania summers, military service) collapse into the compact Earlier
// list so Hermes/Philips lead the section.
const EARLIER_CUTOFF = new Date('2020-01-01').getTime()
const recentCompanies = computed(() =>
  companiesByDate.value.filter(
    c => c.start_date && new Date(c.start_date).getTime() >= EARLIER_CUTOFF
  )
)
const earlierCompanies = computed(() =>
  companiesByDate.value.filter(
    c => !c.start_date || new Date(c.start_date).getTime() < EARLIER_CUTOFF
  )
)

// Compact year label for Earlier rows: "2016" or "2014–2015"
const yearRange = (company: Company): string => {
  if (!company.start_date) return ''
  // getUTCFullYear, not getFullYear: date-only strings parse as UTC
  // midnight, so local extraction rolls Jan-1 dates back a year for
  // every UTC-negative visitor (FDF 2014 would render 2013 in New York).
  const start = new Date(company.start_date).getUTCFullYear()
  if (Number.isNaN(start)) return ''
  const end = company.end_date ? new Date(company.end_date).getUTCFullYear() : start
  return start === end || Number.isNaN(end) ? String(start) : `${start}–${end}`
}

// Methods
const formatDate = (dateString: string | null | undefined): string => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short'
  })
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

/* D3-DSN-03: light-mode signal trace. pathLength="1" on the SVG path
   normalizes the dash math so a 1-unit dash covers the whole trace; the
   draw runs once on load, and each gate node fades in as the trace
   reaches it (staggered by --node-i). Reduced motion: fully drawn. */
.trace-path {
  stroke-dasharray: 1;
  stroke-dashoffset: 1;
  animation: trace-draw 1.6s cubic-bezier(0.4, 0, 0.2, 1) 0.3s forwards;
}

.trace-node {
  opacity: 0;
  animation: trace-node-in 0.5s ease-out forwards;
  animation-delay: calc(0.45s + var(--node-i) * 0.28s);
}

.node-box {
  fill: #ffffff;
  stroke: var(--primary-500);
  stroke-width: 1.5;
}

.node-end {
  fill: var(--primary-500);
}

.node-label {
  font-family: var(--font-mono);
  font-size: 10px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  fill: var(--color-slate-500);
}

@keyframes trace-draw {
  to {
    stroke-dashoffset: 0;
  }
}

@keyframes trace-node-in {
  to {
    opacity: 1;
  }
}

@media (prefers-reduced-motion: reduce) {
  .trace-path {
    animation: none;
    stroke-dashoffset: 0;
  }

  .trace-node {
    animation: none;
    opacity: 1;
  }
}
</style>
