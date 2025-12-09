<template>
  <div ref="imageContainer" class="lazy-image-container">
    <div v-if="!loaded" class="image-placeholder">
      <div class="shimmer"></div>
    </div>
    <img
      v-show="loaded"
      :src="currentSrc"
      :alt="alt"
      :class="imageClass"
      @load="onImageLoad"
      @error="onImageError"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

interface Props {
  src: string
  placeholder?: string | null
  alt?: string
  imageClass?: string
  threshold?: number
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: null,
  alt: '',
  imageClass: '',
  threshold: 0.1
})

const imageContainer = ref<HTMLDivElement | null>(null)
const loaded = ref<boolean>(false)
const error = ref<boolean>(false)
const isIntersecting = ref<boolean>(false)
const currentSrc = ref<string>('')

let observer: IntersectionObserver | null = null

const loadImage = (): void => {
  if (!isIntersecting.value) return

  // Start with placeholder if available
  if (props.placeholder && !currentSrc.value) {
    currentSrc.value = props.placeholder
  }

  // Create a new image to preload
  const img = new Image()
  img.src = props.src

  img.onload = () => {
    currentSrc.value = props.src
    loaded.value = true
    error.value = false
  }

  img.onerror = () => {
    error.value = true
    loaded.value = false
  }
}

const onImageLoad = (): void => {
  loaded.value = true
  error.value = false
}

const onImageError = (): void => {
  error.value = true
  loaded.value = false
}

const setupIntersectionObserver = (): void => {
  const options: IntersectionObserverInit = {
    root: null,
    rootMargin: '50px',
    threshold: props.threshold
  }

  observer = new IntersectionObserver((entries: IntersectionObserverEntry[]) => {
    entries.forEach(entry => {
      if (entry.isIntersecting && !isIntersecting.value) {
        isIntersecting.value = true
        loadImage()

        // Disconnect after loading
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
  background: #f0f0f0;
}

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

.lazy-image-container img {
  display: block;
  width: 100%;
  height: auto;
  transition: opacity 0.3s ease-in-out;
}

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


/* Dark mode shimmer */
[data-theme='dark'] .image-placeholder {
  background: #1e293b;
}

[data-theme='dark'] .shimmer::before {
  background: linear-gradient(90deg, #1e293b 25%, #334155 50%, #1e293b 75%);
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
  .shimmer::before {
    animation: none;
  }
}
</style>
