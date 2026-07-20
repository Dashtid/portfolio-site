<template>
  <footer
    class="footer-section border-t border-slate-200 bg-white py-16 text-slate-500 dark:border-slate-800 dark:bg-slate-950 dark:text-slate-400"
  >
    <div
      class="mx-auto flex max-w-7xl flex-col items-center gap-5 px-6 text-center sm:px-8 lg:px-12"
    >
      <span
        class="footer-name text-base font-semibold tracking-tight text-slate-900 dark:text-white"
      >
        David Dashti
      </span>
      <p class="footer-tagline text-sm">Product security for medical software</p>

      <div class="flex items-center gap-3">
        <a
          href="https://www.linkedin.com/in/david-dashti/"
          target="_blank"
          rel="noopener noreferrer"
          class="social-link inline-flex h-10 w-10 items-center justify-center rounded-full border border-slate-200 text-slate-600 transition-colors hover:border-primary-400/60 hover:text-primary-600 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-primary-500 dark:border-slate-800 dark:text-slate-300 dark:hover:border-primary-400/40 dark:hover:text-primary-400"
          aria-label="LinkedIn Profile (opens in new tab)"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="currentColor"
            aria-hidden="true"
          >
            <path
              d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"
            />
          </svg>
        </a>
        <a
          href="https://github.com/Dashtid"
          target="_blank"
          rel="noopener noreferrer"
          class="social-link inline-flex h-10 w-10 items-center justify-center rounded-full border border-slate-200 text-slate-600 transition-colors hover:border-primary-400/60 hover:text-primary-600 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-primary-500 dark:border-slate-800 dark:text-slate-300 dark:hover:border-primary-400/40 dark:hover:text-primary-400"
          aria-label="GitHub Profile (opens in new tab)"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="currentColor"
            aria-hidden="true"
          >
            <path
              d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"
            />
          </svg>
        </a>
      </div>

      <!-- D3-CNT-03: text links close the page usefully; the full-width
           border-t below replaces the orphaned 64px hairline gradient -->
      <nav aria-label="Footer">
        <ul class="flex flex-wrap items-center justify-center gap-x-6 gap-y-2 text-sm">
          <li v-for="link in footerLinks" :key="link.href">
            <a
              :href="link.href"
              class="transition-colors hover:text-primary-600 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-primary-500 dark:hover:text-primary-400"
            >
              {{ link.name }}
            </a>
          </li>
        </ul>
      </nav>
    </div>

    <div
      class="mx-auto mt-10 max-w-7xl border-t border-slate-200 px-6 pt-6 text-center sm:px-8 lg:px-12 dark:border-slate-800"
    >
      <!-- dark:text-slate-400 — slate-500 on slate-950 fails WCAG AA at this size -->
      <p class="footer-copyright text-xs text-slate-500 dark:text-slate-400">
        &copy; {{ currentYear }} David Dashti. All rights reserved.
      </p>
    </div>
  </footer>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const currentYear = computed<number>(() => new Date().getFullYear())

const footerLinks = [
  { name: 'Experience', href: '/#experience' },
  { name: 'Education', href: '/#education' },
  { name: 'Publications', href: '/#publications' },
  { name: 'Projects', href: '/#projects' },
  { name: 'About', href: '/#about' }
]
</script>
