<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from './stores/auth'
import ToastContainer from './components/ToastContainer.vue'
import ErrorBoundary from './components/ErrorBoundary.vue'

// Store
const authStore = useAuthStore()
const route = useRoute()

// Move focus to the incoming page's <main> so screen readers announce the
// new page. Runs on the Transition's after-enter — the earliest moment the
// INCOMING view is actually in the DOM (router.afterEach + nextTick fired
// while the out-in transition still showed the outgoing view, so focus
// landed on a dying node and dropped to <body> — D3-A11Y-01). No `appear`
// on the Transition means this never fires on initial page load, only on
// SPA navigations. Skipped for hash navigations: scrollBehavior owns those,
// and focusing #main-content would yank the viewport back to the top.
const focusMainContent = (): void => {
  if (route.hash) return
  document.getElementById('main-content')?.focus({ preventScroll: false })
}

// On mount, just remove the loading skeleton. Auth is initialized lazily
// by the route guard for admin routes only — calling checkAuth here would
// hit /auth/me on every public page load and surface a 401 in the console
// for unauthenticated visitors (the dominant case).
onMounted((): void => {
  document.getElementById('app-loading')?.remove()
  authStore.initializeFromCallback()
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
  background: var(--primary-600, #2563eb);
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
