import { defineStore } from 'pinia'
import apiClient from '../api/client'

export const usePortfolioStore = defineStore('portfolio', {
  state: () => ({
    companies: [],
    skills: [],
    projects: [],
    loading: false,
    error: null
  }),

  getters: {
    currentCompany: (state) => {
      return state.companies.find(c => c.end_date === null) || state.companies[0]
    },

    companiesByDate: (state) => {
      return [...state.companies].sort((a, b) => {
        if (!a.start_date) return 1
        if (!b.start_date) return -1
        return new Date(b.start_date) - new Date(a.start_date)
      })
    },

    skillsByCategory: (state) => {
      const grouped = {}
      state.skills.forEach(skill => {
        const category = skill.category || 'other'
        if (!grouped[category]) {
          grouped[category] = []
        }
        grouped[category].push(skill)
      })
      return grouped
    },

    featuredProjects: (state) => {
      return state.projects.filter(p => p.featured)
    }
  },

  actions: {
    async fetchCompanies() {
      this.loading = true
      this.error = null
      try {
        const response = await apiClient.get('/api/v1/companies')
        this.companies = response.data
      } catch (error) {
        this.error = error.message
        console.error('Error fetching companies:', error)
      } finally {
        this.loading = false
      }
    },

    async fetchSkills() {
      try {
        const response = await apiClient.get('/api/v1/skills')
        this.skills = response.data
      } catch (error) {
        console.error('Error fetching skills:', error)
      }
    },

    async fetchProjects() {
      try {
        const response = await apiClient.get('/api/v1/projects')
        this.projects = response.data
      } catch (error) {
        console.error('Error fetching projects:', error)
      }
    },

    async fetchAllData() {
      await Promise.all([
        this.fetchCompanies(),
        this.fetchSkills(),
        this.fetchProjects()
      ])
    }
  }
})