<template>
  <div v-if="hasError" class="error-boundary">
    <div class="error-container">
      <div class="error-icon">
        <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <circle cx="12" cy="12" r="10"></circle>
          <line x1="12" y1="8" x2="12" y2="12"></line>
          <line x1="12" y1="16" x2="12.01" y2="16"></line>
        </svg>
      </div>
      <h2 class="error-title">{{ title }}</h2>
      <p class="error-message">{{ message }}</p>
      <div v-if="showDetails && errorDetails" class="error-details">
        <pre>{{ errorDetails }}</pre>
      </div>
      <div class="error-actions">
        <button @click="handleRetry" class="btn-retry">
          Try Again
        </button>
        <button @click="handleGoHome" class="btn-home">
          Go to Homepage
        </button>
      </div>
    </div>
  </div>
  <slot v-else />
</template>

<script setup lang="ts">
import { ref, onErrorCaptured, type ComponentPublicInstance } from 'vue'
import { useRouter } from 'vue-router'

interface Props {
  title?: string
  message?: string
  showDetails?: boolean
  onRetry?: (() => void) | null
}

const props = withDefaults(defineProps<Props>(), {
  title: 'Oops! Something went wrong',
  message: 'We encountered an unexpected error. Please try again.',
  showDetails: false,
  onRetry: null
})

// Extend Window interface for analytics
declare global {
  interface Window {
    analytics?: {
      trackEvent: (category: string, action: string, label: string) => void
    }
  }
}

const router = useRouter()
const hasError = ref<boolean>(false)
const errorDetails = ref<string | null>(null)

const handleRetry = (): void => {
  if (props.onRetry) {
    props.onRetry()
  } else {
    // Default retry: reload the page
    window.location.reload()
  }
  hasError.value = false
  errorDetails.value = null
}

const handleGoHome = (): void => {
  hasError.value = false
  errorDetails.value = null
  router.push('/')
}

onErrorCaptured((err: Error, _instance: ComponentPublicInstance | null, info: string) => {
  console.error('Error caught in boundary:', err)
  hasError.value = true
  errorDetails.value = import.meta.env.DEV ? `${err.message}\n\nComponent: ${info}` : null

  // Log to analytics if available
  if (window.analytics) {
    window.analytics.trackEvent('Error', 'Boundary', err.message)
  }

  // Prevent the error from propagating
  return false
})

// Expose method to manually trigger error state
const showError = (error?: Error | null): void => {
  hasError.value = true
  errorDetails.value = error?.message || 'Unknown error'
}

defineExpose({
  showError,
  hasError
})
</script>

<style scoped>
.error-boundary {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  padding: 2rem;
}

.error-container {
  text-align: center;
  max-width: 500px;
  padding: 2rem;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

[data-theme="dark"] .error-container {
  background: #1a1a1a;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
}

.error-icon {
  display: flex;
  justify-content: center;
  margin-bottom: 1.5rem;
  color: #dc3545;
}

.error-title {
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 1rem;
  color: var(--text-color, #333);
}

.error-message {
  font-size: 1rem;
  color: var(--text-secondary, #666);
  margin-bottom: 1.5rem;
  line-height: 1.6;
}

.error-details {
  background: #f5f5f5;
  border: 1px solid #ddd;
  border-radius: 4px;
  padding: 1rem;
  margin-bottom: 1.5rem;
  text-align: left;
  max-height: 200px;
  overflow-y: auto;
}

[data-theme="dark"] .error-details {
  background: #0a0a0a;
  border-color: #333;
}

.error-details pre {
  margin: 0;
  font-size: 0.875rem;
  color: #d73a49;
  white-space: pre-wrap;
  word-break: break-word;
}

.error-actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
}

.btn-retry,
.btn-home {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-retry {
  background: var(--primary-color, #007bff);
  color: white;
}

.btn-retry:hover {
  background: var(--primary-hover, #0056b3);
  transform: translateY(-1px);
}

.btn-home {
  background: transparent;
  color: var(--primary-color, #007bff);
  border: 2px solid var(--primary-color, #007bff);
}

.btn-home:hover {
  background: var(--primary-color, #007bff);
  color: white;
  transform: translateY(-1px);
}

/* Animation */
@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.error-container {
  animation: slideIn 0.3s ease-out;
}
</style>