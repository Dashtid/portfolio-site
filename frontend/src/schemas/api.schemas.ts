/**
 * Zod Schemas for API Response Validation
 *
 * These schemas provide runtime validation for API responses,
 * ensuring data integrity and catching backend/API contract changes early.
 *
 * Usage:
 * ```ts
 * import { CompanySchema, validateApiResponse } from '@/schemas/api.schemas'
 *
 * const response = await apiClient.get('/api/v1/companies')
 * const companies = validateApiResponse(CompanyArraySchema, response.data)
 * ```
 */

import { z } from 'zod'

// ============================================================================
// Company/Experience Schemas
// ============================================================================

export const CompanySchema = z.object({
  id: z.string(),
  name: z.string(),
  title: z.string(),
  description: z.string(),
  detailed_description: z.string().nullable().optional(),
  logo_url: z.string().nullable().optional(),
  start_date: z.string(),
  end_date: z.string().nullable().optional(),
  location: z.string().nullable().optional(),
  website: z.string().nullable().optional(),
  video_url: z.string().nullable().optional(),
  video_title: z.string().nullable().optional(),
  map_url: z.string().nullable().optional(),
  map_title: z.string().nullable().optional(),
  technologies: z.array(z.string()).nullable().optional(),
  responsibilities: z.array(z.string()).nullable().optional()
})

export const CompanyArraySchema = z.array(CompanySchema)

export const CompanyCreateSchema = CompanySchema.omit({ id: true })
export const CompanyUpdateSchema = CompanySchema.partial().omit({ id: true })

// ============================================================================
// Education Schemas
// ============================================================================

export const EducationSchema = z.object({
  id: z.string(),
  institution: z.string(),
  degree: z.string(),
  field_of_study: z.string(),
  start_date: z.string(),
  end_date: z.string().nullable().optional(),
  description: z.string().nullable().optional(),
  location: z.string().nullable().optional(),
  logo_url: z.string().nullable().optional()
})

export const EducationArraySchema = z.array(EducationSchema)

export const EducationCreateSchema = EducationSchema.omit({ id: true })
export const EducationUpdateSchema = EducationSchema.partial().omit({ id: true })

// ============================================================================
// Project Schemas
// ============================================================================

export const ProjectSchema = z.object({
  id: z.string(),
  name: z.string(),
  description: z.string(),
  detailed_description: z.string().nullable().optional(),
  technologies: z.array(z.string()),
  github_url: z.string().nullable().optional(),
  live_url: z.string().nullable().optional(),
  image_url: z.string().nullable().optional(),
  company_id: z.string().nullable().optional(),
  featured: z.boolean(),
  order_index: z.number().optional(),
  video_url: z.string().nullable().optional(),
  video_title: z.string().nullable().optional(),
  map_url: z.string().nullable().optional(),
  map_title: z.string().nullable().optional(),
  responsibilities: z.string().nullable().optional(),
  created_at: z.string().optional(),
  updated_at: z.string().nullable().optional()
})

export const ProjectArraySchema = z.array(ProjectSchema)

export const ProjectCreateSchema = ProjectSchema.omit({ id: true })
export const ProjectUpdateSchema = ProjectSchema.partial().omit({ id: true })

// ============================================================================
// Skill Schemas
// ============================================================================

export const SkillSchema = z.object({
  id: z.string(),
  name: z.string(),
  category: z.string(),
  proficiency_level: z.number().min(0).max(100),
  years_of_experience: z.number().nullable().optional()
})

export const SkillArraySchema = z.array(SkillSchema)

export const SkillCreateSchema = SkillSchema.omit({ id: true })
export const SkillUpdateSchema = SkillSchema.partial().omit({ id: true })

// ============================================================================
// Document Schemas
// ============================================================================

export const DocumentSchema = z.object({
  id: z.string(),
  title: z.string(),
  description: z.string().nullable().optional(),
  document_type: z.string(),
  file_path: z.string(),
  file_size: z.number(),
  file_url: z.string(),
  published_date: z.string().nullable().optional(),
  created_at: z.string()
})

export const DocumentArraySchema = z.array(DocumentSchema)

// ============================================================================
// Auth Schemas
// ============================================================================

