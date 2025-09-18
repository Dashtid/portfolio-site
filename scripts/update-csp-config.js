#!/usr/bin/env node
/* eslint-disable no-console */

/**
 * Update CSP configuration with current nonces
 * This script reads the generated nonces and updates the staticwebapp.config.json
 */

const fs = require('fs')
const path = require('path')

/**
 * Update CSP headers with current nonces
 */
async function updateCSPConfig() {
  console.log('🔧 Updating CSP configuration with current nonces...')

  try {
    // Read the current nonces
    const noncesPath = path.join(__dirname, '..', '.cache', 'csp-nonces.json')
    if (!fs.existsSync(noncesPath)) {
      console.log('❌ No nonces file found. Run add-csp-nonces.js first.')
      return false
    }

    const nonceData = JSON.parse(fs.readFileSync(noncesPath, 'utf8'))
    const { nonces } = nonceData

    // Read the current staticwebapp config
    const configPath = path.join(__dirname, '..', 'config', 'staticwebapp.config.json')
    const config = JSON.parse(fs.readFileSync(configPath, 'utf8'))

    // Update CSP header with current nonces
    const oldCSP = config.globalHeaders['Content-Security-Policy']

    // Replace nonce values in CSP
    let newCSP = oldCSP
      .replace(/'nonce-[^']*'/g, (match) => {
        if (match.includes('script')) return `'nonce-${nonces.script}'`
        if (match.includes('style')) return `'nonce-${nonces.style}'`
        return match
      })

    // If no nonces were found in CSP, add them
    if (!newCSP.includes('nonce-')) {
      newCSP = newCSP
        .replace(/script-src 'self'/, `script-src 'self' 'nonce-${nonces.script}'`)
        .replace(/style-src 'self'/, `style-src 'self' 'nonce-${nonces.style}'`)
    }

    config.globalHeaders['Content-Security-Policy'] = newCSP

    // Write updated config
    fs.writeFileSync(configPath, JSON.stringify(config, null, 2))

    console.log('✅ CSP configuration updated successfully!')
    console.log(`📄 Config updated: ${path.relative(process.cwd(), configPath)}`)
    console.log(`🔑 Script nonce: ${nonces.script}`)
    console.log(`🔑 Style nonce: ${nonces.style}`)

    return true
  } catch (error) {
    console.error('❌ Error updating CSP config:', error.message)
    return false
  }
}

/**
 * Main function
 */
async function main() {
  try {
    const success = await updateCSPConfig()
    if (!success) {
      process.exit(1)
    }
  } catch (error) {
    console.error('❌ Error:', error.message)
    process.exit(1)
  }
}

// Run if called directly
if (require.main === module) {
  main()
}

module.exports = { updateCSPConfig, main }