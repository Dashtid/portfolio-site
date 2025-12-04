import { describe, it, expect, vi, beforeEach } from 'vitest'
import {
  CompanySchema,
  CompanyArraySchema,
  EducationSchema,
  ProjectSchema,
  SkillSchema,
  DocumentSchema,
  UserSchema,
  LoginResponseSchema,
  HealthResponseSchema,
  ErrorResponseSchema,
  validateApiResponse,
  safeValidateApiResponse,
  createValidator,
  ApiValidationError
} from '@/schemas/api.schemas'

describe('API Schemas', () => {
  describe('CompanySchema', () => {
    const validCompany = {
      id: '1',
      name: 'Test Company',
      title: 'Software Engineer',
      description: 'Test description',
      start_date: '2020-01-01'
    }

    it('should validate a valid company', () => {
      const result = CompanySchema.safeParse(validCompany)
      expect(result.success).toBe(true)
    })

    it('should validate a company with optional fields', () => {
      const companyWithOptionals = {
        ...validCompany,
        end_date: '2022-12-31',
        location: 'Stockholm, Sweden',
        technologies: ['Python', 'FastAPI'],
        responsibilities: ['Lead development', 'Code review']
      }

      const result = CompanySchema.safeParse(companyWithOptionals)
      expect(result.success).toBe(true)
    })

    it('should accept null for nullable fields', () => {
      const companyWithNulls = {
        ...validCompany,
        end_date: null,
        location: null,
        technologies: null
      }

      const result = CompanySchema.safeParse(companyWithNulls)
      expect(result.success).toBe(true)
    })

    it('should reject invalid company - missing required fields', () => {
      const invalidCompany = {
        id: '1',
        name: 'Test Company'
        // missing title, description, start_date
      }

      const result = CompanySchema.safeParse(invalidCompany)
      expect(result.success).toBe(false)
    })

    it('should reject invalid company - wrong types', () => {
      const invalidCompany = {
        ...validCompany,
        id: 123 // should be string
      }

      const result = CompanySchema.safeParse(invalidCompany)
      expect(result.success).toBe(false)
    })
  })

  describe('CompanyArraySchema', () => {
    it('should validate an array of companies', () => {
      const companies = [
        {
          id: '1',
          name: 'Company A',
          title: 'Engineer',
          description: 'Desc A',
          start_date: '2020-01-01'
        },
        {
          id: '2',
          name: 'Company B',
          title: 'Manager',
          description: 'Desc B',
          start_date: '2021-01-01'
        }
      ]

      const result = CompanyArraySchema.safeParse(companies)
      expect(result.success).toBe(true)
    })

    it('should validate empty array', () => {
      const result = CompanyArraySchema.safeParse([])
      expect(result.success).toBe(true)
    })

    it('should reject if one company is invalid', () => {
      const companies = [
        {
          id: '1',
          name: 'Company A',
          title: 'Engineer',
          description: 'Desc A',
          start_date: '2020-01-01'
        },
        {
          id: 2, // invalid - should be string
          name: 'Company B'
        }
      ]

      const result = CompanyArraySchema.safeParse(companies)
      expect(result.success).toBe(false)
    })
  })

  describe('EducationSchema', () => {
    const validEducation = {
      id: '1',
      institution: 'University',
      degree: 'BSc',
      field_of_study: 'Computer Science',
      start_date: '2015-09-01'
    }

    it('should validate valid education', () => {
      const result = EducationSchema.safeParse(validEducation)
      expect(result.success).toBe(true)
    })

    it('should validate with optional fields', () => {
      const education = {
        ...validEducation,
        end_date: '2019-06-15',
        description: 'Graduated with honors',
        location: 'Stockholm'
      }

      const result = EducationSchema.safeParse(education)
      expect(result.success).toBe(true)
    })

    it('should reject missing required fields', () => {
      const invalid = {
        id: '1',
        institution: 'University'
        // missing degree, field_of_study, start_date
      }

      const result = EducationSchema.safeParse(invalid)
      expect(result.success).toBe(false)
    })
  })

  describe('ProjectSchema', () => {
    const validProject = {
      id: '1',
      name: 'Test Project',
      description: 'Project description',
      technologies: ['Vue.js', 'TypeScript'],
      featured: true
    }

    it('should validate valid project', () => {
      const result = ProjectSchema.safeParse(validProject)
      expect(result.success).toBe(true)
    })

    it('should validate with optional fields', () => {
      const project = {
        ...validProject,
        github_url: 'https://github.com/test/project',
        live_url: 'https://example.com',
        order_index: 1
      }

      const result = ProjectSchema.safeParse(project)
      expect(result.success).toBe(true)
    })

    it('should require technologies array', () => {
      const invalid = {
        ...validProject,
        technologies: 'not-an-array'
      }

      const result = ProjectSchema.safeParse(invalid)
      expect(result.success).toBe(false)
    })

    it('should require featured boolean', () => {
      const invalid = {
        ...validProject,
        featured: 'yes' // should be boolean
      }

      const result = ProjectSchema.safeParse(invalid)
      expect(result.success).toBe(false)
    })
  })

  describe('SkillSchema', () => {
    const validSkill = {
      id: '1',
      name: 'Python',
      category: 'Programming Languages',
      proficiency_level: 90
    }

    it('should validate valid skill', () => {
      const result = SkillSchema.safeParse(validSkill)
      expect(result.success).toBe(true)
    })

    it('should accept proficiency between 0 and 100', () => {
      const skill0 = { ...validSkill, proficiency_level: 0 }
      const skill100 = { ...validSkill, proficiency_level: 100 }

      expect(SkillSchema.safeParse(skill0).success).toBe(true)
      expect(SkillSchema.safeParse(skill100).success).toBe(true)
    })

    it('should reject proficiency below 0', () => {
      const invalid = { ...validSkill, proficiency_level: -1 }
      const result = SkillSchema.safeParse(invalid)
      expect(result.success).toBe(false)
    })

    it('should reject proficiency above 100', () => {
      const invalid = { ...validSkill, proficiency_level: 101 }
      const result = SkillSchema.safeParse(invalid)
      expect(result.success).toBe(false)
    })
  })

  describe('DocumentSchema', () => {
    const validDocument = {
      id: '1',
      title: 'Resume',
      document_type: 'pdf',
      file_path: '/documents/resume.pdf',
      file_size: 1024,
      file_url: 'https://example.com/resume.pdf',
      created_at: '2024-01-15T10:00:00Z'
    }

    it('should validate valid document', () => {
      const result = DocumentSchema.safeParse(validDocument)
      expect(result.success).toBe(true)
    })

    it('should require file_size to be number', () => {
      const invalid = { ...validDocument, file_size: '1024' }
      const result = DocumentSchema.safeParse(invalid)
      expect(result.success).toBe(false)
    })
  })

  describe('UserSchema', () => {
    const validUser = {
      id: '1',
      username: 'testuser'
    }

    it('should validate minimal user', () => {
      const result = UserSchema.safeParse(validUser)
      expect(result.success).toBe(true)
    })

    it('should validate full user', () => {
      const fullUser = {
        ...validUser,
        name: 'Test User',
        email: 'test@example.com',
        avatar_url: 'https://example.com/avatar.png',
        github_id: '12345'
      }

      const result = UserSchema.safeParse(fullUser)
      expect(result.success).toBe(true)
    })
  })

  describe('LoginResponseSchema', () => {
    it('should validate valid login response', () => {
      const response = {
        access_token: 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...',
        token_type: 'bearer'
      }

      const result = LoginResponseSchema.safeParse(response)
      expect(result.success).toBe(true)
    })

    it('should validate with optional refresh_token', () => {
      const response = {
        access_token: 'access',
        refresh_token: 'refresh',
        token_type: 'bearer'
      }

      const result = LoginResponseSchema.safeParse(response)
      expect(result.success).toBe(true)
    })
  })

  describe('HealthResponseSchema', () => {
    it('should validate health response', () => {
      const response = {
        status: 'healthy',
        service: 'portfolio-api',
        version: '1.0.0'
      }

      const result = HealthResponseSchema.safeParse(response)
      expect(result.success).toBe(true)
    })
  })

  describe('ErrorResponseSchema', () => {
    it('should validate simple error', () => {
      const error = { detail: 'Not found' }
      const result = ErrorResponseSchema.safeParse(error)
      expect(result.success).toBe(true)
    })

    it('should validate validation error array', () => {
      const error = {
        detail: [{ loc: ['body', 'name'], msg: 'field required', type: 'value_error.missing' }]
      }

      const result = ErrorResponseSchema.safeParse(error)
      expect(result.success).toBe(true)
    })
  })
})

