<script setup>
import { onMounted } from 'vue'
import { useAuthStore } from './stores/auth'

// Store
const authStore = useAuthStore()

// Check auth on mount
onMounted(() => {
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