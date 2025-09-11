#!/usr/bin/env node

/**
 * Image optimization script
 * Converts images to WebP format and optimizes existing images
 */

const fs = require('fs')
const path = require('path')
const sharp = require('sharp')
const { promisify } = require('util')

const readdir = promisify(fs.readdir)
const stat = promisify(fs.stat)
const mkdir = promisify(fs.mkdir)

const SUPPORTED_FORMATS = ['.jpg', '.jpeg', '.png', '.tiff', '.gif']
const OUTPUT_FORMATS = {
  webp: { quality: 85, effort: 6 },
  jpeg: { quality: 85, progressive: true },
  png: { compressionLevel: 9, progressive: true }
}

/**
 * Get all image files recursively
 */
async function getImageFiles(dir, files = []) {
  const entries = await readdir(dir)
  
  for (const entry of entries) {
    const fullPath = path.join(dir, entry)
    const stats = await stat(fullPath)
    
    if (stats.isDirectory()) {
      await getImageFiles(fullPath, files)
    } else if (SUPPORTED_FORMATS.some(ext => entry.toLowerCase().endsWith(ext))) {
      files.push(fullPath)
    }
  }
  
  return files
}

/**
 * Optimize single image
 */
async function optimizeImage(inputPath, outputDir) {
  const filename = path.basename(inputPath, path.extname(inputPath))
  const originalStats = await stat(inputPath)
  const results = []
  
  try {
    // Create output directory if it doesn't exist
    await mkdir(outputDir, { recursive: true })
    
    console.log(`🖼️  Processing ${path.basename(inputPath)}...`)
    
    // Generate WebP version
    const webpPath = path.join(outputDir, `${filename}.webp`)
    await sharp(inputPath)
      .webp(OUTPUT_FORMATS.webp)
      .toFile(webpPath)
    
    const webpStats = await stat(webpPath)
    const webpSavings = ((originalStats.size - webpStats.size) / originalStats.size * 100).toFixed(1)
    
    results.push({
      format: 'WebP',
      path: webpPath,
      originalSize: originalStats.size,
      newSize: webpStats.size,
      savings: webpSavings
    })
    
    // Optimize original format
    const ext = path.extname(inputPath).toLowerCase()
    let outputPath, optimized
    
    if (ext === '.jpg' || ext === '.jpeg') {
      outputPath = path.join(outputDir, `${filename}.jpg`)
      optimized = sharp(inputPath).jpeg(OUTPUT_FORMATS.jpeg)
    } else if (ext === '.png') {
      outputPath = path.join(outputDir, `${filename}.png`)
      optimized = sharp(inputPath).png(OUTPUT_FORMATS.png)
    } else {
      // For other formats, just copy
      outputPath = path.join(outputDir, path.basename(inputPath))
      optimized = sharp(inputPath)
    }
    
    await optimized.toFile(outputPath)
    const optimizedStats = await stat(outputPath)
    const optimizedSavings = ((originalStats.size - optimizedStats.size) / originalStats.size * 100).toFixed(1)
    
    results.push({
      format: 'Optimized Original',
      path: outputPath,
      originalSize: originalStats.size,
      newSize: optimizedStats.size,
      savings: optimizedSavings
    })
    
    return results
    
  } catch (error) {
    console.error(`❌ Error processing ${inputPath}:`, error.message)
    return []
  }
}

/**
 * Update HTML files to use optimized images
 */
async function updateHtmlReferences(siteDir, optimizedDir) {
  console.log('📝 Updating HTML files...')
  
  const htmlFiles = fs.readdirSync(siteDir)
    .filter(file => file.endsWith('.html'))
    .map(file => path.join(siteDir, file))
  
  for (const htmlFile of htmlFiles) {
    let content = fs.readFileSync(htmlFile, 'utf8')
    let modified = false
    
    // Update image references to use picture element with WebP
    const imgRegex = /<img([^>]*src="[^"]*\.(jpg|jpeg|png)"[^>]*)>/gi
    
    content = content.replace(imgRegex, (match, attributes) => {
      const srcMatch = attributes.match(/src="([^"]*)"/)
      if (!srcMatch) return match
      
      const originalSrc = srcMatch[1]
      const filename = path.basename(originalSrc, path.extname(originalSrc))
      const webpSrc = originalSrc.replace(/\.(jpg|jpeg|png)$/i, '.webp')
      
      // Create picture element with WebP source
      const pictureElement = `<picture>
        <source srcset="${webpSrc}" type="image/webp">
        <img${attributes}>
      </picture>`
      
      modified = true
      return pictureElement
    })
    
    if (modified) {
      fs.writeFileSync(htmlFile, content, 'utf8')
      console.log(`✅ Updated ${path.basename(htmlFile)}`)
    }
  }
}

