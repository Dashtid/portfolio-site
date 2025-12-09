<template>
  <div v-if="url" class="video-embed">
    <h2 v-if="heading" class="video-heading">{{ heading }}</h2>
    <div class="ratio ratio-16x9">
      <iframe
        :src="url"
        :title="title"
        :aria-label="'YouTube video: ' + title"
        role="application"
        tabindex="0"
        allow="
          accelerometer;
          autoplay;
          clipboard-write;
          encrypted-media;
          gyroscope;
          picture-in-picture;
          web-share;
        "
        referrerpolicy="strict-origin-when-cross-origin"
        allowfullscreen
        loading="lazy"
        class="video-iframe"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
/**
 * VideoEmbed Component
 *
 * Responsive YouTube video embed with lazy loading and accessibility features.
 * Uses 16:9 aspect ratio and Bootstrap styling.
 */

interface Props {
  url: string
  title?: string
  heading?: string | null
}

withDefaults(defineProps<Props>(), {
  title: 'Video content',
  heading: null
})
</script>

<style scoped>
.video-embed {
  margin-bottom: 2rem;
}

.video-heading {
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

.video-iframe {
  border: none;
  width: 100%;
  height: 100%;
}

/* Responsive adjustments */
@media (max-width: 768px) {
  .video-heading {
    font-size: 1.25rem;
  }
}
</style>
