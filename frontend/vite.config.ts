import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'
import { VitePWA } from 'vite-plugin-pwa'
import path from 'path'
import os from 'os'
import fs from 'fs'
import { visualizer } from 'rollup-plugin-visualizer'
import { sentryVitePlugin } from '@sentry/vite-plugin'

// D3-INF-03: sourcemap upload is gated on a build-time SENTRY_AUTH_TOKEN
// (passed via `vercel deploy --build-env` from the SENTRY_AUTH_TOKEN GitHub
// secret). Without it the plugin is absent and sourcemap stays off — exactly
// the pre-change behavior — so maps can never ship to the CDN unprotected:
// with the token, 'hidden' maps are generated, uploaded to Sentry, then
// deleted before deploy by filesToDeleteAfterUpload.
const SENTRY_UPLOAD_ENABLED = Boolean(process.env.SENTRY_AUTH_TOKEN)

// https://vite.dev/config/
export default defineConfig({
  // Use temp directory to avoid OneDrive path issues with spaces
  cacheDir: path.join(os.tmpdir(), 'vite-cache-portfolio'),
  // vite-ssg reads `ssgOptions` from the resolved config (Object.assign of
  // config.ssgOptions then CLI args). onFinished runs once after every
  // route is prerendered.
  ssgOptions: {
    // Inject the experience detail pages into the sitemap. They're derived
    // from the actual prerendered output (dist/experience/*.html) — the same
    // route set includedRoutes builds from the live company list — so the
    // sitemap never drifts from what's deployed and no company UUID is
    // hardcoded. The static base (home + section anchors) lives in
    // public/sitemap.xml and is copied into dist before this hook runs.
    onFinished() {
      const distDir = path.resolve(__dirname, 'dist')

      // D3-SEC-03: convert vite-ssg's executable state script into a
      // non-executing JSON data block so script-src needs no per-build
      // hashes. The captured group is the double-encoded JSON string
      // literal serializeState emits (with <, >, / escaped, so a literal
      // </script> can never appear inside and the lazy match is safe);
      // it is kept verbatim as the block's content, and the shim at the
      // top of src/main.ts feeds it back to vite-ssg's deserializeState
      // unchanged. Every prerendered page (including 404.html) carries
      // the script, so walk the whole tree.
      const htmlFiles: string[] = []
      const walk = (dir: string): void => {
        for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
          const full = path.join(dir, entry.name)
          if (entry.isDirectory()) walk(full)
          else if (entry.name.endsWith('.html')) htmlFiles.push(full)
        }
      }
      walk(distDir)

      const stateScript = /<script>window\.__INITIAL_STATE__=(".*?")<\/script>/s
      let rewritten = 0
      for (const file of htmlFiles) {
        const html = fs.readFileSync(file, 'utf-8')
        if (!stateScript.test(html)) continue
        fs.writeFileSync(
          file,
          html.replace(
            stateScript,
            '<script type="application/json" id="__INITIAL_STATE__">$1</script>'
          )
        )
        rewritten++
      }
      // eslint-disable-next-line no-console
      console.log(`[csp] state script -> JSON data block in ${rewritten} pages`)

      const sitemapPath = path.join(distDir, 'sitemap.xml')
      const experienceDir = path.join(distDir, 'experience')
      if (!fs.existsSync(sitemapPath) || !fs.existsSync(experienceDir)) return

      const ids = fs
        .readdirSync(experienceDir)
        .filter(f => f.endsWith('.html'))
        .map(f => f.replace(/\.html$/, ''))
        .sort()
      if (ids.length === 0) return

      let xml = fs.readFileSync(sitemapPath, 'utf-8')
      // Idempotent: key off the generated marker, not '/experience/' — the
      // static base contains that substring in a comment.
      if (xml.includes('auto-generated from prerendered routes')) return

      // D3-SEO-02: derive lastmod from the company's updated_at baked into
      // the page's __INITIAL_STATE__ — a fresh build no longer claims every
      // page changed today, so Google keeps trusting the sitemap.
      const buildDate = new Date().toISOString().slice(0, 10)
      const lastmodFor = (id: string): string => {
        try {
          const html = fs.readFileSync(path.join(experienceDir, `${id}.html`), 'utf-8')
          const m = html.match(
            /<script type="application\/json" id="__INITIAL_STATE__">(".*?")<\/script>/s
          )
          if (!m) return buildDate
          const state = JSON.parse(JSON.parse(m[1]))
          const updated = state?.pinia?.experienceDetail?.byId?.[id]?.updated_at
          return typeof updated === 'string' ? updated.slice(0, 10) : buildDate
        } catch {
          return buildDate
        }
      }
      const entries = ids
        .map(
          id =>
            `    <url>\n        <loc>https://dashti.se/experience/${id}</loc>\n        <lastmod>${lastmodFor(id)}</lastmod>\n        <changefreq>monthly</changefreq>\n        <priority>0.7</priority>\n    </url>`
        )
        .join('\n')

      xml = xml.replace(
        '</urlset>',
        `\n    <!-- Experience detail pages (auto-generated from prerendered routes) -->\n${entries}\n</urlset>`
      )
      fs.writeFileSync(sitemapPath, xml)
      // eslint-disable-next-line no-console
      console.log(`[sitemap] injected ${ids.length} experience detail routes`)
    }
  },
  plugins: [
    vue(),
    tailwindcss(),
    // PWA with Workbox for better offline support
    VitePWA({
      registerType: 'autoUpdate',
      // Nothing from public/ is precached — logos, previews and manifest
      // icons are fetched on demand and land in the runtime image cache.
      // includeAssets images/*.{svg,webp,png} used to push ~1.5MB (854KB
      // preview.png, 296KB icon-512, 176KB scania.svg, ...) into every
      // visitor's precache, and vite-plugin-pwa additionally injects
      // manifest.icons unless told not to.
      includeManifestIcons: false,
      manifest: {
        name: 'David Dashti',
        short_name: 'David Dashti',
        description:
          'Product security for medical software — securing medical devices and the AI moving into healthcare',
        theme_color: '#2563eb',
        background_color: '#f8fafc',
        display: 'standalone',
        start_url: '/',
        scope: '/',
        orientation: 'portrait-primary',
        prefer_related_applications: false,
        lang: 'en',
        categories: ['business', 'healthcare', 'cybersecurity'],
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
            type: 'image/png',
            purpose: 'any'
          },
          {
            src: '/images/icon-512.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'any'
          },
          {
            src: '/images/icon-512.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'maskable'
          }
        ],
        screenshots: [
          {
            src: '/images/optimized/stockholm-desktop.webp',
            sizes: '1920x1080',
            type: 'image/webp',
            form_factor: 'wide',
            label: 'Desktop view of portfolio'
          }
        ],
        shortcuts: [
          {
            name: 'Experience',
            url: '/#experience',
            description: 'View professional experience'
          },
          {
            name: 'Education',
            url: '/#education',
            description: 'View educational background'
          },
          {
            name: 'Projects',
            url: '/#projects',
            description: 'View GitHub projects'
          },
          {
            name: 'Contact',
            url: '/#contact',
            description: 'Get in touch'
          }
        ]
      },
      workbox: {
        // Precache the app shell only. SVGs (company logos) and images go
        // through the runtime image-cache instead of inflating every
        // visitor's SW install.
        globPatterns: ['**/*.{js,css,html,ico,woff2}'],
        globIgnores: [
          '**/images/stockholm*',
          '**/images/optimized/*',
          // Admin bundle (one user needs it) and the ~500KB three.js chunk
          // (lazy-loaded by the hero) stay out of the install-time
          // precache; the asset-cache runtime rule below picks them up on
          // first use so offline revisits still work.
          '**/Admin*',
          '**/three-*'
        ],
        // Backstop against a single chunk bloating the precache
        maximumFileSizeToCacheInBytes: 1024 * 1024,
        // Runtime caching strategies
        runtimeCaching: [
          {
            // Hashed build chunks not in the precache (Admin*, three-*).
            // Content-hashed filenames are immutable, so cache-first is
            // safe; new deploys produce new URLs.
            urlPattern: /\/assets\/.*\.(?:js|css)$/i,
            handler: 'CacheFirst',
            options: {
              cacheName: 'asset-cache',
              expiration: {
                maxEntries: 80,
                maxAgeSeconds: 60 * 60 * 24 * 30 // 30 days
              }
            }
          },
          {
            // Public API GETs: network-first, short-lived offline fallback.
            // Auth, admin, analytics and metrics endpoints are deliberately
            // excluded — Workbox ignores response Cache-Control, so cached
            // private payloads would survive logout in CacheStorage.
            urlPattern: /^https?:\/\/[^/]+\/api\/(?!v1\/(?:auth|admin|analytics|metrics)(?:\/|$))/i,
            handler: 'NetworkFirst',
            options: {
              cacheName: 'api-cache',
              expiration: {
                maxEntries: 50,
                maxAgeSeconds: 60 * 5 // 5 minutes — matches backend stats TTL
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
            // Cache Google Fonts CSS + font files (stale-while-revalidate).
            // 30-day TTL: font CSS rarely changes but can; long TTL risks
            // stale @font-face URLs for up to a year otherwise.
            urlPattern: /^https:\/\/(?:fonts\.googleapis\.com|fonts\.gstatic\.com)\/.*/i,
            handler: 'StaleWhileRevalidate',
            options: {
              cacheName: 'google-fonts-cache',
              expiration: {
                maxEntries: 20,
                maxAgeSeconds: 60 * 60 * 24 * 30 // 30 days
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
      }),
    // Sentry sourcemap upload — only when a token is present at build time
    // (D3-INF-03; see SENTRY_UPLOAD_ENABLED above). Must come after all
    // code-emitting plugins so it sees the final chunks.
    SENTRY_UPLOAD_ENABLED &&
      sentryVitePlugin({
        org: process.env.SENTRY_ORG,
        project: process.env.SENTRY_PROJECT,
        authToken: process.env.SENTRY_AUTH_TOKEN,
        telemetry: false,
        sourcemaps: {
          filesToDeleteAfterUpload: ['dist/**/*.map']
        }
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
    // 'hidden': maps generated without sourceMappingURL comments; uploaded
    // to Sentry then deleted (see SENTRY_UPLOAD_ENABLED above)
    sourcemap: SENTRY_UPLOAD_ENABLED ? 'hidden' : false,
    minify: 'terser',
    terserOptions: {
      compress: {
        // No drop_console here (D3-FE-02): it deleted console.error/warn too,
        // breaking logger.ts's "errors always logged in production" contract.
        // pure_funcs below strips only the noisy tiers.
        drop_debugger: true,
        pure_funcs: ['console.log', 'console.info', 'console.debug'],
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
