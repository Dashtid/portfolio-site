<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuthStore } from './stores/auth'

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
  <router-view />
</template>

<style>
/* Global styles */
#app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}
</style>
