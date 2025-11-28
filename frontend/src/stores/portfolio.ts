import { defineStore } from 'pinia'
import apiClient from '../api/client'
import type { Company, Skill, Project, Education } from '@/types'

interface PortfolioState {
  companies: Company[]
  skills: Skill[]
  projects: Project[]
  education: Education[]
  loading: boolean
  error: string | null
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
        const errorMessage = error instanceof Error ? error.message : 'Unknown error'
        this.error = errorMessage
        console.error('Error fetching companies:', error)
      } finally {
        this.loading = false
      }
    },

    async fetchSkills(): Promise<void> {
      try {
        const response = await apiClient.get<Skill[]>('/api/v1/skills/')
        this.skills = response.data
      } catch (error) {
        console.error('Error fetching skills:', error)
      }
    },

    async fetchProjects(): Promise<void> {
      try {
        const response = await apiClient.get<Project[]>('/api/v1/projects/')
        this.projects = response.data
      } catch (error) {
        console.error('Error fetching projects:', error)
      }
    },

    async fetchEducation(): Promise<void> {
      try {
        const response = await apiClient.get<Education[]>('/api/v1/education/')
        this.education = response.data
      } catch (error) {
        console.error('Error fetching education:', error)
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
