import { describe, it, expect } from 'vitest'
import fs from 'node:fs'
import path from 'node:path'
import {
  EXCLUDED_REPO_DIGESTS,
  MAX_WORDS,
  candidates,
  digest,
  findTerms
} from '../../scripts/hashedTerms.mjs'

/**
 * scripts/hashedTerms.mjs matches text against SHA-256 digests of lowercased
 * terms; scripts/verify-dist-invariants.mjs runs it over every baked page with
 * EXCLUDED_REPO_DIGESTS. A synthetic name is added to a copy of the list to
 * show what the matcher finds and what it leaves alone.
 */

const REPO_ROOT = path.resolve(__dirname, '../../..')
const BACKEND_COPY = path.join(REPO_ROOT, 'backend/tests/hashed_terms.py')

const SYNTHETIC = 'example-tool'
const withSynthetic = (): Set<string> => new Set([...EXCLUDED_REPO_DIGESTS, digest(SYNTHETIC)])

describe('hashedTerms digest list', () => {
  it('holds five SHA-256 digests', () => {
    expect(EXCLUDED_REPO_DIGESTS.size).toBe(5)
    for (const d of EXCLUDED_REPO_DIGESTS) expect(d).toMatch(/^[0-9a-f]{64}$/)
  })

  it('matches the backend copy in backend/tests/hashed_terms.py', () => {
    const source = fs.readFileSync(BACKEND_COPY, 'utf-8')
    const block = /^EXCLUDED_REPO_DIGESTS: frozenset\[str\] = frozenset\(\s*\{([^}]*)\}/m.exec(
      source
    )
    expect(block).not.toBeNull()
    const backend = new Set([...block![1].matchAll(/"([0-9a-f]{64})"/g)].map(m => m[1]))
    expect(backend).toEqual(new Set(EXCLUDED_REPO_DIGESTS))
  })

  it('names none of the allowlisted repositories', () => {
    const text = 'subvectors subcheck portfolio-site github.com/Dashtid/portfolio-site'
    expect(findTerms(text, EXCLUDED_REPO_DIGESTS)).toEqual([])
  })
})

describe('hashedTerms matcher', () => {
  it.each([
    'example-tool',
    'Example-Tool.',
    'https://github.com/Dashtid/example-tool',
    'git clone git@github.com:Dashtid/example-tool.git',
    '{"full_name":"Dashtid/example-tool"}',
    'the example-tool-docs page',
    '<a href="/x">EXAMPLE-TOOL</a>'
  ])('finds a listed name in %s', text => {
    expect(findTerms(text, withSynthetic())).toEqual([SYNTHETIC])
  })

  it('does not find a listed name inside a longer word or with other separators', () => {
    expect(findTerms('example-toolkit, example tool, exampletool', withSynthetic())).toEqual([])
  })

  it('finds a multi-word term across collapsed whitespace', () => {
    const digests = new Set([digest('alpha beta gamma')])
    expect(findTerms('x Alpha\n   Beta\tgamma y', digests)).toEqual(['alpha beta gamma'])
  })

  it('caps a candidate at MAX_WORDS words', () => {
    const words = Array.from({ length: MAX_WORDS + 1 }, (_, i) => `w${i}`)
    const all = [...candidates(words.join('-'))]
    expect(all).toContain(words.slice(0, MAX_WORDS).join('-'))
    expect(all).not.toContain(words.join('-'))
  })
})
