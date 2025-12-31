<template>
  <button
    class="theme-toggle"
    data-testid="theme-toggle"
    :aria-label="isDark ? 'Switch to light mode' : 'Switch to dark mode'"
    :title="isDark ? 'Switch to light mode' : 'Switch to dark mode'"
    @click="toggleTheme"
  >
    <transition name="icon-fade" mode="out-in">
      <svg
        v-if="isDark"
        key="sun"
        class="theme-icon"
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <!-- Sun icon -->
        <circle cx="12" cy="12" r="5"></circle>
        <line x1="12" y1="1" x2="12" y2="3"></line>
        <line x1="12" y1="21" x2="12" y2="23"></line>
        <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
        <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
        <line x1="1" y1="12" x2="3" y2="12"></line>
        <line x1="21" y1="12" x2="23" y2="12"></line>
        <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
        <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
      </svg>
      <svg
        v-else
        key="moon"
        class="theme-icon"
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <!-- Moon icon -->
        <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
      </svg>
    </transition>
  </button>
</template>

<script setup lang="ts">
import { useTheme } from '../composables/useTheme'

const { isDark, toggleTheme: toggle } = useTheme()

const handleClick = (): void => {
  toggle()
}

// Alias for template usage
const toggleTheme = handleClick
</script>

<style scoped>
.theme-toggle {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  padding: 0;
  background: transparent;
  border: 2px solid var(--color-border, #e2e8f0);
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.3s ease;
  outline: none;
}

.theme-toggle:hover {
  background: var(--color-hover-bg, rgba(37, 99, 235, 0.1));
  border-color: var(--color-primary, #2563eb);
  transform: rotate(20deg) scale(1.1);
}

.theme-toggle:focus-visible {
  outline: 3px solid var(--color-primary, #2563eb);
  outline-offset: 3px;
}

.theme-toggle:active {
  transform: rotate(20deg) scale(0.95);
}

.theme-icon {
  width: 20px;
  height: 20px;
  color: var(--color-icon, #64748b);
  transition: color 0.3s ease;
}

.theme-toggle:hover .theme-icon {
  color: var(--color-primary, #2563eb);
}

/* Icon transition animations */
.icon-fade-enter-active,
.icon-fade-leave-active {
  transition: all 0.3s ease;
}

.icon-fade-enter-from {
  opacity: 0;
  transform: rotate(-90deg) scale(0.5);
}

.icon-fade-leave-to {
  opacity: 0;
  transform: rotate(90deg) scale(0.5);
}

/* Dark mode specific styles */
[data-theme='dark'] .theme-toggle {
  border-color: var(--color-border);
}

[data-theme='dark'] .theme-toggle:hover {
  background: rgba(251, 191, 36, 0.15);
  border-color: var(--color-warning);
}

[data-theme='dark'] .theme-icon {
  /* Brighter icon color for better visibility on dark backgrounds */
  color: var(--text-secondary, #cbd5e1);
}

[data-theme='dark'] .theme-toggle:hover .theme-icon {
  color: var(--color-warning);
}

[data-theme='dark'] .theme-toggle:focus-visible {
  outline-color: var(--primary-400, #60a5fa);
}

/* Responsive sizing - maintain 44px minimum for WCAG 2.5.8 */
@media (max-width: 768px) {
  .theme-toggle {
    width: 44px;
    height: 44px;
  }

  .theme-icon {
    width: 20px;
    height: 20px;
  }
}

/* Reduced motion preference */
@media (prefers-reduced-motion: reduce) {
  .theme-toggle,
  .theme-icon,
  .icon-fade-enter-active,
  .icon-fade-leave-active {
    transition: none;
  }

  .theme-toggle:hover {
    transform: none;
  }
}
</style>
