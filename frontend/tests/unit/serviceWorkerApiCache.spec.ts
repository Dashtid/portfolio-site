import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

/**
 * The service worker's api-cache keeps what its route matches in
 * CacheStorage, where a response outlives a logout: Workbox ignores the
 * response's Cache-Control. So the route may match public reads only.
 *
 * The pattern is read from vite.config.ts, the runtimeCaching entry whose
 * cacheName is 'api-cache', and applied the way workbox-routing's
 * RegExpRoute applies it: exec() on the full URL, and for a cross-origin
 * request only a match that starts at the URL's first character.
 */

const FRONTEND_ROOT = resolve(__dirname, '../..')

const apiCachePattern = (): RegExp => {
  const config = readFileSync(resolve(FRONTEND_ROOT, 'vite.config.ts'), 'utf-8')
  const head = config.slice(0, config.indexOf("cacheName: 'api-cache'"))
  const literal = head
    .slice(head.lastIndexOf('urlPattern:') + 'urlPattern:'.length, head.lastIndexOf('handler:'))
    .trim()
    .replace(/,$/, '')
  const end = literal.lastIndexOf('/')
  if (!literal.startsWith('/') || end < 1) {
    throw new Error("no urlPattern regex literal before cacheName 'api-cache' in vite.config.ts")
  }
  return new RegExp(literal.slice(1, end), literal.slice(end + 1))
}

/** Whether the service worker of https://dashti.se routes a GET of `url` to api-cache. */
const routed = (url: string): boolean => {
  const target = new URL(url)
  const result = apiCachePattern().exec(target.href)
  return result !== null && (target.origin === 'https://dashti.se' || result.index === 0)
}

const API = 'https://api.dashti.se/api/v1'
const UUID = '0b9a43f5-5c2e-4f0e-9d3b-2d8e6c1f7a90'

describe('service worker api-cache route', () => {
  it('matches none of the authenticated reads the frontend makes', () => {
    for (const path of [
      '/skills/admin/all',
      '/education/admin/all',
      '/admin/cv/profile',
      '/admin/cv/export',
      '/admin/oss',
      '/admin/sentry-panel',
      '/auth/me',
      '/analytics/stats/summary?days=30',
      '/analytics/stats/visitors?days=7',
      '/metrics/'
    ]) {
      expect(routed(`${API}${path}`), path).toBe(false)
    }
  })

  it('matches no other path under a public collection than the collection and one id', () => {
    // /skills/admin/all is an admin route mounted under a public prefix; the
    // next one must not be cached either. Query strings change nothing.
    for (const path of [
      '/skills/admin/all?fresh=1',
      '/education/admin/all?fresh=1',
      '/companies/admin',
      `/companies/${UUID}/admin`,
      '/projects/admin/all',
      '/documents/upload',
      '/oss/contributions/admin',
      '/github/stats/Dashtid/admin',
      '/auth?probe=1',
      '/metrics?probe=1',
      '/health'
    ]) {
      expect(routed(`${API}${path}`), path).toBe(false)
    }
  })

  it('still matches every public read the site makes', () => {
    for (const path of [
      '/companies',
      '/companies/',
      `/companies/${UUID}`,
      '/skills',
      '/projects',
      '/education',
      '/education/',
      '/documents',
      '/documents/',
      '/oss/contributions',
      '/github/stats/Dashtid'
    ]) {
      expect(routed(`${API}${path}`), path).toBe(true)
    }
  })
})
