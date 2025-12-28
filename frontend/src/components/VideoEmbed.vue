<template>
  <div class="video-embed">
    <h2 v-if="heading" class="video-heading">{{ heading }}</h2>
    <div v-if="safeUrl" class="ratio ratio-16x9">
      <iframe
        :src="safeUrl"
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
    <div v-else class="video-fallback" role="alert">
      <span class="fallback-icon" aria-hidden="true">🎬</span>
      <p class="fallback-text">Video could not be loaded</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

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

const props = withDefaults(defineProps<Props>(), {
  title: 'Video content',
  heading: null
})

// Allowed YouTube embed domains
const ALLOWED_VIDEO_HOSTS = [
  'www.youtube.com',
  'youtube.com',
  'www.youtube-nocookie.com',
  'youtube-nocookie.com'
]

// Validate URL is a safe YouTube embed URL
const safeUrl = computed<string | null>(() => {
  if (!props.url) return null

  try {
    const parsed = new URL(props.url)

    // Only allow https protocol
    if (parsed.protocol !== 'https:') {
      if (import.meta.env.DEV) {
        console.warn(`[VideoEmbed] Blocked non-https URL: ${props.url}`)
      }
      return null
    }

    // Only allow YouTube embed domains
    if (!ALLOWED_VIDEO_HOSTS.includes(parsed.hostname)) {
      if (import.meta.env.DEV) {
        console.warn(`[VideoEmbed] Blocked non-YouTube URL: ${props.url}`)
      }
      return null
    }

    // Must be embed path
    if (!parsed.pathname.startsWith('/embed/')) {
      if (import.meta.env.DEV) {
        console.warn(`[VideoEmbed] Blocked non-embed URL: ${props.url}`)
      }
      return null
    }

    return props.url
  } catch {
    if (import.meta.env.DEV) {
      console.warn(`[VideoEmbed] Invalid URL: ${props.url}`)
    }
    return null
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

/* Fallback UI when video cannot be loaded */
.video-fallback {
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
[data-theme='dark'] .video-fallback {
  background: var(--bg-secondary, #1e293b);
  border-color: var(--border-color, #334155);
}
</style>
