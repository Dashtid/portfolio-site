<template>
  <div class="min-h-screen bg-white text-slate-900 dark:bg-slate-950 dark:text-slate-100">
    <NavBar />

    <main id="main-content" tabindex="-1" class="pt-24">
      <!-- Unknown slug: same honest-404 treatment as ExperienceDetail
           (served 200 by the SPA rewrite; noindex is the crawler signal) -->
      <div v-if="!post" class="mx-auto max-w-3xl px-6 py-20 text-center">
        <p class="font-mono text-xs uppercase tracking-[0.2em] text-slate-500 dark:text-slate-400">
          HTTP 404 — article not found
        </p>
        <h1
          class="mt-6 font-mono text-8xl font-semibold tracking-tight text-slate-900 dark:text-white"
        >
          404
        </h1>
        <p
          class="mx-auto mt-6 max-w-md text-balance text-base font-light leading-relaxed text-slate-500 sm:text-lg dark:text-slate-400"
        >
          This article doesn't exist — it may have moved, or the link is stale.
        </p>
        <router-link
          to="/writing"
          class="mt-8 inline-flex items-center gap-2 rounded-lg bg-primary-600 px-5 py-2.5 text-sm font-medium text-white transition-colors hover:bg-primary-700 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-primary-500 dark:bg-primary-500 dark:text-slate-950 dark:hover:bg-primary-400"
        >
          All writing
        </router-link>
      </div>

      <article v-else class="mx-auto max-w-3xl px-6 py-12">
        <header>
          <p
            class="font-mono text-xs uppercase tracking-[0.2em] text-slate-500 dark:text-slate-400"
          >
            {{ formatDate(post.date) }}
          </p>
          <h1 class="mt-3 text-balance text-title font-semibold text-slate-900 dark:text-white">
            {{ post.title }}
          </h1>
        </header>

        <!-- Trusted input: repo-committed, owner-reviewed markdown (see
             data/writing.ts) -->
        <!-- eslint-disable-next-line vue/no-v-html -->
        <div class="article-prose mt-8" v-html="post.html"></div>

        <footer class="mt-12 border-t border-slate-200 pt-8 dark:border-slate-800">
          <router-link
            to="/writing"
            class="inline-flex items-center gap-1 text-sm font-medium text-primary-600 transition-all hover:gap-2 hover:text-primary-700 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-primary-500 dark:text-primary-400 dark:hover:text-primary-300"
          >
            All writing
          </router-link>
        </footer>
      </article>
    </main>

    <FooterSection />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useHead } from '@unhead/vue'
import NavBar from '@/components/NavBar.vue'
import FooterSection from '@/components/FooterSection.vue'
import { findPost } from '@/data/writing'

const route = useRoute()
const post = computed(() => findPost(route.params.slug as string))

const selfUrl = computed(() => `https://dashti.se/writing/${route.params.slug as string}`)

useHead({
  title: computed(() =>
    post.value ? `${post.value.title} | David Dashti` : '404 — Article Not Found | David Dashti'
  ),
  meta: [
    { name: 'description', content: computed(() => post.value?.description ?? '') },
    { property: 'og:title', content: computed(() => post.value?.title ?? '') },
    { property: 'og:description', content: computed(() => post.value?.description ?? '') },
    { property: 'og:type', content: 'article' },
    // og:url stays the SELF url even for cross-posted pieces: shares of
    // this page should attribute to this page; rel=canonical alone
    // carries the cross-post signal for crawlers.
    { property: 'og:url', content: selfUrl },
    {
      property: 'article:published_time',
      content: computed(() => post.value?.date ?? '')
    },
    { name: 'twitter:title', content: computed(() => post.value?.title ?? '') },
    {
      name: 'robots',
      content: computed(() => (post.value ? 'index, follow' : 'noindex'))
    }
  ],
  link: [
    // D3-FEAT-03: canonical support — cross-posted pieces can point their
    // canonical elsewhere, but the default is that dashti.se IS the
    // canonical channel.
    { rel: 'canonical', href: computed(() => post.value?.canonical ?? selfUrl.value) }
  ]
})

const formatDate = (dateString: string): string => {
  const date = new Date(dateString)
  // timeZone UTC: date-only frontmatter parses as UTC midnight
  return date.toLocaleDateString('en-US', {
    month: 'long',
    day: 'numeric',
    year: 'numeric',
    timeZone: 'UTC'
  })
}
</script>

<style scoped>
/* Article typography — hand-rolled (no typography plugin in the build).
   :deep reaches the v-html-rendered markdown. */
.article-prose {
  line-height: 1.75;
  color: var(--text-secondary);
  max-width: 65ch;
}

.article-prose :deep(h2) {
  margin-top: 2.5rem;
  font-size: 1.25rem;
  font-weight: 600;
  letter-spacing: -0.015em;
  color: var(--text-primary);
}

.article-prose :deep(h3) {
  margin-top: 2rem;
  font-size: 1.05rem;
  font-weight: 600;
  color: var(--text-primary);
}

.article-prose :deep(p) {
  margin-top: 1.25rem;
}

.article-prose :deep(a) {
  color: var(--link-color);
  text-decoration: underline;
  text-underline-offset: 3px;
}

.article-prose :deep(ul),
.article-prose :deep(ol) {
  margin-top: 1.25rem;
  padding-left: 1.5rem;
}

.article-prose :deep(ul) {
  list-style: disc;
}

.article-prose :deep(ol) {
  list-style: decimal;
}

.article-prose :deep(li) {
  margin-top: 0.5rem;
}

.article-prose :deep(code) {
  font-family: var(--font-mono, monospace);
  font-size: 0.875em;
  background: var(--bg-tertiary);
  border-radius: 4px;
  padding: 0.125rem 0.375rem;
}

.article-prose :deep(pre) {
  margin-top: 1.25rem;
  padding: 1rem 1.25rem;
  border-radius: 12px;
  background: var(--color-slate-900);
  color: var(--color-slate-100);
  overflow-x: auto;
}

.article-prose :deep(pre code) {
  background: transparent;
  padding: 0;
  font-size: 0.85rem;
}

.article-prose :deep(blockquote) {
  margin-top: 1.25rem;
  border-left: 3px solid var(--primary-300);
  padding-left: 1.25rem;
  font-style: italic;
}

.article-prose :deep(strong) {
  font-weight: 600;
  color: var(--text-primary);
}
</style>
