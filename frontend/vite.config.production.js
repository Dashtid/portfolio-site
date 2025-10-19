import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { visualizer } from 'rollup-plugin-visualizer'
import viteCompression from 'vite-plugin-compression'
import { VitePWA } from 'vite-plugin-pwa'

// Production configuration
export default defineConfig({
  plugins: [
    vue(),

    // Bundle analyzer
    visualizer({
      filename: './dist/stats.html',
      open: false,
      gzipSize: true,
      brotliSize: true
    }),

    // Gzip compression
    viteCompression({
      algorithm: 'gzip',
      threshold: 10240,
      deleteOriginFile: false
    }),

    // Brotli compression
    viteCompression({
      algorithm: 'brotliCompress',
      threshold: 10240,
      deleteOriginFile: false,
      ext: '.br'
    }),

    // PWA plugin
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.ico', 'apple-touch-icon.png', 'masked-icon.svg'],
      manifest: {
        name: 'David Dashti Portfolio',
        short_name: 'DD Portfolio',
        description: 'Security & Technology Professional Portfolio',
        theme_color: '#007bff',
        background_color: '#ffffff',
        display: 'standalone',
        icons: [
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
        globPatterns: ['**/*.{js,css,html,ico,png,svg,webp}'],
        runtimeCaching: [
          {
            urlPattern: /^https:\/\/api\.dashti\.se\/.*/i,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'api-cache',
              expiration: {
                maxEntries: 50,
                maxAgeSeconds: 60 * 60 // 1 hour
              },
              cacheableResponse: {
                statuses: [0, 200]
              }
            }
          },
          {
            urlPattern: /^https:\/\/api\.github\.com\/.*/i,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'github-api-cache',
              expiration: {
                maxEntries: 30,
                maxAgeSeconds: 60 * 30 // 30 minutes
              }
            }
          }
        ]
      }
    })
  ],

  build: {
    // Output directory
    outDir: 'dist',

    // Assets directory
    assetsDir: 'assets',

    // Source maps for production (external)
    sourcemap: 'hidden',

    // Minification
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true
      }
    },

    // Rollup options
    rollupOptions: {
      output: {
        // Manual chunks for better caching
        manualChunks: {
          'vendor': ['vue', 'vue-router', 'pinia'],
          'ui': ['@headlessui/vue'],
          'utils': ['axios']
        },

        // Asset file naming
        assetFileNames: (assetInfo) => {
          const extType = assetInfo.name.split('.').pop()
          if (/png|jpe?g|svg|gif|tiff|bmp|ico/i.test(extType)) {
            return `assets/images/[name]-[hash][extname]`
          }
          if (/woff2?|ttf|otf|eot/i.test(extType)) {
            return `assets/fonts/[name]-[hash][extname]`
          }
          return `assets/[name]-[hash][extname]`
        },

        // Chunk file naming
        chunkFileNames: 'assets/js/[name]-[hash].js',

        // Entry file naming
        entryFileNames: 'assets/js/[name]-[hash].js'
      }
    },

    // Chunk size warnings
    chunkSizeWarningLimit: 1000,

    // CSS code splitting
    cssCodeSplit: true,

    // Asset size limit (4kb)
    assetsInlineLimit: 4096,

    // Target browsers
    target: ['es2020', 'edge88', 'firefox78', 'chrome87', 'safari14']
  },

  // Optimizations
  optimizeDeps: {
    include: ['vue', 'vue-router', 'pinia', 'axios'],
    exclude: []
  },

  // Server configuration (for preview)
  preview: {
    port: 3000,
    host: true,
    strictPort: false
  },

  // Environment variable prefix
  envPrefix: 'VITE_'
})