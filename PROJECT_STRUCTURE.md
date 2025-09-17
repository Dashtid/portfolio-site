# Portfolio Site - Project Structure Documentation

## 📁 Directory Overview

```
Portfolio-site/
├── .claude/                    # Claude Code configuration
│   └── CLAUDE.md              # Project guidelines for Claude
├── .github/                   # GitHub Actions CI/CD
│   └── workflows/
│       └── ci.yml            # CI/CD pipeline configuration
├── build/                     # Build tools and configurations
│   ├── lighthouse.config.js   # Lighthouse CI configuration
│   ├── playwright.config.js   # Playwright test configuration
│   └── server.js             # Development server
├── config/                    # Additional configurations
│   ├── jest.config.js         # Jest testing configuration (duplicate)
│   └── staticwebapp.config.json # Azure Static Web Apps config
├── coverage/                  # Test coverage reports (generated)
├── docs/                      # Documentation
│   ├── CLAUDE.md             # Claude guidelines (duplicate)
│   └── README.md             # Main documentation
├── scripts/                   # Build and utility scripts
│   ├── add-sri-hashes.js     # Security: Add SRI hashes to CDN resources
│   ├── optimize-images.js    # Image optimization and WebP generation
│   ├── security-check.js     # Security vulnerability scanning
│   └── validate-links.js     # Link validation and health checks
├── site/                      # Main website content
│   ├── education/            # Education detail pages
│   ├── experience/           # Experience detail pages
│   ├── static/              # Static assets
│   │   ├── css/             # Stylesheets
│   │   ├── documents/       # PDFs and documents
│   │   ├── fonts/           # Web fonts (if any)
│   │   ├── images/          # Images and optimized variants
│   │   │   └── optimized/   # WebP and optimized images
│   │   └── js/              # JavaScript files
│   ├── index.html           # Main homepage
│   ├── market-analysis.html # Market analysis page
│   ├── manifest.webmanifest # PWA manifest
│   ├── robots.txt           # Search engine instructions
│   ├── sitemap.xml          # Site map for SEO
│   └── sw.js                # Service worker for PWA
├── tests/                    # Test suite
│   ├── integration/         # Integration tests
│   ├── unit/                # Unit tests
│   ├── *.spec.js           # Playwright E2E tests
│   ├── global-setup.js     # Test setup
│   └── global-teardown.js  # Test cleanup
├── .babelrc                 # Babel configuration
├── .gitignore              # Git ignore rules
├── jest.config.js          # Jest configuration (main)
├── package.json            # Project dependencies and scripts
├── package-lock.json       # Locked dependency versions
├── server.js               # Development server (duplicate)
└── staticwebapp.config.json # Azure config (duplicate)
```

## 🔧 Key Components Explained

### Core Website (`site/`)
- **Main Content**: Homepage and market analysis functionality
- **Detail Pages**: Separate pages for experience and education entries
- **Static Assets**: Organized CSS, JS, images, and documents
- **PWA Features**: Manifest, service worker for offline capability

### Build System (`scripts/`, `build/`)
- **Image Optimization**: Automatic WebP conversion and responsive variants
- **Security Tools**: SRI hash generation and vulnerability scanning
- **Link Validation**: Automated link health checking
- **Development Server**: Local development with live reload

### Testing Framework (`tests/`)
- **Unit Tests**: Component-level testing with Jest
- **Integration Tests**: Cross-component functionality testing
- **E2E Tests**: Browser automation with Playwright
- **Coverage Reports**: Comprehensive test coverage analysis

### CI/CD Pipeline (`.github/workflows/`)
- **Quality Checks**: Code formatting, linting, security scans
- **Automated Testing**: Unit, integration, and E2E tests
- **Performance Monitoring**: Lighthouse CI for performance metrics
- **Deployment**: Azure Static Web Apps integration

### Configuration Files
- **Jest**: Testing framework setup
- **Babel**: JavaScript transpilation
- **Playwright**: Browser automation configuration
- **Lighthouse**: Performance and accessibility auditing

## 📊 File Purpose Reference

### Essential Production Files
| File | Purpose | Status |
|------|---------|---------|
| `site/index.html` | Main homepage | ✅ Active |
| `site/market-analysis.html` | Trading widgets page | ✅ Active |
| `site/static/css/style.css` | Main stylesheet | ✅ Active |
| `site/static/js/theme.js` | Dark/light theme toggle | ✅ Active |
| `site/static/js/trading-widgets.js` | TradingView integration | ✅ Active |
| `site/manifest.webmanifest` | PWA configuration | ✅ Active |

### Build & Development Tools
| File | Purpose | Status |
|------|---------|---------|
| `scripts/optimize-images.js` | Image compression and WebP | ✅ Active |
| `scripts/security-check.js` | Vulnerability scanning | ✅ Active |
| `build/server.js` | Development server | ✅ Active |
| `package.json` | Dependencies and scripts | ✅ Active |

### Testing Infrastructure
| File | Purpose | Status |
|------|---------|---------|
| `jest.config.js` | Unit test configuration | ✅ Active |
| `build/playwright.config.js` | E2E test configuration | ✅ Active |
| `tests/unit/` | Jest unit tests | ✅ Active |
| `tests/*.spec.js` | Playwright E2E tests | ✅ Active |

### Duplicate Files (Candidates for Cleanup)
| File | Duplicate Location | Recommendation |
|------|-------------------|----------------|
| `server.js` | `build/server.js` | Remove root version |
| `config/jest.config.js` | `jest.config.js` | Remove config/ version |
| `staticwebapp.config.json` | `config/staticwebapp.config.json` | Keep root version |
| `docs/CLAUDE.md` | `.claude/CLAUDE.md` | Keep .claude/ version |

## 🎯 Optimization Opportunities

### 1. File Organization
- **Remove duplicate configurations** in `config/` directory
- **Consolidate documentation** to avoid version conflicts
- **Move build tools** to dedicated build directory structure

### 2. Asset Management
- **Optimize images** using the fixed image optimization script
- **Implement responsive images** for better performance
- **Add WebP fallbacks** for older browser support

### 3. Code Quality
- **Fix remaining test failures** in Jest unit tests
- **Improve test coverage** for better reliability
- **Update security dependencies** to resolve vulnerabilities

### 4. Performance
- **Enable compression** for static assets
- **Implement caching strategies** for better loading times
- **Optimize bundle sizes** for JavaScript and CSS

## 🚀 Technology Stack

- **Frontend**: Vanilla HTML5, CSS3, JavaScript (ES6+)
- **Styling**: Bootstrap 5.3.0 + Custom CSS
- **Build**: npm scripts with custom Node.js tools
- **Testing**: Jest (unit) + Playwright (E2E)
- **CI/CD**: GitHub Actions
- **Hosting**: Azure Static Web Apps
- **Performance**: Lighthouse CI monitoring
- **Security**: SRI hashes, vulnerability scanning
- **PWA**: Service worker, manifest, offline capability

## 📈 Current Status

### ✅ Working Well
- Development server with live reload
- Comprehensive testing framework
- Security-focused build pipeline
- PWA capabilities with offline support
- Responsive design with dark/light themes

### 🔧 Areas for Improvement
- Remove duplicate configuration files
- Fix remaining unit test failures
- Update Node.js dependencies
- Optimize image pipeline for existing files
- Consolidate documentation

### 🎯 Next Steps
1. Clean up duplicate files and configurations
2. Fix failing unit tests for complete CI/CD pipeline
3. Optimize assets and improve performance metrics
4. Update dependencies to resolve security warnings
5. Document deployment and maintenance procedures