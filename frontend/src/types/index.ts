/**
 * Central Type Exports
 *
 * All application types are exported from here for easy importing.
 * Types are inferred from Zod schemas for single source of truth.
 */

export type {
  Company,
  Education,
  Project,
  Skill,
  Document,
  User,
  LoginRequest,
  LoginResponse,
  HealthResponse,
  ErrorResponse
} from '@/schemas/api.schemas'
