<template>
  <Teleport to="body">
    <div class="toast-container" role="region" aria-label="Notifications" aria-live="polite">
      <TransitionGroup name="toast">
        <div
          v-for="toast in toasts"
          :key="toast.id"
          class="toast"
          :class="[`toast--${toast.type}`]"
          role="alert"
          @click="remove(toast.id)"
        >
          <span class="toast__icon" aria-hidden="true">
            <template v-if="toast.type === 'success'">&#10003;</template>
            <template v-else-if="toast.type === 'error'">&#10005;</template>
            <template v-else-if="toast.type === 'warning'">&#9888;</template>
            <template v-else>&#8505;</template>
          </span>
          <span class="toast__message">{{ toast.message }}</span>
          <button
            class="toast__close"
            type="button"
            aria-label="Dismiss notification"
            @click.stop="remove(toast.id)"
          >
            &times;
          </button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { useToast } from '@/composables/useToast'

const { toasts, remove } = useToast()
</script>

<style scoped>
.toast-container {
  position: fixed;
  top: 1rem;
  right: 1rem;
  z-index: 10000;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-width: 400px;
  pointer-events: none;
}

.toast {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.875rem 1rem;
  border-radius: 8px;
  background: var(--bg-secondary, #fff);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  border-left: 4px solid;
  cursor: pointer;
  pointer-events: auto;
  animation: slideIn 0.3s ease-out;
}

.toast--success {
  border-left-color: #10b981;
  background: linear-gradient(to right, rgba(16, 185, 129, 0.1), var(--bg-secondary, #fff));
}

.toast--error {
  border-left-color: #ef4444;
  background: linear-gradient(to right, rgba(239, 68, 68, 0.1), var(--bg-secondary, #fff));
}

.toast--warning {
  border-left-color: #f59e0b;
  background: linear-gradient(to right, rgba(245, 158, 11, 0.1), var(--bg-secondary, #fff));
}

.toast--info {
  border-left-color: #3b82f6;
  background: linear-gradient(to right, rgba(59, 130, 246, 0.1), var(--bg-secondary, #fff));
}

.toast__icon {
  font-size: 1.25rem;
  flex-shrink: 0;
}

.toast--success .toast__icon {
  color: #10b981;
}

.toast--error .toast__icon {
  color: #ef4444;
}

.toast--warning .toast__icon {
  color: #f59e0b;
}

.toast--info .toast__icon {
  color: #3b82f6;
}

.toast__message {
  flex: 1;
  color: var(--text-primary, #1e293b);
  font-size: 0.9375rem;
  line-height: 1.4;
}

.toast__close {
  background: none;
  border: none;
  font-size: 1.25rem;
  color: var(--text-tertiary, #94a3b8);
  cursor: pointer;
  padding: 0 0.25rem;
  line-height: 1;
  transition: color 0.2s;
}

.toast__close:hover {
  color: var(--text-primary, #1e293b);
}

/* Transition animations */
.toast-enter-active {
  animation: slideIn 0.3s ease-out;
}

.toast-leave-active {
  animation: slideOut 0.2s ease-in forwards;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(100%);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes slideOut {
  from {
    opacity: 1;
    transform: translateX(0);
  }
  to {
    opacity: 0;
    transform: translateX(100%);
  }
}

/* Dark theme */
[data-theme='dark'] .toast {
  background: var(--bg-secondary, #1e293b);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

[data-theme='dark'] .toast--success {
  background: linear-gradient(to right, rgba(16, 185, 129, 0.15), var(--bg-secondary, #1e293b));
}

[data-theme='dark'] .toast--error {
  background: linear-gradient(to right, rgba(239, 68, 68, 0.15), var(--bg-secondary, #1e293b));
}

[data-theme='dark'] .toast--warning {
  background: linear-gradient(to right, rgba(245, 158, 11, 0.15), var(--bg-secondary, #1e293b));
}

[data-theme='dark'] .toast--info {
  background: linear-gradient(to right, rgba(59, 130, 246, 0.15), var(--bg-secondary, #1e293b));
}

[data-theme='dark'] .toast__message {
  color: var(--text-primary, #f1f5f9);
}

[data-theme='dark'] .toast__close {
  color: var(--text-tertiary, #64748b);
}

[data-theme='dark'] .toast__close:hover {
  color: var(--text-primary, #f1f5f9);
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
  .toast,
  .toast-enter-active,
  .toast-leave-active {
    animation: none;
  }

  .toast-enter-active {
    opacity: 1;
  }

  .toast-leave-active {
    opacity: 0;
  }
}
</style>
