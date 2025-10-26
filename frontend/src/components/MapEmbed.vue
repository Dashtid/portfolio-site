<template>
  <div v-if="url" class="map-embed">
    <h2 v-if="heading" class="map-heading">{{ heading }}</h2>
    <div class="ratio ratio-16x9">
      <iframe
        :src="url"
        :title="title"
        allowfullscreen
        loading="lazy"
        referrerpolicy="no-referrer-when-downgrade"
        class="map-iframe"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * MapEmbed Component
 *
 * Responsive Google Maps embed with lazy loading and accessibility features.
 * Uses 16:9 aspect ratio and Bootstrap styling.
 */

interface Props {
  url: string
  title: string
  heading?: string | null
}

withDefaults(defineProps<Props>(), {
  title: 'Location map',
  heading: null
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
</style>