/**
 * Generate responsive image variants
 */
async function generateResponsiveVariants(inputPath, outputDir) {
  const filename = path.basename(inputPath, path.extname(inputPath))
  const sizes = [
    { width: 320, suffix: '-mobile' },
    { width: 768, suffix: '-tablet' },
    { width: 1200, suffix: '-desktop' },
    { width: 1920, suffix: '-large' }
  ]
  
  const image = sharp(inputPath)
  const metadata = await image.metadata()
  
  const variants = []
  
  for (const size of sizes) {
    if (metadata.width && metadata.width >= size.width) {
      // WebP variant
      const webpPath = path.join(outputDir, `${filename}${size.suffix}.webp`)
      await image
        .resize(size.width)
        .webp(OUTPUT_FORMATS.webp)
        .toFile(webpPath)
      
      // JPEG variant
      const jpegPath = path.join(outputDir, `${filename}${size.suffix}.jpg`)
      await image
        .resize(size.width)
        .jpeg(OUTPUT_FORMATS.jpeg)
        .toFile(jpegPath)
      
      variants.push({
        width: size.width,
        webp: webpPath,
        jpeg: jpegPath
      })
    }
  }
  
  return variants
}

/**
 * Main optimization function
 */
async function optimizeImages() {
  try {
    console.log('🚀 Starting image optimization...')
    
    const siteDir = path.join(__dirname, '..', 'site')
    const imagesDir = path.join(siteDir, 'static', 'images')
    const outputDir = path.join(siteDir, 'static', 'images', 'optimized')
    
    if (!fs.existsSync(imagesDir)) {
      console.log('📁 No images directory found, skipping optimization')
      return
    }
    
    // Get all image files
    const imageFiles = await getImageFiles(imagesDir)
    
    if (imageFiles.length === 0) {
      console.log('📷 No images found to optimize')
      return
    }
    
    console.log(`📊 Found ${imageFiles.length} images to optimize`)
    
    let totalOriginalSize = 0
    let totalOptimizedSize = 0
    const allResults = []
    
    // Process each image
    for (const imagePath of imageFiles) {
      const results = await optimizeImage(imagePath, outputDir)
      allResults.push(...results)
      
      // Generate responsive variants for hero images
      if (imagePath.includes('stockholm') || imagePath.includes('hero')) {
        console.log(`🖼️  Generating responsive variants for ${path.basename(imagePath)}...`)
        await generateResponsiveVariants(imagePath, outputDir)
      }
    }
    
    // Calculate total savings
    allResults.forEach(result => {
      totalOriginalSize += result.originalSize
      totalOptimizedSize += result.newSize
    })
    
    const totalSavings = ((totalOriginalSize - totalOptimizedSize) / totalOriginalSize * 100).toFixed(1)
    const savedBytes = totalOriginalSize - totalOptimizedSize
    
    // Update HTML files
    await updateHtmlReferences(siteDir, outputDir)
    
    // Report results
    console.log('\n📊 Optimization Results:')
    console.log(`📁 Original size: ${(totalOriginalSize / 1024 / 1024).toFixed(2)} MB`)
    console.log(`📁 Optimized size: ${(totalOptimizedSize / 1024 / 1024).toFixed(2)} MB`)
    console.log(`💾 Saved: ${(savedBytes / 1024 / 1024).toFixed(2)} MB (${totalSavings}%)`)
    console.log(`🖼️  Generated ${allResults.length} optimized images`)
    
    console.log('\n🎉 Image optimization completed successfully!')
    
  } catch (error) {
    console.error('❌ Error during image optimization:', error)
    process.exit(1)
  }
}

// Run if called directly
if (require.main === module) {
  optimizeImages()
}

module.exports = { optimizeImages, optimizeImage }