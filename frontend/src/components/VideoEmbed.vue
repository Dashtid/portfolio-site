<template>
  <div v-if="url" class="video-embed">
    <h2 v-if="heading" class="video-heading">{{ heading }}</h2>
    <div class="ratio ratio-16x9">
      <iframe
        :src="url"
        :title="title"
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
        referrerpolicy="strict-origin-when-cross-origin"
        allowfullscreen
        loading="lazy"
        class="video-iframe"
      />
    </div>
  </div>
</template>

<script setup>
import { defineProps } from 'vue'

const props = defineProps({
  url: {
    type: String,
    required: true,
    default: null
  },
  title: {
    type: String,
    required: true,
    default: 'Video content'
  },
  heading: {
    type: String,
    required: false,
    default: null
  }
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
