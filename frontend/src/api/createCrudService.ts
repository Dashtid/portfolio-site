/**
 * CRUD Service Factory
 *
 * Creates type-safe CRUD operations for API resources,
 * reducing boilerplate while maintaining full type safety.
 */

import apiClient from './client'

/**
 * Interface for standard CRUD operations
 */
export interface CrudService<T extends { id: string }> {
  getAll: () => Promise<T[]>
  getById: (id: string) => Promise<T>
  create: (data: Omit<T, 'id'>) => Promise<T>
  update: (id: string, data: Partial<T>) => Promise<T>
  delete: (id: string) => Promise<void>
}

/**
 * Creates a CRUD service for a given API endpoint
 *
 * @param endpoint - The API endpoint path (e.g., '/api/v1/companies')
 * @returns Object with CRUD methods
 *
 * @example
 * ```ts
 * const companyService = createCrudService<Company>('/api/v1/companies')
 * const companies = await companyService.getAll()
 * ```
 */
export function createCrudService<T extends { id: string }>(endpoint: string): CrudService<T> {
  // Normalize endpoint to not have trailing slash for consistent URL construction
  const baseUrl = endpoint.endsWith('/') ? endpoint.slice(0, -1) : endpoint

  return {
    getAll: async (): Promise<T[]> => {
      const response = await apiClient.get<T[]>(baseUrl)
      return response.data
    },

    getById: async (id: string): Promise<T> => {
      const response = await apiClient.get<T>(`${baseUrl}/${id}`)
      return response.data
    },

    create: async (data: Omit<T, 'id'>): Promise<T> => {
      const response = await apiClient.post<T>(baseUrl, data)
      return response.data
    },

    update: async (id: string, data: Partial<T>): Promise<T> => {
      const response = await apiClient.put<T>(`${baseUrl}/${id}`, data)
      return response.data
    },

    delete: async (id: string): Promise<void> => {
      await apiClient.delete(`${baseUrl}/${id}`)
    }
  }
}

/**
 * Creates a read-only service for resources without write operations
 *
 * @param endpoint - The API endpoint path
 * @returns Object with read-only methods
 */
export function createReadOnlyService<T extends { id: string }>(
  endpoint: string
): Pick<CrudService<T>, 'getAll' | 'getById'> {
  // Normalize endpoint to not have trailing slash for consistent URL construction
  const baseUrl = endpoint.endsWith('/') ? endpoint.slice(0, -1) : endpoint

  return {
    getAll: async (): Promise<T[]> => {
      const response = await apiClient.get<T[]>(baseUrl)
      return response.data
    },

    getById: async (id: string): Promise<T> => {
      const response = await apiClient.get<T>(`${baseUrl}/${id}`)
      return response.data
    }
  }
}
