import { describe, it, expect } from 'vitest'
import fs from 'node:fs'
import path from 'node:path'

/**
 * /.well-known/gpc.json states that the site honours Global Privacy Control:
 * a JSON object whose gpc member is true and whose lastUpdate is the date of
 * the statement, an RFC 3339 full-date. The service worker's navigation
 * fallback skips paths that end in a file extension, and no header rule in
 * vercel.json sets this file's Content-Type, so it is served as the JSON its
 * extension names.
 */

const FILE = path.resolve(__dirname, '../../public/.well-known/gpc.json')
const DAY_MS = 24 * 60 * 60 * 1000

const statement = JSON.parse(fs.readFileSync(FILE, 'utf-8')) as Record<string, unknown>

describe('public gpc.json', () => {
  it('holds gpc set to true and a lastUpdate, and nothing else', () => {
    expect(Object.keys(statement).sort()).toEqual(['gpc', 'lastUpdate'])
    expect(statement.gpc).toBe(true)
  })

  it('dates lastUpdate as an RFC 3339 full-date that exists and is at most a day ahead', () => {
    const lastUpdate = statement.lastUpdate
    expect(lastUpdate).toMatch(/^\d{4}-\d{2}-\d{2}$/)
    // The pattern alone admits 2026-02-30, which Date.parse rolls over to a
    // later day, so the date must come back as written.
    const parsed = Date.parse(`${lastUpdate}T00:00:00Z`)
    expect(Number.isNaN(parsed)).toBe(false)
    expect(new Date(parsed).toISOString().slice(0, 10)).toBe(lastUpdate)
    // A date that is already today east of UTC can still be tomorrow in UTC,
    // so the bound is one day ahead of the UTC clock.
    expect(parsed).toBeLessThanOrEqual(Date.now() + DAY_MS)
  })
})
