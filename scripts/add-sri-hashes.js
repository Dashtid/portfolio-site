#!/usr/bin/env node

/**
 * Add Subresource Integrity (SRI) hashes to external resources
 */

const fs = require('fs')
const path = require('path')
const crypto = require('crypto')
const https = require('https')
const { promisify } = require('util')

const readFile = promisify(fs.readFile)
const writeFile = promisify(fs.writeFile)

// External resources that need SRI hashes
const externalResources = [
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js',
  'https://repowidget.vercel.app/assets/js/repoWidget.min.js'
]

/**
 * Fetch resource and calculate SRI hash
 */
async function calculateSRIHash(url) {
  return new Promise((resolve, reject) => {
    https.get(url, (response) => {
      if (response.statusCode !== 200) {
        reject(new Error(`HTTP ${response.statusCode} for ${url}`))
        return
      }

      const chunks = []
      response.on('data', chunk => chunks.push(chunk))
      response.on('end', () => {
        const content = Buffer.concat(chunks)
        const hash = crypto
          .createHash('sha384')
          .update(content)
          .digest('base64')
        
        resolve(`sha384-${hash}`)
      })
    }).on('error', reject)
  })
}

/**
 * Process HTML files and add SRI hashes
 */
async function addSRIHashes() {
  try {
    console.log('🔐 Adding SRI hashes to external resources...')
    
    // Calculate hashes for external resources
    const hashes = new Map()
    for (const url of externalResources) {
      try {
        console.log(`📦 Calculating hash for ${url}`)
        const hash = await calculateSRIHash(url)
        hashes.set(url, hash)
        console.log(`✅ ${url}: ${hash.substring(0, 20)}...`)
      } catch (error) {
        console.warn(`⚠️  Failed to calculate hash for ${url}:`, error.message)
      }
    }

    // Find all HTML files
    const siteDir = path.join(__dirname, '..', 'site')
    const htmlFiles = fs.readdirSync(siteDir)
      .filter(file => file.endsWith('.html'))
      .map(file => path.join(siteDir, file))

    // Process each HTML file
    for (const htmlFile of htmlFiles) {
      console.log(`📝 Processing ${path.basename(htmlFile)}`)
      
      let content = await readFile(htmlFile, 'utf8')
      let modified = false

      // Add SRI to CSS links
      content = content.replace(
        /<link[^>]*href="([^"]*)"[^>]*>/g,
        (match, href) => {
          if (hashes.has(href) && !match.includes('integrity=')) {
            const hash = hashes.get(href)
            const updated = match.replace(
              /\/>/,
              ` integrity="${hash}" crossorigin="anonymous" />`
            )
            modified = true
            return updated
          }
          return match
        }
      )

      // Add SRI to script tags
      content = content.replace(
        /<script[^>]*src="([^"]*)"[^>]*>/g,
        (match, src) => {
          if (hashes.has(src) && !match.includes('integrity=')) {
            const hash = hashes.get(src)
            const updated = match.replace(
              />/,
              ` integrity="${hash}" crossorigin="anonymous">`
            )
            modified = true
            return updated
          }
          return match
        }
      )

      if (modified) {
        await writeFile(htmlFile, content, 'utf8')
        console.log(`✅ Updated ${path.basename(htmlFile)}`)
      }
    }

    console.log('🎉 SRI hashes added successfully!')
    
  } catch (error) {
    console.error('❌ Error adding SRI hashes:', error)
    process.exit(1)
  }
}

// Run if called directly
if (require.main === module) {
  addSRIHashes()
}

module.exports = { addSRIHashes, calculateSRIHash }