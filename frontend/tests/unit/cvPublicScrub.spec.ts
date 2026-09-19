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

/**
 * Tree-wide banned-term guard.
 *
 * The suite above scans cv/ for PII only. A scrubber that inspects one
 * directory and a clean COMMITTED tree are different claims, so this guard
 * scans every tracked text file instead.
 *
 * Two rules, and they are deliberately different shapes:
 *
 * 1. The dynamic-testing technique name is zero-match anywhere in the tree,
 *    once the one repository identifier below has been masked out of each line.
 * 2. The imaging protocol may never share a line with a weakness class. That
 *    one is an ADJACENCY gate, not zero-match, because the bare protocol name
 *    is a load-bearing medtech ATS keyword that is deliberately KEPT (the
 *    resume.json skills list, the seed_data.py skills taxonomy, earlier role
 *    descriptions). A literal zero-match rule there would either fail forever
 *    or get "fixed" by deleting a keyword worth keeping.
 *
 * Tokens are assembled from fragments so this guard never matches itself, and
 * so that the file stating the rule does not publish the terms it bans.
 */
const PROTOCOL = 'DI' + 'COM'
const TECHNIQUE = 'fu' + 'zz'
// One repository identifier happens to contain both tokens. It is an
// identifier, not CV copy, so it is masked out of every line before testing:
// an off-portfolio allowlist that has to name it must not trip the pair test.
const REPO_IDENTIFIER = `${PROTOCOL.toLowerCase()}-${TECHNIQUE}er`

// A line naming the protocol AND any of these is the banned pair.
const WEAKNESS_TERMS = [TECHNIQUE, 'vulnerab', 'exploit', 'attack surface', 'pentest']

const SKIP_EXT = new Set([
  '.png',
  '.jpg',
  '.jpeg',
  '.gif',
  '.webp',
  '.avif',
  '.ico',
  '.svg',
  '.pdf',
  '.woff',
  '.woff2',
  '.ttf',
  '.eot',
  '.zip',
  '.gz',
  '.lock'
])

const trackedTextFiles = (): string[] =>
  execFileSync('git', ['ls-files'], {
    cwd: REPO_ROOT,
    encoding: 'utf-8',
    maxBuffer: 32 * 1024 * 1024
  })
    .split('\n')
    .map(l => l.trim())
    .filter(Boolean)
    .filter(f => !SKIP_EXT.has(path.extname(f).toLowerCase()))

/** Every tracked line, with the tool repo's name masked out. */
const scanLines = (): Array<{ file: string; line: number; text: string }> => {
  const out: Array<{ file: string; line: number; text: string }> = []
  for (const file of trackedTextFiles()) {
    const abs = path.join(REPO_ROOT, file)
    let raw: string
    try {
      raw = fs.readFileSync(abs, 'utf-8')
    } catch {
      continue // unreadable or deleted-but-tracked; not this guard's business
    }
    if (raw.includes('\u0000')) continue // binary
    raw.split('\n').forEach((text, i) => {
      const masked = text.replaceAll(new RegExp(REPO_IDENTIFIER, 'gi'), '')
      out.push({ file, line: i + 1, text: masked })
    })
  }
  return out
}

describe('tracked-tree banned-term guard', () => {
  it('names the dynamic-testing technique nowhere in the tracked tree', () => {
    const hits = scanLines()
      .filter(({ text }) => text.toLowerCase().includes(TECHNIQUE))
      .map(({ file, line, text }) => `${file}:${line}: ${text.trim().slice(0, 160)}`)
    expect(hits, `Technique name found in tracked files:\n${hits.join('\n')}`).toEqual([])
  })

  it('never puts the imaging protocol on the same line as a weakness class', () => {
    const hits = scanLines()
      .filter(({ text }) => {
        const lower = text.toLowerCase()
        if (!lower.includes(PROTOCOL.toLowerCase())) return false
        return WEAKNESS_TERMS.some(term => lower.includes(term))
      })
      .map(({ file, line, text }) => `${file}:${line}: ${text.trim().slice(0, 160)}`)
    expect(hits, `Banned pair found in tracked files:\n${hits.join('\n')}`).toEqual([])
  })

  it('keeps the bare protocol name, which is a load-bearing medtech keyword', () => {
    // Asserts the gate is adjacency and not zero-match. If this ever fails,
    // someone "fixed" the guard above by deleting a keyword worth keeping.
    const resume = JSON.parse(fs.readFileSync(path.join(CV_DIR, 'resume.json'), 'utf-8'))
    const keywords = (resume.skills as Array<{ keywords?: string[] }>).flatMap(
      s => s.keywords ?? []
    )
    expect(keywords).toContain(PROTOCOL)
  })
})
