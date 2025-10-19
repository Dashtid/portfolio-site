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

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'

const props = defineProps({
  src: {
    type: String,
    required: true
  },
  placeholder: {
    type: String,
    default: null
  },
  alt: {
    type: String,
    default: ''
  },
  imageClass: {
    type: String,
    default: ''
  },
  threshold: {
    type: Number,
    default: 0.1
  }
})

const imageContainer = ref(null)
const loaded = ref(false)
const error = ref(false)
const isIntersecting = ref(false)
const currentSrc = ref('')

let observer = null

// Create a low-quality placeholder
const placeholderSrc = computed(() => {
  if (props.placeholder) return props.placeholder
  // Could generate a data URL placeholder or use a default image
  return 'data:image/svg+xml,%3Csvg width="400" height="300" xmlns="http://www.w3.org/2000/svg"%3E%3Crect width="100%25" height="100%25" fill="%23f0f0f0"/%3E%3C/svg%3E'
})

const loadImage = () => {
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

const onImageLoad = () => {
  loaded.value = true
  error.value = false
}

const onImageError = () => {
  error.value = true
  loaded.value = false
}

const setupIntersectionObserver = () => {
  const options = {
    root: null,
    rootMargin: '50px',
    threshold: props.threshold
  }

  observer = new IntersectionObserver((entries) => {
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
</style>