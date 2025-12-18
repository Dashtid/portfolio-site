import { defineStore } from 'pinia'
import { AxiosError } from 'axios'
import apiClient from '../api/client'
import type { Company, Skill, Project, Education } from '@/types'
import { apiLogger } from '../utils/logger'

interface PortfolioState {
  companies: Company[]
  skills: Skill[]
  projects: Project[]
  education: Education[]
  loading: boolean
  error: string | null
}

interface ValidationError {
  msg?: string
  message?: string
  loc?: string[]
  type?: string
}

/**
 * Extract user-friendly error message from various error types
 * Handles both string details and FastAPI validation error arrays
 */
function extractErrorMessage(error: unknown): string {
  if (error instanceof AxiosError) {
    // Try to get error detail from response body
    const detail = error.response?.data?.detail
    if (typeof detail === 'string') return detail
    // Handle FastAPI validation errors (array of {msg, loc, type})
    if (Array.isArray(detail)) {
      return detail
        .map((err: ValidationError) => err.msg || err.message || String(err))
        .join(', ')
    }
    // Fallback to status text or generic message
    return error.response?.statusText || error.message || 'Network error'
  }
  if (error instanceof Error) {
    return error.message
  }
  return 'Unknown error occurred'
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
    error: null
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
    async fetchCompanies(): Promise<void> {
      this.loading = true
      this.error = null
      try {
        const response = await apiClient.get<Company[]>('/api/v1/companies/')
        this.companies = response.data
      } catch (error) {
        this.error = extractErrorMessage(error)
        apiLogger.error('Error fetching companies:', error)
      } finally {
        this.loading = false
      }
    },

    async fetchSkills(): Promise<void> {
      this.loading = true
      try {
        const response = await apiClient.get<Skill[]>('/api/v1/skills/')
        this.skills = response.data
      } catch (error) {
        this.error = extractErrorMessage(error)
        apiLogger.error('Error fetching skills:', error)
      } finally {
        this.loading = false
      }
    },

    async fetchProjects(): Promise<void> {
      this.loading = true
      try {
        const response = await apiClient.get<Project[]>('/api/v1/projects/')
        this.projects = response.data
      } catch (error) {
        this.error = extractErrorMessage(error)
        apiLogger.error('Error fetching projects:', error)
      } finally {
        this.loading = false
      }
    },

    async fetchEducation(): Promise<void> {
      this.loading = true
      try {
        const response = await apiClient.get<Education[]>('/api/v1/education/')
        this.education = response.data
      } catch (error) {
        this.error = extractErrorMessage(error)
        apiLogger.error('Error fetching education:', error)
      } finally {
        this.loading = false
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
