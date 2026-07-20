import { test, expect } from '@playwright/test'

/**
 * Visual regression tests for portfolio site
 * Run with: npm run test:e2e:visual
 * Update baselines with: npm run test:e2e:visual:update
 *
 * These tests capture baseline screenshots of the UI and compare
 * future runs against them to detect unintended visual changes.
 */

// Helper to wait for page to be stable
async function waitForStableUI(page: import('@playwright/test').Page) {
  await page.waitForLoadState('networkidle')
  // Wait for animations and transitions to complete
  await page.waitForTimeout(500)
}

// ---- Hermetic home-page data ----------------------------------------------
// The home page renders whatever /api/v1/* returns (falling back to static
// markup when fetches fail), and the SSG build bakes ANOTHER copy of
// build-time live data into window.__INITIAL_STATE__. Live data changes
// whenever content is edited, and API reachability differs between the
// local rebaseline container and CI — which made baselines
// environment-dependent (CI rendered the 3-card fallback at 544px against
// a 1513px live-data baseline). Fixtures pin the rendered content
// everywhere. Detail-page tests intentionally do NOT use this: they cover
// the SSG-prerendered pages, whose content is baked at build time.
const FIXTURE_COMPANIES = [
  {
    id: 'fixture-hermes',
    name: 'Hermes Medical Solutions',
    title: 'QA/RA & Security Specialist',
    description:
      'Ensuring NIS2/ISO 27001 compliance, regulatory clearance, and V&V processes for nuclear medicine software solutions.',
    detailed_description: null,
    logo_url: null,
    start_date: '2024-05-01T00:00:00Z',
    end_date: null,
    location: 'Stockholm, Sweden',
    website: 'https://example.com',
    video_url: null,
    video_title: null,
    map_url: null,
    map_title: null,
    technologies: ['ISO 27001', 'NIS2', 'DICOM'],
    responsibilities: ['Regulatory compliance', 'Security assessments'],
    // Primary fixture carries outcomes so the baselines cover the D3-UX-03
    // panel; the other fixtures omit the field to pin the absent state.
    outcomes: [
      'Delivered premarket security documentation for regulatory submissions',
      'Stood up secure development lifecycle processes'
    ],
    order_index: 1
  },
  {
    id: 'fixture-philips',
    name: 'Philips Healthcare',
    title: 'Incident Support Specialist, Nordics',
    description:
      'Level 1 support for Intellispace Portal and Cardiovascular in the Nordics and UK/Ireland, troubleshooting incidents and supporting deployments.',
    detailed_description: null,
    logo_url: null,
    start_date: '2022-03-01T00:00:00Z',
    end_date: '2024-05-01T00:00:00Z',
    location: 'Stockholm, Sweden',
    website: null,
    video_url: null,
    video_title: null,
    map_url: null,
    map_title: null,
    technologies: ['PACS', 'HL7'],
    responsibilities: [],
    order_index: 2
  },
  {
    id: 'fixture-karolinska',
    name: 'Karolinska University Hospital',
    title: 'Biomedical Engineer, Medical Imaging and Physiology',
    description:
      'First-line support for imaging equipment fleet, incident management for RIS/PACS systems, working with GE, Philips, and Siemens solutions.',
    detailed_description: null,
    logo_url: null,
    start_date: '2021-06-01T00:00:00Z',
    end_date: '2021-12-01T00:00:00Z',
    location: 'Stockholm, Sweden',
    website: null,
    video_url: null,
    video_title: null,
    map_url: null,
    map_title: null,
    technologies: [],
    responsibilities: [],
    order_index: 3
  }
]

const FIXTURE_EDUCATION = [
  {
    id: 'fixture-comptia',
    institution: 'CompTIA',
    degree: 'Security+ Certification',
    field_of_study: 'Cybersecurity',
    start_date: '2025-10-01T00:00:00Z',
    end_date: '2026-01-01T00:00:00Z',
    description:
      'Industry-standard certification covering network security, threats, vulnerabilities, and risk management.',
    location: null,
    logo_url: null,
    is_certification: true,
    certificate_number: null,
    certificate_url: 'https://example.com/cert',
    order_index: 1
  },
  {
    id: 'fixture-kth',
    institution: 'KTH Royal Institute of Technology',
    degree: 'M.Sc. Medical Engineering',
    field_of_study: 'Medical Technology and Bioengineering',
    start_date: '2017-08-01T00:00:00Z',
    end_date: '2022-06-01T00:00:00Z',
    description:
      'Specialized in medical imaging, signal processing, and healthcare informatics. Thesis on AI-driven diagnostic systems.',
    location: 'Stockholm, Sweden',
    logo_url: null,
    is_certification: false,
    certificate_number: null,
    certificate_url: null,
    order_index: 2
  },
  {
    id: 'fixture-lund',
    institution: 'Lund University',
    degree: 'B.Sc. Biomedical Engineering (Exchange)',
    field_of_study: 'Biomedical Engineering',
    start_date: '2020-01-01T00:00:00Z',
    end_date: '2021-06-01T00:00:00Z',
    description: 'Exchange program focusing on medical device development and regulatory affairs.',
    location: 'Lund, Sweden',
    logo_url: null,
    is_certification: false,
    certificate_number: null,
    certificate_url: null,
    order_index: 3
  }
]

