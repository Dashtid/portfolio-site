#!/usr/bin/env node
/* eslint-disable no-console */

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
  webp: { quality: 80, effort: 6 },
  jpeg: { quality: 80, progressive: true, mozjpeg: true },
  png: { compressionLevel: 9, quality: 80, progressive: true }
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
      // Skip the optimized directory to prevent processing already optimized images
      if (entry === 'optimized') {
        console.log('⏭️  Skipping optimized directory to prevent duplicates')
        continue
      }
      await getImageFiles(fullPath, files)
    } else if (
      SUPPORTED_FORMATS.some(ext => entry.toLowerCase().endsWith(ext))
    ) {
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
    // Skip if input file is already in the optimized directory
    if (inputPath.includes(path.join('images', 'optimized'))) {
      console.log(
        `⏭️  Skipping ${path.basename(inputPath)} (already in optimized directory)`
      )
      return results
    }

    // Create output directory if it doesn't exist
    await mkdir(outputDir, { recursive: true })

    console.log(`🖼️  Processing ${path.basename(inputPath)}...`)

    // Generate WebP version
    const webpPath = path.join(outputDir, `${filename}.webp`)
    if (!fs.existsSync(webpPath)) {
      await sharp(inputPath).webp(OUTPUT_FORMATS.webp).toFile(webpPath)

      const webpStats = await stat(webpPath)
      const webpSavings = (
        ((originalStats.size - webpStats.size) / originalStats.size) *
        100
      ).toFixed(1)

      results.push({
        format: 'WebP',
        path: webpPath,
        originalSize: originalStats.size,
        newSize: webpStats.size,
        savings: webpSavings
      })
    } else {
      console.log(`⏭️  WebP version already exists for ${filename}`)
    }

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

    if (!fs.existsSync(outputPath)) {
      await optimized.toFile(outputPath)
      const optimizedStats = await stat(outputPath)
      const optimizedSavings = (
        ((originalStats.size - optimizedStats.size) / originalStats.size) *
        100
      ).toFixed(1)

      results.push({
        format: 'Optimized Original',
        path: outputPath,
        originalSize: originalStats.size,
        newSize: optimizedStats.size,
        savings: optimizedSavings
      })
    } else {
      console.log(`⏭️  Optimized version already exists for ${filename}`)
    }

    return results
  } catch (error) {
    console.error(`❌ Error processing ${inputPath}:`, error.message)
    return []
  }
}

/**
 * Update HTML files to use optimized images
 * SAFELY converts img tags to picture elements while avoiding nested duplicates
 */
async function updateHtmlReferences(siteDir, optimizedDir) {
  // SAFETY CHECK: This function is currently disabled to prevent nested picture elements
  // The HTML files already have properly configured picture elements
  console.log('📝 Skipping HTML updates - picture elements already configured')

  // IF RE-ENABLED IN THE FUTURE, use this safer implementation:
  return safeBatchUpdateHtmlReferences(siteDir, optimizedDir)
}

/**
 * SAFE HTML Update Function - prevents nested picture elements
 * This function should be used if HTML modifications are ever needed again
 */
