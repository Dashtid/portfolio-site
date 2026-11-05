import { describe, it, expect } from 'vitest'
import fs from 'node:fs'
import path from 'node:path'

/**
 * The site's security.txt (RFC 9116) lists only working channels and stays
 * current. The API serves its own copy (SECURITY_TXT_CONTENT in
 * backend/app/main.py), and backend/tests/test_security_txt.py applies the
 * same rules to it, plus two checks of how the API serves it. A renewal
 * changes both Expires lines, and .github/workflows/security-txt-expiry.yml
 * checks both live copies every week.
 */

const FILE = path.resolve(__dirname, '../../public/.well-known/security.txt')
const CANONICAL = 'https://dashti.se/.well-known/security.txt'
const POLICY = 'https://github.com/Dashtid/portfolio-site/blob/main/SECURITY.md'
const PVR = 'https://github.com/Dashtid/portfolio-site/security/advisories/new'
const LINKEDIN = 'https://www.linkedin.com/in/david-dashti/'
const DAY_MS = 24 * 60 * 60 * 1000
// RFC 9116 section 2.5.5 recommends an Expires less than a year ahead. No
// calendar year is shorter than 365 days, so under 365 days is always under a
// year. The 30-day margin turns CI red before the file goes stale, not after.
const RENEW_MARGIN_MS = 30 * DAY_MS
const MAX_AHEAD_MS = 365 * DAY_MS
// The date-time of RFC 3339 section 5.6, which section 2.5.5 requires, with an
// upper-case T and Z only. RFC 3339 also allows a lower-case t and z, but
// fromisoformat in the backend rejects the z that Date.parse here accepts.
const RFC3339 = /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$/
// An offset's hours run 00-23 and its minutes 00-59 (RFC 3339 section 5.6).
const OFFSET = /^(Z|[+-]([01]\d|2[0-3]):[0-5]\d)$/
// A field is a name, a colon, one space and a non-empty value (the ABNF's
// "fs SP"). The name is RFC 5322's field-name: visible ASCII except the colon.
const FIELD = /^[!-9;-~]+: \S.*$/
// The email and phone shapes of cvPublicScrub.spec.ts, global to list every hit.
const EMAIL = /\S+@\S+\.\S+/g
const PHONE = /\+\d[\d\s-]{7,}/g

const text = fs.readFileSync(FILE, 'utf-8')
const lines = text.split(/\r?\n/)
// Field names are case-insensitive (RFC 9116 section 2); "#" starts a comment.
const fields = (name: string): string[] =>
  lines
    .filter(line => !line.startsWith('#') && line.includes(':'))
    .filter(line => line.slice(0, line.indexOf(':')).trim().toLowerCase() === name.toLowerCase())
    .map(line => line.slice(line.indexOf(':') + 1).trim())

describe('public security.txt', () => {
  it('has only blank lines, comments and well-formed fields', () => {
    const malformed = lines.filter(
      line => line.trim() !== '' && !line.startsWith('#') && !FIELD.test(line)
    )
    expect(malformed).toEqual([])
  })

  it('ends every line with LF or CRLF, the last one included', () => {
    // RFC 9116 section 2.2. A carriage return is allowed only before a line feed.
    expect(text.endsWith('\n')).toBe(true)
    expect(text.match(/\r(?!\n)/g) ?? []).toEqual([])
  })

  it('lists the working channels only, GitHub private vulnerability reporting first', () => {
    // A dashti.se mailbox bounced for as long as one was listed: the domain has
    // no MX record. The channels are SECURITY.md's preferred one and its
    // LinkedIn alternative.
    expect(fields('Contact')).toEqual([PVR, LINKEDIN])
  })

  it('has no mailto: or tel: and nothing shaped like an email or phone, comments included', () => {
    expect(text.match(/mailto:|tel:/gi) ?? []).toEqual([])
    expect(text.match(EMAIL) ?? []).toEqual([])
    expect(text.match(PHONE) ?? []).toEqual([])
  })

  it('names its own canonical URL and SECURITY.md as the policy', () => {
    expect(fields('Canonical')).toEqual([CANONICAL])
    expect(fields('Policy')).toEqual([POLICY])
  })

  it('sets Preferred-Languages at most once', () => {
    // RFC 9116 section 2.5.8: the field MUST NOT appear more than once.
    expect(fields('Preferred-Languages').length).toBeLessThanOrEqual(1)
  })

  it('sets Expires once, as RFC 3339, more than 30 and under 365 days ahead', () => {
    const values = fields('Expires')
    expect(values).toHaveLength(1)
    const expires = values[0]
    const notRfc3339 = `Expires ${expires} is not an RFC 3339 date-time (upper-case T and Z)`
    expect(expires, notRfc3339).toMatch(RFC3339)
    // The pattern alone admits 2027-02-30, T24:00:00 and offsets such as +24:00
    // and +01:60, none of which RFC 3339 allows (sections 5.6 and 5.7: hours
    // 00-23, minutes 00-59, days up to the month's last). Date.parse rolls the
    // first two over to a later day and gives NaN for the offsets. So the offset
    // must be in range, and the date and time, read as UTC, must come back as
    // written. That also refuses a leap second's :60, which RFC 3339 allows; no
    // plausible Expires uses one.
    const zone = RFC3339.exec(expires)?.[2] ?? ''
    const asWritten = Date.parse(`${expires.slice(0, 19)}Z`)
    const real =
      OFFSET.test(zone) &&
      !Number.isNaN(asWritten) &&
      new Date(asWritten).toISOString().slice(0, 19) === expires.slice(0, 19)
    expect(real, `Expires ${expires} is not an RFC 3339 date-time: no such date or time`).toBe(true)
    const ahead = Date.parse(expires) - Date.now()
    expect(
      ahead,
      `Expires ${expires} leaves 30 days or less: renew it in frontend/public/.well-known/security.txt and in backend/app/main.py (SECURITY_TXT_CONTENT)`
    ).toBeGreaterThan(RENEW_MARGIN_MS)
    expect(
      ahead,
      `Expires ${expires} is 365 days or more ahead; RFC 9116 section 2.5.5 recommends less than a year`
    ).toBeLessThan(MAX_AHEAD_MS)
  })
})
