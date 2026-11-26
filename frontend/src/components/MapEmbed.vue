<template>
  <figure class="map-embed">
    <div v-if="localizedUrl" class="ratio">
      <iframe
        v-if="loaded"
        ref="frame"
        :src="localizedUrl"
        :title="title"
        allowfullscreen
        referrerpolicy="strict-origin-when-cross-origin"
        class="map-iframe"
      />
      <div
        v-else
        class="embed-facade flex aspect-video w-full flex-col items-center justify-center bg-slate-50 px-4 py-3 text-center dark:bg-slate-900/60"
      >
        <button
          type="button"
          class="inline-flex items-center gap-2 rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-primary-700 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-primary-500 dark:bg-primary-500 dark:text-slate-950 dark:hover:bg-primary-400"
          :aria-label="`Show map: ${title}`"
          :aria-describedby="noticeId"
          @click="show"
        >
          <svg class="h-4 w-4" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
            <path
              fill-rule="evenodd"
              d="M12 2a7 7 0 0 0-7 7c0 5.25 7 13 7 13s7-7.75 7-13a7 7 0 0 0-7-7Zm0 4.5a2.5 2.5 0 1 1 0 5 2.5 2.5 0 0 1 0-5Z"
            />
          </svg>
          Show map
        </button>
        <p
          :id="noticeId"
          class="mt-3 max-w-sm text-balance font-mono text-xs leading-normal text-slate-600 dark:text-slate-400"
        >
          Loads Google Maps, which may store data on your device. Nothing is requested from Google
          until you press the button.
        </p>
      </div>
    </div>
    <div v-else class="map-fallback" role="alert">
      <span class="fallback-icon" aria-hidden="true">📍</span>
      <p class="fallback-text">Map could not be loaded</p>
    </div>
    <figcaption v-if="heading" class="embed-caption">{{ heading }}</figcaption>
  </figure>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, toRef, useId } from 'vue'
import { useEmbedValidator } from '@/composables/useEmbedValidator'

/**
 * MapEmbed Component
 *
 * Google Maps embed that loads on a click. Until then the box holds a
 * placeholder: a button described by a notice. The server and the first
 * client render both produce the placeholder; only the button's click
 * creates the iframe, which then takes focus. The iframe carries no
 * role/tabindex overrides (D3-FE-05): role="application" forced screen
 * readers into application mode and tabindex="0" double-stopped keyboard
 * focus. The heading renders as a figcaption below the media, so it no
 * longer outranks the page's section headings in the document outline.
 * referrerpolicy matches the site's Referrer-Policy header: Google gets the
 * page's origin, not its full URL.
 *
 * The iframe has no sandbox and no credentialless attribute: either one needs
 * a manual check of the map's controls and links in Chrome, Firefox and
 * Safari.
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

const loaded = ref(false)
const frame = ref<HTMLIFrameElement | null>(null)
// useId gives the server render and the hydrated client the same id.
const noticeId = useId()

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

async function show() {
  loaded.value = true
  await nextTick()
  frame.value?.focus()
}
</script>

<style scoped>
/* No margin here: the parent media grid owns spacing (gap-6). A scoped
   margin-bottom cannot collapse out of a grid cell and double-spaced the
   section while spacing utilities were rediscovered in S3. */

.ratio {
  /* Identical treatment to VideoEmbed (D3-FE-05): a 1px ring, no shadow —
     the case-study layout keeps media quiet. The 16:9 ratio sits on the
     iframe and on the placeholder, not on this box, so the placeholder can
     grow taller when its text needs the room (a narrow screen, enlarged
     text) instead of being cut off by overflow: hidden. */
  width: 100%;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid var(--border-primary);
}

.map-iframe {
  border: none;
  width: 100%;
  aspect-ratio: 16 / 9;
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
