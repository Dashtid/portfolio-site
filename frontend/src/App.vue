<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useHead } from '@unhead/vue'
import ToastContainer from './components/ToastContainer.vue'
import ErrorBoundary from './components/ErrorBoundary.vue'
// D3-PERF-03: the hero h1 is the LCP element, but Geist's latin woff2 was
// only discovered after the vendor CSS parsed. The ?url import resolves
// the hashed build filename; preloading it starts the fetch alongside the
// CSS. Rendered on every prerendered page via SSG head capture.
import geistLatinUrl from '@fontsource-variable/geist/files/geist-latin-wght-normal.woff2?url'

useHead({
  link: [
    {
      rel: 'preload',
      href: geistLatinUrl,
      as: 'font',
      type: 'font/woff2',
      crossorigin: ''
    }
  ]
})

const route = useRoute()

// Move focus to the incoming page's <main> so screen readers announce the
// new page. Runs on the Transition's after-enter — the earliest moment the
// INCOMING view is actually in the DOM (router.afterEach + nextTick fired
// while the out-in transition still showed the outgoing view, so focus
// landed on a dying node and dropped to <body> — D3-A11Y-01). No `appear`
// on the Transition means this never fires on initial page load, only on
// SPA navigations.
//
// Hash navigations used to `return` here, which left keyboard users with no
// focus at all: EVERY cross-route nav click carries a hash (NavBar's non-home
// branch pushes { path: '/', hash: '#section' }, as do the "back to
// experience" links on the detail and 404 pages), and the <a> that was
// clicked lives inside the NavBar mounted *within* the outgoing view — so the
// out-in Transition unmounts it and the browser resets activeElement to
// <body>. The section scrolled into view but the next Tab restarted at the
// skip link, and screen readers announced nothing. Now the hash target itself
// takes focus, using the same temporary-tabindex dance as NavBar's same-page
// path. preventScroll is what makes this safe: scrollBehavior and
// useHashAlignment keep sole ownership of the viewport, so the alignment
// behaviour is unchanged.
const focusMainContent = (): void => {
  const el = document.getElementById(route.hash ? route.hash.slice(1) : 'main-content')
  if (!el) return
  const hadTabindex = el.hasAttribute('tabindex')
  if (!hadTabindex) {
    el.setAttribute('tabindex', '-1')
    // Remove on BLUR, never synchronously — stripping tabindex from the
    // focused element blurs it straight back to <body>.
    el.addEventListener('blur', () => el.removeAttribute('tabindex'), { once: true })
  }
  el.focus({ preventScroll: true })
}

// On mount, just remove the loading skeleton. Auth is initialized lazily
// by the route guard for admin routes only — calling checkAuth here would
// hit /auth/me on every public page load and surface a 401 in the console
// for unauthenticated visitors (the dominant case). The post-OAuth landing
// on /admin needs no special casing either: every /admin route is guarded,
// so the guard's initializeAuth() fetches /auth/me exactly once (the old
// initializeFromCallback here double-fetched it on every admin entry —
// it never set isInitialized, so the guard always refetched).
onMounted((): void => {
  document.getElementById('app-loading')?.remove()
})
</script>

<template>
  <a href="#main-content" class="skip-link">Skip to main content</a>
  <ErrorBoundary>
    <!-- No <Suspense> here, deliberately. Route components must keep
         setup() synchronous (SSR data fetching goes through
         onServerPrefetch — see HomeView/ExperienceDetail). A Suspense
         boundary + async setup() made hydration discard the entire
         prerendered DOM on every load and re-render it through this
         Transition, blanking the page until data arrived. If a future
         view adds a top-level await, Vue will warn that Suspense is
         missing — the fix is to remove the await, not re-add Suspense. -->
    <router-view v-slot="{ Component, route: viewRoute }">
      <Transition name="page-fade" mode="out-in" @after-enter="focusMainContent">
        <component :is="Component" :key="viewRoute.path" />
      </Transition>
    </router-view>
  </ErrorBoundary>
  <ToastContainer />
</template>

<style>
/* Global styles */
#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* Skip to main content link - WCAG 2.2 requirement */
.skip-link {
  position: absolute;
  top: -100px;
  left: 50%;
  transform: translateX(-50%);
  z-index: var(--z-index-skip-link);
  padding: 0.75rem 1.5rem;
  /* --color-primary-600 (the Tailwind @theme scale), NOT --primary-600 (the
     alias family). variables.css redefines --primary-600 to #2f88e8 under
     [data-theme='dark'], which put white on #2f88e8 = 3.62:1 — below AA for
     16px semibold — on the ONE control a low-vision keyboard user must be
     able to read, and only in dark mode, which is why it went unnoticed. The
     @theme scale is not shadowed by the dark block, so #1a6ad1 = 5.22:1 holds
     in both themes. Do not "fix" this by reaching for --primary-700: dark
     redefines that one to a pale #93c7f9. */
  background: var(--color-primary-600, #1a6ad1);
  color: white;
  text-decoration: none;
  font-weight: 600;
  border-radius: 0 0 0.5rem 0.5rem;
  transition: top 0.2s ease;
}

.skip-link:focus {
  top: 0;
  outline: 3px solid var(--primary-300, #93c5fd);
  outline-offset: 2px;
}

/* #main-content receives PROGRAMMATIC focus after route changes (the
   Transition's after-enter above) and from the skip link. tabindex="-1"
   keeps it out of the tab order, so a visible ring is pure noise — and
   Chromium's UA ring on a full-page <main> painted a 2px white hairline
   above the footer in every dark visual baseline (D3-A11Y-01). */
#main-content:focus {
  outline: none;
}

@media (prefers-reduced-motion: reduce) {
  .skip-link {
    transition: none;
  }
}

/* Page transitions */
.page-fade-enter-active,
.page-fade-leave-active {
  transition:
    opacity 0.2s ease,
    transform 0.2s ease;
}

.page-fade-enter-from {
  opacity: 0;
  transform: translateY(10px);
}

.page-fade-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

@media (prefers-reduced-motion: reduce) {
  .page-fade-enter-active,
  .page-fade-leave-active {
    transition: none;
  }

  .page-fade-enter-from,
  .page-fade-leave-to {
    opacity: 1;
    transform: none;
  }
}
</style>
