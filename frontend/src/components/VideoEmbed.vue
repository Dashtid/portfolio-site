<template>
  <figure class="video-embed">
    <div v-if="safeUrl" class="ratio">
      <iframe
        :src="safeUrl"
        :title="title"
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
    <figcaption v-if="heading" class="embed-caption">{{ heading }}</figcaption>
  </figure>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useEmbedValidator } from '@/composables/useEmbedValidator'

/**
 * VideoEmbed Component
 *
 * Responsive YouTube video embed with lazy loading. The iframe carries no
 * role/tabindex overrides (D3-FE-05): role="application" forced screen
 * readers into application mode and tabindex="0" double-stopped keyboard
 * focus — the iframe is already focusable and YouTube's player manages
 * its own keyboard interaction. The heading renders as a figcaption below
 * the media, so it no longer outranks the page's section headings in the
 * document outline.
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

// YouTube's privacy-enhanced mode lives on www.youtube-nocookie.com. The
// stored URLs name www.youtube.com, so the host is swapped here, and the si
// parameter that YouTube's share dialog appends is dropped with it.
const embedUrl = computed(() => {
  try {
    const parsed = new URL(props.url)
    if (parsed.hostname !== 'www.youtube.com') return props.url
    parsed.hostname = 'www.youtube-nocookie.com'
    parsed.searchParams.delete('si')
    return parsed.href
  } catch {
    return props.url
  }
})

// D3-SEC-04: www hosts only — the bare-domain entries used to pass this
// validator while the CSP frame-src (www hosts only) blocked the iframe,
// rendering a blank box instead of failing validation. Allowlist and CSP
// now describe the same set. (accelerometer/gyroscope were dropped from
// the iframe allow attr above: Permissions-Policy denies them site-wide,
// so the grants were dead and Chrome logged violations when the player
// probed sensors.)
const ALLOWED_VIDEO_HOSTS = ['www.youtube-nocookie.com']

const safeUrl = useEmbedValidator(embedUrl, ALLOWED_VIDEO_HOSTS, '/embed/', 'VideoEmbed')
</script>

<style scoped>
/* No margin here: the parent media grid owns spacing (gap-6). A scoped
   margin-bottom cannot collapse out of a grid cell and double-spaced the
   section while spacing utilities were rediscovered in S3. */

.ratio {
  /* Identical treatment to MapEmbed (D3-FE-05): aspect-video + a 1px
     ring, no shadow — the case-study layout keeps media quiet. */
  aspect-ratio: 16 / 9;
  width: 100%;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid var(--border-primary);
}

.video-iframe {
  border: none;
  width: 100%;
  height: 100%;
  display: block;
}

.embed-caption {
  /* Mono caption below the media — the same --font-mono stack as the rail's dt labels. */
  font-family: var(--font-mono);
  font-size: 0.75rem;
  font-weight: 400;
  text-transform: uppercase;
  letter-spacing: 0.15em;
  margin-top: 0.75rem;
  color: var(--text-secondary);
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
  border-radius: 12px;
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
