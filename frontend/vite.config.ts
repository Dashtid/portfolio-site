import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { VitePWA } from 'vite-plugin-pwa'
import path from 'path'
import os from 'os'
import { visualizer } from 'rollup-plugin-visualizer'

// https://vite.dev/config/
export default defineConfig({
  // Use temp directory to avoid OneDrive path issues with spaces
  cacheDir: path.join(os.tmpdir(), 'vite-cache-portfolio'),
  plugins: [
    vue(),
    // PWA with Workbox for better offline support
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.ico', 'images/*.svg', 'images/*.webp', 'images/*.png'],
      manifest: {
        name: 'David Dashti - Portfolio',
        short_name: 'Dashti',
        description: 'Biomedical Engineer & Cybersecurity Specialist Portfolio',
        theme_color: '#0d6efd',
        background_color: '#ffffff',
        display: 'standalone',
        start_url: '/',
        scope: '/',
        icons: [
          {
            src: '/images/D.svg',
            sizes: 'any',
            type: 'image/svg+xml',
            purpose: 'any'
          },
          {
            src: '/images/icon-192.png',
            sizes: '192x192',
            type: 'image/png'
          },
          {
            src: '/images/icon-512.png',
            sizes: '512x512',
            type: 'image/png'
          }
        ]
      },
      workbox: {
        // Precache app shell (exclude large images from precaching)
        globPatterns: ['**/*.{js,css,html,ico,svg,woff2}'],
        // Exclude large images from precaching - they'll be runtime cached
        globIgnores: ['**/images/stockholm*', '**/images/optimized/*'],
        // Allow larger files (up to 3MB)
        maximumFileSizeToCacheInBytes: 3 * 1024 * 1024,
        // Runtime caching strategies
        runtimeCaching: [
          {
            // Cache API responses (network-first with fallback)
            urlPattern: /^https?:\/\/.*\/api\/.*/i,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'api-cache',
              expiration: {
                maxEntries: 50,
                maxAgeSeconds: 60 * 60 * 24 // 24 hours
              },
              networkTimeoutSeconds: 10,
              cacheableResponse: {
                statuses: [0, 200]
              }
            }
          },
          {
            // Cache images (cache-first)
            urlPattern: /\.(?:png|jpg|jpeg|svg|gif|webp|avif)$/i,
            handler: 'CacheFirst',
            options: {
              cacheName: 'image-cache',
              expiration: {
                maxEntries: 100,
                maxAgeSeconds: 60 * 60 * 24 * 30 // 30 days
              }
            }
          },
          {
            // Cache fonts (cache-first)
            urlPattern: /\.(?:woff|woff2|ttf|eot)$/i,
            handler: 'CacheFirst',
            options: {
              cacheName: 'font-cache',
              expiration: {
                maxEntries: 20,
                maxAgeSeconds: 60 * 60 * 24 * 365 // 1 year
              }
            }
          },
          {
            // Cache external resources (stale-while-revalidate)
            urlPattern: /^https:\/\/(?:fonts\.googleapis\.com|fonts\.gstatic\.com)\/.*/i,
            handler: 'StaleWhileRevalidate',
            options: {
              cacheName: 'google-fonts-cache',
              expiration: {
                maxEntries: 20,
                maxAgeSeconds: 60 * 60 * 24 * 365 // 1 year
              }
            }
          }
        ],
        // Skip waiting to activate new service worker immediately
        skipWaiting: true,
        clientsClaim: true,
        // Clean up old caches
        cleanupOutdatedCaches: true
      },
      devOptions: {
        enabled: false // Disable in development
      }
    }),
    // Bundle analyzer (optional, only in analysis mode)
    process.env.ANALYZE &&
      visualizer({
        open: true,
        filename: 'dist/stats.html',
        gzipSize: true,
        brotliSize: true
      })
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  },
  build: {
    // Production build optimizations
    target: 'es2015',
    outDir: 'dist',
    assetsDir: 'assets',
    sourcemap: false,
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true, // Remove console.logs in production
        drop_debugger: true,
        pure_funcs: ['console.log', 'console.info', 'console.debug'], // Remove specific console methods
        passes: 2 // Run compression twice for better results
      },
      mangle: {
        safari10: true // Fix Safari 10+ issues
      }
    },
    rollupOptions: {
      output: {
        // Manual chunk splitting for better caching and performance
        manualChunks: (id: string) => {
          // Three.js - isolated for lazy loading (~172KB gzipped)
          if (id.includes('node_modules/three')) {
            return 'three'
          }
          // GSAP - isolated for potential lazy loading (~60KB gzipped)
          if (id.includes('node_modules/gsap')) {
            return 'gsap'
          }
          // Vue ecosystem
          if (id.includes('node_modules/vue') || id.includes('node_modules/@vue')) {
            return 'vue-vendor'
          }
          // Vue Router
          if (id.includes('node_modules/vue-router')) {
            return 'vue-vendor'
          }
          // Pinia
          if (id.includes('node_modules/pinia')) {
            return 'vue-vendor'
          }
          // VueUse
          if (id.includes('node_modules/@vueuse')) {
            return 'vueuse'
          }
          // Axios
          if (id.includes('node_modules/axios')) {
            return 'axios'
          }
          // Other node_modules
          if (id.includes('node_modules')) {
            return 'vendor'
          }
        },
        // Asset naming for cache busting
        chunkFileNames: 'assets/js/[name]-[hash].js',
        entryFileNames: 'assets/js/[name]-[hash].js',
        assetFileNames: assetInfo => {
          // Organize assets by type
          const info = assetInfo.name?.split('.') || []
          let extType = info[info.length - 1]
          if (/\.(png|jpe?g|svg|gif|tiff|bmp|ico|webp)$/i.test(assetInfo.name || '')) {
            extType = 'img'
          } else if (/\.(woff2?|eot|ttf|otf)$/i.test(assetInfo.name || '')) {
            extType = 'fonts'
          }
          return `assets/${extType}/[name]-[hash].[ext]`
        }
      }
    },
    // Chunk size warning limit (in KB) - stricter for performance budget
    chunkSizeWarningLimit: 200,
    // CSS code splitting
    cssCodeSplit: true,
    // Report compressed size
    reportCompressedSize: true,
    // Aggressive minification
    cssMinify: true
  },
  // Optimize dependencies
  optimizeDeps: {
    include: ['vue', 'vue-router', 'pinia', '@vueuse/core', 'axios']
  }
})
