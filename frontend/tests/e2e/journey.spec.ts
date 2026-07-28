import { test, expect } from '@playwright/test'
import { HomePage } from './pages'

/**
 * Recruiter conversion path: home -> experience card -> detail -> back.
 *
 * This is the e2e guard for the "client app never boots / router dead"
 * class of regression. The catch: without a working client app a card
 * click still "works" — the stretched router-link is a real <a href>, and
 * the target page is SSG-prerendered, so a full-page load lands on the
 * right URL and every content assertion passes. The window marker below
 * is what tells the two apart: it survives SPA navigation and dies with a
 * full reload. (The subtler mount-vs-HYDRATE regression — losing
 * vite-ssg's `hydration: true` and flash-remounting over the prerendered
 * DOM — keeps the app fully working and is guarded separately by
 * home.spec.ts "Hydration", which tags a prerendered node and asserts the
 * client adopts it.)
 */

// The detail fetch is mocked (echoing whatever id was clicked) so that
// leg is hermetic. The HOME leg is deliberately NOT: hydration has to
// adopt the real baked SSG payload, so the test inherits the dist's
// bake quality. A bake that shipped companies empty renders the static
// fallback cards — same .experience-card class, but no router-link —
// which is why the click is preceded by a link precondition: failing
// there says "empty bake", not "router regression".
const fixtureCompany = (id: string) => ({
  id,
  name: 'E2E Fixture Company',
  title: 'E2E Fixture Role',
  description: 'Deterministic detail-page content for the journey test.',
  detailed_description: null,
  logo_url: null,
  start_date: '2024-01-01T00:00:00Z',
  end_date: null,
  location: 'Stockholm, Sweden',
  website: null,
  video_url: null,
  video_title: null,
  map_url: null,
  map_title: null,
  technologies: ['E2E'],
  responsibilities: [],
  outcomes: [],
  order_index: 1
})

test.describe('Experience Journey', () => {
  test('card click navigates client-side to detail and back', async ({ page }) => {
    await page.route('**/api/v1/companies/*', route => {
      const id = new URL(route.request().url()).pathname.split('/').pop() ?? ''
      return route.fulfill({ json: fixtureCompany(id) })
    })

    const homePage = new HomePage(page)
    await homePage.goto()

    // Wait for the client app to be up ([data-anim] is applied in
    // onMounted), THEN plant the marker — planting earlier proves nothing.
    await page.locator('[data-anim]').first().waitFor({ state: 'attached' })
    await page.evaluate(() => {
      ;(window as unknown as { __spaJourney?: boolean }).__spaJourney = true
    })

    // Precondition (see the mock note above): a dynamic card carries the
    // stretched detail link; the empty-bake static fallback does not.
    await expect(homePage.experienceCards.first().locator('a[href^="/experience/"]')).toBeAttached()

    await homePage.clickExperienceCard(0)
    await page.waitForURL(/\/experience\/[^/]+$/)

    // SPA navigation keeps the JS context; a boot failure downgrades the
    // click to a full page load and wipes the marker.
    expect(
      await page.evaluate(() => (window as unknown as { __spaJourney?: boolean }).__spaJourney)
    ).toBe(true)

    // Detail rendered from the mocked fetch — the SPA data path, not the
    // prerendered fallback HTML.
    await expect(page.locator('h1')).toHaveText('E2E Fixture Role')

    await page.goBack()
    await page.waitForURL(url => new URL(url).pathname === '/')
    // The URL flip (and marker survival) are browser-guaranteed on a
    // same-document traversal even with a dead popstate handler — only
    // home-specific content proves the router actually swapped the view.
    await expect(page.locator('#hero')).toBeVisible()
    await expect(page.locator('h1')).not.toHaveText('E2E Fixture Role')
  })
})
