/**
 * Shared CV types for the admin-only export (Campaign 2026-08 Sprint 2).
 *
 * `CvResume` mirrors the JSON Resume payload assembled by the backend
 * GET /api/v1/admin/cv/export endpoint. `CvProfile` mirrors the editable
 * singleton behind GET/PUT /api/v1/admin/cv/profile — it carries the private
 * contact fields, which only ever reach an authenticated admin.
 */

export interface CvLanguage {
  language: string
  fluency: string
}

export interface CvResume {
  basics: {
    name: string
    label: string
    email?: string
    phone?: string
    url?: string
    summary: string
    focus?: string
    /** Optional, off by default — present only when the owner filled it in. */
    personalNumber?: string
    location: { city: string; region?: string; countryCode: string }
    profiles?: Array<{ network: string; url: string }>
  }
  work: Array<{
    name: string
    position: string
    location?: string
    startDate: string
    endDate?: string
    highlights?: string[]
  }>
  education: Array<{
    institution: string
    area?: string
    studyType: string
    startDate: string
    endDate: string
    courses?: string[]
  }>
  certificates: Array<{ name: string; date: string; issuer: string; url?: string }>
  skills: Array<{ name: string; keywords: string[] }>
  languages: CvLanguage[]
}

export interface CvProfile {
  id?: number
  name: string
  label: string
  summary: string
  focus: string
  location_city: string
  location_region: string
  location_country: string
  url: string
  linkedin_url: string
  github_url: string
  languages: CvLanguage[]
  email: string
  phone: string
  personnummer: string
}