const FIXTURE_DOCUMENTS = [
  {
    id: 'fixture-thesis-msc',
    title: 'Master Thesis: Improving Quality Assurance of Radiology Equipment',
    description:
      'Research conducted at KTH in collaboration with SoftPro Medical Solutions on QA processes for radiology equipment.',
    document_type: 'thesis',
    file_path: 'documents/fixture-msc.pdf',
    file_size: 3900000,
    file_url: '/media/fixture-msc.pdf',
    published_date: '2020-06-01T00:00:00Z',
    created_at: '2020-06-01T00:00:00Z',
    order_index: 1
  },
  {
    id: 'fixture-thesis-bsc',
    title: 'Bachelor Thesis: Processing Data from Ergonomics Measurements',
    description:
      'Research project on user-friendly data processing methods for ergonomics measurements using inclinometer sensors.',
    document_type: 'thesis',
    file_path: 'documents/fixture-bsc.pdf',
    file_size: 1230000,
    file_url: '/media/fixture-bsc.pdf',
    published_date: '2015-06-01T00:00:00Z',
    created_at: '2015-06-01T00:00:00Z',
    order_index: 2
  }
]

const FIXTURE_GITHUB_STATS = {
  username: 'Dashtid',
  avatar_url: null,
  bio: 'QA/RA & Security Specialist',
  public_repos: 12,
  followers: 5,
  following: 7,
  total_stars: 17,
  total_forks: 3,
  total_watchers: 0,
  top_languages: [
    { name: 'Python', percentage: 69.6 },
    { name: 'PowerShell', percentage: 13 },
    { name: 'TypeScript', percentage: 6.3 },
    { name: 'Vue', percentage: 5.1 }
  ],
  featured_repos: [
    {
      name: 'offensive-toolkit',
      description:
        'Offensive security toolkit for authorized penetration testing and defensive research.',
      html_url: 'https://github.com/Dashtid/offensive-toolkit',
      language: 'Python',
      stars: 12,
      forks: 3
    },
    {
      name: 'sysadmin-toolkit',
      description: 'Automation scripts for Windows and Linux system administration.',
      html_url: 'https://github.com/Dashtid/sysadmin-toolkit',
      language: 'PowerShell',
      stars: 5,
      forks: 0
    },
    {
      name: 'portfolio-site',
      description: 'This site: Vue 3 + FastAPI portfolio with CI/CD on Fly.io and Vercel.',
      html_url: 'https://github.com/Dashtid/portfolio-site',
      language: 'Vue',
      stars: 0,
      forks: 0
    }
  ]
}

// Registered LAST-wins in Playwright: the catch-all abort goes first so
// any unmocked /api/v1/* call fails fast (no NetworkFirst timeouts), then
// the fixture fulfillments take precedence for the known endpoints.
function useHermeticHome() {
  test.beforeEach(async ({ page }) => {
    await page.addInitScript(() => {
      // Ignore the SSG-baked hydration payload — it embeds build-time
      // live data that varies between environments and over time.
      Object.defineProperty(window, '__INITIAL_STATE__', {
        get: () => undefined,
        set: () => {
          /* discard the SSG payload */
        }
      })
      // Wipe the prerendered DOM too: it embeds the same build-time data,
      // and with vite-ssg hydration enabled the app would try to hydrate
      // it against a client render built from the fixtures below — a
      // structural mismatch that can crash Vue's recovery ("null
      // nextSibling") into the ErrorBoundary. An empty #app makes Vue
      // fall back to a clean client mount, which is exactly what these
      // hermetic baselines capture. readystatechange(interactive) fires
      // after parsing but BEFORE deferred module scripts execute, so the
      // wipe always beats the app mount.
      document.addEventListener('readystatechange', () => {
        if (document.readyState === 'interactive') {
          document.getElementById('app')?.replaceChildren()
        }
      })
    })
    await page.route('**/api/v1/**', route => route.abort())
    await page.route('**/api/v1/companies', route => route.fulfill({ json: FIXTURE_COMPANIES }))
    await page.route('**/api/v1/companies/*', route => {
      const id = new URL(route.request().url()).pathname.split('/').pop()
      const company = FIXTURE_COMPANIES.find(c => c.id === id)
      if (company) return route.fulfill({ json: company })
      return route.fulfill({ status: 404, json: { detail: 'Company not found' } })
    })
    await page.route('**/api/v1/education', route => route.fulfill({ json: FIXTURE_EDUCATION }))
    await page.route('**/api/v1/documents', route => route.fulfill({ json: FIXTURE_DOCUMENTS }))
    await page.route('**/api/v1/skills', route => route.fulfill({ json: [] }))
    await page.route('**/api/v1/projects', route => route.fulfill({ json: [] }))
    await page.route('**/api/v1/github/stats/*', route =>
      route.fulfill({ json: FIXTURE_GITHUB_STATS })
    )
    await page.route('**/api/v1/analytics/**', route => route.fulfill({ json: { status: 'ok' } }))
  })
}

