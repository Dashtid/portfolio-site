#!/usr/bin/env node

/**
 * Link validator for portfolio site
 * Checks internal and external links for validity
 */

const fs = require('fs')
const path = require('path')
const https = require('https')
const http = require('http')
const { promisify } = require('util')
const { JSDOM } = require('jsdom')

const readFile = promisify(fs.readFile)

/**
 * Check if URL is reachable
 */
async function checkUrl(url, timeout = 10000) {
  return new Promise((resolve) => {
    const urlObj = new URL(url)
    const client = urlObj.protocol === 'https:' ? https : http
    
    const request = client.request({
      hostname: urlObj.hostname,
      port: urlObj.port,
      path: urlObj.pathname + urlObj.search,
      method: 'HEAD',
      timeout: timeout,
      headers: {
        'User-Agent': 'Mozilla/5.0 (compatible; LinkChecker/1.0)'
      }
    }, (response) => {
      resolve({
        url,
        status: response.statusCode,
        ok: response.statusCode >= 200 && response.statusCode < 400
      })
    })
    
    request.on('error', (error) => {
      resolve({
        url,
        status: 0,
        ok: false,
        error: error.message
      })
    })
    
    request.on('timeout', () => {
      request.destroy()
      resolve({
        url,
        status: 0,
        ok: false,
        error: 'Timeout'
      })
    })
    
    request.end()
  })
}

/**
 * Extract links from HTML content
 */
function extractLinks(html, baseUrl = '') {
  const dom = new JSDOM(html)
  const document = dom.window.document
  
  const links = []
  
  // Extract href links
  const aElements = document.querySelectorAll('a[href]')
  aElements.forEach(el => {
    const href = el.getAttribute('href')
    if (href && !href.startsWith('#') && !href.startsWith('mailto:') && !href.startsWith('tel:')) {
      links.push({
        type: 'link',
        url: href.startsWith('http') ? href : baseUrl + href,
        text: el.textContent.trim(),
        element: 'a'
      })
    }
  })
  
  // Extract image sources
  const imgElements = document.querySelectorAll('img[src]')
  imgElements.forEach(el => {
    const src = el.getAttribute('src')
    if (src) {
      links.push({
        type: 'image',
        url: src.startsWith('http') ? src : baseUrl + src,
        alt: el.getAttribute('alt') || '',
        element: 'img'
      })
    }
  })
  
  // Extract script sources
  const scriptElements = document.querySelectorAll('script[src]')
  scriptElements.forEach(el => {
    const src = el.getAttribute('src')
    if (src) {
      links.push({
        type: 'script',
        url: src.startsWith('http') ? src : baseUrl + src,
        element: 'script'
      })
    }
  })
  
  // Extract stylesheet links
  const linkElements = document.querySelectorAll('link[href]')
  linkElements.forEach(el => {
    const href = el.getAttribute('href')
    const rel = el.getAttribute('rel')
    if (href && (rel === 'stylesheet' || rel === 'preload')) {
      links.push({
        type: 'stylesheet',
        url: href.startsWith('http') ? href : baseUrl + href,
        rel: rel,
        element: 'link'
      })
    }
  })
  
  return links
}

/**
 * Check if file exists
 */
function fileExists(filePath) {
  try {
    return fs.existsSync(filePath)
  } catch {
    return false
  }
}

/**
 * Validate all links
 */
async function validateLinks() {
  try {
    console.log('🔗 Starting link validation...')
    
    const siteDir = path.join(__dirname, '..', 'site')
    const htmlFiles = fs.readdirSync(siteDir)
      .filter(file => file.endsWith('.html'))
    
    const allLinks = []
    const results = {
      valid: [],
      invalid: [],
      warnings: []
    }
    
    // Extract links from all HTML files
    for (const file of htmlFiles) {
      const filePath = path.join(siteDir, file)
      const content = await readFile(filePath, 'utf8')
      const links = extractLinks(content)
      
      links.forEach(link => {
        link.source = file
        allLinks.push(link)
      })
    }
    
    console.log(`📊 Found ${allLinks.length} links to validate`)
    
    // Group links by URL to avoid duplicate checks
    const uniqueUrls = [...new Set(allLinks.map(link => link.url))]
    const urlChecks = new Map()
    
    // Check external URLs
    const externalUrls = uniqueUrls.filter(url => url.startsWith('http'))
    console.log(`🌐 Checking ${externalUrls.length} external URLs...`)
    
    for (const url of externalUrls) {
      try {
        const result = await checkUrl(url)
        urlChecks.set(url, result)
        
        if (result.ok) {
          console.log(`✅ ${url}`)
        } else {
          console.log(`❌ ${url} (${result.status || result.error})`)
        }
      } catch (error) {
        console.log(`❌ ${url} (${error.message})`)
        urlChecks.set(url, { url, ok: false, error: error.message })
      }
    }
    
    // Check internal URLs
    const internalUrls = uniqueUrls.filter(url => !url.startsWith('http'))
    console.log(`🏠 Checking ${internalUrls.length} internal URLs...`)
    
    for (const url of internalUrls) {
      let filePath
      
      if (url.startsWith('/')) {
        filePath = path.join(siteDir, url.substring(1))
      } else {
        filePath = path.join(siteDir, url)
      }
      
      const exists = fileExists(filePath)
      urlChecks.set(url, { url, ok: exists })
      
      if (exists) {
        console.log(`✅ ${url}`)
      } else {
        console.log(`❌ ${url} (File not found)`)
      }
    }
    
    // Process results
    for (const link of allLinks) {
      const check = urlChecks.get(link.url)
      const result = {
        ...link,
        ...check
      }
      
      if (check.ok) {
        results.valid.push(result)
      } else {
        results.invalid.push(result)
      }
      
      // Check for common issues
      if (link.type === 'image' && !link.alt) {
        results.warnings.push({
          ...result,
          issue: 'Missing alt text'
        })
      }
      
      if (link.type === 'link' && link.url.startsWith('http://')) {
        results.warnings.push({
          ...result,
          issue: 'Using HTTP instead of HTTPS'
        })
      }
    }
    
    // Report results
    console.log('\n📊 Link Validation Results:')
    console.log(`✅ Valid links: ${results.valid.length}`)
    console.log(`❌ Invalid links: ${results.invalid.length}`)
    console.log(`⚠️  Warnings: ${results.warnings.length}`)
    
    if (results.invalid.length > 0) {
      console.log('\n❌ Invalid Links:')
      results.invalid.forEach(link => {
        console.log(`  ${link.url} (${link.source}) - ${link.error || link.status}`)
      })
    }
    
    if (results.warnings.length > 0) {
      console.log('\n⚠️  Warnings:')
      results.warnings.forEach(warning => {
        console.log(`  ${warning.url} (${warning.source}) - ${warning.issue}`)
      })
    }
    
    if (results.invalid.length === 0) {
      console.log('\n🎉 All links are valid!')
    } else {
      console.log(`\n💡 Fix ${results.invalid.length} invalid links before deployment`)
      process.exit(1)
    }
    
  } catch (error) {
    console.error('❌ Error validating links:', error)
    process.exit(1)
  }
}

// Run if called directly
if (require.main === module) {
  validateLinks()
}

module.exports = { validateLinks, checkUrl, extractLinks }