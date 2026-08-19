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
    /**
     * Headshot as a `data:` URI, served only inside this 401-gated payload —
     * never as a file on the public host. Empty when no photo is set.
     */
    image?: string
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
    location?: string
    startDate: string
    endDate: string
    courses?: string[]
    /** Verification link (e.g. a course certificate) when one is stored. */
    url?: string
  }>
  certificates: Array<{ name: string; date: string; issuer: string; url?: string }>
  skills: Array<{ name: string; keywords: string[] }>
  languages: CvLanguage[]
  /**
   * Övrigt / logistics one-liners (e.g. B-körkort), rendered LAST — a
   * separate section so they can never be presented as credentials.
   */
  other?: string[]
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
  other_items: string[]
  email: string
  phone: string
  personnummer: string
  /** Headshot as a `data:` URI (or empty). Private, like the contact fields. */
  photo: string
}
