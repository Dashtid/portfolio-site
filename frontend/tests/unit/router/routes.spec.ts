import { describe, it, expect } from 'vitest'
import { createRouter, createMemoryHistory } from 'vue-router'
import { routes } from '@/router'

// The experience id becomes a path segment of an API request
// (stores/experienceDetail.ts). vue-router matches the still-encoded path and
// decodes params afterwards, so the pattern decides what the decoded id holds.

const resolve = (path: string) =>
  createRouter({ history: createMemoryHistory(), routes }).resolve(path)

describe('experience route id', () => {
  it.each(['9ca80fd5-2015-4cff-acc8-1b900ed495e0', 'fixture-hermes'])(
    'matches the id %s on both paths',
    id => {
      for (const path of [`/experience/${id}`, `/company/${id}`]) {
        const route = resolve(path)
        expect(route.name).toBe('experience-detail')
        expect(route.params.id).toBe(id)
      }
    }
  )

  it.each([
    '/experience/..%2Fauth%2Fme',
    '/experience/%2E%2E%2Fauth%2Fme',
    '/experience/..%2Fauth%2Fme%3Fx%3D1',
    '/company/..%2Fauth%2Fme',
    '/experience/..'
  ])('sends %s to the not-found page', path => {
    expect(resolve(path).name).toBe('not-found-catchall')
  })
})
