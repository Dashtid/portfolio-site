<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuthStore } from './stores/auth'
import ToastContainer from './components/ToastContainer.vue'

// Store
const authStore = useAuthStore()

// Check auth on mount and remove loading skeleton
onMounted((): void => {
  // Remove loading skeleton once Vue has mounted
  document.getElementById('app-loading')?.remove()

  authStore.checkAuth()
  authStore.initializeFromCallback()
})
</script>

<template>
  <a href="#main-content" class="skip-link">Skip to main content</a>
  <router-view />
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
  z-index: 9999;
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
</style>
