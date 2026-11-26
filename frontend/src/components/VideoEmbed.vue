<template>
  <figure class="video-embed">
    <div v-if="safeUrl" class="ratio">
      <iframe
        v-if="loaded"
        ref="frame"
        :src="playUrl"
        :title="title"
        allow="autoplay; encrypted-media; picture-in-picture"
        referrerpolicy="strict-origin-when-cross-origin"
        allowfullscreen
        class="video-iframe"
      />
      <div
        v-else
        class="embed-facade flex aspect-video w-full flex-col items-center justify-center bg-slate-50 px-4 py-3 text-center dark:bg-slate-900/60"
      >
        <button
          type="button"
          class="inline-flex items-center gap-2 rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-primary-700 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-primary-500 dark:bg-primary-500 dark:text-slate-950 dark:hover:bg-primary-400"
          :aria-label="`Play video: ${title}`"
          :aria-describedby="noticeId"
          @click="play"
        >
          <svg class="h-4 w-4" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
            <path d="M8 5v14l11-7z" />
          </svg>
          Play video
        </button>
        <p
          :id="noticeId"
          class="mt-3 max-w-sm text-balance font-mono text-xs leading-normal text-slate-600 dark:text-slate-400"
        >
          Plays from YouTube, run by Google, which may store data on your device. Nothing is
          requested from YouTube until you press play.
        </p>
        <a
          v-if="watchUrl"
          :href="watchUrl"
          target="_blank"
          rel="noopener noreferrer"
          class="mt-2 inline-flex items-center gap-1.5 text-xs font-medium text-primary-600 transition-colors hover:text-primary-700 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-primary-500 dark:text-primary-400 dark:hover:text-primary-300"
        >
          Watch on YouTube<span class="sr-only"> (opens in a new tab)</span>
          <svg
            class="h-3 w-3"
            fill="none"
            viewBox="0 0 24 24"
            stroke-width="2"
            stroke="currentColor"
            aria-hidden="true"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25"
            />
          </svg>
        </a>
      </div>
    </div>
    <div v-else class="video-fallback" role="alert">
      <span class="fallback-icon" aria-hidden="true">🎬</span>
      <p class="fallback-text">Video could not be loaded</p>
    </div>
    <figcaption v-if="heading" class="embed-caption">{{ heading }}</figcaption>
  </figure>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, useId } from 'vue'
import { useEmbedValidator } from '@/composables/useEmbedValidator'

/**
 * VideoEmbed Component
 *
 * YouTube embed that loads on a click. Until then the box holds a
 * placeholder: a play button described by a notice, and a link to the video
 * on youtube.com. The server and the first client render both produce the
 * placeholder; only the button's click creates the iframe, which then takes
 * focus. The iframe carries no role/tabindex overrides (D3-FE-05):
 * role="application" forced screen readers into application mode and
 * tabindex="0" double-stopped keyboard focus — the iframe is already
 * focusable and YouTube's player manages its own keyboard interaction. The
 * heading renders as a figcaption below the media, so it no longer outranks
 * the page's section headings in the document outline.
 *
 * The iframe has no sandbox and no credentialless attribute: either one needs
 * a manual check of playback, fullscreen and the player's own links in
 * Chrome, Firefox and Safari.
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

const loaded = ref(false)
const frame = ref<HTMLIFrameElement | null>(null)
// useId gives the server render and the hydrated client the same id.
const noticeId = useId()

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
// now describe the same set. (The iframe's allow attribute grants autoplay,
// encrypted media and picture-in-picture only. accelerometer and gyroscope
// were dropped because Permissions-Policy denies them site-wide, so the
// grants were dead and Chrome logged violations when the player probed
// sensors; clipboard-write and web-share are not granted either.
// Fullscreen comes from allowfullscreen alone: Chrome logs a warning when
// allow also names it.)
const ALLOWED_VIDEO_HOSTS = ['www.youtube-nocookie.com']

const safeUrl = useEmbedValidator(embedUrl, ALLOWED_VIDEO_HOSTS, '/embed/', 'VideoEmbed')

// The frame's source: the validated URL with autoplay=1, so the click that
// creates the frame also starts the video.
const playUrl = computed(() => {
  if (!safeUrl.value) return undefined
  const parsed = new URL(safeUrl.value)
  parsed.searchParams.set('autoplay', '1')
  return parsed.href
})

// A YouTube video id is 11 characters of [A-Za-z0-9_-]. The watch link is
// built only from a path segment of that shape. Two embed paths have that
// shape and name no video: /embed/videoseries (a playlist) and
// /embed/live_stream (a channel's live stream).
const VIDEO_ID = /^[A-Za-z0-9_-]{11}$/
const NOT_VIDEO_IDS = new Set(['videoseries', 'live_stream'])

const watchUrl = computed(() => {
  if (!safeUrl.value) return null
  const id = new URL(safeUrl.value).pathname.slice('/embed/'.length)
  if (!VIDEO_ID.test(id) || NOT_VIDEO_IDS.has(id)) return null
  return `https://www.youtube.com/watch?v=${id}`
})

async function play() {
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
  /* Identical treatment to MapEmbed (D3-FE-05): a 1px ring, no shadow —
     the case-study layout keeps media quiet. The 16:9 ratio sits on the
     iframe and on the placeholder, not on this box, so the placeholder can
     grow taller when its text needs the room (a narrow screen, enlarged
     text) instead of being cut off by overflow: hidden. */
  width: 100%;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid var(--border-primary);
}

.video-iframe {
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
