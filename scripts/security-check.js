#!/usr/bin/env node

/**
 * Security checker for portfolio site
 * Validates security headers, checks for vulnerabilities, etc.
 */

const fs = require('fs')
const path = require('path')
const { promisify } = require('util')

const readFile = promisify(fs.readFile)

/**
 * Check for potential security issues
 */
async function runSecurityCheck() {
  console.log('🔒 Running security checks...')

  const issues = []
  const warnings = []

  try {
    // Check staticwebapp.config.json
    const configPath = path.join(
      __dirname,
      '..',
      'config',
      'staticwebapp.config.json'
    )
    const config = JSON.parse(await readFile(configPath, 'utf8'))

    // Check CSP
    const csp = config.globalHeaders['Content-Security-Policy']
    if (!csp) {
      issues.push('Missing Content-Security-Policy header')
    } else {
      if (csp.includes("'unsafe-inline'")) {
        warnings.push('CSP contains unsafe-inline directive')
      }
      if (csp.includes("'unsafe-eval'")) {
        issues.push('CSP contains unsafe-eval directive')
      }
      if (!csp.includes('upgrade-insecure-requests')) {
        warnings.push('CSP missing upgrade-insecure-requests')
      }
    }

    // Check HSTS
    const hsts = config.globalHeaders['Strict-Transport-Security']
    if (!hsts) {
      issues.push('Missing HSTS header')
    } else if (!hsts.includes('preload')) {
      warnings.push('HSTS header missing preload directive')
    }

    // Check other security headers
    const requiredHeaders = [
      'X-Content-Type-Options',
      'X-Frame-Options',
      'Referrer-Policy'
    ]

    for (const header of requiredHeaders) {
      if (!config.globalHeaders[header]) {
        issues.push(`Missing ${header} header`)
      }
    }

    // Check HTML files for security issues
    const siteDir = path.join(__dirname, '..', 'site')
    const htmlFiles = fs
      .readdirSync(siteDir)
      .filter((file) => file.endsWith('.html'))

    for (const file of htmlFiles) {
      const content = await readFile(path.join(siteDir, file), 'utf8')

      // Check for inline scripts without nonce
      const inlineScripts = content.match(/<script(?![^>]*src=)[^>]*>/g) || []
      for (const script of inlineScripts) {
        if (
          !script.includes('nonce=') &&
          !script.includes('type="application/ld+json"')
        ) {
          warnings.push(`Inline script without nonce in ${file}`)
        }
      }

      // Check for inline styles without nonce
      const inlineStyles = content.match(/<style[^>]*>/g) || []
      for (const style of inlineStyles) {
        if (!style.includes('nonce=')) {
          warnings.push(`Inline style without nonce in ${file}`)
        }
      }

      // Check for external resources without SRI
      const externalLinks =
        content.match(/<link[^>]*href="https?:\/\/[^"]*"[^>]*>/g) || []
      const externalScripts =
        content.match(/<script[^>]*src="https?:\/\/[^"]*"[^>]*>/g) || []

      for (const link of externalLinks) {
        const url = link.match(/href="([^"]*)"/)?.[1]

        // Skip self-referencing canonical URLs and known 404 resources
        const skipSRI = [
          'https://dashti.se', // Canonical self-reference
          'https://fonts.gstatic.com/s/segoui/v1/segoui.woff2' // Known 404 font URL
        ]

        if (!link.includes('integrity=') && !skipSRI.includes(url)) {
          warnings.push(
            `External resource without SRI in ${file}: ${url}`
          )
        }
      }

      for (const script of externalScripts) {
        if (!script.includes('integrity=')) {
          warnings.push(
            `External script without SRI in ${file}: ${script.match(/src="([^"]*)"/)?.[1]}`
          )
        }
      }
    }

    // Check package.json for vulnerable dependencies
    const packagePath = path.join(__dirname, '..', 'package.json')
    if (fs.existsSync(packagePath)) {
      const pkg = JSON.parse(await readFile(packagePath, 'utf8'))

      // Check for dev dependencies in production
      if (pkg.dependencies) {
        const devOnlyPackages = ['nodemon', 'webpack-dev-server', 'jest']
        for (const devPkg of devOnlyPackages) {
          if (pkg.dependencies[devPkg]) {
            warnings.push(
              `Dev dependency ${devPkg} found in production dependencies`
            )
          }
        }
      }
    }

    // Report results
    console.log('\n📊 Security Check Results:')

    if (issues.length === 0 && warnings.length === 0) {
      console.log('✅ No security issues found!')
    } else {
      if (issues.length > 0) {
        console.log('\n🚨 Critical Issues:')
        issues.forEach((issue) => console.log(`  ❌ ${issue}`))
      }

      if (warnings.length > 0) {
        console.log('\n⚠️  Warnings:')
        warnings.forEach((warning) => console.log(`  ⚠️  ${warning}`))
      }
    }

    console.log(
      `\n📈 Summary: ${issues.length} issues, ${warnings.length} warnings`
    )

    if (issues.length > 0) {
      console.log('\n💡 Fix critical issues before deployment!')
      process.exit(1)
    }
  } catch (error) {
    console.error('❌ Error running security check:', error)
    process.exit(1)
  }
}

// Run if called directly
if (require.main === module) {
  runSecurityCheck()
}

module.exports = { runSecurityCheck }
