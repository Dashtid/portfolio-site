import { defineStore } from 'pinia'
import apiClient from '../api/client'
import type { Company, Skill, Project, Education } from '@/types'
import { apiLogger } from '../utils/logger'
import { getErrorMessage } from '../utils/typeGuards'

interface PortfolioState {
  companies: Company[]
  skills: Skill[]
  projects: Project[]
  education: Education[]
  loading: boolean
  error: string | null
  // Track active requests to handle parallel fetches correctly
  _activeRequests: number
}

interface SkillsByCategory {
  [category: string]: Skill[]
}

export const usePortfolioStore = defineStore('portfolio', {
  state: (): PortfolioState => ({
    companies: [],
    skills: [],
    projects: [],
    education: [],
    loading: false,
    error: null,
    _activeRequests: 0
  }),

  getters: {
    currentCompany: (state): Company | undefined => {
      return state.companies.find(c => c.end_date === null) || state.companies[0]
    },

    companiesByDate: (state): Company[] => {
      return [...state.companies].sort((a, b) => {
        if (!a.start_date) return 1
        if (!b.start_date) return -1
        return new Date(b.start_date).getTime() - new Date(a.start_date).getTime()
      })
    },

    skillsByCategory: (state): SkillsByCategory => {
      const grouped: SkillsByCategory = {}
      state.skills.forEach(skill => {
        const category = skill.category || 'other'
        if (!grouped[category]) {
          grouped[category] = []
        }
        grouped[category].push(skill)
      })
      return grouped
    },

    featuredProjects: (state): Project[] => {
      return state.projects.filter(p => p.featured)
    }
  },

  actions: {
    // BUGS-06: clear `error` exactly once when a new batch of fetches
    // begins (i.e. when the request counter transitions from 0 to 1).
    // Previously every individual fetcher cleared `error` at its top, so
    // when fetchAllData() ran fetches in parallel a successful late
    // fetcher's `error = null` would erase the failure recorded by an
    // earlier-completing fetcher in the same batch. Once one fetch is
    // already in-flight, subsequent ones leave any recorded error alone.
    _startRequest(): void {
      if (this._activeRequests === 0) {
        this.error = null
      }
      this._activeRequests++
      this.loading = true
    },

    _endRequest(): void {
      this._activeRequests = Math.max(0, this._activeRequests - 1)
      // Only set loading to false when all requests complete
      if (this._activeRequests === 0) {
        this.loading = false
      }
    },

    async fetchCompanies(): Promise<void> {
      this._startRequest()
      try {
        const response = await apiClient.get<Company[]>('/api/v1/companies')
        this.companies = response.data
      } catch (error) {
        this.error = getErrorMessage(error)
        apiLogger.error('Error fetching companies:', error)
      } finally {
        this._endRequest()
      }
    },

    async fetchSkills(): Promise<void> {
      this._startRequest()
      try {
        const response = await apiClient.get<Skill[]>('/api/v1/skills')
        this.skills = response.data
      } catch (error) {
        this.error = getErrorMessage(error)
        apiLogger.error('Error fetching skills:', error)
      } finally {
        this._endRequest()
      }
    },

    async fetchProjects(): Promise<void> {
      this._startRequest()
      try {
        const response = await apiClient.get<Project[]>('/api/v1/projects')
        this.projects = response.data
      } catch (error) {
        this.error = getErrorMessage(error)
        apiLogger.error('Error fetching projects:', error)
      } finally {
        this._endRequest()
      }
    },

    async fetchEducation(): Promise<void> {
      this._startRequest()
      try {
        const response = await apiClient.get<Education[]>('/api/v1/education')
        this.education = response.data
      } catch (error) {
        this.error = getErrorMessage(error)
        apiLogger.error('Error fetching education:', error)
      } finally {
        this._endRequest()
      }
    },

    async fetchAllData(): Promise<void> {
      await Promise.all([
        this.fetchCompanies(),
        this.fetchSkills(),
        this.fetchProjects(),
        this.fetchEducation()
      ])
    }
  }
})
