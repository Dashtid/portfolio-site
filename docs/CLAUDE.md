# Portfolio Website Development Guide

## Overview
This is David Dashti's professional portfolio website - a static site focused on cybersecurity in healthcare, built with modern web standards and deployed via Azure Static Web Apps.

## Project Architecture

### Tech Stack
- **Frontend**: Vanilla HTML5, CSS3 (with CSS custom properties), ES6+ JavaScript
- **Styling**: Custom CSS with design tokens, Bootstrap 5 for layout
- **Build**: No build process - static files only
- **Deployment**: GitHub Actions → Azure Static Web Apps
- **PWA**: Service Worker, Web App Manifest
- **Security**: Comprehensive CSP, security headers

### Directory Structure
```
├── .github/workflows/        # GitHub Actions CI/CD
├── site/                    # Source code (gets deployed)
│   ├── *.html              # Individual pages (8 pages total)
│   ├── static/
│   │   ├── css/style.css   # Main stylesheet (1,112 lines)
│   │   ├── js/             # JavaScript modules
│   │   ├── images/         # Optimized assets
│   │   └── documents/      # PDF files
│   ├── manifest.json       # PWA manifest
│   └── sw.js              # Service worker
├── staticwebapp.config.json # Azure SWA configuration
├── package.json            # Development dependencies
└── CLAUDE.md              # This file (NOT tracked in git)
```

## Development Workflow

### Local Development
```bash
# Start local server (if available)
npm run dev

# Or serve files directly
python -m http.server 8000
# Then visit: http://localhost:8000/site/
```

### Code Quality
```bash
# Format code
npm run format

# Lint code
npm run lint

# Run tests
npm test

# Build optimizations
npm run build
```

### Git Workflow
1. Create feature branch from `master`
2. Make changes in `site/` directory
3. Run quality checks: `npm run lint && npm test`
4. Commit with conventional commits format
5. Push and create PR
6. GitHub Actions will run CI/CD pipeline
7. Merge to `master` triggers production deployment

## Key Features & Implementation

### Theme System
- Located: `site/static/js/theme.js`
- Uses CSS custom properties for theming
- Supports system preference detection
- Persists user choice in localStorage
- Accessible with proper ARIA attributes

### Security Implementation
- **CSP**: Restrictive Content Security Policy in `staticwebapp.config.json`
- **Headers**: HSTS, X-Frame-Options, etc.
- **SRI**: Subresource Integrity for CDN resources
- **Input Validation**: Client-side form validation

### Performance Features
- **Service Worker**: Caches static assets for offline support
- **Image Optimization**: WebP with JPEG fallbacks
- **Lazy Loading**: Images and non-critical resources
- **Preloading**: Critical resources in HTML head
- **CSS**: Critical CSS inlined, non-critical deferred

### Accessibility
- **ARIA**: Proper roles, labels, and properties
- **Focus Management**: Visible focus indicators
- **Keyboard Navigation**: Full keyboard support
- **Screen Reader**: Optimized for assistive technology
- **Color Contrast**: WCAG AA compliant

## External Integrations

### GitHub API
- Fetches repository data dynamically
- Displays project cards with filtering/sorting
- Rate limiting handled gracefully

### TradingView Widgets
- Financial market data embedding
- Responsive widget configuration
- Privacy-conscious loading

## Common Tasks

### Adding New Pages
1. Create HTML file in `site/` directory
2. Follow existing structure and accessibility patterns
3. Add navigation links to relevant pages
4. Update service worker cache list
5. Test across browsers and devices

### Updating Styles
- Use CSS custom properties (design tokens) in `:root`
- Follow BEM naming convention for new classes
- Ensure dark theme compatibility
- Test with reduced motion preferences

### JavaScript Enhancements
- Use ES6+ classes and modules
- Follow established patterns (ThemeManager, ScrollManager, etc.)
- Maintain accessibility in dynamic interactions
- Handle errors gracefully with fallbacks

### Content Updates
- Edit HTML files directly
- Optimize images before adding (WebP + fallbacks)
- Update meta tags and structured data
- Validate markup and check accessibility

## Testing Strategy

### Manual Testing
- Cross-browser compatibility (Chrome, Firefox, Safari, Edge)
- Mobile responsiveness (iOS Safari, Chrome Mobile)
- Accessibility testing with screen readers
- Performance testing with throttled connections

### Automated Testing (when implemented)
- **Unit Tests**: JavaScript utility functions
- **Integration Tests**: Theme switching, navigation
- **E2E Tests**: User workflows with Playwright
- **Performance Tests**: Lighthouse CI
- **Visual Regression**: Screenshot comparisons

## Deployment Process

### Staging
- Feature branches deploy to preview environments
- GitHub Actions creates preview URLs
- Manual testing before merge

### Production
- Merges to `master` trigger production deployment
- Zero-downtime deployment via Azure Static Web Apps
- Automatic cache invalidation
- DNS pointed to dashti.se

## Performance Standards

### Lighthouse Targets
- Performance: 95+
- Accessibility: 100
- Best Practices: 95+
- SEO: 100

### Core Web Vitals
- LCP: < 2.5s
- FID: < 100ms
- CLS: < 0.1

## Security Checklist

- [ ] CSP headers properly configured
- [ ] No inline scripts without nonces
- [ ] External resources use SRI
- [ ] HTTPS enforced everywhere
- [ ] No sensitive data in client code
- [ ] XSS prevention measures in place

## Maintenance

### Regular Tasks
- Dependency updates (monthly)
- Performance audit (quarterly)
- Accessibility audit (quarterly)
- Security review (quarterly)
- Content updates (as needed)

### Monitoring
- Azure Static Web Apps analytics
- Lighthouse CI performance tracking
- Error tracking in browser console
- User feedback collection

## Troubleshooting

### Common Issues

**Service Worker not updating:**
```javascript
// Clear cache and reload
caches.keys().then(names => {
    names.forEach(name => caches.delete(name));
});
```

**Theme not persisting:**
- Check localStorage availability
- Verify ThemeManager initialization
- Confirm CSS custom properties support

**Images not loading:**
- Verify file paths are relative to site root
- Check image formats and optimization
- Confirm lazy loading implementation

### Debug Tools
- Chrome DevTools Lighthouse
- Firefox Developer Tools Accessibility Inspector
- axe browser extension
- WAVE accessibility checker

## Best Practices

### HTML
- Semantic markup with proper document outline
- Valid HTML5 with proper DOCTYPE
- Accessible form labels and ARIA attributes
- Optimized meta tags and Open Graph data

### CSS
- Use CSS custom properties for theming
- Follow mobile-first responsive approach
- Minimize layout shifts with proper sizing
- Use logical properties for internationalization

### JavaScript
- Progressive enhancement approach
- Handle errors gracefully with try/catch
- Use modern APIs with feature detection
- Optimize for performance with requestAnimationFrame

### Images
- Use appropriate formats (WebP, AVIF when supported)
- Provide proper alt text for accessibility
- Implement lazy loading for below-fold images
- Use responsive images with srcset

## Resources

- [Azure Static Web Apps Documentation](https://docs.microsoft.com/en-us/azure/static-web-apps/)
- [Web Content Accessibility Guidelines](https://www.w3.org/WAG/WCAG21/quickref/)
- [Core Web Vitals](https://web.dev/vitals/)
- [Progressive Web Apps](https://web.dev/progressive-web-apps/)
- [Security Headers](https://securityheaders.com/)

---

*This file contains comprehensive development instructions and should NOT be committed to git. It's maintained locally for Claude Code and other AI assistants.*