import { describe, it, expect } from 'vitest'
import fs from 'node:fs'
import path from 'node:path'

/**
 * HomeView's static fallback renders whenever an SSG build could not reach
 * the API — a real production state, not a theoretical one (a Vercel build
 * once shipped with education and skills baked empty). It is hand-written
 * markup that duplicates database content, so it drifts silently: nobody
 * sees it in review, and the pages that DO show it are exactly the pages
 * nobody is looking at.
 *
 * It has now drifted twice. In Aug 2026 it carried an invented KTH thesis
 * and demoted Lund to an exchange term. In Sep 2026 it carried LinkedIn-style
 * degree suffixes ("Master of Science - MS") that matched neither the live
 * API nor seed_data. Both were "cosmetic" until you notice the site was
 * publishing a third, contradictory version of the owner's CV.
 *
 * seed_data.py is the committed representation of the database (kept in
 * sync with it, and itself asserted by backend tests), so it is the
 * checkable proxy here: every hard-coded fallback value must appear in it
 * VERBATIM. This test does not care how many fallback cards exist — it
 * cares that no fallback card invents a fact.
 */

const REPO_ROOT = path.resolve(__dirname, '../../../..')
const HOME_VIEW = path.join(REPO_ROOT, 'frontend/src/views/HomeView.vue')
const SEED_DATA = path.join(REPO_ROOT, 'backend/app/seed_data.py')

const home = fs.readFileSync(HOME_VIEW, 'utf-8')
const seed = fs.readFileSync(SEED_DATA, 'utf-8')

/** Text content of every element carrying `cls`, excluding Vue-interpolated ones. */
const staticTextsFor = (cls: string): string[] =>
  [...home.matchAll(new RegExp(`class="${cls}[^"]*"[^>]*>([\\s\\S]*?)</`, 'g'))]
    .map(m =>
      m[1]
        .replace(/<[^>]*>/g, ' ')
        .replace(/\s+/g, ' ')
        .trim()
    )
    .filter(t => t.length > 0 && !t.includes('{{'))
    .map(t =>
      t
        .replace(/&amp;/g, '&')
        .replace(/&ndash;/g, '–')
        .replace(/&middot;/g, '·')
        .replace(/&nbsp;/g, ' ')
    )

/** Values of `key` across seed_data.py's dict literals. */
const seedValues = (key: string): string[] =>
  [...seed.matchAll(new RegExp(`"${key}":\\s*"([^"]*)"`, 'g'))].map(m => m[1])

describe('HomeView static fallback parity with seed_data', () => {
  it('every fallback degree exists verbatim in seed_data', () => {
    const degrees = staticTextsFor('education-degree')
    expect(degrees.length).toBeGreaterThan(0)
    expect(seedValues('degree')).toEqual(expect.arrayContaining(degrees))
  })

  it('every fallback field of study exists verbatim in seed_data', () => {
    const fields = staticTextsFor('education-field')
    expect(fields.length).toBeGreaterThan(0)
    expect(seedValues('field_of_study')).toEqual(expect.arrayContaining(fields))
  })

  it('every fallback institution exists verbatim in seed_data', () => {
    const institutions = staticTextsFor('education-institution')
    expect(institutions.length).toBeGreaterThan(0)
    expect(seedValues('institution')).toEqual(expect.arrayContaining(institutions))
  })

  it('every fallback job title exists verbatim in seed_data', () => {
    const titles = staticTextsFor('job-title')
    expect(titles.length).toBeGreaterThan(0)
    expect(seedValues('title')).toEqual(expect.arrayContaining(titles))
  })

  it('every fallback company name exists verbatim in seed_data', () => {
    const names = staticTextsFor('company-name')
    expect(names.length).toBeGreaterThan(0)
    expect(seedValues('name')).toEqual(expect.arrayContaining(names))
  })

  it('no fallback card claims a credential seed_data does not list', () => {
    // The fabricated-certification class of bug (CEH / AZ-500 / ISO 27001-LI,
    // removed 2026-07-22) hid in BOTH seed_data and this fallback. Security+
    // is the only earned certification; anything else appearing here must be
    // labelled a course, and must exist in seed_data either way.
    const degrees = staticTextsFor('education-degree')
    const certLike = degrees.filter(d => !/^(Master|Bachelor) of Science$/.test(d))
    for (const cert of certLike) {
      expect(seedValues('degree')).toContain(cert)
    }
  })
})
