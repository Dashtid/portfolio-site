#!/usr/bin/env node
/* eslint-disable no-console */

/**
 * Add CSP nonces to inline scripts and styles
 * This script generates cryptographically secure nonces and adds them to inline content
 */

const fs = require('fs')
const path = require('path')
const crypto = require('crypto')

/**
 * Generate a cryptographically secure nonce
 */
function generateNonce() {
  return crypto.randomBytes(16).toString('base64')
}

/**
 * Add nonces to HTML files
 */
async function addCSPNonces(siteDir) {
  console.log('🔐 Adding CSP nonces to inline scripts and styles...')

  const htmlFiles = fs
    .readdirSync(siteDir, { recursive: true })
    .filter(file => file.endsWith('.html'))
    .map(file => path.join(siteDir, file))

  const nonces = {
    style: generateNonce(),
    script: generateNonce()
  }

  console.log('🔑 Generated nonces:')
  console.log(`   Style nonce: ${nonces.style}`)
  console.log(`   Script nonce: ${nonces.script}`)

  for (const htmlFile of htmlFiles) {
    const originalContent = fs.readFileSync(htmlFile, 'utf8')
    let content = originalContent
    let modified = false

    // Add nonce to inline style tags
    content = content.replace(/<style(\s[^>]*)?>/gi, (match, attributes) => {
      // Replace existing nonce or add new one
      if (match.includes('nonce=')) {
        const withoutNonce = match.replace(/\s*nonce="[^"]*"/, '')
        modified = true
        return withoutNonce.replace('>', ` nonce="${nonces.style}">`)
      }
      modified = true
      const attrs = attributes || ''
      return `<style${attrs} nonce="${nonces.style}">`
    })

    // Add nonce to inline script tags (but not external scripts or JSON-LD)
    content = content.replace(/<script(\s[^>]*)?>/gi, (match, attributes) => {
      // Replace existing nonce or add new one
      if (match.includes('nonce=')) {
        const withoutNonce = match.replace(/\s*nonce="[^"]*"/, '')
        return withoutNonce.replace('>', ` nonce="${nonces.script}">`)
      }

      // Skip external scripts (those with src attribute)
      if (match.includes('src=')) {
        return match
      }

      // Skip JSON-LD scripts (structured data)
      if (match.includes('type="application/ld+json"')) {
        return match
      }

      modified = true
      const attrs = attributes || ''
      return `<script${attrs} nonce="${nonces.script}">`
    })

    if (modified) {
      fs.writeFileSync(htmlFile, content, 'utf8')
      console.log(`✅ Added nonces to ${path.basename(htmlFile)}`)
    } else {
      console.log(`⏭️  No changes needed for ${path.basename(htmlFile)}`)
    }
  }

  // Create a nonce configuration file for reference
  const nonceConfig = {
    generated: new Date().toISOString(),
    nonces,
    note: 'These nonces should be used in your CSP headers'
  }

  const configPath = path.join(siteDir, '..', '.cache', 'csp-nonces.json')
  fs.mkdirSync(path.dirname(configPath), { recursive: true })
  fs.writeFileSync(configPath, JSON.stringify(nonceConfig, null, 2))

  console.log(
    `📄 Nonce configuration saved to: ${path.relative(process.cwd(), configPath)}`
  )
  console.log('\n💡 CSP Header Example:')
  console.log(
    `Content-Security-Policy: script-src 'self' 'nonce-${nonces.script}' https://repowidget.vercel.app; style-src 'self' 'nonce-${nonces.style}' https://cdn.jsdelivr.net https://fonts.gstatic.com; font-src 'self' https://fonts.gstatic.com;`
  )

  return nonces
}

/**
 * Main function
 */
async function main() {
  try {
    const siteDir = path.join(__dirname, '..', 'site')
    const nonces = await addCSPNonces(siteDir)

    console.log('\n🎉 CSP nonces added successfully!')
    console.log('💡 Remember to update your CSP headers with these nonces')

    return nonces
  } catch (error) {
    console.error('❌ Error adding CSP nonces:', error.message)
    process.exit(1)
  }
}

// Run if called directly
if (require.main === module) {
  main()
}

module.exports = { addCSPNonces, generateNonce, main }
