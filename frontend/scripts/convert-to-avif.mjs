#!/usr/bin/env node
/**
 * Convert images to AVIF format for better compression
 * AVIF provides 30-50% better compression than WebP
 */

import sharp from 'sharp'
import { readdir, stat } from 'fs/promises'
import { join, parse } from 'path'
import { fileURLToPath } from 'url'
import { dirname } from 'path'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)

const IMAGES_DIR = join(__dirname, '../public/images')
const OPTIMIZED_DIR = join(IMAGES_DIR, 'optimized')

// AVIF quality settings (0-100, higher = better quality, larger file)
// Lower quality for hero backgrounds, higher for logos/portraits
const AVIF_QUALITY_HERO = 50 // Hero backgrounds can use lower quality
const AVIF_QUALITY_LOGO = 75 // Logos need higher quality for crisp edges

// Images to convert with quality settings
const IMAGES_TO_CONVERT = [
  // Hero image - convert from original JPEG for best results
  { src: 'optimized/stockholm-mobile.jpg', quality: AVIF_QUALITY_HERO },
  { src: 'optimized/stockholm-tablet.jpg', quality: AVIF_QUALITY_HERO },
  { src: 'optimized/stockholm-desktop.jpg', quality: AVIF_QUALITY_HERO },
  { src: 'optimized/stockholm-large.jpg', quality: AVIF_QUALITY_HERO },
  // Company logos - from original formats
  { src: 'hermes.jpg', quality: AVIF_QUALITY_LOGO, outDir: 'optimized' },
  { src: 'karolinska.jpg', quality: AVIF_QUALITY_LOGO, outDir: 'optimized' },
  { src: 'philips.jpeg', quality: AVIF_QUALITY_LOGO, outDir: 'optimized' },
  { src: 'softpro.jpg', quality: AVIF_QUALITY_LOGO, outDir: 'optimized' },
  // Education logos
  { src: 'KTH.png', quality: AVIF_QUALITY_LOGO, outDir: 'optimized' },
  { src: 'LTH.png', quality: AVIF_QUALITY_LOGO, outDir: 'optimized' },
  // Other
  { src: 'cropped.png', quality: AVIF_QUALITY_LOGO, outDir: 'optimized' },
  { src: 'CompTIA.png', quality: AVIF_QUALITY_LOGO, outDir: 'optimized' },
  { src: 'FDF.png', quality: AVIF_QUALITY_LOGO, outDir: 'optimized' },
  { src: 'foretagsuniversitet.png', quality: AVIF_QUALITY_LOGO, outDir: 'optimized' },
  { src: 'sös.png', quality: AVIF_QUALITY_LOGO, outDir: 'optimized' }
]

async function convertToAvif(inputPath, outputPath, quality = 65) {
  try {
    const inputStats = await stat(inputPath)

    await sharp(inputPath)
      .avif({ quality, effort: 6 }) // effort 6 = better compression
      .toFile(outputPath)

    const outputStats = await stat(outputPath)
    const savings = ((inputStats.size - outputStats.size) / inputStats.size * 100).toFixed(1)

    console.log(`[+] ${parse(inputPath).base} -> ${parse(outputPath).base}`)
    console.log(`    ${(inputStats.size / 1024).toFixed(1)}KB -> ${(outputStats.size / 1024).toFixed(1)}KB (${savings}% smaller)`)

    return { input: inputStats.size, output: outputStats.size }
  } catch (error) {
    console.error(`[-] Failed to convert ${inputPath}: ${error.message}`)
    return null
  }
}

async function main() {
  console.log('='.repeat(60))
  console.log('AVIF Image Conversion')
  console.log('='.repeat(60))
  console.log(`Hero quality: ${AVIF_QUALITY_HERO}, Logo quality: ${AVIF_QUALITY_LOGO}`)
  console.log(`Source: ${IMAGES_DIR}`)
  console.log('')

  let totalInputSize = 0
  let totalOutputSize = 0
  let successCount = 0
  let failCount = 0

  for (const imageConfig of IMAGES_TO_CONVERT) {
    const inputPath = join(IMAGES_DIR, imageConfig.src)
    const parsed = parse(inputPath)
    const outDir = imageConfig.outDir ? join(IMAGES_DIR, imageConfig.outDir) : parsed.dir
    const outputPath = join(outDir, `${parsed.name}.avif`)

    const result = await convertToAvif(inputPath, outputPath, imageConfig.quality)
    if (result) {
      totalInputSize += result.input
      totalOutputSize += result.output
      successCount++
    } else {
      failCount++
    }
  }

  console.log('')
  console.log('='.repeat(60))
  console.log('Summary')
  console.log('='.repeat(60))
  console.log(`Converted: ${successCount}/${IMAGES_TO_CONVERT.length}`)
  console.log(`Failed: ${failCount}`)
  console.log(`Total size: ${(totalInputSize / 1024).toFixed(1)}KB -> ${(totalOutputSize / 1024).toFixed(1)}KB`)
  console.log(`Total savings: ${((totalInputSize - totalOutputSize) / totalInputSize * 100).toFixed(1)}%`)
}

main().catch(console.error)
