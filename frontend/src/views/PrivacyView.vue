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
          <h1 class="mt-2 text-title font-semibold text-slate-900 dark:text-white">Privacy</h1>
          <p class="mt-3 font-mono text-xs text-slate-500 dark:text-slate-400">
            Last updated: {{ LAST_UPDATED }}
          </p>
          <p class="mt-6 leading-relaxed text-slate-600 dark:text-slate-300">{{ INTRO }}</p>
        </header>

        <section v-for="section in sections" :key="section.id" class="mt-12">
          <h2
            :id="section.id"
            class="text-lg font-semibold tracking-tight text-slate-900 dark:text-white"
          >
            {{ section.title }}
          </h2>

          <template v-for="(block, index) in section.blocks" :key="index">
            <h3
              v-if="block.kind === 'heading'"
              class="mt-8 font-mono text-xs font-normal uppercase tracking-[0.12em] text-slate-500 dark:text-slate-400"
            >
              {{ block.text }}
            </h3>

            <p
              v-else-if="block.kind === 'paragraph'"
              class="mt-3 leading-relaxed text-slate-600 dark:text-slate-300"
            >
              <template v-for="(run, position) in block.runs" :key="position">
                <a
                  v-if="typeof run !== 'string'"
                  :href="run.href"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="font-medium text-primary-600 underline-offset-4 transition-colors hover:underline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-primary-500 dark:text-primary-400"
                  >{{ run.text }}<span class="sr-only"> (opens in a new tab)</span></a
                >
                <template v-else>{{ run }}</template>
              </template>
            </p>

            <ul
              v-else-if="block.kind === 'list'"
              class="mt-3 list-disc space-y-2 pl-5 leading-relaxed text-slate-600 marker:text-slate-400 dark:text-slate-300 dark:marker:text-slate-500"
            >
              <li v-for="item in block.items" :key="item">{{ item }}</li>
            </ul>

            <div v-else-if="block.kind === 'table'" class="mt-5 overflow-x-auto">
              <table :aria-labelledby="section.id" class="w-full border-collapse text-left text-sm">
                <thead>
                  <tr class="border-b border-slate-200 dark:border-slate-800">
                    <th
                      v-for="label in block.head"
                      :key="label"
                      scope="col"
                      class="py-2 pr-6 font-mono text-xs font-normal uppercase tracking-[0.12em] text-slate-500 dark:text-slate-400"
                    >
                      {{ label }}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="[what, howLong] in block.rows"
                    :key="what"
                    class="border-b border-slate-200 align-top dark:border-slate-800"
                  >
                    <th scope="row" class="py-3 pr-6 font-medium text-slate-900 dark:text-white">
                      {{ what }}
                    </th>
                    <td class="py-3 leading-relaxed text-slate-600 dark:text-slate-300">
                      {{ howLong }}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div
              v-else-if="block.kind === 'switch' && hydrated"
              class="mt-5 rounded-lg border border-slate-200 p-5 dark:border-slate-800"
            >
              <p
                aria-live="polite"
                class="text-sm leading-relaxed text-slate-700 dark:text-slate-300"
              >
                {{ switchStatus }}
              </p>
              <button
                v-if="!signalSent"
                type="button"
                class="mt-4 inline-flex items-center rounded-lg border border-slate-200 px-5 py-2.5 text-sm font-medium text-slate-700 transition-colors hover:border-primary-400/60 hover:text-primary-600 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-primary-500 dark:border-slate-800 dark:text-slate-200 dark:hover:border-primary-400/40 dark:hover:text-primary-400"
                @click="toggleCounting"
              >
                {{ declined ? SWITCH.resume : SWITCH.stop }}
              </button>
            </div>
          </template>
        </section>

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
import { computed, onMounted, ref } from 'vue'
import { useHead } from '@unhead/vue'
import NavBar from '@/components/NavBar.vue'
import FooterSection from '@/components/FooterSection.vue'
import {
  privacySignalSent,
  setVisitCountingOptOut,
  visitCountingDeclined
} from '@/services/analytics'

/**
 * What the site records about its readers, as static text: no API call, so
 * the page prerenders the same whether or not the backend answers. A change
 * to what the site records, shares or keeps changes this text in the same
 * commit and moves LAST_UPDATED, a literal rather than a date formatted at
 * render time, so the prerendered page and the client always agree on it.
 */
