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
          <h1 class="mt-2 text-title font-semibold text-slate-900 dark:text-white">Colophon</h1>
          <p class="mt-4 leading-relaxed text-slate-600 dark:text-slate-300">
            How this site is built, and how it is secured. I work on product security for regulated
            medical software, so it seemed fair to show the same practices applied to something of
            my own rather than only describe them.
          </p>
          <p class="mt-4 leading-relaxed text-slate-600 dark:text-slate-300">
            Everything below is checkable. The response headers are visible to anyone who looks, and
            the pipeline that produces them is in the
            <a
              href="https://github.com/Dashtid/portfolio-site"
              target="_blank"
              rel="noopener noreferrer"
              class="font-medium text-primary-600 underline-offset-4 transition-colors hover:underline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-primary-500 dark:text-primary-400"
              >public repository</a
            >.
          </p>
        </header>

        <section v-for="section in sections" :key="section.id" class="mt-12">
          <h2 class="text-lg font-semibold tracking-tight text-slate-900 dark:text-white">
            {{ section.title }}
          </h2>
          <p
            v-if="section.blurb"
            class="mt-2 max-w-xl text-sm leading-relaxed text-slate-600 dark:text-slate-300"
          >
            {{ section.blurb }}
          </p>

          <dl class="mt-5 space-y-4 border-l border-slate-200 pl-5 dark:border-slate-800">
            <div v-for="fact in section.facts" :key="fact.term">
              <dt
                class="font-mono text-xs uppercase tracking-[0.12em] text-slate-500 dark:text-slate-400"
              >
                {{ fact.term }}
              </dt>
              <dd class="mt-1 text-sm leading-relaxed text-slate-700 dark:text-slate-300">
                {{ fact.detail }}
              </dd>
            </div>
          </dl>
        </section>

        <!-- An engineering page that lists only strengths is marketing, so
             this section names the limits that are real. When a listed gap
             gets closed (the inline-style allowance, 4 Sep 2026), the entry
             is replaced, not silently deleted — a test in ColophonView.spec
             fails if the policy and this prose ever diverge. -->
        <section class="mt-12">
          <h2 class="text-lg font-semibold tracking-tight text-slate-900 dark:text-white">
            Where it falls short
          </h2>
          <p class="mt-2 leading-relaxed text-slate-600 dark:text-slate-300">
            One person builds, reviews and deploys this site. There is no second reviewer, so review
            pressure comes from the pipeline — tests, scanners, budgets — rather than from another
            human, and the dependency chain ultimately rests on trusting GitHub, PyPI and npm, as
            everyone's does. Those are the honest limits of a personal site. An earlier version of
            this section also admitted that the style policy still allowed inline styles; that gap
            was closed on 4 September 2026, which is the outcome this section exists to force.
          </p>
        </section>

        <section class="mt-12">
          <h2 class="text-lg font-semibold tracking-tight text-slate-900 dark:text-white">
            Reporting something
          </h2>
          <p class="mt-2 leading-relaxed text-slate-600 dark:text-slate-300">
            If you find a problem here, there is an RFC 9116
            <a
              href="/.well-known/security.txt"
              class="font-medium text-primary-600 underline-offset-4 transition-colors hover:underline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-primary-500 dark:text-primary-400"
              >security.txt</a
            >
            with contact details. Reports are welcome, including the small ones.
          </p>
        </section>

        <div class="mt-12 border-t border-slate-200 pt-8 dark:border-slate-800">
          <p class="font-mono text-xs text-slate-500 dark:text-slate-400">
            Claims on this page last verified against the live site on {{ VERIFIED_ON }}.
          </p>
          <router-link
            to="/"
            class="mt-4 inline-flex items-center gap-1 text-sm font-medium text-primary-600 transition-all hover:gap-2 hover:text-primary-700 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-primary-500 dark:text-primary-400 dark:hover:text-primary-300"
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

/**
 * Every line below was verified against the running site or the repository
 * on the date shown, not written from memory. If you change the CSP, the
 * cookie policy, the pin verifier or the backup schedule, change this page in
 * the same commit and move VERIFIED_ON — a stale security claim on a public
 * page is worse than no page, and this one invites the reader to check.
 */
const VERIFIED_ON = '4 September 2026'

interface Fact {
  term: string
  detail: string
}

interface Section {
  id: string
  title: string
  blurb?: string
  facts: Fact[]
}

