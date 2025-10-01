/**
 * @jest-environment node
 */

/**
 * Unit tests for image optimization script
 */

const { optimizeImage } = require('../../scripts/optimize-images')

// Mock all dependencies
jest.mock('fs', () => ({
  existsSync: jest.fn(),
  readdirSync: jest.fn(),
  readFileSync: jest.fn(),
  writeFileSync: jest.fn(),
  readdir: jest.fn(),
  stat: jest.fn(),
  mkdir: jest.fn()
}))

jest.mock('path', () => ({
  join: jest.fn((...args) => args.join('/')),
  basename: jest.fn((filePath, ext) => {
    const base = filePath.split('/').pop()
    return ext ? base.replace(ext, '') : base
  }),
  extname: jest.fn(filePath => {
    const parts = filePath.split('.')
    return parts.length > 1 ? `.${parts.pop()}` : ''
  })
}))

jest.mock('sharp', () => {
  const mockSharpInstance = {
    webp: jest.fn().mockReturnThis(),
    jpeg: jest.fn().mockReturnThis(),
    png: jest.fn().mockReturnThis(),
    resize: jest.fn().mockReturnThis(),
    toFile: jest.fn().mockResolvedValue(),
    metadata: jest.fn().mockResolvedValue({ width: 1920, height: 1080 })
  }
  const sharpMock = jest.fn(() => mockSharpInstance)
  sharpMock.mockSharpInstance = mockSharpInstance
  return sharpMock
})

jest.mock('util', () => ({
  promisify: jest.fn(fn => fn)
}))

