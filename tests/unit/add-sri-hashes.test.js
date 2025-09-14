/**
 * Unit tests for SRI hash addition script
 */

const { calculateSRIHash } = require('../../scripts/add-sri-hashes')
const { EventEmitter } = require('events')

// Mock all dependencies
jest.mock('fs', () => ({
  readdirSync: jest.fn(),
  readFile: jest.fn(),
  writeFile: jest.fn()
}))

jest.mock('path', () => ({
  join: jest.fn((...args) => args.join('/')),
  basename: jest.fn((filePath) => filePath.split('/').pop())
}))

jest.mock('crypto', () => ({
  createHash: jest.fn(() => ({
    update: jest.fn().mockReturnThis(),
    digest: jest.fn().mockReturnValue('mock-base64-hash')
  }))
}))

jest.mock('https', () => ({
  get: jest.fn()
}))

jest.mock('util', () => ({
  promisify: jest.fn((fn) => fn)
}))

describe('SRI Hash Script', () => {
  let mockConsole
  let fs, crypto, https
  let mockResponse, mockRequest

  beforeEach(() => {
    jest.clearAllMocks()

    // Get mocked modules
    fs = require('fs')
    crypto = require('crypto')
    https = require('https')

    // Mock console methods
    mockConsole = {
      log: jest.fn(),
      error: jest.fn(),
      warn: jest.fn()
    }
    global.console = { ...console, ...mockConsole }

    // Mock response and request objects
    mockResponse = new EventEmitter()
    mockResponse.statusCode = 200

    mockRequest = new EventEmitter()

    // Mock https.get
    https.get.mockImplementation((url, callback) => {
      setTimeout(() => callback(mockResponse), 0)
      return mockRequest
    })
  })

  describe('calculateSRIHash function', () => {
    test('should calculate SRI hash for valid URL', async () => {
      const url = 'https://example.com/script.js'
      const mockContent = 'console.log("Hello World");'

      // Simulate successful HTTP response
      setTimeout(() => {
        mockResponse.emit('data', Buffer.from(mockContent))
        mockResponse.emit('end')
      }, 10)

      const result = await calculateSRIHash(url)

      expect(result).toBe('sha384-mock-base64-hash')
      expect(https.get).toHaveBeenCalledWith(url, expect.any(Function))
      expect(crypto.createHash).toHaveBeenCalledWith('sha384')
    })

    test('should handle HTTP error status codes', async () => {
      const url = 'https://example.com/not-found.js'
      mockResponse.statusCode = 404

      await expect(calculateSRIHash(url)).rejects.toThrow(
        'HTTP 404 for https://example.com/not-found.js'
      )
    })

    test('should handle network errors', async () => {
      const url = 'https://example.com/script.js'

      // Simulate network error
      setTimeout(() => {
        mockRequest.emit('error', new Error('Network error'))
      }, 10)

      await expect(calculateSRIHash(url)).rejects.toThrow('Network error')
    })

    test('should handle response with multiple data chunks', async () => {
      const url = 'https://example.com/large-script.js'
      const chunk1 = 'console.log("Part 1");'
      const chunk2 = 'console.log("Part 2");'

      setTimeout(() => {
        mockResponse.emit('data', Buffer.from(chunk1))
        mockResponse.emit('data', Buffer.from(chunk2))
        mockResponse.emit('end')
      }, 10)

      const result = await calculateSRIHash(url)

      expect(result).toBe('sha384-mock-base64-hash')
      expect(crypto.createHash().update).toHaveBeenCalledWith(
        Buffer.concat([Buffer.from(chunk1), Buffer.from(chunk2)])
      )
    })

    test('should handle empty response', async () => {
      const url = 'https://example.com/empty.js'

      setTimeout(() => {
        mockResponse.emit('end')
      }, 10)

      const result = await calculateSRIHash(url)

      expect(result).toBe('sha384-mock-base64-hash')
    })

    test('should handle different HTTP status codes', async () => {
      const testCases = [
        { statusCode: 301, shouldReject: true },
        { statusCode: 302, shouldReject: true },
        { statusCode: 404, shouldReject: true },
        { statusCode: 500, shouldReject: true }
      ]

      for (const testCase of testCases) {
        mockResponse.statusCode = testCase.statusCode

        if (testCase.shouldReject) {
          await expect(
            calculateSRIHash('https://example.com/test.js')
          ).rejects.toThrow(
            `HTTP ${testCase.statusCode} for https://example.com/test.js`
          )
        }
      }
    })
  })

  describe('hash calculation', () => {
    test('should use SHA-384 algorithm', async () => {
      setTimeout(() => {
        mockResponse.emit('data', Buffer.from('test content'))
        mockResponse.emit('end')
      }, 10)

      await calculateSRIHash('https://example.com/test.js')

      expect(crypto.createHash).toHaveBeenCalledWith('sha384')
    })

    test('should update hash with complete content', async () => {
      const content = 'console.log("test content");'

      setTimeout(() => {
        mockResponse.emit('data', Buffer.from(content))
        mockResponse.emit('end')
      }, 10)

      await calculateSRIHash('https://example.com/test.js')

      const hashInstance = crypto.createHash()
      expect(hashInstance.update).toHaveBeenCalledWith(Buffer.from(content))
      expect(hashInstance.digest).toHaveBeenCalledWith('base64')
    })
  })

  describe('URL handling', () => {
    test('should handle various URL formats', async () => {
      const urls = [
        'https://cdn.example.com/script.js',
        'https://example.com/path/to/file.css',
        'https://subdomain.example.com/file.min.js'
      ]

      for (const url of urls) {
        setTimeout(() => {
          mockResponse.emit('data', Buffer.from('content'))
          mockResponse.emit('end')
        }, 10)

        const result = await calculateSRIHash(url)
        expect(result).toBe('sha384-mock-base64-hash')
        expect(https.get).toHaveBeenCalledWith(url, expect.any(Function))
      }
    })

    test('should handle URLs with query parameters', async () => {
      const url = 'https://example.com/script.js?version=1.2.3'

      setTimeout(() => {
        mockResponse.emit('data', Buffer.from('content'))
        mockResponse.emit('end')
      }, 10)

      const result = await calculateSRIHash(url)

      expect(result).toBe('sha384-mock-base64-hash')
      expect(https.get).toHaveBeenCalledWith(url, expect.any(Function))
    })
  })

  describe('error handling', () => {
    test('should handle timeout errors', async () => {
      setTimeout(() => {
        mockRequest.emit('timeout')
      }, 10)

      await expect(
        calculateSRIHash('https://example.com/test.js')
      ).rejects.toThrow()
    })

    test('should handle connection refused', async () => {
      setTimeout(() => {
        mockRequest.emit('error', new Error('ECONNREFUSED'))
      }, 10)

      await expect(
        calculateSRIHash('https://example.com/test.js')
      ).rejects.toThrow('ECONNREFUSED')
    })

    test('should handle DNS resolution errors', async () => {
      setTimeout(() => {
        mockRequest.emit('error', new Error('ENOTFOUND'))
      }, 10)

      await expect(
        calculateSRIHash('https://example.com/test.js')
      ).rejects.toThrow('ENOTFOUND')
    })
  })

  describe('response parsing', () => {
    test('should handle binary data correctly', async () => {
      const binaryData = Buffer.from([0x89, 0x50, 0x4e, 0x47]) // PNG header

      setTimeout(() => {
        mockResponse.emit('data', binaryData)
        mockResponse.emit('end')
      }, 10)

      const result = await calculateSRIHash('https://example.com/image.png')

      expect(result).toBe('sha384-mock-base64-hash')
      expect(crypto.createHash().update).toHaveBeenCalledWith(binaryData)
    })

    test('should accumulate multiple chunks correctly', async () => {
      const chunks = [
        Buffer.from('chunk1'),
        Buffer.from('chunk2'),
        Buffer.from('chunk3')
      ]

      setTimeout(() => {
        chunks.forEach((chunk) => mockResponse.emit('data', chunk))
        mockResponse.emit('end')
      }, 10)

      await calculateSRIHash('https://example.com/test.js')

      expect(crypto.createHash().update).toHaveBeenCalledWith(
        Buffer.concat(chunks)
      )
    })
  })

  describe('edge cases', () => {
    test('should handle very large responses', async () => {
      const largeContent = 'x'.repeat(1024 * 1024) // 1MB of data

      setTimeout(() => {
        mockResponse.emit('data', Buffer.from(largeContent))
        mockResponse.emit('end')
      }, 10)

      const result = await calculateSRIHash('https://example.com/large-file.js')

      expect(result).toBe('sha384-mock-base64-hash')
    })

    test('should handle response with no content-length header', async () => {
      setTimeout(() => {
        mockResponse.emit('data', Buffer.from('content without content-length'))
        mockResponse.emit('end')
      }, 10)

      const result = await calculateSRIHash('https://example.com/test.js')

      expect(result).toBe('sha384-mock-base64-hash')
    })
  })
})
