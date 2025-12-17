<template>
  <transition name="slide-fade">
    <button
      v-if="isVisible"
      class="back-to-top"
      data-testid="back-to-top"
      :aria-label="'Scroll back to top'"
      title="Back to top"
      @click="scrollToTop"
    >
      <svg
        class="arrow-icon"
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="2"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <line x1="12" y1="19" x2="12" y2="5"></line>
        <polyline points="5 12 12 5 19 12"></polyline>
      </svg>
    </button>
  </transition>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

const isVisible = ref<boolean>(false)
const scrollThreshold: number = 300 // Show button after scrolling 300px

// Handle scroll events to show/hide button
const handleScroll = (): void => {
  isVisible.value = window.scrollY > scrollThreshold
}

// Scroll to top with smooth animation
const scrollToTop = (): void => {
  window.scrollTo({
    top: 0,
    behavior: 'smooth'
  })
}

// Throttle scroll events for performance
let ticking = false
const throttledScroll = (): void => {
  if (!ticking) {
    window.requestAnimationFrame(() => {
      handleScroll()
      ticking = false
    })
    ticking = true
  }
}

onMounted(() => {
  window.addEventListener('scroll', throttledScroll, { passive: true })
  handleScroll() // Initial check
})

onUnmounted(() => {
  window.removeEventListener('scroll', throttledScroll)
})
</script>

<style scoped>
.back-to-top {
  position: fixed;
  bottom: 2rem;
  right: 2rem;
  z-index: var(--z-index-fixed, 1030);
  width: 50px;
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-primary, #2563eb);
  color: white;
  border: none;
  border-radius: 50%;
  cursor: pointer;
  box-shadow: var(--shadow-lg, 0 10px 15px -3px rgba(0, 0, 0, 0.1));
  transition: all 0.3s ease;
  outline: none;
}

.back-to-top:hover {
  background: var(--color-primary-dark, #1d4ed8);
  transform: translateY(-3px);
  box-shadow: var(--shadow-xl, 0 20px 25px -5px rgba(0, 0, 0, 0.1));
}

.back-to-top:active {
  transform: translateY(-1px);
  box-shadow: var(--shadow-md, 0 4px 6px -1px rgba(0, 0, 0, 0.1));
}

.back-to-top:focus-visible {
  outline: 2px solid var(--color-primary, #2563eb);
  outline-offset: 2px;
}

.arrow-icon {
  width: 24px;
  height: 24px;
  animation: bounce 2s infinite;
}

/* Bounce animation for the arrow */
@keyframes bounce {
  0%,
  20%,
  50%,
  80%,
  100% {
    transform: translateY(0);
  }
  40% {
    transform: translateY(-5px);
  }
  60% {
    transform: translateY(-3px);
  }
}

/* Slide-fade transition for button appearance */
.slide-fade-enter-active {
  transition: all 0.3s ease;
}

.slide-fade-leave-active {
  transition: all 0.3s ease;
}

.slide-fade-enter-from {
  transform: translateY(20px);
  opacity: 0;
}

.slide-fade-leave-to {
  transform: translateY(20px);
  opacity: 0;
}

/* Dark mode styles */
[data-theme='dark'] .back-to-top {
  background: var(--color-teal);
}

[data-theme='dark'] .back-to-top:hover {
  background: var(--color-teal-dark);
}

/* Responsive sizing */
@media (max-width: 768px) {
  .back-to-top {
    width: 45px;
    height: 45px;
    bottom: 1.5rem;
    right: 1.5rem;
  }

  .arrow-icon {
    width: 20px;
    height: 20px;
  }
}

@media (max-width: 480px) {
  .back-to-top {
    width: 40px;
    height: 40px;
    bottom: 1rem;
    right: 1rem;
  }

  .arrow-icon {
    width: 18px;
    height: 18px;
  }
}

/* Reduced motion preference */
@media (prefers-reduced-motion: reduce) {
  .back-to-top,
  .arrow-icon,
  .slide-fade-enter-active,
  .slide-fade-leave-active {
    transition: none;
    animation: none;
  }

  .back-to-top:hover {
    transform: none;
  }
}
</style>
