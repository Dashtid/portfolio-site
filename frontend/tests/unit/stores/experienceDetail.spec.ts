import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useExperienceDetailStore } from '@/stores/experienceDetail'
import apiClient from '@/api/client'

vi.mock('@/api/client', () => ({ default: { get: vi.fn() } }))

const mockedApiClient = vi.mocked(apiClient, true)

const company = {
  id: 'co-1',
  name: 'Acme Corp',
  title: 'Engineer',
  description: 'Did things.',
  start_date: '2020-01-01'
}

describe('experienceDetail store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('fetches a company by id and caches it in byId', async () => {
    mockedApiClient.get.mockResolvedValue({ data: company })
    const store = useExperienceDetailStore()

    await store.fetchCompany('co-1')

    expect(mockedApiClient.get).toHaveBeenCalledTimes(1)
    expect(mockedApiClient.get).toHaveBeenCalledWith('/api/v1/companies/co-1', {
      signal: undefined
    })
    expect(store.byId['co-1']).toEqual(company)
  })

  it('forwards the AbortSignal to apiClient', async () => {
    mockedApiClient.get.mockResolvedValue({ data: company })
    const store = useExperienceDetailStore()
    const controller = new AbortController()

    await store.fetchCompany('co-1', controller.signal)

    expect(mockedApiClient.get).toHaveBeenCalledWith('/api/v1/companies/co-1', {
      signal: controller.signal
    })
  })

  it('is a no-op when the company is already cached', async () => {
    mockedApiClient.get.mockResolvedValue({ data: company })
    const store = useExperienceDetailStore()

    await store.fetchCompany('co-1')
    await store.fetchCompany('co-1')

    expect(mockedApiClient.get).toHaveBeenCalledTimes(1)
  })

  it('propagates fetch errors and leaves byId untouched', async () => {
    mockedApiClient.get.mockRejectedValue(new Error('boom'))
    const store = useExperienceDetailStore()

    await expect(store.fetchCompany('co-1')).rejects.toThrow('boom')
    expect(store.byId['co-1']).toBeUndefined()
  })
})
