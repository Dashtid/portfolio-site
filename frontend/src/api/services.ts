import apiClient from './client'
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
export const getCompanies = async (): Promise<Company[]> => {
  const response = await apiClient.get<Company[]>('/api/v1/companies/')
  return response.data
}

export const getCompanyById = async (id: string): Promise<Company> => {
  const response = await apiClient.get<Company>(`/api/v1/companies/${id}`)
  return response.data
}

export const createCompany = async (company: Omit<Company, 'id'>): Promise<Company> => {
  const response = await apiClient.post<Company>('/api/v1/companies/', company)
  return response.data
}

export const updateCompany = async (id: string, company: Partial<Company>): Promise<Company> => {
  const response = await apiClient.patch<Company>(`/api/v1/companies/${id}`, company)
  return response.data
}

export const deleteCompany = async (id: string): Promise<void> => {
  await apiClient.delete(`/api/v1/companies/${id}`)
}

/**
 * Education APIs
 */
export const getEducation = async (): Promise<Education[]> => {
  const response = await apiClient.get<Education[]>('/api/v1/education/')
  return response.data
}

export const getEducationById = async (id: string): Promise<Education> => {
  const response = await apiClient.get<Education>(`/api/v1/education/${id}`)
  return response.data
}

export const createEducation = async (education: Omit<Education, 'id'>): Promise<Education> => {
  const response = await apiClient.post<Education>('/api/v1/education/', education)
  return response.data
}

export const updateEducation = async (
  id: string,
  education: Partial<Education>
): Promise<Education> => {
  const response = await apiClient.patch<Education>(`/api/v1/education/${id}`, education)
  return response.data
}

export const deleteEducation = async (id: string): Promise<void> => {
  await apiClient.delete(`/api/v1/education/${id}`)
}

/**
 * Project APIs
 */
export const getProjects = async (): Promise<Project[]> => {
  const response = await apiClient.get<Project[]>('/api/v1/projects/')
  return response.data
}

export const getProjectById = async (id: string): Promise<Project> => {
  const response = await apiClient.get<Project>(`/api/v1/projects/${id}`)
  return response.data
}

export const createProject = async (project: Omit<Project, 'id'>): Promise<Project> => {
  const response = await apiClient.post<Project>('/api/v1/projects/', project)
  return response.data
}

export const updateProject = async (id: string, project: Partial<Project>): Promise<Project> => {
  const response = await apiClient.patch<Project>(`/api/v1/projects/${id}`, project)
  return response.data
}

export const deleteProject = async (id: string): Promise<void> => {
  await apiClient.delete(`/api/v1/projects/${id}`)
}

/**
 * Skills APIs
 */
export const getSkills = async (): Promise<Skill[]> => {
  const response = await apiClient.get<Skill[]>('/api/v1/skills/')
  return response.data
}

export const getSkillById = async (id: string): Promise<Skill> => {
  const response = await apiClient.get<Skill>(`/api/v1/skills/${id}`)
  return response.data
}

export const createSkill = async (skill: Omit<Skill, 'id'>): Promise<Skill> => {
  const response = await apiClient.post<Skill>('/api/v1/skills/', skill)
  return response.data
}

export const updateSkill = async (id: string, skill: Partial<Skill>): Promise<Skill> => {
  const response = await apiClient.patch<Skill>(`/api/v1/skills/${id}`, skill)
  return response.data
}

export const deleteSkill = async (id: string): Promise<void> => {
  await apiClient.delete(`/api/v1/skills/${id}`)
}

/**
 * Document APIs
 */
export const getDocuments = async (): Promise<Document[]> => {
  const response = await apiClient.get<Document[]>('/api/v1/documents/')
  return response.data
}

export const getDocumentById = async (id: string): Promise<Document> => {
  const response = await apiClient.get<Document>(`/api/v1/documents/${id}`)
  return response.data
}

/**
 * Authentication APIs
 */
export const login = async (credentials: LoginRequest): Promise<LoginResponse> => {
  const response = await apiClient.post<LoginResponse>('/api/v1/auth/login', credentials)
  return response.data
}

export const logout = async (): Promise<void> => {
  // Clear local storage
  localStorage.removeItem('accessToken')
  localStorage.removeItem('refreshToken')
}
