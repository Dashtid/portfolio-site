# Portfolio Site - Project Structure Documentation

## 📁 Directory Overview

```
Portfolio-site/
├── .claude/                    # Claude Code configuration
│   └── CLAUDE.md              # Project guidelines for Claude
├── .github/                   # GitHub Actions CI/CD
│   └── workflows/
│       ├── ci.yml            # Main CI/CD pipeline configuration
│       └── azure-static-web-apps.yml # Azure deployment workflow
├── .husky/                    # Git hooks for code quality
│   └── pre-commit            # Pre-commit hook for linting
├── .lighthouseci/             # Lighthouse CI reports (generated)
├── .vscode/                   # VS Code configuration
├── .zap/                      # OWASP ZAP security scan results (generated)
├── build/                     # Build tools and development server
│   └── server.js             # Development server with live reload
├── coverage/                  # Test coverage reports (generated)
├── scripts/                   # Build and utility scripts
│   ├── optimize-images.js    # Image optimization and WebP generation
│   ├── security-check.js     # Security vulnerability scanning
│   └── validate-links.js     # Link validation and health checks
├── site/                      # Main website content
│   ├── education/            # Education detail pages
│   ├── experience/           # Experience detail pages
│   ├── static/              # Static assets
│   │   ├── css/             # Stylesheets (source and minified)
│   │   ├── documents/       # PDFs and documents
│   │   ├── images/          # Images and optimized variants
│   │   │   └── optimized/   # WebP and responsive image variants
│   │   └── js/              # JavaScript files (source and bundled)
│   ├── index.html           # Main homepage
│   ├── market-analysis.html # Market analysis page
│   ├── manifest.webmanifest # PWA manifest
│   ├── robots.txt           # Search engine instructions
│   ├── sitemap.xml          # Site map for SEO
│   └── sw.js                # Service worker for PWA
├── test-results/             # Playwright test results (generated)
├── tests/                    # Test suite
│   ├── unit/                # Unit tests (Jest)
│   ├── *.spec.js           # Playwright E2E tests
│   ├── global-setup.js     # Test setup
│   └── global-teardown.js  # Test cleanup
├── .babelrc                 # Babel configuration
├── .editorconfig           # Editor configuration
├── .eslintignore           # ESLint ignore patterns
├── .eslintrc.js            # ESLint configuration
├── .gitignore              # Git ignore rules
├── .htmlvalidaterc.json    # HTML validation configuration
├── .lighthouserc.js        # Lighthouse CI configuration
├── .prettierignore         # Prettier ignore patterns
├── .prettierrc.json        # Prettier formatting configuration
├── .stylelintignore        # Stylelint ignore patterns
├── .stylelintrc.json       # Stylelint CSS linting configuration
├── jest.config.js          # Jest testing configuration
├── lighthouse.config.js    # Lighthouse performance testing
├── package.json            # Project dependencies and scripts
├── package-lock.json       # Locked dependency versions
├── playwright.config.js    # Playwright E2E testing configuration
├── PROJECT_STRUCTURE.md    # This documentation file
└── staticwebapp.config.json # Azure Static Web Apps configuration
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

### Configuration Files Organization
| File | Purpose | Location |
|------|---------|----------|
| `.eslintrc.js` | JavaScript linting rules | Root (with .prettierignore integration) |
| `.prettierrc.json` | Code formatting configuration | Root |
| `.stylelintrc.json` | CSS linting rules | Root |
| `jest.config.js` | Unit testing configuration | Root |
| `playwright.config.js` | E2E testing configuration | Root |
| `lighthouse.config.js` | Performance testing | Root |

## 🎯 Recent Improvements

### 1. File Organization ✅
- **Removed duplicate configurations** - cleaned up build/ directory duplicates
- **Consolidated configuration files** - all configs now in root directory
- **Updated ignore files** - added .prettierignore and .stylelintignore

### 2. Asset Management ✅
- **Fixed image optimization script** - prevented duplicate image generation
- **Cleaned up 124 duplicate images** - reduced from 162 to 38 optimized images
- **Implemented proper responsive variants** - logical mobile/tablet/desktop/large sizes

### 3. Code Quality ✅
- **Resolved ESLint/Prettier conflicts** - disabled conflicting rules
- **Enhanced security** - added SRI hashes to Bootstrap CDN resources
- **Improved HTML validation** - fixed DOCTYPE and void element issues

### 4. CI/CD Pipeline ✅
- **Fixed infinite formatting loops** - resolved space-before-function-paren conflicts
- **Enhanced ignore patterns** - prevent processing of generated files
- **Improved build reliability** - eliminated recurring pipeline failures

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
- **Stable CI/CD pipeline** - resolved all formatting conflicts
- **Clean project structure** - removed duplicates and organized configs
- **Optimized assets** - efficient image handling with responsive variants
- **Security enhancements** - SRI hashes and vulnerability scanning
- **Development experience** - reliable build and testing processes
- **PWA capabilities** - offline support and manifest configuration
- **Responsive design** - dark/light themes with smooth transitions

### 🔧 Areas for Future Enhancement
- **Test coverage expansion** - additional unit tests for new features
- **Performance monitoring** - continued Lighthouse CI optimization
- **Dependency updates** - regular security and feature updates
- **Documentation** - API and component documentation as project grows

### 🎯 Maintenance Tasks
1. **Regular dependency updates** - monthly security and feature updates
2. **Performance monitoring** - track Core Web Vitals through Lighthouse CI
3. **Security scanning** - automated vulnerability assessment in CI/CD
4. **Image optimization** - automatic processing of new assets
5. **Code quality** - continuous linting and formatting enforcement