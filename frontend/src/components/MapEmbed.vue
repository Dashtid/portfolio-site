<template>
  <div class="map-embed">
    <h2 v-if="heading" class="map-heading">{{ heading }}</h2>
    <div v-if="safeUrl" class="ratio">
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
import { toRef } from 'vue'
import { useEmbedValidator } from '@/composables/useEmbedValidator'

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

const ALLOWED_MAP_HOSTS = ['www.google.com', 'google.com', 'maps.google.com']

const safeUrl = useEmbedValidator(toRef(props, 'url'), ALLOWED_MAP_HOSTS, '/maps/embed', 'MapEmbed')
</script>

<style scoped>
/* No margin here: the parent media-section grid owns spacing (mb-12 +
   gap-6). A scoped margin-bottom cannot collapse out of a grid cell and
   double-spaced the section while spacing utilities were rediscovered
   in S3. */

.map-heading {
  /* Mono section-label recipe (matches the detail page's h2 labels) —
     the old 1.5rem/600 caption out-shouted the page h1. */
  font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, monospace;
  font-size: 0.75rem;
  font-weight: 400;
  text-transform: uppercase;
  letter-spacing: 0.2em;
  margin-bottom: 1rem;
  color: var(--text-secondary);
}

.ratio {
  /* Bootstrap's .ratio-16x9 is gone from the bundle — without an explicit
     aspect ratio the iframe collapses to a 150px letterbox strip. */
  aspect-ratio: 16 / 9;
  width: 100%;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: var(--elevation-md);
}

.map-iframe {
  border: none;
  width: 100%;
  height: 100%;
}

/* Google's embed has no dark theme — invert+rotate approximates one so
   the map stops glaring white on slate-950 pages. Saturate/contrast pull
   the inverted colors back toward plausible map hues. */
[data-theme='dark'] .map-iframe {
  filter: invert(0.86) hue-rotate(180deg) saturate(0.7) contrast(0.95);
}

/* Fallback UI when map cannot be loaded. Uses semantic tokens that
   swap via variables.css — no [data-theme='dark'] override needed. */
.map-fallback {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  background: var(--bg-secondary);
  border-radius: 8px;
  border: 1px dashed var(--border-primary);
  min-height: 200px;
  text-align: center;
}

.fallback-icon {
  font-size: 2rem;
  margin-bottom: 0.5rem;
}

.fallback-text {
  color: var(--text-secondary);
  margin: 0;
  font-size: 0.95rem;
}
</style>
