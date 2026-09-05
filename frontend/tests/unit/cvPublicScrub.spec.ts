import { describe, it, expect } from 'vitest'
import { execFileSync } from 'node:child_process'
import fs from 'node:fs'
import path from 'node:path'

/**
 * cv/ sits in a PUBLIC repo but is fed from PII-carrying local files
 * (cv/source/, cv/exports/ — phone, personal email, photo). The split is
 * deliberate: those two directories are git-ignored and have never been
 * committed, while resume.json is the scrubbed public JSON Resume record.
 *
 * These tests are the tree-scanning tripwire the repo's own
 * committed-something-sensitive policy requires: resume.json's history
 * already carried a personal email once (added d45da5f, removed 56f37bb,
 * fixed forward per policy). A correct .gitignore and a clean working
 * copy are different claims from a clean COMMITTED tree — so this scans
 * what git actually tracks, not what the ignore file promises.
 * ci-cd.yml's `changes` filter includes cv/** for the same reason: a
 * commit touching only cv/ must still run this suite.
 */

const REPO_ROOT = path.resolve(__dirname, '../../..')
const CV_DIR = path.join(REPO_ROOT, 'cv')

// The complete allowed public surface of cv/. Adding ANY new tracked file
// under cv/ must be a deliberate act that updates this list.
const ALLOWED_TRACKED = ['cv/.gitignore', 'cv/README.md', 'cv/resume.json']

const trackedUnderCv = (): string[] =>
  execFileSync('git', ['ls-files', 'cv/'], { cwd: REPO_ROOT, encoding: 'utf-8' })
    .split('\n')
    .map(l => l.trim())
    .filter(Boolean)

// Collect every string value in a JSON tree, with its object path for
// readable failure output.
const stringValues = (node: unknown, at = '$'): Array<{ at: string; value: string }> => {
  if (typeof node === 'string') return [{ at, value: node }]
  if (Array.isArray(node)) return node.flatMap((v, i) => stringValues(v, `${at}[${i}]`))
  if (node && typeof node === 'object') {
    return Object.entries(node).flatMap(([k, v]) => stringValues(v, `${at}.${k}`))
  }
  return []
}

describe('cv/ public-repo scrub guard', () => {
  it('tracks exactly the three scrubbed files — source/ and exports/ stay out of git', () => {
    expect(trackedUnderCv().sort()).toEqual([...ALLOWED_TRACKED].sort())
  })

  it('resume.json keeps contact channels empty (site is the CV; contact is LinkedIn-only)', () => {
    const resume = JSON.parse(fs.readFileSync(path.join(CV_DIR, 'resume.json'), 'utf-8'))
    expect(resume.basics.email).toBe('')
    expect(resume.basics.phone).toBe('')
  })

  it('no string in resume.json smells like an email, phone number or personnummer', () => {
    const resume = JSON.parse(fs.readFileSync(path.join(CV_DIR, 'resume.json'), 'utf-8'))
    const pii = [
      /\S+@\S+\.\S+/, // email
      /\+\d[\d\s-]{7,}/, // international phone
      /\b\d{6}[-+]\d{4}\b/ // personnummer
    ]
    const hits = stringValues(resume).filter(({ value }) => pii.some(re => re.test(value)))
    expect(hits, JSON.stringify(hits, null, 2)).toEqual([])
  })

  it("cv/.gitignore still declares the PII directories, so the tripwire's belt keeps its braces", () => {
    const ignore = fs.readFileSync(path.join(CV_DIR, '.gitignore'), 'utf-8')
    expect(ignore).toMatch(/^source\/$/m)
    expect(ignore).toMatch(/^exports\/$/m)
  })
})