describe('Validation Utilities', () => {
  describe('validateApiResponse', () => {
    const validCompany = {
      id: '1',
      name: 'Test',
      title: 'Engineer',
      description: 'Desc',
      start_date: '2020-01-01'
    }

    it('should return validated data for valid input', () => {
      const result = validateApiResponse(CompanySchema, validCompany)
      expect(result).toEqual(validCompany)
    })

    it('should throw ApiValidationError for invalid input', () => {
      const invalid = { id: 1 }

      expect(() => validateApiResponse(CompanySchema, invalid)).toThrow(ApiValidationError)
    })

    it('should not throw in non-strict mode', () => {
      const consoleSpy = vi.spyOn(console, 'warn').mockImplementation(() => {})
      const invalid = { id: 1 }

      const result = validateApiResponse(CompanySchema, invalid, { strict: false })
      expect(result).toEqual(invalid)
      expect(consoleSpy).toHaveBeenCalled()

      consoleSpy.mockRestore()
    })
  })

  describe('safeValidateApiResponse', () => {
    const validSkill = {
      id: '1',
      name: 'Python',
      category: 'Languages',
      proficiency_level: 90
    }

    it('should return success result for valid data', () => {
      const result = safeValidateApiResponse(SkillSchema, validSkill)
      expect(result.success).toBe(true)
      if (result.success) {
        expect(result.data).toEqual(validSkill)
      }
    })

    it('should return error result for invalid data', () => {
      const invalid = { id: 1 }
      const result = safeValidateApiResponse(SkillSchema, invalid)
      expect(result.success).toBe(false)
      if (!result.success) {
        expect(result.errors).toBeDefined()
      }
    })
  })

  describe('createValidator', () => {
    it('should create a reusable validator function', () => {
      const validateEducation = createValidator(EducationSchema)

      const validData = {
        id: '1',
        institution: 'Uni',
        degree: 'BSc',
        field_of_study: 'CS',
        start_date: '2020-01-01'
      }

      const result = validateEducation(validData)
      expect(result).toEqual(validData)
    })

    it('should throw for invalid data', () => {
      const validateProject = createValidator(ProjectSchema)

      expect(() => validateProject({})).toThrow(ApiValidationError)
    })
  })

  describe('ApiValidationError', () => {
    it('should have correct name and errors property', () => {
      const parseResult = CompanySchema.safeParse({})
      if (!parseResult.success) {
        const error = new ApiValidationError('Test error', parseResult.error)

        expect(error.name).toBe('ApiValidationError')
        expect(error.message).toBe('Test error')
        expect(error.errors).toBe(parseResult.error)
      }
    })
  })
})
