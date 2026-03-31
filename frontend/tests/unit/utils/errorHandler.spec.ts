/**
 * Tests for errorHandler utility
 */
/* eslint-disable @typescript-eslint/no-explicit-any */
import { describe, it, expect } from 'vitest'
import { getUserMessage } from '@/utils/errorHandler'

describe('getUserMessage', () => {
  it('returns string directly', () => {
    expect(getUserMessage('Test message')).toBe('Test message')
  })

  it('returns custom userMessage if present', () => {
    const error = {
      message: 'Technical error',
      userMessage: 'User-friendly message'
    } as any

    expect(getUserMessage(error)).toBe('User-friendly message')
  })

  it('returns response data message', () => {
    const error = {
      response: {
        data: {
          message: 'API error message'
        }
      }
    } as any

    expect(getUserMessage(error)).toBe('API error message')
  })

  it('returns FastAPI detail string', () => {
    const error = {
      response: {
        data: {
          detail: 'FastAPI validation error'
        }
      }
    } as any

    expect(getUserMessage(error)).toBe('FastAPI validation error')
  })

  it('joins FastAPI detail array', () => {
    const error = {
      response: {
        data: {
          detail: [{ msg: 'Field 1 error' }, { msg: 'Field 2 error' }]
        }
      }
    } as any

    expect(getUserMessage(error)).toBe('Field 1 error, Field 2 error')
  })

  it('returns status-based message for 404', () => {
    const error = {
      response: { status: 404 }
    } as any

    expect(getUserMessage(error)).toBe('The requested resource was not found.')
  })

  it('returns status-based message for 500', () => {
    const error = {
      response: { status: 500 }
    } as any

    expect(getUserMessage(error)).toBe('Server error. Please try again later.')
  })

  it('returns error message as fallback', () => {
    const error = {
      message: 'Fallback message'
    } as any

    expect(getUserMessage(error)).toBe('Fallback message')
  })
})
