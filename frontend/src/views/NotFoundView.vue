<template>
  <div class="not-found-page flex min-h-screen flex-col bg-white dark:bg-slate-950">
    <NavBar />

    <main
      id="main-content"
      role="main"
      tabindex="-1"
      class="flex flex-1 items-center justify-center px-6 pt-20"
    >
      <div class="max-w-xl text-center">
        <p class="font-mono text-xs uppercase tracking-[0.2em] text-slate-500 dark:text-slate-400">
          HTTP 404 — page not found
        </p>

        <h1
          class="not-found-code mt-6 font-mono text-8xl font-semibold tracking-tight text-slate-900 dark:text-white"
        >
          404
        </h1>

        <p
          class="mx-auto mt-6 max-w-md text-balance text-base font-light leading-relaxed text-slate-500 sm:text-lg dark:text-slate-400"
        >
          This page doesn't exist — the link may be stale, or the address mistyped.
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
    </main>

    <FooterSection />
  </div>
</template>

<script setup lang="ts">
import { useHead } from '@unhead/vue'
import NavBar from '../components/NavBar.vue'
import FooterSection from '../components/FooterSection.vue'

// D3-UX-01: designed 404. Served for the router catch-all and the
// prerendered /404 path. Since S3 the vercel.json rewrite serves this
// document with a REAL 404 status (verified live), so the noindex below is
// belt-and-braces rather than the only signal it used to be.
// The og/canonical tags in index.html are the HOMEPAGE's, and every
// prerendered page inherits them unless it overrides. On /404 that meant a
// dead link pasted into LinkedIn or Slack unfurled as the live homepage —
// a broken URL presenting itself as working — and the page declared
// rel=canonical to a different, 200 document. noindex + the real 404 status
// mean this was never an indexing risk, but the preview was a lie.
useHead({
  title: '404 — Page Not Found | David Dashti',
  link: [{ rel: 'canonical', href: 'https://dashti.se/404' }],
  meta: [
    { name: 'robots', content: 'noindex' },
    { name: 'description', content: 'This page does not exist.' },
    { property: 'og:title', content: 'Page not found — dashti.se' },
    { property: 'og:description', content: 'This page does not exist.' },
    { property: 'og:url', content: 'https://dashti.se/404' },
    { name: 'twitter:title', content: 'Page not found — dashti.se' },
    { name: 'twitter:description', content: 'This page does not exist.' }
  ]
})
</script>