const LAST_UPDATED = '27 November 2026'

const DESCRIPTION =
  'This page says what this website records about the people who read it, why, who else handles it, how long it is kept, and what you can do about it.'

const INTRO = `${DESCRIPTION} It describes how the site works today, and it changes whenever that does.`

const LINKEDIN = 'https://www.linkedin.com/in/david-dashti/'
const GOOGLE_PRIVACY_POLICY = 'https://policies.google.com/privacy'
const IMY = 'https://www.imy.se/'

/** Text, or a link to another site, which opens in a new tab. */
type Run = string | { text: string; href: string }

type Block =
  | { kind: 'heading'; text: string }
  | { kind: 'paragraph'; runs: Run[] }
  | { kind: 'list'; items: string[] }
  | { kind: 'table'; head: [string, string]; rows: [string, string][] }
  | { kind: 'switch' }

interface Section {
  id: string
  title: string
  blocks: Block[]
}

const sections: Section[] = [
  {
    id: 'in-short',
    title: 'In short',
    blocks: [
      {
        kind: 'list',
        items: [
          "This site sets no cookies for visitors (starting the owner's sign-in sets one), and nothing here follows you to other websites.",
          'For each page you open, the site records the page, your country, the website that sent you (its domain only) and a visitor key that changes every day. Your IP address and browser details are not stored with it.',
          'Videos and maps stay switched off until you click them. Until then, nothing is requested from YouTube or Google; after a click, Google may set its own cookies.',
          'If your browser sends Global Privacy Control or Do Not Track, nothing is counted. You can also switch counting off below.'
        ]
      }
    ]
  },
  {
    id: 'responsible',
    title: 'Who is responsible',
    blocks: [
      {
        kind: 'paragraph',
        runs: [
          'This is the personal website of David Dashti, who decides what is recorded here and why (the "controller" under the GDPR). To reach me about anything on this page, send a message on LinkedIn: ',
          { text: 'linkedin.com/in/david-dashti', href: LINKEDIN },
          '.'
        ]
      }
    ]
  },
  {
    id: 'recorded',
    title: 'What is recorded, and why',
    blocks: [
      { kind: 'heading', text: 'Visit statistics' },
      {
        kind: 'paragraph',
        runs: [
          "When a page opens, your browser sends a short note to this site's server, api.dashti.se. The server stores:"
        ]
      },
      {
        kind: 'list',
        items: [
          'the address of the page on this site, such as /colophon (a page that does not exist is stored as /404);',
          'the domain of the website that linked here, if your browser passes one on, such as www.linkedin.com, but never the rest of that address;',
          'your country, as a two-letter code;',
          'the date and time;',
          "a visitor key, so that one person reading several pages on the same day counts as one visitor. The server makes the key from your IP address and browser details, mixed with a random value that exists only in the server's memory and is replaced every day. None of the three is stored. Once the day is over, the key cannot be turned back into an address, not even by the site."
        ]
      },
      {
        kind: 'paragraph',
        runs: [
          "A click on one of the site's LinkedIn, GitHub or open-source links is stored the same way, as a visit to that link."
        ]
      },
      {
        kind: 'paragraph',
        runs: [
          'To find your country, the server sends a shortened form of your IP address (the last part removed, so that it names a network rather than a device) to ipapi.co, a location lookup service, which returns only the country code. The server keeps the shortened address and its country in memory until the end of the day (UTC), so that it does not ask ipapi.co about the same network on every visit.'
        ]
      },
      {
        kind: 'paragraph',
        runs: [
          'The purpose is to see, in total, how much the site is read and which pages are read. The legal basis is legitimate interest (GDPR Article 6(1)(f)): knowing whether a professional portfolio reaches anyone.'
        ]
      },
      { kind: 'heading', text: 'Server logs' },
      {
        kind: 'paragraph',
        runs: [
          "The server keeps a technical log of requests to api.dashti.se: the time, what was requested and the result. A request refused by the rate limit is also logged with a keyed digest of your IP address, never the address itself. Each sign-in the server accepts or refuses, and each sign-out, is logged with that digest and the first 64 characters of your browser's user-agent string. The digest is the same for every request from one address, so that abuse can be traced and blocked. The visit notes described above are logged only when they fail. To limit abuse, the server also counts requests per address for one minute at a time, in memory only. The purpose is to keep the service secure and working; the legal basis is legitimate interest (Article 6(1)(f))."
        ]
      },
      { kind: 'heading', text: 'Error and performance reports' },
      {
        kind: 'paragraph',
        runs: [
          "When something breaks in your browser, a report goes to Sentry, an error-tracking service: what went wrong, the page address, your browser and operating system as named in its user-agent string, your browser's language and time zone, the page's latest performance measurement, and a short trail of what happened on the page before the error (pages opened, buttons clicked, requests made, messages written to the browser console). On one page view in ten, the browser also sends performance measurements. Reports do not include your IP address, cookies or anything you type."
        ]
      },
      {
        kind: 'paragraph',
        runs: [
          'If your browser sends Global Privacy Control or Do Not Track, or you switch counting off below, no performance measurements are sent. Error reports still are, because they are how a broken or attacked page gets noticed. The purpose is finding and fixing faults and attacks; the legal basis is legitimate interest (Article 6(1)(f)).'
        ]
      },
      { kind: 'heading', text: 'What is kept in your browser' },
      {
        kind: 'paragraph',
        runs: [
          "This site sets no cookies for visitors; only starting the owner's sign-in, described below, sets one. The site uses your browser's own storage for:"
        ]
      },
      {
        kind: 'list',
        items: [
          'your colour theme (light, dark or automatic), in local storage;',
          'your choice to switch counting off, if you make it, in local storage;',
          'where you had scrolled to on each page, in session storage, so that going back returns you there;',
          'the time of the last automatic reload after a site update, in session storage, so that it cannot repeat in a loop;',
          "copies of the site's own files and public content, so that pages load fast and work offline."
        ]
      },
      {
        kind: 'paragraph',
        runs: [
          "None of these names you, and none is sent anywhere. You can clear them in your browser's settings for this site at any time."
        ]
      },
      { kind: 'heading', text: 'Videos and maps' },
      {
        kind: 'paragraph',
        runs: [
          "The videos come from YouTube and the maps from Google Maps, both run by Google. Each shows a placeholder until you click it, and nothing is requested from Google before that. When you click, your browser connects to Google, which receives your IP address, your browser details and this site's address (not the page's), and may store cookies or other data on your device under its own privacy policy (",
          { text: 'policies.google.com/privacy', href: GOOGLE_PRIVACY_POLICY },
          '). Videos play in YouTube\'s privacy-enhanced mode (youtube-nocookie.com). Each click is your choice for that one video or map; reloading the page shows the placeholder again. You can also follow the "Watch on YouTube" link instead.'
        ]
      },
      { kind: 'heading', text: 'Signing in' },
      {
        kind: 'paragraph',
        runs: [
          "The sign-in at /admin is for the site owner only, and goes through GitHub. Starting it sets a cookie on api.dashti.se that ties the sign-in to your browser for five minutes. If GitHub then names an account other than the owner's, the sign-in is refused, and the server log keeps that account's GitHub username and account number with the refusal."
        ]
      }
    ]
  },
  {
    id: 'recipients',
    title: 'Who else handles the data',
    blocks: [
      {
        kind: 'list',
        items: [
          'Vercel hosts the website. Like any web host, it receives your IP address and browser details with each page you open.',
          'Fly.io hosts the server and its database, in Stockholm, and keeps the server logs.',
          'Sentry receives the error and performance reports, and stores them in its EU region, in Germany.',
          'ipapi.co receives the shortened IP address for the country lookup.',
          'GitHub stores encrypted backups of the database, which include the visit records. It cannot read them.',
          'Google receives data only after you click a video or a map, as described above.'
        ]
      },
      {
        kind: 'paragraph',
        runs: [
          "Most of these companies are based in the United States. Where your data leaves the EU or EEA, they rely on the EU-US Data Privacy Framework or the European Commission's standard contractual clauses, as their terms describe. Nothing is sold, and nothing is used for advertising."
        ]
      }
    ]
  },
  {
    id: 'retention',
    title: 'How long it is kept',
    blocks: [
      {
        kind: 'table',
        head: ['What', 'How long'],
        rows: [
          ['Visit records', '180 days, then deleted automatically'],
          ['Server logs', 'about 7 days, kept by Fly.io'],
          ['Error and performance reports', '30 days, kept by Sentry'],
          [
            'Encrypted database backups',
            "30 days on GitHub, and up to 60 days in Fly.io's disk snapshots, so a deleted record can survive that long in a backup"
          ],
          ["Vercel's request logs", 'a short time, kept by Vercel to run its service'],
          [
            'The daily random value behind the visitor key',
            'until the end of the day (UTC), in memory only'
          ],
          [
            'The shortened IP address used for the country lookup',
            'until the end of the day (UTC), in memory only'
          ],
          [
            'What your browser keeps',
            'until you clear it, and what is in session storage only until you close the tab'
          ]
        ]
      }
    ]
  },
  {
    id: 'objection',
    title: 'Your right to object',
    blocks: [
      {
        kind: 'paragraph',
        runs: [
          'You can object to the visit statistics at any time, without giving a reason. Two ways:'
        ]
      },
      {
        kind: 'list',
        items: [
          'Turn on Global Privacy Control or Do Not Track in your browser. This site then counts nothing, and its server throws away any visit note that carries the signal.',
          'Use the switch below. It applies to this browser.'
        ]
      },
      { kind: 'switch' },
      { kind: 'paragraph', runs: ['Without JavaScript, the site counts nothing at all.'] }
    ]
  },
  {
    id: 'rights',
    title: 'Your other rights',
    blocks: [
      {
        kind: 'paragraph',
        runs: [
          'Under the GDPR you can ask to see the data held about you, to have it corrected or deleted, or to limit how it is used. Apart from a refused sign-in, which the server log keeps with its GitHub account, the records above are built so that they cannot be traced back to a person, so there is usually nothing I can find and connect to you; if you send the date and time of a visit, or the GitHub username you tried to sign in with, I will look and tell you what I found. Send requests as a LinkedIn message; you will get an answer within a month.'
        ]
      },
      {
        kind: 'paragraph',
        runs: [
          'You can also complain to the Swedish Authority for Privacy Protection (Integritetsskyddsmyndigheten, IMY) at ',
          { text: 'imy.se', href: IMY },
          ', or to the data protection authority where you live or work.'
        ]
      },
      {
        kind: 'paragraph',
        runs: [
          'Nothing on this site makes automated decisions about you, and you do not have to give anything to use it.'
        ]
      }
    ]
  }
]