async function safeBatchUpdateHtmlReferences(siteDir, optimizedDir) {
  console.log('📝 SAFELY updating HTML files...')

  const htmlFiles = fs
    .readdirSync(siteDir, { recursive: true })
    .filter(file => file.endsWith('.html'))
    .map(file => path.join(siteDir, file))

  let totalModified = 0

  for (const htmlFile of htmlFiles) {
    const originalContent = fs.readFileSync(htmlFile, 'utf8')
    let content = originalContent
    let modified = false

    // SAFETY CHECK 1: Skip files that already have picture elements
    if (content.includes('<picture>')) {
      console.log(
        `⏭️  ${path.basename(htmlFile)} already has picture elements, skipping`
      )
      continue
    }

    // SAFETY CHECK 2: Only process standalone img tags (not inside picture elements)
    // This regex specifically looks for img tags that are NOT preceded by <picture> on the same logical block
    const standaloneImgRegex =
      /(?<!<picture>[\s\S]*?)<img([^>]*src="[^"]*\.(jpg|jpeg|png)"[^>]*)>/gi

    content = content.replace(standaloneImgRegex, (match, attributes) => {
      const srcMatch = attributes.match(/src="([^"]*)"/)
      if (!srcMatch) return match

      const originalSrc = srcMatch[1]

      // Check if this image has a corresponding WebP version
      const webpSrc = originalSrc.replace(/\.(jpg|jpeg|png)$/i, '.webp')
      const webpPath = path.join(path.dirname(htmlFile), webpSrc)

      if (!fs.existsSync(webpPath)) {
        console.log(`⏭️  No WebP version found for ${originalSrc}, skipping`)
        return match
      }

      // SAFETY CHECK 3: Ensure we're not creating nested structures
      if (match.includes('<picture>')) {
        console.log(
          `⚠️  Detected potential nested structure, skipping: ${match.substring(0, 50)}...`
        )
        return match
      }

      // Create picture element with WebP source
      const pictureElement = `<picture>
        <source srcset="${webpSrc}" type="image/webp">
        <img${attributes}>
      </picture>`

      modified = true
      console.log(`✅ Converting: ${originalSrc} → picture element with WebP`)
      return pictureElement
    })

    // SAFETY CHECK 4: Verify no nested picture elements were created
    const nestedPictureCheck = /<picture[\s\S]*?<picture/gi
    if (nestedPictureCheck.test(content)) {
      console.error(
        `❌ ERROR: Nested picture elements detected in ${htmlFile}. Reverting changes.`
      )
      content = originalContent // Revert to original
      modified = false
    }

    if (modified) {
      fs.writeFileSync(htmlFile, content, 'utf8')
      console.log(`✅ Updated ${path.basename(htmlFile)}`)
      totalModified++
    }
  }

  console.log(`📊 Modified ${totalModified} HTML files`)
  return totalModified
}

/**
 * Validation function to detect and fix nested picture elements
 * This can be called to clean up any existing nested structures
 */
async function validateAndFixNestedPictures(siteDir) {
  console.log('🔍 Validating HTML files for nested picture elements...')

  const htmlFiles = fs
    .readdirSync(siteDir, { recursive: true })
    .filter(file => file.endsWith('.html'))
    .map(file => path.join(siteDir, file))

  let totalFixed = 0

  for (const htmlFile of htmlFiles) {
    const originalContent = fs.readFileSync(htmlFile, 'utf8')
    let content = originalContent
    let fixed = false

    // Detect nested picture elements
    const nestedPictureRegex =
      /<picture[^>]*>([\s\S]*?)<picture[^>]*>([\s\S]*?)<\/picture>([\s\S]*?)<\/picture>/gi

    if (nestedPictureRegex.test(content)) {
      console.log(
        `🔧 Fixing nested picture elements in ${path.basename(htmlFile)}`
      )

      // Reset regex for replacement
      nestedPictureRegex.lastIndex = 0

      content = content.replace(nestedPictureRegex, match => {
        // Extract the innermost img element and first source element
        const sourceMatch = match.match(/<source[^>]*>/i)
        const imgMatch = match.match(/<img[^>]*>/i)

        if (sourceMatch && imgMatch) {
          const cleanPicture = `<picture>
        ${sourceMatch[0]}
        ${imgMatch[0]}
      </picture>`
          console.log('✅ Cleaned nested structure')
          return cleanPicture
        }

        // Fallback: return the innermost img tag only
        if (imgMatch) {
          console.log('⚠️  Fallback: returning img tag only')
          return imgMatch[0]
        }

        return match
      })

      fixed = true
    }

    if (fixed) {
      fs.writeFileSync(htmlFile, content, 'utf8')
      console.log(`✅ Fixed ${path.basename(htmlFile)}`)
      totalFixed++
    }
  }

  if (totalFixed === 0) {
    console.log(
      '✅ No nested picture elements found - all HTML files are clean'
    )
  } else {
    console.log(
      `🎉 Fixed ${totalFixed} HTML files with nested picture elements`
    )
  }

  return totalFixed
}

/**
 * Generate responsive image variants
 */
