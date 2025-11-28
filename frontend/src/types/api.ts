/**
 * API Type Definitions
 *
 * These types match the FastAPI backend schema and provide
 * type safety for API requests and responses throughout the application.
 */

/**
 * Company/Experience Entry
 */
export interface Company {
  id: string
  name: string
  title: string
  description: string
  detailed_description?: string | null
  logo_url?: string | null
  start_date: string
  end_date?: string | null
  location?: string | null
  video_url?: string | null
  video_title?: string | null
  map_url?: string | null
  map_title?: string | null
  technologies?: string[] | null
  responsibilities?: string[] | null
}

/**
 * Education Entry
 */
export interface Education {
  id: string
  institution: string
  degree: string
  field_of_study: string
  start_date: string
  end_date?: string | null
  description?: string | null
  location?: string | null
  logo_url?: string | null
}

/**
 * Project Entry
 */
export interface Project {
  id: string
  name: string
  description: string
  detailed_description?: string | null
  technologies: string[]
  github_url?: string | null
  live_url?: string | null
  image_url?: string | null
  company_id?: string | null
  featured: boolean
  order_index?: number
  video_url?: string | null
  video_title?: string | null
  map_url?: string | null
  map_title?: string | null
  responsibilities?: string | null
  created_at?: string
  updated_at?: string | null
}

/**
 * Skill Entry
 */
export interface Skill {
  id: string
  name: string
  category: string
  proficiency_level: number
  years_of_experience?: number | null
}

/**
 * Admin Login Request
 */
export interface LoginRequest {
  username: string
  password: string
}

/**
 * Admin Login Response
 */
export interface LoginResponse {
  access_token: string
  token_type: string
}

/**
 * API Health Check Response
 */
export interface HealthResponse {
  status: string
  service: string
  version: string
}

/**
 * Document Entry
 */
export interface Document {
  id: string
  title: string
  description?: string | null
  document_type: string
  file_path: string
  file_size: number
  file_url: string
  published_date?: string | null
  created_at: string
}

/**
 * API Error Response
 */
export interface ErrorResponse {
  detail: string
}
