<template>
  <button
    class="theme-toggle"
    data-testid="theme-toggle"
    :aria-label="isDark ? 'Switch to light mode' : 'Switch to dark mode'"
    :title="isDark ? 'Switch to light mode' : 'Switch to dark mode'"
    @click="handleToggle"
  >
    <!-- Both icons are ALWAYS in the DOM; [data-theme] CSS below decides
         which one shows. This is what keeps hydration clean: the SSG pass
         bakes the light page (Node has no matchMedia), so a v-if on isDark
         made every dark-preference visitor hydrate against DOM that didn't
         match — "Hydration completed but contains mismatches" on every
         page. Markup that is identical in both themes cannot mismatch, and
         the pre-paint theme script in index.html has already set
         data-theme, so the right icon is correct from first paint. -->
    <svg
      class="theme-icon icon-sun"
      aria-hidden="true"
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
      class="theme-icon icon-moon"
      aria-hidden="true"
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
  </button>
</template>

<script setup lang="ts">
import { useTheme } from '../composables/useTheme'

const { isDark, toggleTheme } = useTheme()

// Wrapped because Vue's `@click="toggleTheme"` would pass the MouseEvent
// as the first argument to useToggle(isDark), which interprets a truthy
// value as "set to true" instead of "flip current value." Calling with no
// args is the correct VueUse no-arg toggle behavior.
const handleToggle = (): void => {
  toggleTheme()
}
</script>

<style scoped>
.theme-toggle {
  position: relative;
  display: grid;
  place-items: center;
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

/* Both icons share the single grid cell (stacked, centered); opacity +
   transform crossfade replaces the old <transition> swap, driven purely by
   [data-theme] so no JS render depends on the theme. */
.theme-icon {
  grid-area: 1 / 1;
  width: 20px;
  height: 20px;
  color: var(--color-icon, #64748b);
  transition:
    color 0.3s ease,
    opacity 0.3s ease,
    transform 0.3s ease;
}

.icon-sun {
  opacity: 0;
  transform: rotate(-90deg) scale(0.5);
}

.icon-moon {
  opacity: 1;
  transform: none;
}

[data-theme='dark'] .icon-sun {
  opacity: 1;
  transform: none;
}

[data-theme='dark'] .icon-moon {
  opacity: 0;
  transform: rotate(90deg) scale(0.5);
}

.theme-toggle:hover .theme-icon {
  color: var(--color-primary, #2563eb);
}

/* Dark mode overrides. The base rule uses --color-border which already
   swaps via [data-theme='dark']; only genuinely different dark styling
   stays here — warm amber hover for the sun/moon flip, brighter icon
   resting color, and the --primary-400 focus ring. */
[data-theme='dark'] .theme-toggle:hover {
  background: rgba(251, 191, 36, 0.15);
  border-color: var(--color-warning);
}

[data-theme='dark'] .theme-icon {
  color: var(--text-secondary);
}

[data-theme='dark'] .theme-toggle:hover .theme-icon {
  color: var(--color-warning);
}

[data-theme='dark'] .theme-toggle:focus-visible {
  outline-color: var(--primary-400);
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
  .theme-icon {
    transition: none;
  }

  .theme-toggle:hover {
    transform: none;
  }
}
</style>
