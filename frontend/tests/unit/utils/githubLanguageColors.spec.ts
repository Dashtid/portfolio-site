import { describe, it, expect } from 'vitest'
import { githubLanguageColors, getLanguageColor } from '@/utils/githubLanguageColors'

describe('getLanguageColor', () => {
  it('returns the linguist hex for a known language', () => {
    expect(getLanguageColor('TypeScript')).toBe('#3178c6')
    expect(getLanguageColor('Python')).toBe('#3572A5')
    expect(getLanguageColor('Vue')).toBe('#41b883')
  })

  it('falls back to primary blue for an unknown language', () => {
    expect(getLanguageColor('Brainfuck')).toBe('#3b82f6')
  })

  it('falls back when language is null or undefined', () => {
    expect(getLanguageColor(null)).toBe('#3b82f6')
    expect(getLanguageColor(undefined)).toBe('#3b82f6')
  })

  it('falls back when language is an empty string', () => {
    expect(getLanguageColor('')).toBe('#3b82f6')
  })

  it('is case-sensitive (matches GitHub Linguist exactly)', () => {
    // 'typescript' (lowercase) is not the same as 'TypeScript' in Linguist
    expect(getLanguageColor('typescript')).toBe('#3b82f6')
  })
})

describe('githubLanguageColors map', () => {
  it('exports the expected core languages', () => {
    expect(githubLanguageColors).toMatchObject({
      TypeScript: '#3178c6',
      JavaScript: '#f1e05a',
      Python: '#3572A5',
      Vue: '#41b883'
    })
  })
})
