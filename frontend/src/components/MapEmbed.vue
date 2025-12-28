<template>
  <div class="map-embed">
    <h2 v-if="heading" class="map-heading">{{ heading }}</h2>
    <div v-if="safeUrl" class="ratio ratio-16x9">
      <iframe
        :src="safeUrl"
        :title="title"
        :aria-label="'Google Maps location: ' + title"
        role="application"
        tabindex="0"
        allowfullscreen
        loading="lazy"
        referrerpolicy="no-referrer-when-downgrade"
        class="map-iframe"
      />
    </div>
    <div v-else class="map-fallback" role="alert">
      <span class="fallback-icon" aria-hidden="true">📍</span>
      <p class="fallback-text">Map could not be loaded</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

/**
 * MapEmbed Component
 *
 * Responsive Google Maps embed with lazy loading and accessibility features.
 * Uses 16:9 aspect ratio and Bootstrap styling.
 */

interface Props {
  url: string
  title?: string
  heading?: string | null
}

const props = withDefaults(defineProps<Props>(), {
  title: 'Location map',
  heading: null
})

// Allowed Google Maps embed domains
const ALLOWED_MAP_HOSTS = ['www.google.com', 'google.com', 'maps.google.com']

// Validate URL is a safe Google Maps embed URL
const safeUrl = computed<string | null>(() => {
  if (!props.url) return null

  try {
    const parsed = new URL(props.url)

    // Only allow https protocol
    if (parsed.protocol !== 'https:') {
      if (import.meta.env.DEV) {
        console.warn(`[MapEmbed] Blocked non-https URL: ${props.url}`)
      }
      return null
    }

    // Only allow Google Maps domains
    if (!ALLOWED_MAP_HOSTS.includes(parsed.hostname)) {
      if (import.meta.env.DEV) {
        console.warn(`[MapEmbed] Blocked non-Google Maps URL: ${props.url}`)
      }
      return null
    }

    // Must be maps embed path
    if (!parsed.pathname.startsWith('/maps/embed')) {
      if (import.meta.env.DEV) {
        console.warn(`[MapEmbed] Blocked non-embed URL: ${props.url}`)
      }
      return null
    }

    return props.url
  } catch {
    if (import.meta.env.DEV) {
      console.warn(`[MapEmbed] Invalid URL: ${props.url}`)
    }
    return null
  }
})
</script>

<style scoped>
.map-embed {
  margin-bottom: 2rem;
}

.map-heading {
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 1rem;
  color: var(--bs-body-color);
}

.ratio {
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.map-iframe {
  border: none;
  width: 100%;
  height: 100%;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .map-heading {
    font-size: 1.25rem;
  }
}

/* Fallback UI when map cannot be loaded */
.map-fallback {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  background: var(--bg-secondary, #f8fafc);
  border-radius: 8px;
  border: 1px dashed var(--border-color, #e2e8f0);
  min-height: 200px;
  text-align: center;
}

.fallback-icon {
  font-size: 2rem;
  margin-bottom: 0.5rem;
}

.fallback-text {
  color: var(--text-secondary, #64748b);
  margin: 0;
  font-size: 0.95rem;
}

/* Dark mode fallback */
[data-theme='dark'] .map-fallback {
  background: var(--bg-secondary, #1e293b);
  border-color: var(--border-color, #334155);
}
</style>
