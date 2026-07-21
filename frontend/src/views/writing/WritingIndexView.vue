<template>
  <div class="min-h-screen bg-white text-slate-900 dark:bg-slate-950 dark:text-slate-100">
    <NavBar />

    <main id="main-content" tabindex="-1" class="pt-24">
      <div class="mx-auto max-w-3xl px-6 py-12">
        <header>
          <p
            class="font-mono text-xs uppercase tracking-[0.2em] text-slate-500 dark:text-slate-400"
          >
            David Dashti
          </p>
          <h1 class="mt-2 text-title font-semibold text-slate-900 dark:text-white">Writing</h1>
          <p class="mt-4 max-w-xl leading-relaxed text-slate-600 dark:text-slate-300">
            Notes from practice — premarket cybersecurity, secure lifecycle work, and the security
            of medical software.
          </p>
        </header>

        <ul v-if="writingPosts.length" class="mt-10 space-y-8">
          <li v-for="post in writingPosts" :key="post.slug">
            <article>
              <p class="font-mono text-xs text-slate-500 dark:text-slate-400">
                {{ formatDate(post.date) }}
              </p>
              <h2 class="mt-1 text-lg font-semibold tracking-tight">
                <router-link
                  :to="`/writing/${post.slug}`"
                  class="text-slate-900 transition-colors hover:text-primary-700 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-primary-500 dark:text-white dark:hover:text-primary-300"
                >
                  {{ post.title }}
                </router-link>
              </h2>
              <p
                v-if="post.description"
                class="mt-2 max-w-xl text-sm leading-relaxed text-slate-600 dark:text-slate-300"
              >
                {{ post.description }}
              </p>
            </article>
          </li>
        </ul>

        <!-- Honest empty state: the surface exists ahead of its first
             article (D3-FEAT-03 launch is owner-gated). noindex while
             empty via the reactive robots meta below. -->
        <p v-else class="mt-10 text-slate-500 dark:text-slate-400">
          Nothing published yet — the first piece is on its way.
        </p>

        <div class="mt-12 border-t border-slate-200 pt-8 dark:border-slate-800">
          <router-link
            to="/"
            class="inline-flex items-center gap-1 text-sm font-medium text-primary-600 transition-all hover:gap-2 hover:text-primary-700 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-primary-500 dark:text-primary-400 dark:hover:text-primary-300"
          >
            Back to Portfolio
          </router-link>
        </div>
      </div>
    </main>

    <FooterSection />
  </div>
</template>

<script setup lang="ts">
import { useHead } from '@unhead/vue'
import NavBar from '@/components/NavBar.vue'
import FooterSection from '@/components/FooterSection.vue'
import { writingPosts } from '@/data/writing'

const WRITING_DESCRIPTION =
  'Writing on premarket cybersecurity, secure lifecycle work, and the security of medical software.'

useHead({
  title: 'Writing | David Dashti',
  meta: [
    { name: 'description', content: WRITING_DESCRIPTION },
    // Full og/twitter override set — unset keys inherit the homepage
    // values hardcoded in index.html (D3-CNT-02 regression class)
    { property: 'og:title', content: 'Writing | David Dashti' },
    { property: 'og:description', content: WRITING_DESCRIPTION },
    { property: 'og:url', content: 'https://dashti.se/writing' },
    { name: 'twitter:title', content: 'Writing | David Dashti' },
    { name: 'twitter:description', content: WRITING_DESCRIPTION },
    // Empty surface stays out of the index until the first article ships
    { name: 'robots', content: writingPosts.length ? 'index, follow' : 'noindex' }
  ],
  link: [
    { rel: 'canonical', href: 'https://dashti.se/writing' },
    {
      rel: 'alternate',
      type: 'application/rss+xml',
      title: 'David Dashti — Writing',
      href: 'https://dashti.se/writing/rss.xml'
    }
  ]
})

const formatDate = (dateString: string): string => {
  const date = new Date(dateString)
  // timeZone UTC: date-only frontmatter parses as UTC midnight
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    timeZone: 'UTC'
  })
}
</script>
