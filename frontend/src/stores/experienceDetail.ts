import { defineStore } from 'pinia'
import apiClient from '../api/client'
import type { Company } from '@/types'

interface ExperienceDetailState {
  // Companies fetched by id. Populated during SSG (so the data is serialized
  // into the page via vite-ssg's initialState) and reused on the client after
  // hydration — avoids the redundant refetch + hydration mismatch the
  // component used to cause by re-fetching in onMounted.
  byId: Record<string, Company>
}

export const useExperienceDetailStore = defineStore('experienceDetail', {
  state: (): ExperienceDetailState => ({
    byId: {}
  }),

  actions: {
    /**
     * Fetch a company by id and cache it. No-op if already cached (e.g.
     * hydrated from SSG). The optional AbortSignal lets callers cancel an
     * in-flight request when the route changes; a cancellation throws and
     * is the caller's responsibility to swallow.
     */
    async fetchCompany(id: string, signal?: AbortSignal): Promise<void> {
      if (this.byId[id]) return
      const response = await apiClient.get<Company>(`/api/v1/companies/${id}`, { signal })
      this.byId[id] = response.data
    }
  }
})
