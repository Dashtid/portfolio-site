/**
 * Tests for Portfolio Store
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { usePortfolioStore } from '@/stores/portfolio'
import apiClient from '@/api/client'

// Mock the api client
vi.mock('@/api/client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn()
  }
}))

// Mock the logger to avoid console output during tests
vi.mock('@/utils/logger', () => ({
  apiLogger: {
    error: vi.fn(),
    warn: vi.fn(),
    log: vi.fn(),
    debug: vi.fn(),
    info: vi.fn()
  }
}))

// Sample test data
const mockCompanies = [
  {
    id: '1',
    name: 'Test Company 1',
    title: 'Software Engineer',
    description: 'Test description',
    start_date: '2022-01-01',
    end_date: null,
    location: 'Stockholm, Sweden'
  },
  {
    id: '2',
    name: 'Test Company 2',
    title: 'Senior Developer',
    description: 'Another description',
    start_date: '2020-01-01',
    end_date: '2021-12-31',
    location: 'Remote'
  }
]

const mockSkills = [
  { id: '1', name: 'Python', category: 'Technical', proficiency_level: 90 },
  { id: '2', name: 'Docker', category: 'Technical', proficiency_level: 85 },
  { id: '3', name: 'Cybersecurity', category: 'Domain Expertise', proficiency_level: 80 }
]

const mockProjects = [
  {
    id: '1',
    name: 'Project 1',
    description: 'A featured project',
    technologies: ['Vue', 'Python'],
    featured: true
  },
  {
    id: '2',
    name: 'Project 2',
    description: 'A regular project',
    technologies: ['React', 'Node'],
    featured: false
  }
]

const mockEducation = [
  {
    id: '1',
    institution: 'KTH Royal Institute of Technology',
    degree: 'Master of Science',
    field_of_study: 'Biomedical Engineering',
    start_date: '2015-09-01',
    end_date: '2018-06-15'
  }
]

describe('Portfolio Store', () => {
  beforeEach(() => {
    // Create a fresh pinia instance for each test
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('initial state', () => {
    it('should have empty companies array', () => {
      const store = usePortfolioStore()
      expect(store.companies).toEqual([])
    })

    it('should have empty skills array', () => {
      const store = usePortfolioStore()
      expect(store.skills).toEqual([])
    })

    it('should have empty projects array', () => {
      const store = usePortfolioStore()
      expect(store.projects).toEqual([])
    })

    it('should have empty education array', () => {
      const store = usePortfolioStore()
      expect(store.education).toEqual([])
    })

    it('should not be loading initially', () => {
      const store = usePortfolioStore()
      expect(store.loading).toBe(false)
    })

    it('should have no error initially', () => {
      const store = usePortfolioStore()
      expect(store.error).toBeNull()
    })
  })

  describe('getters', () => {
    describe('currentCompany', () => {
      it('should return company with null end_date (current job)', () => {
        const store = usePortfolioStore()
        store.companies = mockCompanies

        const current = store.currentCompany

        expect(current).toBeDefined()
        expect(current?.name).toBe('Test Company 1')
        expect(current?.end_date).toBeNull()
      })

      it('should return first company if no current job', () => {
        const store = usePortfolioStore()
        store.companies = [
          { ...mockCompanies[1] } // Only the ended job
        ]

        const current = store.currentCompany

        expect(current).toBeDefined()
        expect(current?.name).toBe('Test Company 2')
      })

      it('should return undefined for empty companies', () => {
        const store = usePortfolioStore()
        store.companies = []

        expect(store.currentCompany).toBeUndefined()
      })
    })

    describe('companiesByDate', () => {
      it('should sort companies by start_date descending', () => {
        const store = usePortfolioStore()
        store.companies = mockCompanies

        const sorted = store.companiesByDate

        expect(sorted[0].name).toBe('Test Company 1') // 2022
        expect(sorted[1].name).toBe('Test Company 2') // 2020
      })

      it('should handle companies without start_date', () => {
        const store = usePortfolioStore()
        store.companies = [
          { ...mockCompanies[0], start_date: undefined as unknown as string },
          mockCompanies[1]
        ]

        const sorted = store.companiesByDate

        // Company without start_date should be at the end
        expect(sorted[sorted.length - 1].start_date).toBeUndefined()
      })
    })

    describe('skillsByCategory', () => {
      it('should group skills by category', () => {
        const store = usePortfolioStore()
        store.skills = mockSkills

        const grouped = store.skillsByCategory

        expect(grouped['Technical']).toHaveLength(2)
        expect(grouped['Domain Expertise']).toHaveLength(1)
      })

      it('should return empty object for no skills', () => {
        const store = usePortfolioStore()
        store.skills = []

        expect(store.skillsByCategory).toEqual({})
      })

      it('should handle skills without category as "other"', () => {
        const store = usePortfolioStore()
        store.skills = [{ id: '1', name: 'Skill', category: '', proficiency_level: 50 }]

        const grouped = store.skillsByCategory

        expect(grouped['other']).toBeDefined()
        expect(grouped['other']).toHaveLength(1)
      })
    })

    describe('featuredProjects', () => {
      it('should return only featured projects', () => {
        const store = usePortfolioStore()
        store.projects = mockProjects

        const featured = store.featuredProjects

        expect(featured).toHaveLength(1)
        expect(featured[0].name).toBe('Project 1')
        expect(featured[0].featured).toBe(true)
      })

      it('should return empty array when no featured projects', () => {
        const store = usePortfolioStore()
        store.projects = [{ ...mockProjects[1] }] // Only non-featured

        expect(store.featuredProjects).toHaveLength(0)
      })
    })
  })

  describe('actions', () => {
    describe('fetchCompanies', () => {
      it('should fetch companies and update state', async () => {
        vi.mocked(apiClient.get).mockResolvedValue({ data: mockCompanies })

        const store = usePortfolioStore()
        await store.fetchCompanies()

        expect(apiClient.get).toHaveBeenCalledWith('/api/v1/companies/')
        expect(store.companies).toEqual(mockCompanies)
        expect(store.loading).toBe(false)
        expect(store.error).toBeNull()
      })

      it('should set loading state during fetch', async () => {
        let loadingDuringFetch = false
        vi.mocked(apiClient.get).mockImplementation(async () => {
          // Check loading state during the fetch
          const store = usePortfolioStore()
          loadingDuringFetch = store.loading
          return { data: mockCompanies }
        })

        const store = usePortfolioStore()
        await store.fetchCompanies()

        expect(loadingDuringFetch).toBe(true)
        expect(store.loading).toBe(false)
      })

      it('should handle fetch error', async () => {
        const error = new Error('Network error')
        vi.mocked(apiClient.get).mockRejectedValue(error)

        const store = usePortfolioStore()
        await store.fetchCompanies()

        expect(store.error).toBe('Network error')
        expect(store.loading).toBe(false)
      })
    })

    describe('fetchSkills', () => {
      it('should fetch skills and update state', async () => {
        vi.mocked(apiClient.get).mockResolvedValue({ data: mockSkills })

        const store = usePortfolioStore()
        await store.fetchSkills()

        expect(apiClient.get).toHaveBeenCalledWith('/api/v1/skills/')
        expect(store.skills).toEqual(mockSkills)
      })

      it('should handle fetch error gracefully', async () => {
        vi.mocked(apiClient.get).mockRejectedValue(new Error('Failed'))

        const store = usePortfolioStore()
        await store.fetchSkills()

        // Should not throw, just log error
        expect(store.skills).toEqual([])
      })
    })

    describe('fetchProjects', () => {
      it('should fetch projects and update state', async () => {
        vi.mocked(apiClient.get).mockResolvedValue({ data: mockProjects })

        const store = usePortfolioStore()
        await store.fetchProjects()

        expect(apiClient.get).toHaveBeenCalledWith('/api/v1/projects/')
        expect(store.projects).toEqual(mockProjects)
      })

      it('should handle fetch error gracefully', async () => {
        vi.mocked(apiClient.get).mockRejectedValue(new Error('Failed'))

        const store = usePortfolioStore()
        await store.fetchProjects()

        expect(store.projects).toEqual([])
      })
    })

    describe('fetchEducation', () => {
      it('should fetch education and update state', async () => {
        vi.mocked(apiClient.get).mockResolvedValue({ data: mockEducation })

        const store = usePortfolioStore()
        await store.fetchEducation()

        expect(apiClient.get).toHaveBeenCalledWith('/api/v1/education/')
        expect(store.education).toEqual(mockEducation)
      })

      it('should handle fetch error gracefully', async () => {
        vi.mocked(apiClient.get).mockRejectedValue(new Error('Failed'))

        const store = usePortfolioStore()
        await store.fetchEducation()

        expect(store.education).toEqual([])
      })
    })

    describe('fetchAllData', () => {
      it('should fetch all data in parallel', async () => {
        vi.mocked(apiClient.get)
          .mockResolvedValueOnce({ data: mockCompanies })
          .mockResolvedValueOnce({ data: mockSkills })
          .mockResolvedValueOnce({ data: mockProjects })
          .mockResolvedValueOnce({ data: mockEducation })

        const store = usePortfolioStore()
        await store.fetchAllData()

        expect(apiClient.get).toHaveBeenCalledTimes(4)
        expect(store.companies).toEqual(mockCompanies)
        expect(store.skills).toEqual(mockSkills)
        expect(store.projects).toEqual(mockProjects)
        expect(store.education).toEqual(mockEducation)
      })

      it('should handle partial failures', async () => {
        vi.mocked(apiClient.get)
          .mockResolvedValueOnce({ data: mockCompanies })
          .mockRejectedValueOnce(new Error('Skills failed'))
          .mockResolvedValueOnce({ data: mockProjects })
          .mockRejectedValueOnce(new Error('Education failed'))

        const store = usePortfolioStore()
        await store.fetchAllData()

        // Should still populate successful fetches
        expect(store.companies).toEqual(mockCompanies)
        expect(store.projects).toEqual(mockProjects)
        // Failed fetches should keep default state
        expect(store.skills).toEqual([])
        expect(store.education).toEqual([])
      })
    })
  })

  describe('reactivity', () => {
    it('should update computed values when state changes', () => {
      const store = usePortfolioStore()

      // Initially empty
      expect(store.featuredProjects).toHaveLength(0)

      // Add projects
      store.projects = mockProjects

      // Computed should update
      expect(store.featuredProjects).toHaveLength(1)
    })

    it('should update skillsByCategory when skills change', () => {
      const store = usePortfolioStore()

      expect(Object.keys(store.skillsByCategory)).toHaveLength(0)

      store.skills = mockSkills

      expect(Object.keys(store.skillsByCategory)).toHaveLength(2)
    })
  })
})
