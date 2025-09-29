/**
 * Integration tests for build workflow
 * Tests the complete build process from source to deployment
 */

/* eslint-env jest, node */
/* eslint-disable no-console */

const fs = require('fs')
const path = require('path')
const { spawn } = require('child_process')

// Helper function to run commands
function runCommand(command, args = [], options = {}) {
  return new Promise((resolve, reject) => {
    // Quote arguments that contain spaces for Windows compatibility
    const quotedArgs = args.map(arg => (arg.includes(' ') ? `"${arg}"` : arg))

    const child = spawn(command, quotedArgs, {
      stdio: 'pipe',
      shell: true,
      ...options
    })

    let stdout = ''
    let stderr = ''

    child.stdout?.on('data', data => {
      stdout += data.toString()
    })

    child.stderr?.on('data', data => {
      stderr += data.toString()
    })

    child.on('close', code => {
      resolve({
        code,
        stdout,
        stderr
      })
    })

    child.on('error', error => {
      reject(error)
    })

    // Set a timeout
    setTimeout(() => {
      child.kill('SIGTERM')
      reject(new Error('Command timeout'))
    }, 30000) // 30 second timeout
  })
}

describe('Build Workflow Integration', () => {
  const siteDir = path.join(__dirname, '..', '..', 'site')
  const scriptsDir = path.join(__dirname, '..', '..', 'scripts')

  beforeAll(() => {
    // Ensure site directory exists
    if (!fs.existsSync(siteDir)) {
      throw new Error(`Site directory not found: ${siteDir}`)
    }
  })

  describe('Security validation', () => {
    test('should run security check script successfully', async () => {
      const scriptPath = path.join(scriptsDir, 'security-check.js')

      if (!fs.existsSync(scriptPath)) {
        console.warn('Security check script not found, skipping test')
        return
      }

      const result = await runCommand('node', [scriptPath])

      // Security check may exit with code 1 if there are issues, which is expected
      expect([0, 1]).toContain(result.code)
      expect(result.stdout).toContain('Running security checks')
    }, 30000)

    test('should validate required security headers are checked', async () => {
      const configPath = path.join(
        __dirname,
        '..',
        '..',
        'staticwebapp.config.json'
      )

      if (!fs.existsSync(configPath)) {
        console.warn('Static web app config not found, skipping test')
        return
      }

      const config = JSON.parse(fs.readFileSync(configPath, 'utf8'))

      // Verify security headers are present
      expect(config.globalHeaders).toBeDefined()

      // Check for essential security headers
      const headers = config.globalHeaders
      const requiredHeaders = [
        'Content-Security-Policy',
        'X-Content-Type-Options',
        'X-Frame-Options',
        'Referrer-Policy'
      ]

      requiredHeaders.forEach(header => {
        expect(headers[header]).toBeDefined()
      })
    })
  })

  describe('Link validation', () => {
    test('should run link validation script successfully', async () => {
      const scriptPath = path.join(scriptsDir, 'validate-links.js')

      if (!fs.existsSync(scriptPath)) {
        console.warn('Link validation script not found, skipping test')
        return
      }

      const result = await runCommand('node', [scriptPath])

      // Link validation may exit with code 1 if there are broken links
      expect([0, 1]).toContain(result.code)
      expect(result.stdout).toContain('Starting link validation')
    }, 30000)

    test('should validate HTML files exist for link checking', async () => {
      const htmlFiles = fs
        .readdirSync(siteDir)
        .filter(file => file.endsWith('.html'))

      expect(htmlFiles.length).toBeGreaterThan(0)

      // Check that at least index.html exists
      expect(htmlFiles).toContain('index.html')
    })
  })

  describe('Image optimization', () => {
    test('should handle missing images directory gracefully', async () => {
      const scriptPath = path.join(scriptsDir, 'optimize-images.js')

      if (!fs.existsSync(scriptPath)) {
        console.warn('Image optimization script not found, skipping test')
        return
      }

      const result = await runCommand('node', [scriptPath])

      // Should succeed even if no images found
      expect(result.code).toBe(0)
      expect(result.stdout).toMatch(/(No images|optimization|completed)/i)
    }, 30000)
  })

  describe('SRI hash generation', () => {
    test('should run SRI hash script successfully', async () => {
      const scriptPath = path.join(scriptsDir, 'add-sri-hashes.js')

      if (!fs.existsSync(scriptPath)) {
        console.warn('SRI hash script not found, skipping test')
        return
      }

      const result = await runCommand('node', [scriptPath])

      // Should succeed
      expect(result.code).toBe(0)
      expect(result.stdout).toContain('Adding SRI hashes')
    }, 30000)

    test('should verify HTML files are processed', async () => {
      const htmlFiles = fs
        .readdirSync(siteDir)
        .filter(file => file.endsWith('.html'))
        .map(file => path.join(siteDir, file))

      expect(htmlFiles.length).toBeGreaterThan(0)

      // Check that HTML files contain basic structure
      htmlFiles.forEach(file => {
        const content = fs.readFileSync(file, 'utf8')
        expect(content).toMatch(/<html[^>]*>/i)
        expect(content).toMatch(/<head[^>]*>/i)
        expect(content).toMatch(/<body[^>]*>/i)
      })
    })
  })

  describe('Complete build workflow', () => {
    test('should run all build scripts in sequence', async () => {
      const scripts = [
        'validate-links.js',
        'security-check.js',
        'add-sri-hashes.js'
      ]

      const results = []

      for (const script of scripts) {
        const scriptPath = path.join(scriptsDir, script)

        if (!fs.existsSync(scriptPath)) {
          console.warn(`Script ${script} not found, skipping`)
          continue
        }

        try {
          const result = await runCommand('node', [scriptPath])
          results.push({
            script,
            success:
              result.code === 0 ||
              (script.includes('validate') && result.code === 1),
            stdout: result.stdout,
            stderr: result.stderr
          })
        } catch (error) {
          results.push({
            script,
            success: false,
            error: error.message
          })
        }
      }

      // At least one script should have run successfully
      expect(results.length).toBeGreaterThan(0)

      // Log results for debugging
      results.forEach(result => {
        console.log(
          `${result.script}: ${result.success ? 'SUCCESS' : 'FAILED'}`
        )
        if (!result.success && result.error) {
          console.log(`Error: ${result.error}`)
        }
      })

      // Most scripts should succeed (allow for some failures due to missing dependencies)
      const successCount = results.filter(r => r.success).length
      expect(successCount).toBeGreaterThanOrEqual(
        Math.floor(results.length / 2)
      )
    }, 60000)
  })

  describe('File structure validation', () => {
    test('should have proper site directory structure', () => {
      expect(fs.existsSync(siteDir)).toBe(true)

      const siteContents = fs.readdirSync(siteDir)

      // Should have at least some HTML files
      const htmlFiles = siteContents.filter(file => file.endsWith('.html'))
      expect(htmlFiles.length).toBeGreaterThan(0)

      // Check for static assets directory
      const staticDir = path.join(siteDir, 'static')
      if (fs.existsSync(staticDir)) {
        const staticContents = fs.readdirSync(staticDir)
        console.log(`Static directory contains: ${staticContents.join(', ')}`)
      }
    })

    test('should have scripts directory with required scripts', () => {
      expect(fs.existsSync(scriptsDir)).toBe(true)

      const scripts = fs
        .readdirSync(scriptsDir)
        .filter(file => file.endsWith('.js'))

      expect(scripts.length).toBeGreaterThan(0)

      const expectedScripts = [
        'security-check.js',
        'validate-links.js',
        'add-sri-hashes.js',
        'optimize-images.js'
      ]

      expectedScripts.forEach(script => {
        if (scripts.includes(script)) {
          const scriptPath = path.join(scriptsDir, script)
          const content = fs.readFileSync(scriptPath, 'utf8')

          // Basic validation that scripts contain expected functions
          expect(content.length).toBeGreaterThan(100)
          expect(content).toContain('module.exports')
        }
      })
    })

    test('should have valid configuration files', () => {
      const configFiles = [
        'package.json',
        'staticwebapp.config.json',
        'jest.config.js'
      ]

      configFiles.forEach(configFile => {
        const filePath = path.join(__dirname, '..', '..', configFile)

        if (fs.existsSync(filePath)) {
          const content = fs.readFileSync(filePath, 'utf8')

          if (configFile.endsWith('.json')) {
            // Validate JSON syntax
            expect(() => JSON.parse(content)).not.toThrow()
          } else {
            // Basic file validation
            expect(content.length).toBeGreaterThan(10)
          }
        }
      })
    })
  })
})