const sections: Section[] = [
  {
    id: 'built',
    title: 'What it is built with',
    facts: [
      {
        term: 'Frontend',
        detail:
          'Vue 3 and TypeScript, pre-rendered to static HTML at build time and served from Vercel. Pages arrive complete rather than assembling themselves in the browser.'
      },
      {
        term: 'Backend',
        detail:
          'FastAPI and PostgreSQL on Fly.io. It holds the content and serves the private admin API. The public pages are plain static files carrying the content baked into them at build time.'
      },
      {
        term: 'Content',
        detail:
          'Edited through a private admin interface, stored in Postgres, and baked into the static pages by a build. Publishing is therefore a deploy, with the same checks as any code change.'
      }
    ]
  },
  {
    id: 'headers',
    title: 'What the browser is told',
    blurb:
      'Response headers are the cheapest security control there is and the easiest to leave half-configured. These are set deliberately and tested.',
    facts: [
      {
        term: 'Content Security Policy',
        detail:
          'Scripts may load only from this origin, plus two SHA-256 hashes covering the only two inline scripts the site ships. Styles are locked the same way — stylesheet files from this origin plus two pinned hashes, one for the offline page and one for the theme switcher’s transition guard, with no blanket inline allowance for either. Inline event handlers are refused outright, as are plugins, framing, and any attempt to rewrite the document base or post a form elsewhere.'
      },
      {
        term: 'Hash drift',
        detail:
          'Every hash in the policy is recomputed from the source on each test run, and the built pages are scanned for styling the policy would not cover. A reformatted script, an edited style block or a stray style attribute fails the build instead of silently breaking the page in production, which is the usual way hash-based policies rot.'
      },
      {
        term: 'Transport',
        detail:
          'Strict transport security for a year, covering subdomains. The domain was submitted to the browser preload list on 4 September 2026 and is pending inclusion; once it ships, a browser that has never been here will refuse plaintext before the first request is ever made.'
      },
      {
        term: 'The rest',
        detail:
          'Framing denied, MIME sniffing off, referrers trimmed across origins, and camera, microphone, geolocation, payment, USB and the motion sensors all switched off for the page and anything it embeds.'
      }
    ]
  },
  {
    id: 'admin',
    title: 'The private half',
    blurb:
      'One person can sign in here. That makes the account worth protecting rather than not worth bothering with.',
    facts: [
      {
        term: 'Sign-in',
        detail:
          'GitHub OAuth against a single permitted account. There is no password to phish, guess or leak.'
      },
      {
        term: 'Sessions',
        detail:
          'Cookies only — HttpOnly and SameSite, never readable by JavaScript. The working credential lasts thirty minutes; the renewal credential is replaced every time it is used.'
      },
      {
        term: 'Stolen-token handling',
        detail:
          'Replaying an already-used renewal token is treated as theft, per RFC 6819, and revokes every session for the account at once. A brief window is carved out for the harmless case of two browser tabs renewing simultaneously, so ordinary use is not mistaken for an attack.'
      },
      {
        term: 'Abuse limits',
        detail:
          'Requests are rate limited and oversized request bodies are rejected before they reach any handler.'
      }
    ]
  },
  {
    id: 'supply-chain',
    title: 'What goes into a build',
    blurb:
      'Most realistic attacks on a site like this arrive through its dependencies or its pipeline, not its pages.',
    facts: [
      {
        term: 'Pinned actions',
        detail:
          'All fifteen third-party build steps are pinned to an exact commit, never a moving tag. A script in the pipeline re-checks every pin against the version written beside it and fails if the two disagree — because a stale comment beside a correct hash is how a pin quietly stops meaning anything.'
      },
      {
        term: 'Verified dependencies',
        detail:
          'Every Python package is installed only if its hash matches a value committed to the repository. That includes the installer itself, so the tool doing the verifying is verified too. JavaScript packages install from a committed lockfile.'
      },
      {
        term: 'Scanning',
        detail:
          'Every change gets static analysis, a vulnerability scan of the tree, a review of any dependency it adds, a supply-chain posture score, and a secret scan of the diff. The scanner binary is itself checksum-verified before it is trusted to run. Findings are triaged rather than left to accumulate.'
      },
      {
        term: 'Gates',
        detail:
          'Nothing deploys until the unit tests, the browser tests and a performance and accessibility budget have all passed. Deploying is not a separate decision from testing.'
      }
    ]
  },
  {
    id: 'backups',
    title: 'Backups, and evidence they work',
    blurb:
      'An untested backup is a belief, not a control. This is the part most personal sites skip, so it is the part worth showing.',
    facts: [
      {
        term: 'Nightly, encrypted',
        detail:
          'The database is dumped every night and encrypted to a public key before it is stored. The matching private key is held offline and never reaches the machine that runs the backup, so the backup process cannot read its own output.'
      },
      {
        term: 'Rehearsed, not assumed',
        detail:
          'A restore checklist is filed automatically every quarter. It has been carried out: the archive was decrypted, restored into a disposable database with zero errors, and its row counts matched production exactly.'
      },
      {
        term: 'When something went wrong',
        detail:
          'That rehearsal is also what caught a stored key being unusable, and the recovery — rotate the key, re-encrypt, run the whole drill again on a fresh backup — was completed the same week. Drills earn their keep on the days they fail.'
      }
    ]
  }
]

const COLOPHON_DESCRIPTION =
  'How dashti.se is built and secured: content security policy, session handling, a hash-verified dependency chain, and backups with a restore drill that has actually been run.'

useHead({
  title: 'Colophon | David Dashti',
  meta: [
    { name: 'description', content: COLOPHON_DESCRIPTION },
    // Full og/twitter override set — unset keys inherit the homepage values
    // hardcoded in index.html (D3-CNT-02 regression class).
    { property: 'og:title', content: 'Colophon | David Dashti' },
    { property: 'og:description', content: COLOPHON_DESCRIPTION },
    { property: 'og:url', content: 'https://dashti.se/colophon' },
    { name: 'twitter:title', content: 'Colophon | David Dashti' },
    { name: 'twitter:description', content: COLOPHON_DESCRIPTION },
    { name: 'robots', content: 'index, follow' }
  ],
  link: [{ rel: 'canonical', href: 'https://dashti.se/colophon' }]
})
</script>
