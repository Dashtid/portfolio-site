/**
 * Match text against SHA-256 digests of lowercased terms, so a term list can
 * be checked against text without the terms being readable in this
 * repository.
 *
 * candidates() lowercases the text, collapses every run of whitespace to one
 * space and splits it into words (runs of a-z and 0-9). Every run of 1 to
 * MAX_WORDS consecutive words joined only by `.`, `_`, `/`, `-` or a space is
 * a candidate, with its separators kept as written. A term is therefore found
 * on its own, inside a longer hyphenated or dotted token, after an `owner/`
 * prefix and before a `.git` suffix, but not inside a longer word.
 *
 * backend/tests/hashed_terms.py runs the same algorithm and carries the same
 * EXCLUDED_REPO_DIGESTS and OTHER_REPO_DIGESTS; tests/unit/hashedTerms.spec.ts
 * checks that each pair agrees.
 */
import { createHash } from 'node:crypto'

/** Longest term, in words, that a candidate can match. */
export const MAX_WORDS = 8

const RUN = /[a-z0-9]+(?:[._/ -]+[a-z0-9]+)*/g
const SEPARATOR = /([._/ -]+)/

/** Digests of the repository names excluded from the public dashboard. */
export const EXCLUDED_REPO_DIGESTS = new Set([
  '3deec02d5707093b099ddfd80276066a84a5acbff860e5d3be87e88faa60aa23',
  '7e48c7b23b459c446e01a5cf805f95bd6ef268933a2c00a349c33d829a50a6ac',
  '8f452d3012fe2f0d1e4deb459db896dd2124b242ea3e1b43f99ba0353fa0ba4a',
  'cada8352d32b8c4bb62c801b1cfb46d7d6c9e03c9107caf4dce40d1c3c52a633',
  'dadded746f1d20cb34cc7eb59726ec80cac6d273bc12394b5ab491d2cefdb645'
])

/**
 * Digest of one more repository name. It is not a dashboard entry, so the
 * baked pages are not checked for it; tests/unit/cvPublicScrub.spec.ts checks
 * the tracked tree for it and for EXCLUDED_REPO_DIGESTS.
 */
export const OTHER_REPO_DIGESTS = new Set([
  '13c59540372a16e775ade0189e39462ad2a91e1c43e3f2d806d8eed980150411'
])

/** SHA-256 hex digest of a term, lowercased. */
export const digest = term => createHash('sha256').update(term.toLowerCase(), 'utf8').digest('hex')

/** Every run of 1 to MAX_WORDS joined words in `text`, lowercased. */
export function* candidates(text) {
  const normalized = text.toLowerCase().split(/\s+/).filter(Boolean).join(' ')
  for (const [run] of normalized.matchAll(RUN)) {
    const parts = run.split(SEPARATOR) // word, separator, word, ...
    for (let start = 0; start < parts.length; start += 2) {
      let span = parts[start]
      yield span
      const stop = Math.min(parts.length, start + 2 * MAX_WORDS - 1)
      for (let end = start + 2; end < stop; end += 2) {
        span += parts[end - 1] + parts[end]
        yield span
      }
    }
  }
}

/**
 * The candidates of `text` whose digest is in `digests`, sorted and unique.
 * Each distinct candidate is hashed once per call.
 */
export const findTerms = (text, digests) => {
  const seen = new Set()
  const found = new Set()
  for (const candidate of candidates(text)) {
    if (seen.has(candidate)) continue
    seen.add(candidate)
    if (digests.has(digest(candidate))) found.add(candidate)
  }
  return [...found].sort()
}
