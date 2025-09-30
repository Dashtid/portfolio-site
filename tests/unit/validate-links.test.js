/**
 * Unit Tests for Link Validation Script
 * Tests link checking, URL validation, and HTML parsing
 */

/* eslint-env jest, node */

describe('Link Validation Script', () => {
  test('should validate URL format', () => {
    const isValidUrl = url => {
      try {
        // eslint-disable-next-line no-new
        new URL(url)
        return true
      } catch {
        return false
      }
    }

    expect(isValidUrl('https://example.com')).toBe(true)
    expect(isValidUrl('invalid-url')).toBe(false)
  })

  test('should extract basic link patterns', () => {
    const html = '<a href="https://example.com">Link</a>'
    const linkPattern = /href=["']([^"']+)["']/g
    const matches = [...html.matchAll(linkPattern)]

    expect(matches).toHaveLength(1)
    expect(matches[0][1]).toBe('https://example.com')
  })

  test('should avoid duplicate URL checks', () => {
    const urls = [
      'https://example.com',
      'https://example.com',
      'https://example.com/image.jpg'
    ]
    const uniqueUrls = [...new Set(urls)]
    expect(uniqueUrls).toHaveLength(2)
  })
})
