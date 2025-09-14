/**
 * Unit Tests for Security Check Script
 * Tests security validation, header checking, and vulnerability detection
 */

const fs = require('fs')
const path = require('path')
const { runSecurityCheck } = require('../../scripts/security-check.js')

// Mock dependencies
jest.mock('fs')
jest.mock('path')

describe('Security Check Script', () => {
  let mockConsoleLog
  let mockConsoleError
  let mockProcessExit

  beforeEach(() => {
    // Mock console methods
    mockConsoleLog = jest.spyOn(console, 'log').mockImplementation()
    mockConsoleError = jest.spyOn(console, 'error').mockImplementation()
    mockProcessExit = jest.spyOn(process, 'exit').mockImplementation()

    // Reset all mocks
    jest.clearAllMocks()
  })

  afterEach(() => {
    mockConsoleLog.mockRestore()
    mockConsoleError.mockRestore()
    mockProcessExit.mockRestore()
  })

  describe('Security Header Validation', () => {
    test('should pass when all required security headers are present', async () => {
      const mockConfig = {
        globalHeaders: {
          'Content-Security-Policy':
            "default-src 'self'; upgrade-insecure-requests",
          'Strict-Transport-Security':
            'max-age=31536000; includeSubDomains; preload',
          'X-Content-Type-Options': 'nosniff',
          'X-Frame-Options': 'DENY',
          'Referrer-Policy': 'strict-origin-when-cross-origin'
        }
      }

      path.join.mockReturnValue('/mock/path/staticwebapp.config.json')
      fs.promises = {
        readFile: jest.fn().mockResolvedValue(JSON.stringify(mockConfig))
      }
      fs.readdirSync = jest.fn().mockReturnValue([])

      await runSecurityCheck()

      expect(mockConsoleLog).toHaveBeenCalledWith(
        '✅ No security issues found!'
      )
      expect(mockProcessExit).not.toHaveBeenCalled()
    })

    test('should detect missing Content-Security-Policy header', async () => {
      const mockConfig = {
        globalHeaders: {
          'X-Content-Type-Options': 'nosniff'
        }
      }

      path.join.mockReturnValue('/mock/path/staticwebapp.config.json')
      fs.promises = {
        readFile: jest.fn().mockResolvedValue(JSON.stringify(mockConfig))
      }
      fs.readdirSync = jest.fn().mockReturnValue([])

      await runSecurityCheck()

      expect(mockConsoleLog).toHaveBeenCalledWith(
        expect.stringContaining('Critical Issues')
      )
      expect(mockConsoleLog).toHaveBeenCalledWith(
        expect.stringContaining('Missing Content-Security-Policy header')
      )
      expect(mockProcessExit).toHaveBeenCalledWith(1)
    })

    test('should warn about unsafe CSP directives', async () => {
      const mockConfig = {
        globalHeaders: {
          'Content-Security-Policy': "default-src 'self' 'unsafe-inline'",
          'Strict-Transport-Security': 'max-age=31536000',
          'X-Content-Type-Options': 'nosniff',
          'X-Frame-Options': 'DENY',
          'Referrer-Policy': 'strict-origin-when-cross-origin'
        }
      }

      path.join.mockReturnValue('/mock/path/staticwebapp.config.json')
      fs.promises = {
        readFile: jest.fn().mockResolvedValue(JSON.stringify(mockConfig))
      }
      fs.readdirSync = jest.fn().mockReturnValue([])

      await runSecurityCheck()

      expect(mockConsoleLog).toHaveBeenCalledWith(
        expect.stringContaining('Warnings')
      )
      expect(mockConsoleLog).toHaveBeenCalledWith(
        expect.stringContaining('CSP contains unsafe-inline directive')
      )
    })

    test('should detect unsafe-eval in CSP as critical issue', async () => {
      const mockConfig = {
        globalHeaders: {
          'Content-Security-Policy': "default-src 'self' 'unsafe-eval'",
          'Strict-Transport-Security': 'max-age=31536000',
          'X-Content-Type-Options': 'nosniff',
          'X-Frame-Options': 'DENY',
          'Referrer-Policy': 'strict-origin-when-cross-origin'
        }
      }

      path.join.mockReturnValue('/mock/path/staticwebapp.config.json')
      fs.promises = {
        readFile: jest.fn().mockResolvedValue(JSON.stringify(mockConfig))
      }
      fs.readdirSync = jest.fn().mockReturnValue([])

      await runSecurityCheck()

      expect(mockConsoleLog).toHaveBeenCalledWith(
        expect.stringContaining('Critical Issues')
      )
      expect(mockConsoleLog).toHaveBeenCalledWith(
        expect.stringContaining('CSP contains unsafe-eval directive')
      )
      expect(mockProcessExit).toHaveBeenCalledWith(1)
    })

    test('should detect missing HSTS header', async () => {
      const mockConfig = {
        globalHeaders: {
          'Content-Security-Policy': "default-src 'self'",
          'X-Content-Type-Options': 'nosniff',
          'X-Frame-Options': 'DENY',
          'Referrer-Policy': 'strict-origin-when-cross-origin'
        }
      }

      path.join.mockReturnValue('/mock/path/staticwebapp.config.json')
      fs.promises = {
        readFile: jest.fn().mockResolvedValue(JSON.stringify(mockConfig))
      }
      fs.readdirSync = jest.fn().mockReturnValue([])

      await runSecurityCheck()

      expect(mockConsoleLog).toHaveBeenCalledWith(
        expect.stringContaining('Missing HSTS header')
      )
      expect(mockProcessExit).toHaveBeenCalledWith(1)
    })

    test('should warn about HSTS missing preload directive', async () => {
      const mockConfig = {
        globalHeaders: {
          'Content-Security-Policy': "default-src 'self'",
          'Strict-Transport-Security': 'max-age=31536000',
          'X-Content-Type-Options': 'nosniff',
          'X-Frame-Options': 'DENY',
          'Referrer-Policy': 'strict-origin-when-cross-origin'
        }
      }

      path.join.mockReturnValue('/mock/path/staticwebapp.config.json')
      fs.promises = {
        readFile: jest.fn().mockResolvedValue(JSON.stringify(mockConfig))
      }
      fs.readdirSync = jest.fn().mockReturnValue([])

      await runSecurityCheck()

      expect(mockConsoleLog).toHaveBeenCalledWith(
        expect.stringContaining('HSTS header missing preload directive')
      )
    })
  })

  describe('HTML Content Security Analysis', () => {
    test('should detect inline scripts without nonce', async () => {
      const mockConfig = {
        globalHeaders: {
          'Content-Security-Policy': "default-src 'self'",
          'Strict-Transport-Security': 'max-age=31536000; preload',
          'X-Content-Type-Options': 'nosniff',
          'X-Frame-Options': 'DENY',
          'Referrer-Policy': 'strict-origin-when-cross-origin'
        }
      }

      const htmlContent = `
        <html>
          <head><title>Test</title></head>
          <body>
            <script>console.log('inline script without nonce');</script>
          </body>
        </html>
      `

      path.join.mockReturnValue('/mock/path')
      fs.promises = {
        readFile: jest
          .fn()
          .mockResolvedValueOnce(JSON.stringify(mockConfig))
          .mockResolvedValueOnce(htmlContent)
      }
      fs.readdirSync = jest.fn().mockReturnValue(['index.html'])

      await runSecurityCheck()

      expect(mockConsoleLog).toHaveBeenCalledWith(
        expect.stringContaining('Inline script without nonce in index.html')
      )
    })

    test('should detect inline styles without nonce', async () => {
      const mockConfig = {
        globalHeaders: {
          'Content-Security-Policy': "default-src 'self'",
          'Strict-Transport-Security': 'max-age=31536000; preload',
          'X-Content-Type-Options': 'nosniff',
          'X-Frame-Options': 'DENY',
          'Referrer-Policy': 'strict-origin-when-cross-origin'
        }
      }

      const htmlContent = `
        <html>
          <head>
            <title>Test</title>
            <style>body { margin: 0; }</style>
          </head>
          <body></body>
        </html>
      `

      path.join.mockReturnValue('/mock/path')
      fs.promises = {
        readFile: jest
          .fn()
          .mockResolvedValueOnce(JSON.stringify(mockConfig))
          .mockResolvedValueOnce(htmlContent)
      }
      fs.readdirSync = jest.fn().mockReturnValue(['index.html'])

      await runSecurityCheck()

      expect(mockConsoleLog).toHaveBeenCalledWith(
        expect.stringContaining('Inline style without nonce in index.html')
      )
    })

    test('should allow JSON-LD scripts without nonce', async () => {
      const mockConfig = {
        globalHeaders: {
          'Content-Security-Policy': "default-src 'self'",
          'Strict-Transport-Security': 'max-age=31536000; preload',
          'X-Content-Type-Options': 'nosniff',
          'X-Frame-Options': 'DENY',
          'Referrer-Policy': 'strict-origin-when-cross-origin'
        }
      }

      const htmlContent = `
        <html>
          <head><title>Test</title></head>
          <body>
            <script type="application/ld+json">{"@context": "https://schema.org"}</script>
          </body>
        </html>
      `

      path.join.mockReturnValue('/mock/path')
      fs.promises = {
        readFile: jest
          .fn()
          .mockResolvedValueOnce(JSON.stringify(mockConfig))
          .mockResolvedValueOnce(htmlContent)
      }
      fs.readdirSync = jest.fn().mockReturnValue(['index.html'])

      await runSecurityCheck()

      expect(mockConsoleLog).not.toHaveBeenCalledWith(
        expect.stringContaining('Inline script without nonce')
      )
    })

    test('should detect external resources without SRI', async () => {
      const mockConfig = {
        globalHeaders: {
          'Content-Security-Policy': "default-src 'self'",
          'Strict-Transport-Security': 'max-age=31536000; preload',
          'X-Content-Type-Options': 'nosniff',
          'X-Frame-Options': 'DENY',
          'Referrer-Policy': 'strict-origin-when-cross-origin'
        }
      }

      const htmlContent = `
        <html>
          <head>
            <title>Test</title>
            <link rel="stylesheet" href="https://cdn.example.com/style.css">
            <script src="https://cdn.example.com/script.js"></script>
          </head>
          <body></body>
        </html>
      `

      path.join.mockReturnValue('/mock/path')
      fs.promises = {
        readFile: jest
          .fn()
          .mockResolvedValueOnce(JSON.stringify(mockConfig))
          .mockResolvedValueOnce(htmlContent)
      }
      fs.readdirSync = jest.fn().mockReturnValue(['index.html'])

      await runSecurityCheck()

      expect(mockConsoleLog).toHaveBeenCalledWith(
        expect.stringContaining('External resource without SRI')
      )
      expect(mockConsoleLog).toHaveBeenCalledWith(
        expect.stringContaining('External script without SRI')
      )
    })
  })

  describe('Package Security Analysis', () => {
    test('should detect dev dependencies in production', async () => {
      const mockConfig = {
        globalHeaders: {
          'Content-Security-Policy': "default-src 'self'",
          'Strict-Transport-Security': 'max-age=31536000; preload',
          'X-Content-Type-Options': 'nosniff',
          'X-Frame-Options': 'DENY',
          'Referrer-Policy': 'strict-origin-when-cross-origin'
        }
      }

      const mockPackage = {
        dependencies: {
          express: '^4.18.0',
          jest: '^29.0.0' // This should be in devDependencies
        }
      }

      path.join.mockReturnValue('/mock/path')
      fs.promises = {
        readFile: jest
          .fn()
          .mockResolvedValueOnce(JSON.stringify(mockConfig))
          .mockResolvedValueOnce(JSON.stringify(mockPackage))
      }
      fs.readdirSync = jest.fn().mockReturnValue([])
      fs.existsSync = jest.fn().mockReturnValue(true)

      await runSecurityCheck()

      expect(mockConsoleLog).toHaveBeenCalledWith(
        expect.stringContaining(
          'Dev dependency jest found in production dependencies'
        )
      )
    })

    test('should handle missing package.json gracefully', async () => {
      const mockConfig = {
        globalHeaders: {
          'Content-Security-Policy': "default-src 'self'",
          'Strict-Transport-Security': 'max-age=31536000; preload',
          'X-Content-Type-Options': 'nosniff',
          'X-Frame-Options': 'DENY',
          'Referrer-Policy': 'strict-origin-when-cross-origin'
        }
      }

      path.join.mockReturnValue('/mock/path')
      fs.promises = {
        readFile: jest.fn().mockResolvedValue(JSON.stringify(mockConfig))
      }
      fs.readdirSync = jest.fn().mockReturnValue([])
      fs.existsSync = jest.fn().mockReturnValue(false)

      await runSecurityCheck()

      expect(mockProcessExit).not.toHaveBeenCalled()
    })
  })

  describe('Error Handling', () => {
    test('should handle missing config file', async () => {
      path.join.mockReturnValue('/mock/path/staticwebapp.config.json')
      fs.promises = {
        readFile: jest.fn().mockRejectedValue(new Error('File not found'))
      }

      await runSecurityCheck()

      expect(mockConsoleError).toHaveBeenCalledWith(
        '❌ Error running security check:',
        expect.any(Error)
      )
      expect(mockProcessExit).toHaveBeenCalledWith(1)
    })

    test('should handle malformed JSON config', async () => {
      path.join.mockReturnValue('/mock/path/staticwebapp.config.json')
      fs.promises = {
        readFile: jest.fn().mockResolvedValue('invalid json {')
      }

      await runSecurityCheck()

      expect(mockConsoleError).toHaveBeenCalledWith(
        '❌ Error running security check:',
        expect.any(Error)
      )
      expect(mockProcessExit).toHaveBeenCalledWith(1)
    })

    test('should handle file read errors for HTML files', async () => {
      const mockConfig = {
        globalHeaders: {
          'Content-Security-Policy': "default-src 'self'",
          'Strict-Transport-Security': 'max-age=31536000; preload',
          'X-Content-Type-Options': 'nosniff',
          'X-Frame-Options': 'DENY',
          'Referrer-Policy': 'strict-origin-when-cross-origin'
        }
      }

      path.join.mockReturnValue('/mock/path')
      fs.promises = {
        readFile: jest
          .fn()
          .mockResolvedValueOnce(JSON.stringify(mockConfig))
          .mockRejectedValueOnce(new Error('Cannot read HTML file'))
      }
      fs.readdirSync = jest.fn().mockReturnValue(['index.html'])

      await runSecurityCheck()

      expect(mockConsoleError).toHaveBeenCalledWith(
        '❌ Error running security check:',
        expect.any(Error)
      )
      expect(mockProcessExit).toHaveBeenCalledWith(1)
    })
  })

  describe('Security Report Generation', () => {
    test.skip('should generate proper summary with counts', async () => {
      const mockConfig = {
        globalHeaders: {
          'Content-Security-Policy': "default-src 'self' 'unsafe-inline'",
          'X-Content-Type-Options': 'nosniff'
          // Missing several required headers
        }
      }

      path.join.mockReturnValue('/mock/path')
      fs.promises = {
        readFile: jest.fn().mockResolvedValue(JSON.stringify(mockConfig))
      }
      fs.readdirSync = jest.fn().mockReturnValue([])

      await runSecurityCheck()

      // Should show summary with issue and warning counts
      expect(mockConsoleLog).toHaveBeenCalledWith(
        expect.stringMatching(/📈 Summary: \d+ issues, \d+ warnings/)
      )
    }, 15000)

    test.skip('should show success message when no issues found', async () => {
      const mockConfig = {
        globalHeaders: {
          'Content-Security-Policy':
            "default-src 'self'; upgrade-insecure-requests",
          'Strict-Transport-Security':
            'max-age=31536000; includeSubDomains; preload',
          'X-Content-Type-Options': 'nosniff',
          'X-Frame-Options': 'DENY',
          'Referrer-Policy': 'strict-origin-when-cross-origin'
        }
      }

      path.join.mockReturnValue('/mock/path')
      fs.promises = {
        readFile: jest.fn().mockResolvedValue(JSON.stringify(mockConfig))
      }
      fs.readdirSync = jest.fn().mockReturnValue([])

      await runSecurityCheck()

      expect(mockConsoleLog).toHaveBeenCalledWith(
        '✅ No security issues found!'
      )
      expect(mockConsoleLog).toHaveBeenCalledWith(
        '📈 Summary: 0 issues, 0 warnings'
      )
    }, 15000)
  })

  describe('Integration Tests', () => {
    test.skip('should handle real-world config with mixed issues', async () => {
      const mockConfig = {
        globalHeaders: {
          'Content-Security-Policy':
            "default-src 'self' 'unsafe-inline'; upgrade-insecure-requests",
          'Strict-Transport-Security': 'max-age=31536000', // Missing preload
          'X-Content-Type-Options': 'nosniff'
          // Missing X-Frame-Options and Referrer-Policy
        }
      }

      const htmlContent = `
        <html>
          <head>
            <title>Test</title>
            <link rel="stylesheet" href="https://cdn.example.com/style.css">
            <script nonce="abc123">console.log('safe');</script>
          </head>
          <body>
            <script>console.log('unsafe');</script>
          </body>
        </html>
      `

      path.join.mockReturnValue('/mock/path')
      fs.promises = {
        readFile: jest
          .fn()
          .mockResolvedValueOnce(JSON.stringify(mockConfig))
          .mockResolvedValueOnce(htmlContent)
      }
      fs.readdirSync = jest.fn().mockReturnValue(['index.html'])

      await runSecurityCheck()

      // Should detect critical issues (missing headers)
      expect(mockConsoleLog).toHaveBeenCalledWith(
        expect.stringContaining('Critical Issues')
      )

      // Should detect warnings (unsafe-inline, HSTS without preload, etc.)
      expect(mockConsoleLog).toHaveBeenCalledWith(
        expect.stringContaining('Warnings')
      )

      // Should exit with failure due to critical issues
      expect(mockProcessExit).toHaveBeenCalledWith(1)
    }, 15000)
  })
})
