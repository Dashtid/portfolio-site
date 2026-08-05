/**
 * Central Type Exports
 *
 * API response shapes, mirroring the backend Pydantic schemas
 * (backend/app/schemas/). Optional-nullable fields (`?: T | null`) match
 * FastAPI's serialization: a field can be absent or explicitly null.
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
  website?: string | null
  video_url?: string | null
  video_title?: string | null
  map_url?: string | null
  map_title?: string | null
  technologies?: string[] | null
  responsibilities?: string[] | null
  outcomes?: string[] | null
  order_index?: number
}

/** One merged upstream PR from the public OSS endpoint (D3-FEAT-01). */
export interface OssContribution {
  repoNameWithOwner: string
  number: number
  title: string
  url: string
  mergedAt: string
}

export interface Education {
  id: string
  institution: string
  degree: string
  field_of_study?: string | null
  start_date: string
  end_date?: string | null
  description?: string | null
  location?: string | null
  logo_url?: string | null
  is_certification?: boolean
  certificate_number?: string | null
  certificate_url?: string | null
  order_index?: number
}

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

/** PUBLIC skill shape. No proficiency_level/years — the public API stopped
 *  serving those (see backend SkillResponse); nothing renders them and an
 *  unfalsifiable 0-100 self-rating is a liability, not proof. */
export interface Skill {
  id: string
  name: string
  category: string
  order_index?: number | null
  created_at?: string
}

/** Full row, only from the admin-authenticated GET /api/v1/skills/admin/all. */
export interface AdminSkill extends Skill {
  proficiency_level: number | null
  years_of_experience?: number | null
}

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
  order_index?: number
}
