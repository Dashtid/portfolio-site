import { describe, it, expect } from 'vitest'
import { execFileSync, spawnSync } from 'node:child_process'
import path from 'node:path'

/**
 * The repository is public, and some files written next to a clone hold
 * private data, such as a restored production database or a printed CV. The
 * root .gitignore keeps them out of `git add -A`. These tests ask git itself
 * which paths it ignores, so a rule that stops matching fails here, and scan
 * what git tracks, which also catches a file added past the rules.
 */

const REPO_ROOT = path.resolve(__dirname, '../../..')

// The subset of paths that git's ignore rules exclude (tracked or not).
const ignored = (paths: string[]): string[] =>
  spawnSync('git', ['check-ignore', '--no-index', ...paths], {
    cwd: REPO_ROOT,
    encoding: 'utf-8'
  })
    .stdout.split('\n')
    .map(line => line.trim())
    .filter(Boolean)

// Every path at the repository root and one level down.
const atRootAndBelow = (names: string[]): string[] => [
  ...names,
  ...names.map(name => `backend/${name}`)
]

describe('backup restore outputs', () => {
  it('are ignored wherever the restore runs', () => {
    const paths = atRootAndBelow([
      'portfolio.dump',
      'portfolio-20261124.dump.age',
      'portfolio.sql',
      'uploads.tar.gz',
      'uploads-20261124.tar.gz',
      'uploads-20261124.tar.gz.age',
      'pg-backup-123456.zip',
      'pg-backup-123456/portfolio-20261124.dump.age',
      'uploads-backup-123456/uploads-20261124.tar.gz.age',
      'age-backup-key.txt',
      'key.txt',
      'recipient.txt'
    ])
    expect(ignored(paths).sort()).toEqual([...paths].sort())
  })

  it('leave ordinary source files alone', () => {
    expect(ignored(['backend/app/main.py', 'frontend/src/main.ts', 'README.md'])).toEqual([])
  })
})

// The only documents the site publishes from the repository.
const PUBLISHED_DOCUMENTS = [
  'backend/static/documents/bachelor-thesis.pdf',
  'backend/static/documents/master-thesis.pdf'
]

// Document and archive formats, in any letter case.
const DOCUMENT = /\.(pdf|docx?|odt|ods|odp|rtf|xlsx?|pptx?|pages|zip|7z|rar|tar|tgz|gz)$/i

describe('documents', () => {
  it('are ignored wherever a printed CV might be saved', () => {
    const paths = [
      ...atRootAndBelow(['cv.pdf', 'cv.doc', 'cv.docx', 'cv.odt', 'cv.rtf', 'cv-exports.zip']),
      'cv/cv-export.pdf',
      'backend/static/documents/cv-export.pdf',
      'frontend/public/documents/cv.pdf',
      'docs/cv.docx'
    ]
    expect(ignored(paths).sort()).toEqual([...paths].sort())
  })

  it('leave the two published theses unignored', () => {
    expect(ignored(PUBLISHED_DOCUMENTS)).toEqual([])
  })

  it('are tracked only as the two published theses', () => {
    const tracked = execFileSync('git', ['ls-files'], {
      cwd: REPO_ROOT,
      encoding: 'utf-8',
      maxBuffer: 32 * 1024 * 1024
    })
      .split('\n')
      .map(line => line.trim())
      .filter(file => DOCUMENT.test(file))
    expect(tracked.sort()).toEqual([...PUBLISHED_DOCUMENTS].sort())
  })
})