const SWITCH = {
  counted: 'Visits from this browser are counted, as described above.',
  declined: 'Visits from this browser are not counted. The choice is saved in this browser only.',
  signal:
    'Your browser sends Global Privacy Control or Do Not Track, so this site counts nothing from it.',
  stop: 'Stop counting my visits',
  resume: 'Count my visits again'
}

// The switch reads this browser's signals and storage, so it renders only
// once `hydrated` is set in onMounted: the prerendered page and the first
// client render both leave it out, and the sentence after it is all that a
// reader without JavaScript gets. One button element serves both choices,
// so focus stays on it when its label changes. A browser signal leaves the
// reader nothing to switch, so it shows a status and no button.
const hydrated = ref(false)
const signalSent = ref(false)
const declined = ref(false)

onMounted(() => {
  signalSent.value = privacySignalSent()
  declined.value = visitCountingDeclined()
  hydrated.value = true
})

const switchStatus = computed(() => {
  if (signalSent.value) return SWITCH.signal
  return declined.value ? SWITCH.declined : SWITCH.counted
})

/**
 * Stores the opposite choice, then shows what visitCountingDeclined() reads
 * back: where storage refuses the write, the status stays as it was.
 */
function toggleCounting(): void {
  setVisitCountingOptOut(!declined.value)
  declined.value = visitCountingDeclined()
}

useHead({
  title: 'Privacy | David Dashti',
  meta: [
    { name: 'description', content: DESCRIPTION },
    // The full og and twitter set: a key left out keeps the homepage value
    // that index.html carries.
    { property: 'og:title', content: 'Privacy | David Dashti' },
    { property: 'og:description', content: DESCRIPTION },
    { property: 'og:url', content: 'https://dashti.se/privacy' },
    { name: 'twitter:title', content: 'Privacy | David Dashti' },
    { name: 'twitter:description', content: DESCRIPTION },
    { name: 'robots', content: 'index, follow' }
  ],
  link: [{ rel: 'canonical', href: 'https://dashti.se/privacy' }]
})
</script>