export const UserSchema = z.object({
  id: z.string(),
  username: z.string(),
  name: z.string().nullable().optional(),
  email: z.string().nullable().optional(),
  avatar_url: z.string().nullable().optional(),
  github_id: z.string().nullable().optional()
})

export const LoginResponseSchema = z.object({
  access_token: z.string(),
  refresh_token: z.string().optional(),
  token_type: z.string(),
  user: UserSchema.optional()
})

export const TokenRefreshResponseSchema = z.object({
  access_token: z.string(),
  refresh_token: z.string().optional(),
  token_type: z.string()
})

// ============================================================================
// Health & Status Schemas
// ============================================================================

export const HealthResponseSchema = z.object({
  status: z.string(),
  service: z.string(),
  version: z.string()
})

// ============================================================================
// Error Schemas
// ============================================================================

export const ErrorResponseSchema = z.object({
  detail: z.string().or(
    z.array(
      z.object({
        loc: z.array(z.string().or(z.number())),
        msg: z.string(),
        type: z.string()
      })
    )
  )
})

// ============================================================================
// Validation Utilities
// ============================================================================

/**
 * ValidationError class for schema validation failures
 */
export class ApiValidationError extends Error {
  public errors: z.ZodError

  constructor(message: string, errors: z.ZodError) {
    super(message)
    this.name = 'ApiValidationError'
    this.errors = errors
  }
}

/**
 * Validate API response data against a schema
 *
 * @param schema - Zod schema to validate against
 * @param data - Data to validate
 * @param options - Validation options
 * @returns Validated and typed data
 * @throws ApiValidationError if validation fails
 *
 * @example
 * ```ts
 * const companies = validateApiResponse(CompanyArraySchema, response.data)
 * ```
 */
export function validateApiResponse<T extends z.ZodTypeAny>(
  schema: T,
  data: unknown,
  options: { strict?: boolean } = {}
): z.infer<T> {
  const { strict = true } = options

  const result = schema.safeParse(data)

  if (!result.success) {
    if (strict) {
      console.error('[API Validation] Schema validation failed:', {
        issues: result.error.issues,
        data
      })
      throw new ApiValidationError(
        `API response validation failed: ${result.error.message}`,
        result.error
      )
    }

    // In non-strict mode, log warning and return data as-is
    console.warn('[API Validation] Schema validation failed (non-strict mode):', {
      issues: result.error.issues
    })
    return data as z.infer<T>
  }

  return result.data
}

/**
 * Safe validation that returns a result object instead of throwing
 *
 * @param schema - Zod schema to validate against
 * @param data - Data to validate
 * @returns Result object with success flag and data or errors
 *
 * @example
 * ```ts
 * const result = safeValidateApiResponse(CompanySchema, data)
 * if (result.success) {
 *   console.log(result.data)
 * } else {
 *   console.error(result.errors)
 * }
 * ```
 */
export function safeValidateApiResponse<T extends z.ZodTypeAny>(
  schema: T,
  data: unknown
): { success: true; data: z.infer<T> } | { success: false; errors: z.ZodError } {
  const result = schema.safeParse(data)

  if (result.success) {
    return { success: true, data: result.data }
  }

  return { success: false, errors: result.error }
}

/**
 * Create a validated API client wrapper
 *
 * @param schema - Zod schema for response validation
 * @returns Function that validates the response
 *
 * @example
 * ```ts
 * const validateCompanies = createValidator(CompanyArraySchema)
 * const response = await apiClient.get('/api/v1/companies')
 * const companies = validateCompanies(response.data)
 * ```
 */
export function createValidator<T extends z.ZodTypeAny>(schema: T) {
  return (data: unknown): z.infer<T> => validateApiResponse(schema, data)
}

// ============================================================================
// Type Exports (inferred from schemas)
// ============================================================================

export type Company = z.infer<typeof CompanySchema>
export type Education = z.infer<typeof EducationSchema>
export type Project = z.infer<typeof ProjectSchema>
export type Skill = z.infer<typeof SkillSchema>
export type Document = z.infer<typeof DocumentSchema>
export type User = z.infer<typeof UserSchema>
export type LoginResponse = z.infer<typeof LoginResponseSchema>
export type HealthResponse = z.infer<typeof HealthResponseSchema>
export type ErrorResponse = z.infer<typeof ErrorResponseSchema>
