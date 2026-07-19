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
// prerendered /404 path. Unknown URLs reach Vercel's SPA rewrite (200 +
// home HTML), so the honest signal for crawlers is the noindex below —
// without it every mistyped URL was a soft-404 indexing the homepage.
useHead({
  title: '404 — Page Not Found | David Dashti',
  meta: [{ name: 'robots', content: 'noindex' }]
})
</script>
