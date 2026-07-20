<template>
  <div class="video-embed">
    <h2 v-if="heading" class="video-heading">{{ heading }}</h2>
    <div v-if="safeUrl" class="ratio">
      <iframe
        :src="safeUrl"
        :title="title"
        :aria-label="'YouTube video: ' + title"
        role="application"
        tabindex="0"
        allow="autoplay; clipboard-write; encrypted-media; picture-in-picture; web-share"
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
import { toRef } from 'vue'
import { useEmbedValidator } from '@/composables/useEmbedValidator'

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

// D3-SEC-04: www hosts only — the bare-domain entries used to pass this
// validator while the CSP frame-src (www hosts only) blocked the iframe,
// rendering a blank box instead of failing validation. Allowlist and CSP
// now describe the same set. (accelerometer/gyroscope were dropped from
// the iframe allow attr above: Permissions-Policy denies them site-wide,
// so the grants were dead and Chrome logged violations when the player
// probed sensors.)
const ALLOWED_VIDEO_HOSTS = ['www.youtube.com', 'www.youtube-nocookie.com']

const safeUrl = useEmbedValidator(toRef(props, 'url'), ALLOWED_VIDEO_HOSTS, '/embed/', 'VideoEmbed')
</script>

<style scoped>
/* No margin here: the parent media-section grid owns spacing (mb-12 +
   gap-6). A scoped margin-bottom cannot collapse out of a grid cell and
   double-spaced the section while spacing utilities were rediscovered
   in S3. */

.video-heading {
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

.video-iframe {
  border: none;
  width: 100%;
  height: 100%;
}

/* Fallback UI when video cannot be loaded. Uses semantic tokens that
   swap via variables.css — no [data-theme='dark'] override needed. */
.video-fallback {
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
