# Changelog

All notable changes to this project will be documented in this file.

## [Hotfix] - 2025-11-05 - Production Media Content & Frontend Deployment Fix

### Fixed
**Frontend Deployment:**
- Fixed blank page issue on Vercel production deployment
- Replaced all hardcoded localhost API URLs with environment variable (VITE_API_URL)
- Updated files: src/api/client.ts, src/stores/auth.ts, src/services/analytics.ts, src/views/CompanyDetailView.vue, src/components/GitHubStats.vue
- Frontend now correctly connects to production backend (https://dashti-portfolio-backend.fly.dev)

**Backend Data:**
- Added complete media content (YouTube videos and Google Maps) for all experience entries
- Added missing 7th company: SoftPro Medical Solutions (Master Thesis Student, 2020)
- Created update_complete_with_media.py script with all media URLs extracted from original site
- Successfully updated production database with all 7 companies including:
  - Scania: YouTube video + Google Maps
  - Finnish Defence Forces: YouTube video + Google Maps
  - Hermes Medical Solutions: YouTube video + Google Maps
  - Södersjukhuset: Google Maps only
  - SoftPro Medical Solutions: No media (thesis entry)
  - Karolinska University Hospital: YouTube video + Google Maps
  - Philips AB: YouTube video + Google Maps

### Root Cause
- Frontend was attempting to connect to localhost:8001 in production instead of using .env.production configuration
- This caused the Vue app to fail loading data, resulting in a blank page
- Missing media URLs meant experience sections were incomplete even when accessible

## [Phase 6] - 2025-10-22 - Monitoring & Performance Optimization

### Added
**Backend Monitoring:**
- Structured JSON logging with request tracking and sensitive data masking
- Error tracking middleware with stack trace capture
- Performance monitoring middleware with response time tracking
- Prometheus-compatible metrics endpoint at `/api/v1/metrics`
- Compression middleware (Gzip) for responses >1KB
- Cache control middleware with appropriate headers per content type
- Configuration options: LOG_LEVEL, ERROR_TRACKING_ENABLED, METRICS_ENABLED

**Frontend Monitoring:**
- Privacy-compliant analytics integration (Plausible/Umami)
- Client-side error tracking for JavaScript errors and promise rejections
- Core Web Vitals monitoring (LCP, FID, CLS, TTFB)
- Navigation Timing API and Resource Timing integration
- Analytics composable for easy event tracking
- Configuration: VITE_ANALYTICS_*, VITE_ERROR_TRACKING_*, VITE_METRICS_*

**Performance Optimization:**
- Enhanced Vite configuration with advanced code splitting
- Dynamic manualChunks function for optimal bundle splitting
- Terser optimization: removes console.log, 2-pass compression
- Asset organization by type (img, fonts, js, css)
- Bundle analyzer support with rollup-plugin-visualizer
- Enhanced Nginx caching: 1-year for static assets, granular per file type
- Improved Gzip compression configuration in Nginx

**Documentation:**
- MONITORING.md - Comprehensive observability guide (500+ lines)
- PERFORMANCE.md - Optimization strategies and targets (600+ lines)
- Updated .env.example files with monitoring configuration

### Changed
- Updated main.py to integrate all monitoring middleware
- Updated config.py with monitoring settings
- Enhanced vite.config.js with performance optimizations
- Improved nginx.conf with better caching and compression
- Updated README.md with Phase 6 completion status

### Dependencies
- Added: python-json-logger (structured logging)

## [Phase 5] - 2025-10-22 - Testing & Quality Assurance

### Added
**Frontend Testing:**
- Vitest configuration with happy-dom environment
- Unit tests for components: ThemeToggle, BackToTop, NavBar
- Unit tests for composables: useTheme
- Test setup with global mocks (matchMedia, IntersectionObserver, localStorage)
- Coverage thresholds: 80% for lines, functions, branches, statements

**Backend Testing:**
- pytest tests for health check endpoints
- pytest tests for GitHub API integration with mocked responses
- Enhanced conftest.py with test fixtures

**E2E Testing:**
- Playwright configuration for 5 browsers (Desktop Chrome/Firefox/Safari, Mobile Chrome/Safari)
- E2E tests for homepage functionality
- E2E tests for navigation flows
- E2E tests for theme switching and persistence
- Accessibility tests with axe-core (WCAG 2.1 AA compliance)
- 17 accessibility tests covering automated scans, keyboard nav, ARIA, contrast

**CI/CD Integration:**
- Frontend unit tests in GitHub Actions workflow
- E2E test job with Playwright browser installation
- Coverage upload to CodeCov
- Test failures block deployment

**Documentation:**
- TESTING.md - Comprehensive testing guide (800+ lines)
- Playwright test scripts in root package.json

### Dependencies
- Added: @playwright/test, @axe-core/playwright
- Added: vitest, @vue/test-utils, happy-dom, @vitest/ui

## [Session 6] - 2025-10-21 - CRITICAL Security Fix

### Fixed
- **CRITICAL**: All admin CRUD endpoints were unprotected (POST/PUT/DELETE)
- Added authentication requirement to 12 endpoints across 4 API modules:
  - Companies: POST, PUT, DELETE
  - Projects: POST, PUT, DELETE
  - Education: POST, PUT, DELETE
  - Auth: token refresh, admin status
- All write operations now require GitHub OAuth + JWT tokens

### Security
- Production security posture significantly improved
- Admin-only operations properly protected

## [Session 5] - 2025-10-21 - Asset Migration & Logo Integration

### Added
- Complete asset migration (48 files: SVG icons, logos, optimized images)
- Logo integration in UI for companies and education
- logo_url fields in database and API responses
- White SVG icon variants for dark theme
- Optimized image directory structure

### Changed
- Visual design now matches original portfolio-site exactly
- Company and education cards display logos (48x48px sizing)

## [Earlier Sessions] - 2025-10-18 to 2025-10-21

### Completed
- Stockholm design replication with glass-morphism hero
- Data migration: 7 companies, 4 education entries, complete project data
- Security headers: CSP, X-Frame-Options, Referrer-Policy, HSTS
- Authentication: GitHub OAuth 2.0 with JWT tokens
- Accessibility: ARIA labels, keyboard navigation, screen reader support
- SEO: Open Graph, Twitter cards, meta tags, sitemap
- PWA: Service worker, manifest, offline functionality
- Performance: Lazy loading, image optimization, bundle splitting
- Navigation: Bordered button style matching original
- Footer: Simplified minimalist design

---

## Upcoming

### Phase 7 - Migration Completion (Planned)
- Side-by-side comparison with portfolio-site
- Verify all features migrated
- Final polish and validation
- Archive portfolio-site

### Phase 8 - TypeScript Migration (Planned)
- TypeScript configuration setup
- Migrate utilities and composables
- Migrate components and views
- Full type coverage across codebase
- Update tests for TypeScript