test.describe('Visual Regression Tests', () => {
  test.describe('Home Page Sections', () => {
    useHermeticHome()

    test('hero section - light mode', async ({ page }) => {
      await page.goto('/')
      await waitForStableUI(page)
      await expect(page.locator('#hero')).toHaveScreenshot('hero-light.png')
    })

    test('hero section - dark mode', async ({ page }) => {
      await page.goto('/')
      await waitForStableUI(page)
      // Toggle to dark mode
      const themeToggle = page.locator('[data-testid="theme-toggle"]')
      if (await themeToggle.isVisible()) {
        await themeToggle.click()
        await page.waitForTimeout(300)
      }
      await expect(page.locator('#hero')).toHaveScreenshot('hero-dark.png')
    })

    test('experience section', async ({ page }) => {
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      await page.locator('#experience').scrollIntoViewIfNeeded()
      // Wait for scroll animations
      await page.waitForTimeout(800)
      await expect(page.locator('#experience')).toHaveScreenshot('experience.png')
    })

    test('education section', async ({ page }) => {
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      await page.locator('#education').scrollIntoViewIfNeeded()
      await page.waitForTimeout(800)
      await expect(page.locator('#education')).toHaveScreenshot('education.png')
    })

    test('projects section', async ({ page }) => {
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      await page.locator('#projects').scrollIntoViewIfNeeded()
      await page.waitForTimeout(800)
      await expect(page.locator('#projects')).toHaveScreenshot('projects.png')
    })

    test('about section', async ({ page }) => {
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      await page.locator('#about').scrollIntoViewIfNeeded()
      await page.waitForTimeout(800)
      await expect(page.locator('#about')).toHaveScreenshot('about.png')
    })

    test('footer section', async ({ page }) => {
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight))
      await page.waitForTimeout(500)
      await expect(page.locator('footer')).toHaveScreenshot('footer.png')
    })
  })

  test.describe('Responsive Breakpoints', () => {
    useHermeticHome()

    test('mobile viewport (375px)', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 })
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      await page.waitForTimeout(500)
      await expect(page).toHaveScreenshot('home-mobile.png', { fullPage: true })
    })

    test('tablet viewport (768px)', async ({ page }) => {
      await page.setViewportSize({ width: 768, height: 1024 })
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      await page.waitForTimeout(500)
      await expect(page).toHaveScreenshot('home-tablet.png', { fullPage: true })
    })

    test('desktop viewport (1920px)', async ({ page }) => {
      await page.setViewportSize({ width: 1920, height: 1080 })
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      await page.waitForTimeout(500)
      await expect(page).toHaveScreenshot('home-desktop.png', { fullPage: true })
    })
  })

  test.describe('Component States', () => {
    useHermeticHome()

    test('navigation bar', async ({ page }) => {
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      await expect(page.locator('nav.navbar-custom')).toHaveScreenshot('nav-default.png')
    })

    test('navigation bar - scrolled', async ({ page }) => {
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      // Scroll down to trigger navbar style change
      await page.evaluate(() => window.scrollTo(0, 200))
      await page.waitForTimeout(300)
      await expect(page.locator('nav.navbar-custom')).toHaveScreenshot('nav-scrolled.png')
    })

    test('theme toggle states', async ({ page }) => {
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      const themeToggle = page.locator('[data-testid="theme-toggle"]')
      if (await themeToggle.isVisible()) {
        await expect(themeToggle).toHaveScreenshot('theme-toggle-light.png')
        await themeToggle.click()
        await page.waitForTimeout(300)
        await expect(themeToggle).toHaveScreenshot('theme-toggle-dark.png')
      }
    })
  })

  test.describe('Interactive Elements', () => {
    useHermeticHome()

    test('experience card hover state', async ({ page }) => {
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      await page.locator('#experience').scrollIntoViewIfNeeded()
      await page.waitForTimeout(800)

      const card = page.locator('.experience-card').first()
      await card.waitFor({ state: 'visible' })
      await card.hover()
      await page.waitForTimeout(300)
      await expect(card).toHaveScreenshot('experience-card-hover.png')
    })

    test('project card hover state', async ({ page }) => {
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      await page.locator('#projects').scrollIntoViewIfNeeded()
      await page.waitForTimeout(800)

      const card = page.locator('.project-card').first()
      await card.waitFor({ state: 'visible' })
      await card.hover()
      await page.waitForTimeout(300)
      await expect(card).toHaveScreenshot('project-card-hover.png')
    })
  })

  test.describe('Detail Pages', () => {
    useHermeticHome()

    // Fixture IDs resolve through the SPA fallback + the mocked
    // /companies/:id endpoint — fully hermetic, unlike the previous
    // live-API IDs whose SSG-baked content changed with every content
    // edit and whose real network calls timed out on networkidle in CI.
    const primaryId = 'fixture-hermes'
    const secondaryId = 'fixture-philips'

    // Skip entrance animations — useIntersectionAnimation jumps elements
    // straight to visible under prefers-reduced-motion. Without this the
    // screenshots race the staggered reveal transitions and flake.
    test.beforeEach(async ({ page }) => {
      await page.emulateMedia({ reducedMotion: 'reduce' })
    })

    test('experience detail page - primary', async ({ page }) => {
      await page.goto(`/experience/${primaryId}`)
      await waitForStableUI(page)
      await expect(page).toHaveScreenshot('experience-detail-primary.png', { fullPage: true })
    })

    test('experience detail page - secondary', async ({ page }) => {
      await page.goto(`/experience/${secondaryId}`)
      await waitForStableUI(page)
      await expect(page).toHaveScreenshot('experience-detail-secondary.png', { fullPage: true })
    })

    test('experience detail page - mobile viewport', async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 667 })
      await page.goto(`/experience/${primaryId}`)
      await waitForStableUI(page)
      await expect(page).toHaveScreenshot('experience-detail-mobile.png', { fullPage: true })
    })

    test('experience detail page - dark mode', async ({ page }) => {
      await page.goto(`/experience/${primaryId}`)
      await waitForStableUI(page)
      const themeToggle = page.locator('[data-testid="theme-toggle"]')
      if (await themeToggle.isVisible()) {
        await themeToggle.click()
        await page.waitForTimeout(300)
      }
      await expect(page).toHaveScreenshot('experience-detail-dark.png', { fullPage: true })
    })
  })

  // Functional (non-snapshot) guard: the ONLY test that exercises the real
  // IntersectionObserver reveal on the detail page. Every other detail test
  // emulates reduced motion, which makes useIntersectionAnimation jump
  // straight to visible without ever constructing an observer — so a broken
  // observer path (selector typo, threshold change, [data-anim] CSS drift)
  // would blank the page for default-motion visitors while all suites
  // stayed green. Asserts the data-anim attribute (not toBeVisible():
  // Playwright treats opacity:0 as visible).
  test.describe('Detail Page Reveal', () => {
    useHermeticHome()

    test('entrance animation reveals sections without reduced motion', async ({ page }) => {
      await page.goto('/experience/fixture-hermes')
      await page.waitForSelector('[data-anim]', { state: 'attached' })

      // Above-the-fold header section reveals on its own
      await expect(page.locator('header.experience-section')).toHaveAttribute(
        'data-anim',
        'visible'
      )

      // A below-the-fold section reveals once scrolled into view
      const lastSection = page.locator('section.experience-section').last()
      await lastSection.scrollIntoViewIfNeeded()
      await expect(lastSection).toHaveAttribute('data-anim', 'visible')
    })
  })

  test.describe('Error States', () => {
    useHermeticHome()

    test('404 page - invalid experience', async ({ page }) => {
      await page.goto('/experience/nonexistent-company')
      await waitForStableUI(page)
      // Capture whatever error/not found state is displayed
      await expect(page).toHaveScreenshot('experience-not-found.png', { fullPage: true })
    })
  })

  test.describe('Print Styles', () => {
    useHermeticHome()

    test('home page print view', async ({ page }) => {
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      await page.emulateMedia({ media: 'print' })
      await page.waitForTimeout(300)
      await expect(page).toHaveScreenshot('home-print.png', { fullPage: true })
    })
  })

  test.describe('Reduced Motion', () => {
    useHermeticHome()

    test('home page with reduced motion', async ({ page }) => {
      await page.emulateMedia({ reducedMotion: 'reduce' })
      await page.goto('/')
      await page.waitForLoadState('networkidle')
      await page.waitForTimeout(300)
      await expect(page).toHaveScreenshot('home-reduced-motion.png', { fullPage: true })
    })
  })
})
