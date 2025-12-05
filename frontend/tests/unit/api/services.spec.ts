/**
 * Tests for API services (TypeScript)
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import * as services from '@/api/services'
import type { Company, Education, Project, Skill, Document, LoginRequest } from '@/types'

// Mock the API client
vi.mock('@/api/client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn()
  }
}))

import apiClient from '@/api/client'

describe('API services', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Health Check', () => {
    it('fetches health status', async () => {
      const mockHealth = { status: 'healthy', version: '1.0.0' }
      vi.mocked(apiClient.get).mockResolvedValue({ data: mockHealth })

      const result = await services.healthCheck()

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/health')
      expect(result).toEqual(mockHealth)
    })
  })

  describe('Company APIs', () => {
    const mockCompany: Company = {
      id: '1',
      name: 'Test Company',
      title: 'Developer',
      start_date: '2020-01-01',
      end_date: '2022-01-01',
      description: 'Test description',
      technologies: ['TypeScript', 'Vue'],
      logo_url: '/logo.png',
      website: 'https://test.com'
    }

    it('gets all companies', async () => {
      const mockCompanies: Company[] = [mockCompany]
      vi.mocked(apiClient.get).mockResolvedValue({ data: mockCompanies })

      const result = await services.getCompanies()

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/companies/')
      expect(result).toEqual(mockCompanies)
    })

    it('gets company by ID', async () => {
      vi.mocked(apiClient.get).mockResolvedValue({ data: mockCompany })

      const result = await services.getCompanyById('1')

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/companies/1')
      expect(result).toEqual(mockCompany)
    })

    it('creates company', async () => {
      const newCompany = { ...mockCompany }
      delete (newCompany as any).id
      vi.mocked(apiClient.post).mockResolvedValue({ data: mockCompany })

      const result = await services.createCompany(newCompany)

      expect(apiClient.post).toHaveBeenCalledWith('/api/v1/companies/', newCompany)
      expect(result).toEqual(mockCompany)
    })

    it('updates company', async () => {
      const updates = { name: 'Updated Company' }
      const updated = { ...mockCompany, ...updates }
      vi.mocked(apiClient.patch).mockResolvedValue({ data: updated })

      const result = await services.updateCompany('1', updates)

      expect(apiClient.patch).toHaveBeenCalledWith('/api/v1/companies/1', updates)
      expect(result).toEqual(updated)
    })

    it('deletes company', async () => {
      vi.mocked(apiClient.delete).mockResolvedValue({ data: undefined })

      await services.deleteCompany('1')

      expect(apiClient.delete).toHaveBeenCalledWith('/api/v1/companies/1')
    })
  })

  describe('Education APIs', () => {
    const mockEducation: Education = {
      id: '1',
      institution: 'Test University',
      degree: 'Bachelor of Science',
      field_of_study: 'Computer Science',
      start_date: '2016-09-01',
      end_date: '2020-06-01',
      description: 'Test education',
      logo_url: '/uni-logo.png'
    }

    it('gets all education', async () => {
      const mockEducations: Education[] = [mockEducation]
      vi.mocked(apiClient.get).mockResolvedValue({ data: mockEducations })

      const result = await services.getEducation()

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/education/')
      expect(result).toEqual(mockEducations)
    })

    it('gets education by ID', async () => {
      vi.mocked(apiClient.get).mockResolvedValue({ data: mockEducation })

      const result = await services.getEducationById('1')

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/education/1')
      expect(result).toEqual(mockEducation)
    })

    it('creates education', async () => {
      const newEducation = { ...mockEducation }
      delete (newEducation as any).id
      vi.mocked(apiClient.post).mockResolvedValue({ data: mockEducation })

      const result = await services.createEducation(newEducation)

      expect(apiClient.post).toHaveBeenCalledWith('/api/v1/education/', newEducation)
      expect(result).toEqual(mockEducation)
    })

    it('updates education', async () => {
      const updates = { degree: 'Master of Science' }
      const updated = { ...mockEducation, ...updates }
      vi.mocked(apiClient.patch).mockResolvedValue({ data: updated })

      const result = await services.updateEducation('1', updates)

      expect(apiClient.patch).toHaveBeenCalledWith('/api/v1/education/1', updates)
      expect(result).toEqual(updated)
    })

    it('deletes education', async () => {
      vi.mocked(apiClient.delete).mockResolvedValue({ data: undefined })

      await services.deleteEducation('1')

      expect(apiClient.delete).toHaveBeenCalledWith('/api/v1/education/1')
    })
  })

  describe('Project APIs', () => {
    const mockProject: Project = {
      id: '1',
      name: 'Test Project',
      description: 'Test description',
      technologies: ['Vue', 'TypeScript'],
      github_url: 'https://github.com/test/project',
      live_url: 'https://test-project.com',
      image_url: '/project.png',
      featured: true
    }

    it('gets all projects', async () => {
      const mockProjects: Project[] = [mockProject]
      vi.mocked(apiClient.get).mockResolvedValue({ data: mockProjects })

      const result = await services.getProjects()

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/projects/')
      expect(result).toEqual(mockProjects)
    })

    it('gets project by ID', async () => {
      vi.mocked(apiClient.get).mockResolvedValue({ data: mockProject })

      const result = await services.getProjectById('1')

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/projects/1')
      expect(result).toEqual(mockProject)
    })

    it('creates project', async () => {
      const newProject = { ...mockProject }
      delete (newProject as any).id
      vi.mocked(apiClient.post).mockResolvedValue({ data: mockProject })

      const result = await services.createProject(newProject)

      expect(apiClient.post).toHaveBeenCalledWith('/api/v1/projects/', newProject)
      expect(result).toEqual(mockProject)
    })

    it('updates project', async () => {
      const updates = { name: 'Updated Project' }
      const updated = { ...mockProject, ...updates }
      vi.mocked(apiClient.patch).mockResolvedValue({ data: updated })

      const result = await services.updateProject('1', updates)

      expect(apiClient.patch).toHaveBeenCalledWith('/api/v1/projects/1', updates)
      expect(result).toEqual(updated)
    })

    it('deletes project', async () => {
      vi.mocked(apiClient.delete).mockResolvedValue({ data: undefined })

      await services.deleteProject('1')

      expect(apiClient.delete).toHaveBeenCalledWith('/api/v1/projects/1')
    })
  })

  describe('Skill APIs', () => {
    const mockSkill: Skill = {
      id: '1',
      name: 'TypeScript',
      category: 'Programming',
      proficiency_level: 90,
      years_of_experience: 5
    }

    it('gets all skills', async () => {
      const mockSkills: Skill[] = [mockSkill]
      vi.mocked(apiClient.get).mockResolvedValue({ data: mockSkills })

      const result = await services.getSkills()

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/skills/')
      expect(result).toEqual(mockSkills)
    })

    it('gets skill by ID', async () => {
      vi.mocked(apiClient.get).mockResolvedValue({ data: mockSkill })

      const result = await services.getSkillById('1')

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/skills/1')
      expect(result).toEqual(mockSkill)
    })

    it('creates skill', async () => {
      const newSkill = { ...mockSkill }
      delete (newSkill as any).id
      vi.mocked(apiClient.post).mockResolvedValue({ data: mockSkill })

      const result = await services.createSkill(newSkill)

      expect(apiClient.post).toHaveBeenCalledWith('/api/v1/skills/', newSkill)
      expect(result).toEqual(mockSkill)
    })

    it('updates skill', async () => {
      const updates = { proficiency_level: 95 }
      const updated = { ...mockSkill, ...updates }
      vi.mocked(apiClient.patch).mockResolvedValue({ data: updated })

      const result = await services.updateSkill('1', updates)

      expect(apiClient.patch).toHaveBeenCalledWith('/api/v1/skills/1', updates)
      expect(result).toEqual(updated)
    })

    it('deletes skill', async () => {
      vi.mocked(apiClient.delete).mockResolvedValue({ data: undefined })

      await services.deleteSkill('1')

      expect(apiClient.delete).toHaveBeenCalledWith('/api/v1/skills/1')
    })
  })

  describe('Document APIs', () => {
    const mockDocument: Document = {
      id: '1',
      title: 'Resume',
      description: 'My resume',
      file_path: '/documents/resume.pdf',
      document_type: 'resume',
      file_size: 1024,
      file_url: '/api/v1/documents/1/download',
      created_at: '2023-01-01T00:00:00Z'
    }

    it('gets all documents', async () => {
      const mockDocuments: Document[] = [mockDocument]
      vi.mocked(apiClient.get).mockResolvedValue({ data: mockDocuments })

      const result = await services.getDocuments()

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/documents/')
      expect(result).toEqual(mockDocuments)
    })

    it('gets document by ID', async () => {
      vi.mocked(apiClient.get).mockResolvedValue({ data: mockDocument })

      const result = await services.getDocumentById('1')

      expect(apiClient.get).toHaveBeenCalledWith('/api/v1/documents/1')
      expect(result).toEqual(mockDocument)
    })
  })

  describe('Authentication APIs', () => {
    it('logs in user', async () => {
      const credentials: LoginRequest = {
        username: 'testuser',
        password: 'testpass'
      }
      const mockResponse = {
        access_token: 'token123',
        refresh_token: 'refresh123',
        token_type: 'bearer'
      }
      vi.mocked(apiClient.post).mockResolvedValue({ data: mockResponse })

      const result = await services.login(credentials)

      expect(apiClient.post).toHaveBeenCalledWith('/api/v1/auth/login', credentials)
      expect(result).toEqual(mockResponse)
    })

    it('logs out user and clears tokens', async () => {
      const mockLocalStorage: { [key: string]: string } = {
        accessToken: 'token123',
        refreshToken: 'refresh123'
      }

      global.localStorage = {
        getItem: vi.fn((key: string) => mockLocalStorage[key] || null),
        setItem: vi.fn((key: string, value: string) => {
          mockLocalStorage[key] = value
        }),
        removeItem: vi.fn((key: string) => {
          delete mockLocalStorage[key]
        }),
        clear: vi.fn(),
        length: 0,
        key: vi.fn()
      } as any

      await services.logout()

      expect(localStorage.removeItem).toHaveBeenCalledWith('accessToken')
      expect(localStorage.removeItem).toHaveBeenCalledWith('refreshToken')
    })
  })

  describe('TypeScript types', () => {
    it('services functions have correct types', () => {
      expect(typeof services.healthCheck).toBe('function')
      expect(typeof services.getCompanies).toBe('function')
      expect(typeof services.getEducation).toBe('function')
      expect(typeof services.getProjects).toBe('function')
      expect(typeof services.getSkills).toBe('function')
      expect(typeof services.getDocuments).toBe('function')
      expect(typeof services.login).toBe('function')
      expect(typeof services.logout).toBe('function')
    })
  })
})
