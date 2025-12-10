<template>
  <div ref="imageContainer" class="lazy-image-container">
    <!-- Shimmer placeholder shown before image starts loading -->
    <div v-if="!isIntersecting" class="image-placeholder">
      <div class="shimmer"></div>
    </div>

    <!-- Blur placeholder shown while high-res image loads -->
    <img
      v-if="showBlurPlaceholder && placeholderSrc"
      :src="placeholderSrc"
      :alt="alt"
      class="blur-placeholder"
      :class="{ 'blur-placeholder--hidden': loaded }"
      aria-hidden="true"
    />

    <!-- Main image with blur-to-clear transition -->
    <img
      v-show="isIntersecting"
      ref="mainImage"
      :src="currentSrc"
      :alt="alt"
      :class="[imageClass, { 'image--loaded': loaded, 'image--blur': !loaded && isIntersecting }]"
      @load="onImageLoad"
      @error="onImageError"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'

interface Props {
  src: string
  placeholder?: string | null
  blurPlaceholder?: string | null
  alt?: string
  imageClass?: string
  threshold?: number
  blurAmount?: number
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: null,
  blurPlaceholder: null,
  alt: '',
  imageClass: '',
  threshold: 0.1,
  blurAmount: 20
})

const imageContainer = ref<HTMLDivElement | null>(null)
const mainImage = ref<HTMLImageElement | null>(null)
const loaded = ref<boolean>(false)
const error = ref<boolean>(false)
const isIntersecting = ref<boolean>(false)
const currentSrc = ref<string>('')

let observer: IntersectionObserver | null = null

// Determine which placeholder to show for blur effect
const placeholderSrc = computed(() => props.blurPlaceholder || props.placeholder)
const showBlurPlaceholder = computed(
  () => isIntersecting.value && !loaded.value && placeholderSrc.value
)

const loadImage = (): void => {
  if (!isIntersecting.value) return

  // Set the source to start loading
  currentSrc.value = props.src
}

const onImageLoad = (): void => {
  // Small delay to ensure smooth transition
  requestAnimationFrame(() => {
    loaded.value = true
    error.value = false
  })
}

const onImageError = (): void => {
  error.value = true
  loaded.value = false
}

const setupIntersectionObserver = (): void => {
  const options: IntersectionObserverInit = {
    root: null,
    rootMargin: '100px',
    threshold: props.threshold
  }

  observer = new IntersectionObserver((entries: IntersectionObserverEntry[]) => {
    entries.forEach(entry => {
      if (entry.isIntersecting && !isIntersecting.value) {
        isIntersecting.value = true
        loadImage()

        // Disconnect after loading starts
        if (observer) {
          observer.disconnect()
        }
      }
    })
  }, options)

  if (imageContainer.value) {
    observer.observe(imageContainer.value)
  }
}

onMounted(() => {
  // Check if IntersectionObserver is supported
  if ('IntersectionObserver' in window) {
    setupIntersectionObserver()
  } else {
    // Fallback: load immediately
    isIntersecting.value = true
    loadImage()
  }
})

onUnmounted(() => {
  if (observer) {
    observer.disconnect()
  }
})
</script>

<style scoped>
.lazy-image-container {
  position: relative;
  overflow: hidden;
  background: var(--lazy-bg, #f0f0f0);
}

/* Shimmer placeholder */
.image-placeholder {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
}

@keyframes shimmer {
  0% {
    background-position: -200% 0;
  }
  100% {
    background-position: 200% 0;
  }
}

/* Blur placeholder image */
.blur-placeholder {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  filter: blur(20px);
  transform: scale(1.1);
  transition: opacity 0.5s ease-out;
  z-index: 1;
}

.blur-placeholder--hidden {
  opacity: 0;
  pointer-events: none;
}

/* Main image */
.lazy-image-container img:not(.blur-placeholder) {
  display: block;
  width: 100%;
  height: auto;
  transition:
    filter 0.5s ease-out,
    opacity 0.5s ease-out;
}

/* Image starts blurred, transitions to clear */
.image--blur {
  filter: blur(20px);
  opacity: 0.8;
}

.image--loaded {
  filter: blur(0);
  opacity: 1;
}

/* Fade in animation for loaded images */
.lazy-image-container img.fade-in {
  animation: fadeIn 0.5s ease-in;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

/* Dark mode styles */
:root[data-theme='dark'] .lazy-image-container,
[data-theme='dark'] .lazy-image-container {
  --lazy-bg: #1e293b;
}

:root[data-theme='dark'] .image-placeholder,
[data-theme='dark'] .image-placeholder {
  background: linear-gradient(90deg, #1e293b 25%, #334155 50%, #1e293b 75%);
  background-size: 200% 100%;
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
  .image-placeholder {
    animation: none;
  }

  .blur-placeholder {
    filter: none;
    transform: none;
  }

  .image--blur {
    filter: none;
  }

  .lazy-image-container img:not(.blur-placeholder) {
    transition: opacity 0.2s ease-out;
  }

  .blur-placeholder {
    transition: opacity 0.2s ease-out;
  }
}
</style>
