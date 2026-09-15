import { describe, it, expect } from 'vitest'
import fs from 'node:fs'
import path from 'node:path'

/**
 * Chrome draws its own print header (the date and the page <title>) and footer
 * (URL and "1/2") INSIDE the page margins, and only when the margin is large
 * enough to hold them. That is not styleable: no @media print rule can remove
 * text the browser paints outside the document. The only lever is to leave it
 * nowhere to draw.
 *
 * Measured 2026-09-15 against Chromium's real printToPDF path (the same code
 * the print dialog uses), printing a two-page document at one-pixel margin
 * steps and diffing the rendered content streams:
 *
 *     top <= 31px  ->  nothing drawn
 *     top >= 32px  ->  header drawn
 *
 * The CV shipped with a 37px top margin, so every export carried a date and
 * "CV Export | David Dashti" stamped across the top, and the only workaround
 * was to remember to untick "Headers and footers" in the dialog every time.
 *
 * This test exists because that margin is an ordinary-looking number that a
 * future layout tweak would raise without a second thought. If it fails, the
 * CV has started stamping headers again — do not "fix" it by raising the
 * limit.
 */

const ADMIN_CV = path.resolve(__dirname, '../../../src/views/admin/AdminCv.vue')

/** Chromium draws the header at 32px and above; 31px is the last clean value. */
const MAX_CLEAN_MARGIN_PX = 31

const source = fs.readFileSync(ADMIN_CV, 'utf-8')

/** The `margin:` shorthand inside the top-level `@page` rule. */
const pageMargin = (): string => {
  const rule = source.match(/@page\s*\{([^}]*)\}/)
  expect(rule, '@page rule not found in AdminCv.vue').toBeTruthy()
  const margin = rule![1].match(/margin:\s*([^;]+);/)
  expect(margin, 'no margin declaration inside @page').toBeTruthy()
  return margin![1].trim()
}

/** CSS shorthand -> { top, bottom } in px. Only px is accepted here. */
const verticalMargins = (shorthand: string): { top: number; bottom: number } => {
  const parts = shorthand.split(/\s+/)
  for (const p of parts) {
    expect(p, `@page margin must be expressed in px, got "${p}"`).toMatch(/^-?\d+(\.\d+)?px$/)
  }
  const px = parts.map(p => parseFloat(p))
  // 1 value: all sides. 2: v/h. 3: top/h/bottom. 4: top/right/bottom/left.
  switch (px.length) {
    case 1:
      return { top: px[0], bottom: px[0] }
    case 2:
      return { top: px[0], bottom: px[0] }
    case 3:
      return { top: px[0], bottom: px[2] }
    case 4:
      return { top: px[0], bottom: px[2] }
    default:
      throw new Error(`unparseable @page margin shorthand: "${shorthand}"`)
  }
}

describe('CV print margins keep Chrome from stamping its own header', () => {
  it('top margin stays at or below the threshold that triggers the header', () => {
    const { top } = verticalMargins(pageMargin())
    expect(
      top,
      `@page top margin is ${top}px. At ${MAX_CLEAN_MARGIN_PX + 1}px and above Chrome ` +
        'stamps the date and page title across every exported CV.'
    ).toBeLessThanOrEqual(MAX_CLEAN_MARGIN_PX)
  })

  it('bottom margin stays below the threshold that triggers the footer', () => {
    const { bottom } = verticalMargins(pageMargin())
    expect(
      bottom,
      `@page bottom margin is ${bottom}px — the URL and page number would be stamped.`
    ).toBeLessThanOrEqual(MAX_CLEAN_MARGIN_PX)
  })

  it('still sets an explicit A4 page size', () => {
    // Without this the export follows the printer's default paper, which is
    // how a US-Letter default silently reflows a CV tuned for A4.
    expect(source).toMatch(/@page\s*\{[^}]*size:\s*A4/)
  })
})
