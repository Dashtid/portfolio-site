# Performance Optimization Guide

Comprehensive guide to performance optimization strategies, benchmarks, and best practices for the portfolio website.

## Table of Contents

- [Overview](#overview)
- [Performance Targets](#performance-targets)
- [Core Web Vitals](#core-web-vitals)
- [Frontend Optimization](#frontend-optimization)
- [Backend Optimization](#backend-optimization)
- [Network Optimization](#network-optimization)
- [Caching Strategy](#caching-strategy)
- [Monitoring Performance](#monitoring-performance)
- [Performance Checklist](#performance-checklist)
- [Troubleshooting](#troubleshooting)

## Overview

This project implements aggressive performance optimizations to ensure fast load times and excellent user experience across all devices and network conditions.

**Key Optimizations:**
- Code splitting and tree shaking
- Image optimization (WebP, lazy loading)
- Gzip/Brotli compression
- Aggressive caching (1-year for static assets)
- CDN-friendly architecture
- Database query optimization
- Response compression

**Current Performance:**
- Lighthouse Score: Target 90+
- First Contentful Paint: Target <1.8s
- Time to Interactive: Target <3.8s
- Total Load Time: Target <2s

## Performance Targets

### Google Core Web Vitals

| Metric | Good | Needs Improvement | Poor | Our Target |
|--------|------|-------------------|------|------------|
| LCP (Largest Contentful Paint) | ≤2.5s | ≤4s | >4s | <2.5s |
| FID (First Input Delay) | ≤100ms | ≤300ms | >300ms | <100ms |
| CLS (Cumulative Layout Shift) | ≤0.1 | ≤0.25 | >0.25 | <0.1 |
| TTFB (Time to First Byte) | ≤800ms | ≤1800ms | >1800ms | <600ms |

### Additional Metrics

| Metric | Target | Max Acceptable |
|--------|--------|----------------|
| First Contentful Paint (FCP) | <1.8s | <3s |
| Time to Interactive (TTI) | <3.8s | <7.3s |
| Speed Index | <3.4s | <5.8s |
| Total Blocking Time (TBT) | <200ms | <600ms |

### Bundle Size Targets

| Asset Type | Target | Max |
|------------|--------|-----|
| Initial JS Bundle | <100KB | <200KB |
| Initial CSS | <50KB | <100KB |
| Total Page Weight | <500KB | <1MB |
| Image Assets | Lazy loaded | N/A |

## Core Web Vitals

### Largest Contentful Paint (LCP)

**What it measures:** Loading performance - when the largest content element becomes visible.

**Optimization Strategies:**

1. **Optimize Images**
   - Use WebP format
   - Proper sizing (responsive images)
   - Lazy loading for below-the-fold images
   - Preload hero images

2. **Reduce Server Response Time**
   - Fast backend (FastAPI with async)
   - Database query optimization
   - Response compression (Gzip/Brotli)

3. **Eliminate Render-Blocking Resources**
   - Critical CSS inlined
   - Defer non-critical JavaScript
   - Use `preconnect` for external resources

**Implementation:**
```html
<!-- Preload hero image -->
<link rel="preload" as="image" href="/hero-image.webp">

<!-- Preconnect to external domains -->
<link rel="preconnect" href="https://fonts.googleapis.com">
```

### First Input Delay (FID)

**What it measures:** Interactivity - time from user interaction to browser response.

**Optimization Strategies:**

1. **Minimize Main Thread Work**
   - Code splitting
   - Lazy loading components
   - Web Workers for heavy computations

2. **Reduce JavaScript Execution Time**
   - Tree shaking unused code
   - Minification with Terser
   - Remove console.log in production

3. **Break Up Long Tasks**
   - Use `requestIdleCallback`
   - Virtualize long lists
   - Debounce/throttle event handlers

**Implementation:**
```javascript
// Lazy load components
const CompanyList = defineAsyncComponent(() =>
  import('./components/CompanyList.vue')
)

// Debounce search
const debouncedSearch = debounce(searchFunction, 300)
```

### Cumulative Layout Shift (CLS)

**What it measures:** Visual stability - unexpected layout shifts.

**Optimization Strategies:**

1. **Reserve Space for Dynamic Content**
   - Set width/height on images
   - Reserve space for ads/embeds
   - Use aspect-ratio CSS

2. **Avoid Inserting Content Above Existing**
   - Add new content below viewport
   - Use transforms instead of position changes

3. **Load Fonts Properly**
   - Use `font-display: swap`
   - Preload critical fonts

**Implementation:**
```css
/* Reserve aspect ratio for images */
.image-container {
  aspect-ratio: 16 / 9;
}

/* Font loading strategy */
@font-face {
  font-family: 'CustomFont';
  font-display: swap;
  src: url('/fonts/custom.woff2') format('woff2');
}
```

## Frontend Optimization

### Code Splitting

**Automatic Route-Based Splitting:**

Vue Router automatically splits by route:
```javascript
const routes = [
  {
    path: '/',
    component: () => import('./views/HomeView.vue')  // Lazy loaded
  }
]
```

**Manual Chunk Splitting:**

Configured in `vite.config.js`:
```javascript
manualChunks: (id) => {
  if (id.includes('node_modules/vue')) {
    return 'vue-vendor'  // Vue ecosystem in separate chunk
  }
  if (id.includes('node_modules/@vueuse')) {
    return 'vueuse'  // VueUse in separate chunk
  }
  if (id.includes('node_modules')) {
    return 'vendor'  // Other dependencies
  }
}
```

### Tree Shaking

**Automatic with Vite:**
- Unused exports are eliminated
- Works with ES modules only

**Best Practices:**
```javascript
// Good - tree-shakeable
import { ref, computed } from 'vue'

// Bad - imports everything
import * as Vue from 'vue'
```

### Minification

**JavaScript Minification (Terser):**
```javascript
terserOptions: {
  compress: {
    drop_console: true,  // Remove console.log
    drop_debugger: true,  // Remove debugger
    pure_funcs: ['console.log', 'console.info'],
    passes: 2  // Multiple compression passes
  },
  mangle: {
    safari10: true  // Safari compatibility
  }
}
```

**CSS Minification:**
- Automatic with Vite
- Removes whitespace, comments
- Optimizes selectors

### Image Optimization

**Format Selection:**
1. **WebP**: Modern format, 25-35% smaller than JPEG
2. **AVIF**: Even smaller, but limited browser support
3. **JPEG**: Fallback for photos
4. **PNG**: Fallback for graphics
5. **SVG**: Vector graphics (icons, logos)

**Lazy Loading:**
```html
<img
  src="image.webp"
  loading="lazy"
  alt="Description"
  width="800"
  height="600"
>
```

**Responsive Images:**
```html
<picture>
  <source
    srcset="hero-small.webp 400w, hero-medium.webp 800w, hero-large.webp 1200w"
    sizes="(max-width: 600px) 400px, (max-width: 1000px) 800px, 1200px"
    type="image/webp"
  >
  <img src="hero-large.jpg" alt="Hero">
</picture>
```

### CSS Optimization

**Critical CSS:**
- Inline critical CSS in `<head>`
- Load non-critical CSS async

**CSS Code Splitting:**
```javascript
// vite.config.js
build: {
  cssCodeSplit: true  // Split CSS by route
}
```

**Remove Unused CSS:**
- Bootstrap loaded via CDN
- Only import needed components
- Use PurgeCSS for custom CSS

## Backend Optimization

### Async Operations

**FastAPI with async/await:**
```python
@router.get("/companies")
async def get_companies(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Company))
    return result.scalars().all()
```

**Benefits:**
- Non-blocking I/O
- Handle more concurrent requests
- Better resource utilization

### Database Optimization

**Query Optimization:**

1. **Use Indexes:**
```python
class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)  # Indexed for fast lookups
```

2. **Avoid N+1 Queries:**
```python
# Good - eager loading
companies = await db.execute(
    select(Company).options(selectinload(Company.projects))
)

# Bad - N+1 problem
companies = await db.execute(select(Company))
for company in companies:
    projects = await db.execute(
        select(Project).where(Project.company_id == company.id)
    )
```

3. **Pagination:**
```python
@router.get("/companies")
async def get_companies(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Company).offset(skip).limit(limit)
    )
    return result.scalars().all()
```

### Response Compression

**Automatic Gzip Compression:**
- Configured in `CompressionMiddleware`
- Minimum size: 1000 bytes
- Compresses text responses

**Brotli Compression (Nginx):**
- Better compression than Gzip (~20% smaller)
- Requires Nginx module
- Fallback to Gzip for unsupported browsers

### Connection Pooling

**SQLAlchemy Connection Pool:**
```python
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,  # Max connections in pool
    max_overflow=10,  # Additional connections if needed
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600  # Recycle connections after 1 hour
)
```

## Network Optimization

### HTTP/2

**Benefits:**
- Multiplexing (multiple requests over one connection)
- Header compression
- Server push capabilities

**Nginx Configuration:**
```nginx
listen 443 ssl http2;
```

### Compression

**Gzip (Nginx):**
```nginx
gzip on;
gzip_comp_level 6;
gzip_min_length 1000;
gzip_types text/plain text/css application/json application/javascript;
```

**Brotli (Nginx with module):**
```nginx
brotli on;
brotli_comp_level 6;
brotli_types text/plain text/css application/json application/javascript;
```

### Resource Hints

**Preconnect to External Domains:**
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://cdn.jsdelivr.net">
```

**Prefetch Next Pages:**
```html
<link rel="prefetch" href="/about">
```

**Preload Critical Resources:**
```html
<link rel="preload" as="font" href="/fonts/custom.woff2" crossorigin>
```

## Caching Strategy

### Frontend Caching

**Service Worker (PWA):**
- Cache static assets
- Offline functionality
- Update strategy: Network-first for API, Cache-first for assets

**Browser Cache:**
```nginx
# JavaScript/CSS with hash in filename - 1 year cache
location ~* \.js$ {
  expires 1y;
  add_header Cache-Control "public, max-age=31536000, immutable";
}

# HTML - short cache with revalidation
location ~* \.html$ {
  expires 1h;
  add_header Cache-Control "public, max-age=3600, must-revalidate";
}

# Images - 1 year cache
location ~* \.(png|jpg|jpeg|gif|svg|webp)$ {
  expires 1y;
  add_header Cache-Control "public, max-age=31536000, immutable";
}
```

### Backend Caching

**Response Caching Middleware:**
```python
# CacheControlMiddleware adds appropriate headers
# GET requests with 200 status get cached
```

**API Response Caching:**
```python
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

@router.get("/companies")
@cache(expire=3600)  # Cache for 1 hour
async def get_companies():
    # Expensive database query
    return companies
```

### CDN Integration

**CloudFlare/Vercel/Netlify:**
- Edge caching worldwide
- Automatic compression
- DDoS protection
- SSL/TLS termination

**Cache-Control Headers:**
```
Cache-Control: public, max-age=31536000, immutable  # Static assets
Cache-Control: public, max-age=3600, must-revalidate  # HTML
Cache-Control: no-cache, no-store, must-revalidate  # Service worker
```

## Monitoring Performance

### Lighthouse Audits

**Run Lighthouse:**
```bash
# Via Chrome DevTools
# Via CLI
npm install -g lighthouse
lighthouse https://dashti.se --view
```

**CI/CD Integration:**

Already configured in `.github/workflows/ci-cd.yml`:
```yaml
- name: Run Lighthouse CI
  uses: treosh/lighthouse-ci-action@v10
  with:
    runs: 3
    uploadArtifacts: true
```

### WebPageTest

**URL:** https://www.webpagetest.org/

**Configuration:**
- Test from multiple locations
- 3G/4G/Cable connection speeds
- Multiple runs for consistency

### Real User Monitoring (RUM)

**Core Web Vitals Tracking:**

Already implemented in `frontend/src/utils/performance.js`:
```javascript
import { performanceMonitor } from '@/utils/performance'

// Automatically tracks:
// - LCP, FID, CLS, TTFB
// - Navigation timing
// - Resource timing
```

**View Metrics:**
- Frontend: Browser DevTools > Performance
- Backend: `GET /api/v1/metrics`

### Performance Budget

**Set in CI/CD:**
```json
{
  "budgets": [{
    "resourceSizes": [{
      "resourceType": "script",
      "budget": 200
    }, {
      "resourceType": "stylesheet",
      "budget": 100
    }, {
      "resourceType": "image",
      "budget": 500
    }]
  }]
}
```

## Performance Checklist

### Development

- [ ] Code split by route
- [ ] Lazy load components below fold
- [ ] Optimize images (WebP, proper sizing)
- [ ] Remove console.log statements
- [ ] Avoid memory leaks (cleanup in onUnmounted)
- [ ] Debounce/throttle frequent events
- [ ] Use production build for testing

### Build

- [ ] Minify JavaScript (Terser)
- [ ] Minify CSS
- [ ] Tree shake unused code
- [ ] Generate source maps (optional)
- [ ] Analyze bundle size (`ANALYZE=true npm run build`)
- [ ] Compress assets (Gzip/Brotli)

### Backend

- [ ] Use async/await for I/O operations
- [ ] Optimize database queries
- [ ] Add database indexes
- [ ] Implement connection pooling
- [ ] Enable response compression
- [ ] Add caching for expensive operations
- [ ] Monitor slow queries (>1s)

### Network

- [ ] Enable HTTP/2
- [ ] Configure Gzip compression
- [ ] Set appropriate cache headers
- [ ] Use CDN for static assets
- [ ] Implement resource hints (preconnect, prefetch)
- [ ] Minimize request count
- [ ] Optimize third-party scripts

### Deployment

- [ ] Configure CDN
- [ ] Set up caching strategy
- [ ] Enable compression
- [ ] Implement rate limiting
- [ ] Monitor Core Web Vitals
- [ ] Run Lighthouse audits
- [ ] Test on slow connections (3G)

## Troubleshooting

### Slow Page Load

**Symptoms:** Long Time to Interactive (TTI)

**Debug Steps:**
1. Run Lighthouse audit
2. Check Network tab for large resources
3. Analyze bundle size: `ANALYZE=true npm run build`
4. Check for render-blocking resources

**Solutions:**
- Code split large components
- Defer non-critical JavaScript
- Optimize images
- Reduce third-party scripts

### High Server Response Time

**Symptoms:** Long TTFB (Time to First Byte)

**Debug Steps:**
1. Check `/api/v1/metrics` for slow endpoints
2. Review logs for slow request warnings
3. Enable database query logging
4. Check server resources (CPU, memory)

**Solutions:**
- Optimize database queries
- Add database indexes
- Implement caching
- Scale server resources
- Use database connection pooling

### Large Bundle Size

**Symptoms:** JavaScript bundle >200KB

**Debug Steps:**
1. Run bundle analyzer: `ANALYZE=true npm run build`
2. Check what's included in each chunk
3. Look for duplicate dependencies

**Solutions:**
- Lazy load heavy components
- Check for accidental imports of large libraries
- Use tree-shakeable imports
- Consider alternative lighter libraries

### Poor CLS Score

**Symptoms:** Layout shifts during page load

**Debug Steps:**
1. Record page load in Chrome DevTools > Performance
2. Look for layout shifts
3. Check images without dimensions
4. Check for font loading causing shifts

**Solutions:**
- Set width/height on images
- Reserve space for dynamic content
- Use `font-display: swap`
- Avoid inserting content above existing

### Memory Leaks

**Symptoms:** Increasing memory usage over time

**Debug Steps:**
1. Chrome DevTools > Memory > Heap snapshot
2. Compare snapshots over time
3. Look for detached DOM nodes
4. Check for global event listeners

**Solutions:**
- Remove event listeners in `onUnmounted`
- Clear intervals/timeouts
- Unsubscribe from observables
- Avoid global references to components

## Resources

### Tools
- [Lighthouse](https://developers.google.com/web/tools/lighthouse) - Performance auditing
- [WebPageTest](https://www.webpagetest.org/) - Real-world performance testing
- [Chrome DevTools](https://developer.chrome.com/docs/devtools/) - Performance profiling
- [Bundle Analyzer](https://github.com/btd/rollup-plugin-visualizer) - Analyze bundle size
- [ImageOptim](https://imageoptim.com/) - Image compression

### Documentation
- [Web Vitals](https://web.dev/vitals/) - Core Web Vitals guide
- [Vite Performance](https://vitejs.dev/guide/performance.html) - Vite optimization guide
- [FastAPI Performance](https://fastapi.tiangolo.com/deployment/concepts/) - FastAPI deployment best practices
- [Nginx Optimization](https://www.nginx.com/blog/tuning-nginx/) - Nginx performance tuning

### Learning Resources
- [web.dev](https://web.dev/) - Web performance best practices
- [MDN Performance](https://developer.mozilla.org/en-US/docs/Web/Performance) - Performance guides
- [High Performance Browser Networking](https://hpbn.co/) - Network optimization

---

**Last Updated:** 2025-10-22
**Maintained By:** David Dashti
