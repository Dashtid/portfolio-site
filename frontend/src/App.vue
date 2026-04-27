<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuthStore } from './stores/auth'
import ToastContainer from './components/ToastContainer.vue'
import ErrorBoundary from './components/ErrorBoundary.vue'

// Store
const authStore = useAuthStore()

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
    <router-view v-slot="{ Component, route }">
      <Transition name="page-fade" mode="out-in">
        <Suspense>
          <component :is="Component" :key="route.path" />
        </Suspense>
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