describe('Image Optimization Script', () => {
  let mockConsole
  let fs
  let sharp

  beforeEach(() => {
    jest.clearAllMocks()

    // Get mocked modules
    fs = require('fs')
    sharp = require('sharp')

    // Reset Sharp mock
    if (sharp.mockSharpInstance) {
      sharp.mockSharpInstance.webp.mockClear().mockReturnThis()
      sharp.mockSharpInstance.jpeg.mockClear().mockReturnThis()
      sharp.mockSharpInstance.png.mockClear().mockReturnThis()
      sharp.mockSharpInstance.resize.mockClear().mockReturnThis()
      sharp.mockSharpInstance.toFile.mockClear().mockResolvedValue()
      sharp.mockSharpInstance.metadata
        .mockClear()
        .mockResolvedValue({ width: 1920, height: 1080 })
    }

    // Mock console methods
    mockConsole = {
      log: jest.fn(),
      error: jest.fn()
    }
    global.console = { ...console, ...mockConsole }
  })

  describe('optimizeImage function', () => {
    test('should optimize JPEG image successfully', async () => {
      const inputPath = '/test/image.jpg'
      const outputDir = '/test/output'

      // Mock file stats
      fs.stat
        .mockResolvedValueOnce({ size: 1000000 }) // Original size
        .mockResolvedValueOnce({ size: 600000 }) // WebP size
        .mockResolvedValueOnce({ size: 700000 }) // Optimized JPEG size

      fs.mkdir.mockResolvedValue()

      const results = await optimizeImage(inputPath, outputDir)

      expect(results).toHaveLength(2)
      expect(results[0]).toEqual({
        format: 'WebP',
        path: '/test/output/image.webp',
        originalSize: 1000000,
        newSize: 600000,
        savings: '40.0'
      })
      expect(results[1]).toEqual({
        format: 'Optimized Original',
        path: '/test/output/image.jpg',
        originalSize: 1000000,
        newSize: 700000,
        savings: '30.0'
      })
    })

    test('should optimize PNG image successfully', async () => {
      const inputPath = '/test/image.png'
      const outputDir = '/test/output'

      fs.stat
        .mockResolvedValueOnce({ size: 800000 })
        .mockResolvedValueOnce({ size: 500000 })
        .mockResolvedValueOnce({ size: 600000 })

      fs.mkdir.mockResolvedValue()

      const results = await optimizeImage(inputPath, outputDir)

      expect(results).toHaveLength(2)
      const sharpInstance = sharp()
      expect(sharpInstance.png).toHaveBeenCalledWith({
        compressionLevel: 9,
        quality: 80,
        progressive: true
      })
    })

    test('should handle optimization errors gracefully', async () => {
      const inputPath = '/test/image.jpg'
      const outputDir = '/test/output'

      fs.stat.mockResolvedValueOnce({ size: 1000000 })
      fs.mkdir.mockResolvedValue()

      const sharpInstance = sharp()
      sharpInstance.toFile.mockRejectedValue(
        new Error('Sharp processing error')
      )

      const results = await optimizeImage(inputPath, outputDir)

      expect(results).toEqual([])
      expect(mockConsole.error).toHaveBeenCalledWith(
        expect.stringContaining('Error processing'),
        'Sharp processing error'
      )
    })

    test('should create output directory if it does not exist', async () => {
      const inputPath = '/test/image.jpg'
      const outputDir = '/test/new-output'

      fs.stat
        .mockResolvedValueOnce({ size: 1000000 })
        .mockResolvedValueOnce({ size: 600000 })
        .mockResolvedValueOnce({ size: 700000 })

      fs.mkdir.mockResolvedValue()

      await optimizeImage(inputPath, outputDir)

      expect(fs.mkdir).toHaveBeenCalledWith(outputDir, { recursive: true })
    })

    test('should handle different image formats', async () => {
      const formats = [
        { input: '/test/image.jpg', expectedCall: 'jpeg' },
        { input: '/test/image.jpeg', expectedCall: 'jpeg' },
        { input: '/test/image.png', expectedCall: 'png' },
        { input: '/test/image.tiff', expectedCall: null } // Unsupported format
      ]

      for (const format of formats) {
        // Reset mocks for each format
        sharp.mockSharpInstance.webp.mockClear().mockReturnThis()
        sharp.mockSharpInstance.jpeg.mockClear().mockReturnThis()
        sharp.mockSharpInstance.png.mockClear().mockReturnThis()
        sharp.mockSharpInstance.toFile.mockClear().mockResolvedValue()

        fs.stat
          .mockResolvedValueOnce({ size: 1000000 })
          .mockResolvedValueOnce({ size: 600000 })
          .mockResolvedValueOnce({ size: 700000 })

        fs.mkdir.mockResolvedValue()

        await optimizeImage(format.input, '/test/output')

        if (format.expectedCall === 'jpeg') {
          expect(sharp.mockSharpInstance.jpeg).toHaveBeenCalledWith({
            quality: 80,
            progressive: true,
            mozjpeg: true
          })
        } else if (format.expectedCall === 'png') {
          expect(sharp.mockSharpInstance.png).toHaveBeenCalledWith({
            compressionLevel: 9,
            quality: 80,
            progressive: true
          })
        } else {
          // For unsupported formats, neither jpeg nor png should be called
          expect(sharp.mockSharpInstance.jpeg).not.toHaveBeenCalled()
          expect(sharp.mockSharpInstance.png).not.toHaveBeenCalled()
        }
      }
    })
  })

  describe('Sharp configuration', () => {
    test('should use correct WebP settings', async () => {
      fs.stat.mockResolvedValue({ size: 1000000 })
      fs.mkdir.mockResolvedValue()

      await optimizeImage('/test/image.jpg', '/test/output')

      expect(sharp.mockSharpInstance.webp).toHaveBeenCalledWith({
        quality: 80,
        effort: 6
      })
    })

    test('should use correct JPEG settings', async () => {
      fs.stat.mockResolvedValue({ size: 1000000 })
      fs.mkdir.mockResolvedValue()

      await optimizeImage('/test/image.jpg', '/test/output')

      expect(sharp.mockSharpInstance.jpeg).toHaveBeenCalledWith({
        quality: 80,
        progressive: true,
        mozjpeg: true
      })
    })

    test('should call toFile twice for WebP and optimized original', async () => {
      fs.stat.mockResolvedValue({ size: 1000000 })
      fs.mkdir.mockResolvedValue()

      await optimizeImage('/test/image.jpg', '/test/output')

      expect(sharp.mockSharpInstance.toFile).toHaveBeenCalledTimes(2)
      expect(sharp.mockSharpInstance.toFile).toHaveBeenCalledWith(
        '/test/output/image.webp'
      )
      expect(sharp.mockSharpInstance.toFile).toHaveBeenCalledWith(
        '/test/output/image.jpg'
      )
    })
  })

  describe('file path handling', () => {
    test('should generate correct output paths', async () => {
      fs.stat
        .mockResolvedValueOnce({ size: 1000000 }) // Original
        .mockResolvedValueOnce({ size: 600000 }) // WebP
        .mockResolvedValueOnce({ size: 700000 }) // JPEG
      fs.mkdir.mockResolvedValue()

      const result = await optimizeImage('/path/to/my-image.jpg', '/output/dir')

      expect(result).toHaveLength(2)
      expect(result[0].path).toBe('/output/dir/my-image.webp')
      expect(result[1].path).toBe('/output/dir/my-image.jpg')
    })

    test('should handle images without extension', async () => {
      fs.stat
        .mockResolvedValueOnce({ size: 1000000 })
        .mockResolvedValueOnce({ size: 600000 })
        .mockResolvedValueOnce({ size: 700000 })
      fs.mkdir.mockResolvedValue()

      const result = await optimizeImage('/path/to/image', '/output/dir')

      expect(result).toHaveLength(2)
      expect(result[0].path).toBe('/output/dir/image.webp')
    })
  })

  describe('savings calculation', () => {
    test('should calculate savings percentage correctly', async () => {
      fs.stat
        .mockResolvedValueOnce({ size: 1000000 }) // Original: 1MB
        .mockResolvedValueOnce({ size: 500000 }) // WebP: 500KB (50% savings)
        .mockResolvedValueOnce({ size: 750000 }) // Optimized: 750KB (25% savings)

      fs.mkdir.mockResolvedValue()

      const results = await optimizeImage('/test/image.jpg', '/test/output')

      expect(results).toHaveLength(2)
      expect(results[0].savings).toBe('50.0')
      expect(results[1].savings).toBe('25.0')
    })

    test('should handle zero savings', async () => {
      fs.stat
        .mockResolvedValueOnce({ size: 1000000 }) // Original
        .mockResolvedValueOnce({ size: 1000000 }) // WebP same size
        .mockResolvedValueOnce({ size: 1000000 }) // Optimized same size

      fs.mkdir.mockResolvedValue()

      const results = await optimizeImage('/test/image.jpg', '/test/output')

      expect(results).toHaveLength(2)
      expect(results[0].savings).toBe('0.0')
      expect(results[1].savings).toBe('0.0')
    })
  })
})
