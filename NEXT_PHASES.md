# Next Phases Planning

Strategic roadmap for completing the portfolio migration and enhancement.

---

## Phase 7: Migration Completion & Verification ✅ COMPLETE

**Goal:** Ensure 100% feature parity with portfolio-site, then archive the old codebase.

**Estimated Time:** 1-2 hours (ACTUAL: ~2 hours including issue resolution)

**Status:** ✅ COMPLETE - All verification passed, APIs fixed, content parity achieved

### Completed Tasks

#### 1. Side-by-Side Visual Comparison (30 min)
- [ ] Open portfolio-site in browser (http://localhost or file://)
- [ ] Open portfolio-migration in browser (http://localhost:3000)
- [ ] Compare every section visually
- [ ] Document any styling differences
- [ ] Screenshot comparison for critical sections

#### 2. Feature Verification Checklist (30 min)
- [ ] Smooth scroll navigation to all sections
- [ ] Theme toggle (light/dark mode persistence)
- [ ] Back-to-top button (appears at 300px scroll)
- [ ] GitHub stats integration
- [ ] All navigation links functional
- [ ] Contact information displayed correctly
- [ ] Social media links (LinkedIn, GitHub, Email)
- [ ] Company logos displaying (7 companies)
- [ ] Education logos displaying (4 institutions)
- [ ] Project cards with all data
- [ ] Footer content and links

#### 3. Content Audit (20 min)
- [ ] All text matches original
- [ ] All images present and loading
- [ ] All SVG icons present (including white variants)
- [ ] Favicon displays correctly
- [ ] Meta tags match (title, description, OG, Twitter)

#### 4. Technical Verification (20 min)
- [ ] Service worker registers correctly
- [ ] Manifest.json loads properly
- [ ] PWA installable on mobile/desktop
- [ ] Offline functionality works
- [ ] Analytics initializes (if configured)
- [ ] Error tracking captures errors
- [ ] Performance monitoring active

#### 5. Final Cleanup (20 min)
- [ ] Fix any discovered issues
- [ ] Run Lighthouse audit (target: 90+ all categories)
- [ ] Update README.md: "Migration 100% Complete ✅"
- [ ] Archive portfolio-site folder:
  ```bash
  cd c:/Code
  mv portfolio-site portfolio-site-archived-2025-10-22
  # Or zip it: tar -czf portfolio-site-backup.tar.gz portfolio-site
  ```

### Success Criteria
✅ Visual parity confirmed
✅ All features working
✅ No missing content
✅ Lighthouse score 90+
✅ portfolio-site archived

### Deliverables
- Comparison notes documenting verification
- Updated README with "100% Complete" status
- Archived portfolio-site folder

---

## Phase 8: Choose Your Path 🔀

After completing Phase 7, you have **three options** for Phase 8:

### Option A: Detailed Experience Pages (RECOMMENDED - Quick Win)
**Estimated Time:** 4-6 hours
**Value:** HIGH - User-facing enhancement with rich content
**See:** [Phase 8A Details](#phase-8a-detailed-experience-pages-recommended)

### Option B: TypeScript Migration (Original Plan)
**Estimated Time:** 8-16 hours
**Value:** HIGH - Developer experience and type safety
**See:** [Phase 8B Details](#phase-8b-typescript-migration)

### Option C: Both in Parallel
**Estimated Time:** 12-22 hours (overlapping work)
**Value:** HIGHEST - Both enhancements
**Strategy:** Separate branches, merge when complete

---

## Phase 8A: Detailed Experience Pages (RECOMMENDED)

**Goal:** Add rich content pages for major companies with videos, maps, and detailed descriptions.

**Why This First:**
- ✅ Database schema already supports it (columns added in Phase 7)
- ✅ Content exists in original portfolio-site (6 detailed HTML pages)
- ✅ High user-facing value (much richer than current card view)
- ✅ Quick win (4-6 hours vs 8-16 for TypeScript)
- ✅ Showcases dynamic backend power vs static site

**Estimated Time:** 4-6 hours

### Benefits
- Users get much deeper insight into your experience
- Product videos show actual work (Hermes HERMIA software)
- Location maps provide geographic context
- Extended descriptions explain responsibilities in detail
- Demonstrates backend content management capabilities

### Tasks

#### 1. Backend - Data Population (1-1.5 hours)
- [ ] Extract content from 6 original HTML pages:
  - `site/experience/hermes.html`
  - `site/experience/karolinska.html`
  - `site/experience/philips.html`
  - `site/experience/scania.html`
  - `site/experience/fdf.html`
  - `site/experience/sos.html`
- [ ] Create data population script (`scripts/populate_experience_details.py`)
- [ ] Populate database fields (already exist):
  - `video_url` - YouTube embed URLs
  - `video_title` - Video titles for accessibility
  - `map_url` - Google Maps embed URLs
  - `map_title` - Map titles for accessibility
  - `detailed_description` - Extended role descriptions
  - `responsibilities` - JSON array of key responsibilities
  - `technologies` - JSON array of technologies used (if missing)
- [ ] Test API returns updated data

#### 2. Frontend - Company Detail View (2-2.5 hours)
- [ ] Create `src/views/CompanyDetailView.vue`
- [ ] Add route: `/experience/:id`
- [ ] Create components:
  - `VideoEmbed.vue` - Responsive 16:9 YouTube embeds
  - `MapEmbed.vue` - Responsive 16:9 Google Maps embeds
  - `DetailedDescription.vue` - Rich text rendering
- [ ] Add "Learn More" buttons to existing company cards
- [ ] Implement breadcrumb navigation (Home → Experience → Company)
- [ ] Add navigation between company detail pages

#### 3. Content & Accessibility (1 hour)
- [ ] Ensure video embeds have proper titles and allow attributes
- [ ] Ensure map embeds have titles and allowfullscreen
- [ ] Add loading states for embedded content
- [ ] Test screen reader accessibility
- [ ] Add meta tags for company detail pages (OG tags)

#### 4. Testing & Documentation (30-60 min)
- [ ] Test all 6 company detail pages load correctly
- [ ] Verify videos and maps embed properly
- [ ] Test responsive design (mobile, tablet, desktop)
- [ ] Update README.md with new feature
- [ ] Document in PHASE8A_COMPLETION.md

### Example Data Structure

```json
{
  "id": "be82b051-c247-4e4f-b69e-451afe26bb72",
  "name": "Hermes Medical Solutions",
  "title": "QA/RA & Security Specialist",
  "description": "QA/RA & Security Specialist at Hermes Medical Solutions...",
  "detailed_description": "Extended description with more details about the role, achievements, and impact...",
  "video_url": "https://www.youtube.com/embed/bdbevZrjdtU",
  "video_title": "HERMIA – ALL-IN-ONE Molecular Imaging Software",
  "map_url": "https://www.google.com/maps/embed?pb=...",
  "map_title": "Hermes Medical Solutions AB Location",
  "responsibilities": [
    "Lead NIS2 and ISO 27001 compliance implementation",
    "Conduct security risk assessments for medical software",
    "Coordinate regulatory submissions (FDA, CE Mark)"
  ],
  "technologies": ["Python", "Azure DevOps", "Docker", "JIRA"]
}
```

### Success Criteria
✅ All 6 companies have detailed pages
✅ Videos and maps embed correctly
✅ Content is accessible and responsive
✅ Navigation flows naturally
✅ Performance remains good (Lighthouse 90+)

### Deliverables
- Company detail view component
- Video and map embed components
- Populated database with rich content
- Updated navigation with "Learn More" links
- Documentation: PHASE8A_COMPLETION.md

---

## Phase 8B: TypeScript Migration

**Goal:** Convert entire frontend codebase from JavaScript to TypeScript for improved type safety and developer experience.

**Estimated Time:** 1-2 days (8-16 hours total)

### Day 1: Foundation & Utilities (4-5 hours)

#### Morning Session: Setup & Configuration (1 hour)
- [ ] Install TypeScript dependencies:
  ```bash
  cd frontend
  npm install -D typescript @types/node vue-tsc
  ```
- [ ] Generate `tsconfig.json`:
  ```bash
  npx tsc --init
  ```
- [ ] Configure `tsconfig.json`:
  ```json
  {
    "compilerOptions": {
      "target": "ES2020",
      "module": "ESNext",
      "lib": ["ES2020", "DOM", "DOM.Iterable"],
      "jsx": "preserve",
      "strict": true,
      "moduleResolution": "bundler",
      "resolveJsonModule": true,
      "isolatedModules": true,
      "esModuleInterop": true,
      "skipLibCheck": true,
      "allowImportingTsExtensions": true,
      "baseUrl": ".",
      "paths": {
        "@/*": ["./src/*"]
      }
    },
    "include": ["src/**/*.ts", "src/**/*.d.ts", "src/**/*.tsx", "src/**/*.vue"],
    "exclude": ["node_modules"]
  }
  ```
- [ ] Update `package.json` scripts:
  ```json
  "type-check": "vue-tsc --noEmit",
  "build": "vue-tsc --noEmit && vite build"
  ```
- [ ] Create `src/types/` directory for shared types
- [ ] Test build: `npm run type-check`

#### Afternoon Session: Utilities Migration (3-4 hours)

**Priority Order (migrate in this sequence):**

1. **Analytics Utility** (45 min)
   - [ ] `src/utils/analytics.js` → `analytics.ts`
   - [ ] Define interfaces for Analytics, EventProps
   - [ ] Type the analytics singleton class
   - [ ] Export typed functions

2. **Error Tracking Utility** (45 min)
   - [ ] `src/utils/errorTracking.js` → `errorTracking.ts`
   - [ ] Define error data interfaces
   - [ ] Type ErrorTracker class methods
   - [ ] Type tracking functions

3. **Performance Monitoring Utility** (45 min)
   - [ ] `src/utils/performance.js` → `performance.ts`
   - [ ] Define PerformanceMetrics interfaces
   - [ ] Type PerformanceMonitor class
   - [ ] Type Web Vitals functions

4. **API Client** (1 hour)
   - [ ] Create `src/types/api.ts` with all API response types:
     ```typescript
     export interface Company {
       id: number
       name: string
       position: string
       start_date: string
       end_date: string | null
       description: string
       logo_url: string | null
     }
     // ... more interfaces
     ```
   - [ ] `src/api/client.js` → `client.ts`
   - [ ] Type all API functions with return types
   - [ ] Use generics for axios requests

**End of Day 1 Checkpoint:**
- [ ] Run `npm run type-check` - should pass
- [ ] Run tests: `npm test` - should pass
- [ ] Commit: "feat: migrate utilities to TypeScript"

### Day 2: Composables & Components (4-6 hours)

#### Morning Session: Composables (2 hours)

1. **useTheme Composable** (30 min)
   - [ ] `src/composables/useTheme.js` → `useTheme.ts`
   - [ ] Define Theme type: `type Theme = 'light' | 'dark'`
   - [ ] Type return values with proper Ref types

2. **useAnalytics Composable** (30 min)
   - [ ] `src/composables/useAnalytics.js` → `useAnalytics.ts`
   - [ ] Import types from analytics utility
   - [ ] Type all tracking functions

3. **useScrollAnimations Composable** (30 min)
   - [ ] `src/composables/useScrollAnimations.js` → `useScrollAnimations.ts`
   - [ ] Type IntersectionObserver callbacks
   - [ ] Type return values

#### Afternoon Session: Components (2-4 hours)

**Component Migration Strategy:**

Start with simple components, progress to complex:

**Simple Components (1 hour):**
- [ ] `ThemeToggle.vue` - Add `<script setup lang="ts">`
- [ ] `BackToTop.vue`
- [ ] `LoadingSpinner.vue`
- [ ] `LazyImage.vue` - Define props interface

**Medium Components (1.5 hours):**
- [ ] `NavBar.vue` - Type navigation items
- [ ] `FooterSection.vue`
- [ ] `ExperienceCard.vue` - Define Company props type
- [ ] `ProjectCard.vue` - Define Project props type

**Complex Components (1.5 hours):**
- [ ] `GitHubStats.vue` - Type GitHub API responses
- [ ] `ErrorBoundary.vue` - Type error handling

**Views (30 min):**
- [ ] `HomeView.vue` - Import typed API functions
- [ ] Update router: `src/router/index.js` → `index.ts`

**Main Files (30 min):**
- [ ] `src/main.js` → `main.ts`
- [ ] Update imports for typed modules

### Testing Updates (1 hour)
- [ ] Update test files to import `.ts` instead of `.js`
- [ ] Fix any type-related test errors
- [ ] Ensure all tests pass: `npm test`
- [ ] Update coverage reports

### Final Verification (1 hour)
- [ ] Run full type check: `npm run type-check`
- [ ] Run all tests: `npm test`
- [ ] Run E2E tests: `npm run test:e2e`
- [ ] Build production: `npm run build`
- [ ] Verify no TypeScript errors
- [ ] Check bundle size (should be similar or smaller)

### Documentation Updates
- [ ] Update README.md with TypeScript badges
- [ ] Add TypeScript section to SETUP_GUIDE.md
- [ ] Update CONTRIBUTING.md (if exists) with TypeScript guidelines

### Success Criteria
✅ Zero TypeScript errors
✅ All tests passing
✅ Production build succeeds
✅ No runtime errors
✅ Bundle size acceptable

### Deliverables
- Fully typed TypeScript codebase
- Updated configuration files
- Passing type checks and tests
- Commit: "feat: complete TypeScript migration"

---

## TypeScript Best Practices for Migration

### 1. Type Definition Conventions
```typescript
// Use interfaces for object shapes
interface User {
  id: number
  name: string
  email?: string  // Optional property
}

// Use type for unions and primitives
type Theme = 'light' | 'dark'
type Status = 'loading' | 'success' | 'error'

// Use generics for reusable patterns
interface ApiResponse<T> {
  data: T
  message?: string
}
```

### 2. Vue 3 + TypeScript Patterns
```typescript
// Use defineProps with generic type
<script setup lang="ts">
import { defineProps } from 'vue'

interface Props {
  title: string
  count?: number
}

const props = defineProps<Props>()
</script>

// Or with defaults
const props = withDefaults(defineProps<Props>(), {
  count: 0
})
```

### 3. Composable Typing
```typescript
import { ref, Ref } from 'vue'

export function useCounter(): {
  count: Ref<number>
  increment: () => void
} {
  const count = ref(0)
  const increment = () => count.value++

  return { count, increment }
}
```

### 4. API Client Typing
```typescript
import axios, { AxiosResponse } from 'axios'

export async function getCompanies(): Promise<Company[]> {
  const response: AxiosResponse<ApiResponse<Company[]>> =
    await axios.get('/api/v1/companies')
  return response.data.data
}
```

### 5. Avoid Common Pitfalls
- ❌ Don't use `any` - defeats purpose of TypeScript
- ❌ Don't over-type everything - let TypeScript infer when possible
- ✅ Use `unknown` instead of `any` when type is truly unknown
- ✅ Enable `strict` mode in tsconfig.json
- ✅ Use utility types: `Partial<T>`, `Pick<T>`, `Omit<T>`

---

## Phase 9: Additional Enhancements (Optional)

After completing Phase 8 (whichever path chosen), consider these additional enhancements:

### 9A: Downloadable Documents (3-4 hours)
**From portfolio-site discovery:**
- Bachelor Thesis PDF (1.3 MB)
- Master Thesis PDF (4.0 MB)

**Implementation:**
- Create `documents` table and API endpoint
- Add Publications/Research section in frontend
- Upload PDFs to static storage or CDN
- Add download links with file size indicators

### 9B: Contact Form (4-5 hours)
- Backend endpoint for contact submissions
- Email integration (SendGrid, AWS SES)
- Spam protection (reCAPTCHA)
- Message storage in database
- Admin view for messages

### 9C: Blog/Articles System (8-12 hours)
- Markdown-based content management
- Create/edit/delete articles via admin panel
- Categories and tags
- RSS feed generation
- Code syntax highlighting

### 9D: Enhanced GitHub Integration (2-3 hours)
- Recent commits/PRs timeline
- Contribution graph visualization
- Pinned repositories showcase
- Language statistics

### 9E: Skills Visualization (3-4 hours)
- Interactive skill charts (Chart.js, D3.js)
- Proficiency levels and categories
- Technology radar chart
- Skills timeline (when learned)

### 9F: Production Deployment
- Set up PostgreSQL database (replace SQLite)
- Configure production environment variables
- Deploy to cloud (Azure, Vercel, DigitalOcean)
- Configure SSL/TLS certificates
- Set up CDN (CloudFlare, Azure CDN)
- Configure custom domain (dashti.se)
- Production monitoring (Plausible, Sentry)

### 9G: Advanced Testing
- Visual regression testing (Percy, Chromatic)
- Load testing (k6, Artillery)
- Security testing (OWASP ZAP automated)
- Accessibility automation (Pa11y CI)

---

## Timeline Summary

| Phase | Duration | Focus | Status |
|-------|----------|-------|--------|
| Phase 7 | 1-2 hours | Migration verification & cleanup | ✅ COMPLETE |
| Phase 8A (Option) | 4-6 hours | Detailed experience pages | ⏳ Pending |
| Phase 8B (Option) | 8-16 hours | TypeScript migration | ⏳ Pending |
| Phase 9 | Variable | Optional enhancements | ⏳ Pending |

### Path Options After Phase 7

**Quick Win Path (Recommended):**
1. Phase 7 ✅ Complete (2025-10-23)
2. Phase 8A: Detailed Experience Pages (4-6 hours)
3. Phase 8B: TypeScript Migration (8-16 hours)
4. Phase 9: Optional enhancements

**Developer-First Path:**
1. Phase 7 ✅ Complete (2025-10-23)
2. Phase 8B: TypeScript Migration (8-16 hours)
3. Phase 8A: Detailed Experience Pages (4-6 hours)
4. Phase 9: Optional enhancements

**Parallel Development Path:**
1. Phase 7 ✅ Complete (2025-10-23)
2. Branch A: Detailed Experience Pages (4-6 hours)
3. Branch B: TypeScript Migration (8-16 hours)
4. Merge both branches
5. Phase 9: Optional enhancements

---

## Key Documentation

- **Phase 7 Verification**: [PHASE7_FINAL_VERIFICATION.md](PHASE7_FINAL_VERIFICATION.md)
- **Content Audit**: [PHASE7_CONTENT_AUDIT_REPORT.md](PHASE7_CONTENT_AUDIT_REPORT.md)
- **Additional Opportunities**: [ADDITIONAL_MIGRATION_OPPORTUNITIES.md](ADDITIONAL_MIGRATION_OPPORTUNITIES.md)
- **Original Analysis**: [PHASE7_VERIFICATION.md](PHASE7_VERIFICATION.md)

---

**Last Updated:** 2025-10-23
**Status:** Phase 7 Complete ✅, Ready for Phase 8 (Choose Path)