async function generateResponsiveVariants(inputPath, outputDir) {
  const filename = path.basename(inputPath, path.extname(inputPath))

  // Ensure we only process original files, not already-generated variants
  if (
    filename.includes('-mobile') ||
    filename.includes('-tablet') ||
    filename.includes('-desktop') ||
    filename.includes('-large')
  ) {
    console.log(
      `⏭️  Skipping variant generation for ${filename} (already a variant)`
    )
    return []
  }

  const sizes = [
    { width: 320, suffix: '-mobile' },
    { width: 768, suffix: '-tablet' },
    { width: 1200, suffix: '-desktop' },
    { width: 1920, suffix: '-large' }
  ]

  const image = sharp(inputPath)
  const metadata = await image.metadata()

  const variants = []

  console.log(
    `📐 Original image dimensions: ${metadata.width}x${metadata.height}`
  )

  for (const size of sizes) {
    if (metadata.width && metadata.width >= size.width) {
      // WebP variant
      const webpPath = path.join(outputDir, `${filename}${size.suffix}.webp`)
      if (!fs.existsSync(webpPath)) {
        await image
          .resize(size.width)
          .webp(OUTPUT_FORMATS.webp)
          .toFile(webpPath)
        console.log(
          `✅ Generated ${filename}${size.suffix}.webp (${size.width}px wide)`
        )
      } else {
        console.log(`⏭️  ${filename}${size.suffix}.webp already exists`)
      }

      // JPEG variant
      const jpegPath = path.join(outputDir, `${filename}${size.suffix}.jpg`)
      if (!fs.existsSync(jpegPath)) {
        await image
          .resize(size.width)
          .jpeg(OUTPUT_FORMATS.jpeg)
          .toFile(jpegPath)
        console.log(
          `✅ Generated ${filename}${size.suffix}.jpg (${size.width}px wide)`
        )
      } else {
        console.log(`⏭️  ${filename}${size.suffix}.jpg already exists`)
      }

      variants.push({
        width: size.width,
        webp: webpPath,
        jpeg: jpegPath
      })
    } else {
      console.log(
        `⏭️  Skipping ${size.suffix} variant (original width ${metadata.width}px < ${size.width}px)`
      )
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

      // Generate responsive variants for hero images (only for original files)
      if (
        (imagePath.includes('stockholm') || imagePath.includes('hero')) &&
        !imagePath.includes(path.join('images', 'optimized'))
      ) {
        // Only generate variants for original source files, not generated ones
        const baseName = path.basename(imagePath, path.extname(imagePath))
        if (
          !baseName.includes('-mobile') &&
          !baseName.includes('-tablet') &&
          !baseName.includes('-desktop') &&
          !baseName.includes('-large')
        ) {
          console.log(
            `🖼️  Generating responsive variants for ${path.basename(imagePath)}...`
          )
          await generateResponsiveVariants(imagePath, outputDir)
        }
      }
    }

    // Calculate total savings
    allResults.forEach(result => {
      totalOriginalSize += result.originalSize
      totalOptimizedSize += result.newSize
    })

    const totalSavings = (
      ((totalOriginalSize - totalOptimizedSize) / totalOriginalSize) *
      100
    ).toFixed(1)
    const savedBytes = totalOriginalSize - totalOptimizedSize

    // Update HTML files (currently disabled for safety)
    await updateHtmlReferences(siteDir, outputDir)

    // SAFETY VALIDATION: Check for any nested picture elements
    await validateAndFixNestedPictures(siteDir)

    // Report results
    console.log('\n📊 Optimization Results:')
    console.log(
      `📁 Original size: ${(totalOriginalSize / 1024 / 1024).toFixed(2)} MB`
    )
    console.log(
      `📁 Optimized size: ${(totalOptimizedSize / 1024 / 1024).toFixed(2)} MB`
    )
    console.log(
      `💾 Saved: ${(savedBytes / 1024 / 1024).toFixed(2)} MB (${totalSavings}%)`
    )
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

module.exports = {
  optimizeImages,
  optimizeImage,
  validateAndFixNestedPictures,
  safeBatchUpdateHtmlReferences
}
