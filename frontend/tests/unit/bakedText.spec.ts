import { describe, it, expect } from 'vitest'
import fs from 'node:fs'
import path from 'node:path'
import { pathToFileURL } from 'node:url'
import { STATE_BLOCK, bakedTexts, jsonStrings } from '../../scripts/bakedText.mjs'
import { EXCLUDED_REPO_DIGESTS, digest, findTerms } from '../../scripts/hashedTerms.mjs'

/**
 * scripts/bakedText.mjs decodes a baked page's JSON blocks for the content
 * checks in scripts/verify-dist-invariants.mjs. The state blocks below are
 * written by vite-ssg's own serializeState and wrapped the way the onFinished
 * hook in vite.config.ts wraps them. A synthetic name is added to a copy of
 * EXCLUDED_REPO_DIGESTS to show what the decoded strings expose that the raw
 * page hides.
 */

const VITE_SSG_SHARED = path.resolve(__dirname, '../../node_modules/vite-ssg/dist/shared')

type Serialize = (state: unknown) => string

const loadSerializeState = async (): Promise<Serialize> => {
  for (const file of fs.readdirSync(VITE_SSG_SHARED)) {
    const full = path.join(VITE_SSG_SHARED, file)
    if (!fs.readFileSync(full, 'utf-8').includes('function serializeState(')) continue
    const mod = (await import(pathToFileURL(full).href)) as Record<string, unknown>
    const found = Object.values(mod).find(
      value => typeof value === 'function' && value.name === 'serializeState'
    )
    if (found) return found as Serialize
  }
  throw new Error(`no serializeState export in ${VITE_SSG_SHARED}`)
}

const SYNTHETIC = 'example-tool'
const digests = new Set([...EXCLUDED_REPO_DIGESTS, digest(SYNTHETIC)])

const statePage = (serialized: string): string =>
  '<!DOCTYPE html><html><head></head><body><div id="app"></div>' +
  `<script type="application/json" id="__INITIAL_STATE__">${serialized}</script></body></html>`

const found = (texts: string[]): string[] =>
  [...new Set(texts.flatMap(text => findTerms(text, digests)))].sort()

describe('bakedTexts on a state block written by serializeState', () => {
  it('finds a name in a URL, which the raw page hides behind an escaped slash', async () => {
    const serializeState = await loadSerializeState()
    const html = statePage(
      serializeState({
        pinia: {
          portfolio: { projects: [{ github_url: `https://github.com/Dashtid/${SYNTHETIC}` }] }
        }
      })
    )
    expect(findTerms(html, digests)).toEqual([])
    const baked = bakedTexts(html)
    expect(baked.state).toBe(true)
    expect(found(baked.texts)).toEqual([SYNTHETIC])
  })

  it('finds a name after a newline, which the raw page glues to the escape', async () => {
    const serializeState = await loadSerializeState()
    const html = statePage(
      serializeState({
        pinia: { portfolio: { companies: [{ description: `One.\n${SYNTHETIC}` }] } }
      })
    )
    expect(findTerms(html, digests)).toEqual([])
    expect(found(bakedTexts(html).texts)).toEqual([SYNTHETIC])
  })

  it('lets a substring with a slash match inside the state', async () => {
    const serializeState = await loadSerializeState()
    const html = statePage(serializeState({ pinia: { note: 'Mapped to alpha/beta.' } }))
    expect(html).not.toContain('alpha/beta')
    expect(bakedTexts(html).texts.some(text => text.includes('alpha/beta'))).toBe(true)
  })

  it('reads the block with the pattern vite.config.ts writes', async () => {
    const serializeState = await loadSerializeState()
    const html = statePage(serializeState({ pinia: {} }))
    expect(STATE_BLOCK.exec(html)).not.toBeNull()
  })
})

describe('bakedTexts on JSON-LD blocks', () => {
  it('finds a name after an escaped newline and counts the block', () => {
    const block = JSON.stringify({ '@type': 'Thing', description: `One.\n${SYNTHETIC}` })
    const html = `<head><script type="application/ld+json">${block}</script></head>`
    expect(findTerms(html, digests)).toEqual([])
    const baked = bakedTexts(html)
    expect(baked.ldJson).toBe(1)
    expect(found(baked.texts)).toEqual([SYNTHETIC])
  })
})

describe('bakedTexts on other pages', () => {
  it('returns the raw page alone when the page has no JSON blocks', () => {
    const html = '<p>static</p>'
    expect(bakedTexts(html)).toEqual({ texts: [html], state: false, ldJson: 0 })
  })

  it('throws on a state block in another form', () => {
    const html = '<script type="application/json" id="__INITIAL_STATE__">{}</script>'
    expect(() => bakedTexts(html)).toThrow(/not in the form/)
  })

  it('throws on a JSON-LD block that does not parse', () => {
    const html = '<script type="application/ld+json">{"broken": </script>'
    expect(() => bakedTexts(html)).toThrow(SyntaxError)
  })
})

describe('jsonStrings', () => {
  it('collects keys and string values depth first, and skips other values', () => {
    expect(jsonStrings({ a: ['x', 1, { b: 'y' }], c: null, d: true })).toEqual([
      'a',
      'x',
      'b',
      'y',
      'c',
      'd'
    ])
  })
})
