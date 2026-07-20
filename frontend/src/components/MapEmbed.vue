<template>
  <figure class="map-embed">
    <div v-if="localizedUrl" class="ratio">
      <iframe
        :src="localizedUrl"
        :title="title"
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
    <figcaption v-if="heading" class="embed-caption">{{ heading }}</figcaption>
  </figure>
</template>

<script setup lang="ts">
import { computed, toRef } from 'vue'
import { useEmbedValidator } from '@/composables/useEmbedValidator'

/**
 * MapEmbed Component
 *
 * Responsive Google Maps embed with lazy loading. The iframe carries no
 * role/tabindex overrides (D3-FE-05): role="application" forced screen
 * readers into application mode and tabindex="0" double-stopped keyboard
 * focus. The heading renders as a figcaption below the media, so it no
 * longer outranks the page's section headings in the document outline.
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

// D3-SEC-04: www.google.com only — bare google.com passed validation but
// CSP frame-src blocked the iframe (blank box), and maps.google.com was
// allowed by CSP yet used by no live content. Allowlist and CSP now match.
const ALLOWED_MAP_HOSTS = ['www.google.com']

const safeUrl = useEmbedValidator(toRef(props, 'url'), ALLOWED_MAP_HOSTS, '/maps/embed', 'MapEmbed')

// D3-FE-05: the stored embed URLs were generated from a Swedish browser
// session (!2sse locale markers), so labels and attribution rendered in
// Swedish. hl=en overrides the UI language without touching the stored URL.
const localizedUrl = computed(() => {
  if (!safeUrl.value) return null
  return safeUrl.value.includes('hl=')
    ? safeUrl.value
    : `${safeUrl.value}${safeUrl.value.includes('?') ? '&' : '?'}hl=en`
})
</script>

<style scoped>
/* No margin here: the parent media grid owns spacing (gap-6). A scoped
   margin-bottom cannot collapse out of a grid cell and double-spaced the
   section while spacing utilities were rediscovered in S3. */

.ratio {
  /* Identical treatment to VideoEmbed (D3-FE-05): aspect-video + a 1px
     ring, no shadow — the case-study layout keeps media quiet. */
  aspect-ratio: 16 / 9;
  width: 100%;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid var(--border-primary);
}

.map-iframe {
  border: none;
  width: 100%;
  height: 100%;
  display: block;
}

.embed-caption {
  /* Mono caption below the media — matches the rail's dt labels. */
  font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, monospace;
  font-size: 0.75rem;
  font-weight: 400;
  text-transform: uppercase;
  letter-spacing: 0.15em;
  margin-top: 0.75rem;
  color: var(--text-secondary);
}

/* Google's embed has no dark theme — a partial invert approximates one so
   the map stops glaring white on slate-950 pages. Softened from the
   original invert(0.86)/saturate(0.7)/contrast(0.95) recipe (D3-FE-05):
   less invert and no contrast crush keep the location pin and the
   attribution line legible. */
[data-theme='dark'] .map-iframe {
  filter: invert(0.8) hue-rotate(180deg) saturate(0.9) brightness(1.05);
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
