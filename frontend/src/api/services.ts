import apiClient from './client'
import { createCrudService, createReadOnlyService } from './createCrudService'
import { storage, STORAGE_KEYS } from '@/utils/storage'
import type {
  Company,
  Education,
  Project,
  Skill,
  Document,
  LoginRequest,
  LoginResponse,
  HealthResponse
} from '@/types'

/**
 * API Services
 *
 * Typed wrapper functions for all backend API endpoints.
 * Uses the configured axios client with auth interceptors.
 */

// ============================================================================
// CRUD Services (using factory pattern)
// ============================================================================

const companyService = createCrudService<Company>('/api/v1/companies')
const educationService = createCrudService<Education>('/api/v1/education')
const projectService = createCrudService<Project>('/api/v1/projects')
const skillService = createCrudService<Skill>('/api/v1/skills')
const documentService = createReadOnlyService<Document>('/api/v1/documents')

// ============================================================================
// Backward-compatible exports
// ============================================================================

/**
 * Health Check
 */
export const healthCheck = async (): Promise<HealthResponse> => {
  const response = await apiClient.get<HealthResponse>('/api/v1/health')
  return response.data
}

/**
 * Company/Experience APIs
 */
export const getCompanies = companyService.getAll
export const getCompanyById = companyService.getById
export const createCompany = companyService.create
export const updateCompany = companyService.update
export const deleteCompany = companyService.delete

/**
 * Education APIs
 */
export const getEducation = educationService.getAll
export const getEducationById = educationService.getById
export const createEducation = educationService.create
export const updateEducation = educationService.update
export const deleteEducation = educationService.delete

/**
 * Project APIs
 */
export const getProjects = projectService.getAll
export const getProjectById = projectService.getById
export const createProject = projectService.create
export const updateProject = projectService.update
export const deleteProject = projectService.delete

/**
 * Skills APIs
 */
export const getSkills = skillService.getAll
export const getSkillById = skillService.getById
export const createSkill = skillService.create
export const updateSkill = skillService.update
export const deleteSkill = skillService.delete

/**
 * Document APIs
 */
export const getDocuments = documentService.getAll
export const getDocumentById = documentService.getById

/**
 * Authentication APIs
 */
export const login = async (credentials: LoginRequest): Promise<LoginResponse> => {
  const response = await apiClient.post<LoginResponse>('/api/v1/auth/login', credentials)
  return response.data
}

export const logout = async (): Promise<void> => {
  // Call API to clear HTTP-only cookies on server
  try {
    await apiClient.post('/api/v1/auth/logout')
  } catch {
    // Continue with local cleanup even if API call fails
  }
  // Clear local storage using storage utility (handles errors gracefully)
  storage.removeMultiple([STORAGE_KEYS.ACCESS_TOKEN, STORAGE_KEYS.REFRESH_TOKEN])
}
