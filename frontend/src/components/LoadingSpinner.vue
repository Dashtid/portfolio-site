<template>
  <div class="loading-container" :class="{ 'full-screen': fullScreen }">
    <div class="loading-spinner" :class="sizeClass">
      <div class="spinner-ring"></div>
      <div class="spinner-ring"></div>
      <div class="spinner-ring"></div>
      <div class="spinner-ring"></div>
    </div>
    <p v-if="message" class="loading-message">{{ message }}</p>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  message: {
    type: String,
    default: ''
  },
  size: {
    type: String,
    default: 'medium',
    validator: (value) => ['small', 'medium', 'large'].includes(value)
  },
  fullScreen: {
    type: Boolean,
    default: false
  }
})

const sizeClass = computed(() => `spinner-${props.size}`)
</script>

<style scoped>
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  min-height: 200px;
}

.loading-container.full-screen {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.95);
  z-index: 9999;
  min-height: 100vh;
}

[data-theme="dark"] .loading-container.full-screen {
  background: rgba(0, 0, 0, 0.95);
}

.loading-spinner {
  display: inline-block;
  position: relative;
}

.spinner-small {
  width: 32px;
  height: 32px;
}

.spinner-medium {
  width: 64px;
  height: 64px;
}

.spinner-large {
  width: 96px;
  height: 96px;
}

.spinner-ring {
  box-sizing: border-box;
  display: block;
  position: absolute;
  width: 100%;
  height: 100%;
  border: 3px solid transparent;
  border-radius: 50%;
  animation: spinner-ring 1.2s cubic-bezier(0.5, 0, 0.5, 1) infinite;
  border-color: var(--primary-color, #007bff) transparent transparent transparent;
}

.spinner-small .spinner-ring {
  border-width: 2px;
}

.spinner-large .spinner-ring {
  border-width: 4px;
}

.spinner-ring:nth-child(1) {
  animation-delay: -0.45s;
}

.spinner-ring:nth-child(2) {
  animation-delay: -0.3s;
}

.spinner-ring:nth-child(3) {
  animation-delay: -0.15s;
}

@keyframes spinner-ring {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

.loading-message {
  margin-top: 1rem;
  color: var(--text-color, #333);
  font-size: 0.95rem;
  text-align: center;
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.6;
  }
}

/* Skeleton loader variant */
.skeleton-loader {
  background: linear-gradient(
    90deg,
    #f0f0f0 25%,
    #e0e0e0 50%,
    #f0f0f0 75%
  );
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.5s infinite;
  border-radius: 4px;
}

@keyframes skeleton-shimmer {
  0% {
    background-position: -200% 0;
  }
  100% {
    background-position: 200% 0;
  }
}

[data-theme="dark"] .skeleton-loader {
  background: linear-gradient(
    90deg,
    #2a2a2a 25%,
    #3a3a3a 50%,
    #2a2a2a 75%
  );
  background-size: 200% 100%;
}
</style>