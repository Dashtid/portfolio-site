<template>
  <picture class="responsive-image" :class="containerClass">
    <!-- WebP source for modern browsers -->
    <source v-if="webpSrc" :srcset="webpSrcset" :sizes="sizes" type="image/webp" />

    <!-- AVIF source for cutting-edge browsers -->
    <source v-if="avifSrc" :srcset="avifSrcset" :sizes="sizes" type="image/avif" />

    <!-- Fallback image with srcset -->
    <img
      ref="imageRef"
      :src="currentSrc"
      :srcset="fallbackSrcset"
      :sizes="sizes"
      :alt="alt"
      :width="width"
      :height="height"
      :loading="loading"
      :decoding="decoding"
      :fetchpriority="fetchpriority"
      :class="[imageClass, { 'image--loaded': isLoaded, 'image--loading': !isLoaded }]"
      @load="onLoad"
      @error="onError"
    />

    <!-- Optional blur placeholder overlay -->
    <div
      v-if="showPlaceholder && !isLoaded"
      class="image-placeholder"
      :style="placeholderStyle"
    ></div>
  </picture>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'

interface Props {
  src: string
  webpSrc?: string
  avifSrc?: string
  alt: string
  width?: number | string
  height?: number | string
  sizes?: string
  loading?: 'lazy' | 'eager'
  decoding?: 'async' | 'sync' | 'auto'
  fetchpriority?: 'high' | 'low' | 'auto'
  imageClass?: string
  containerClass?: string
  placeholder?: string
  breakpoints?: number[]
}

const props = withDefaults(defineProps<Props>(), {
  webpSrc: '',
  avifSrc: '',
  width: undefined,
  height: undefined,
  sizes: '100vw',
  loading: 'lazy',
  decoding: 'async',
  fetchpriority: 'auto',
  imageClass: '',
  containerClass: '',
  placeholder: '',
  breakpoints: () => [320, 640, 768, 1024, 1280, 1536, 1920]
})

const emit = defineEmits<{
  load: [event: Event]
  error: [event: Event]
}>()

const imageRef = ref<HTMLImageElement | null>(null)
const isLoaded = ref(false)
const hasError = ref(false)
const currentSrc = ref(props.src)

// Generate srcset from breakpoints
const generateSrcset = (baseSrc: string): string => {
  if (!baseSrc || baseSrc.startsWith('data:')) return baseSrc

  // If src already contains width parameter, return as-is
  if (baseSrc.includes('?w=')) return baseSrc

  // For local images, generate srcset with width query params
  // This assumes a backend or CDN that supports width resizing
  return props.breakpoints.map(w => `${baseSrc}?w=${w} ${w}w`).join(', ')
}

// Generate srcset for fallback format
const fallbackSrcset = computed(() => {
  return generateSrcset(props.src)
})

// Generate srcset for WebP format
const webpSrcset = computed(() => {
  if (!props.webpSrc) return ''
  return generateSrcset(props.webpSrc)
})

// Generate srcset for AVIF format
const avifSrcset = computed(() => {
  if (!props.avifSrc) return ''
  return generateSrcset(props.avifSrc)
})

// Show placeholder until image loads
const showPlaceholder = computed(() => {
  return props.placeholder || props.loading === 'lazy'
})

// Placeholder styling (blur effect)
const placeholderStyle = computed(() => {
  if (props.placeholder) {
    return {
      backgroundImage: `url(${props.placeholder})`,
      backgroundSize: 'cover',
      filter: 'blur(10px)',
      transform: 'scale(1.1)'
    }
  }
  return {
    backgroundColor: '#e5e7eb'
  }
})

const onLoad = (event: Event): void => {
  isLoaded.value = true
  hasError.value = false
  emit('load', event)
}

const onError = (event: Event): void => {
  hasError.value = true
  emit('error', event)

  // Fallback to original src if srcset fails
  if (imageRef.value && imageRef.value.srcset) {
    imageRef.value.srcset = ''
    currentSrc.value = props.src
  }
}

// Watch for src changes
watch(
  () => props.src,
  newSrc => {
    isLoaded.value = false
    currentSrc.value = newSrc
  }
)

onMounted(() => {
  // Check if image is already cached/loaded
  if (imageRef.value?.complete && imageRef.value?.naturalHeight !== 0) {
    isLoaded.value = true
  }
})
</script>

<style scoped>
.responsive-image {
  display: block;
  position: relative;
  overflow: hidden;
}

.responsive-image img {
  display: block;
  width: 100%;
  height: auto;
  transition: opacity 0.3s ease-in-out;
}

.image--loading {
  opacity: 0;
}

.image--loaded {
  opacity: 1;
}

.image-placeholder {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  transition: opacity 0.3s ease-in-out;
  pointer-events: none;
}

.image--loaded + .image-placeholder {
  opacity: 0;
}

/* Aspect ratio support for preventing layout shift */
.responsive-image[data-aspect-ratio] {
  aspect-ratio: attr(data-aspect-ratio);
}

/* Dark mode placeholder */
[data-theme='dark'] .image-placeholder {
  background-color: #374151;
}

/* Reduced motion */
@media (prefers-reduced-motion: reduce) {
  .responsive-image img,
  .image-placeholder {
    transition: none;
  }
}
</style>
