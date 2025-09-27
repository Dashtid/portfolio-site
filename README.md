# David Dashti - Portfolio Website

> Professional portfolio showcasing expertise in cybersecurity and regulatory compliance for medical software and AI systems.

[![CI/CD Pipeline](https://github.com/Dashtid/portfolio-site/workflows/CI/badge.svg)](https://github.com/Dashtid/portfolio-site/actions)
[![Lighthouse CI](https://img.shields.io/badge/Lighthouse-CI-brightgreen)](https://github.com/Dashtid/portfolio-site/actions)
[![Security Scan](https://img.shields.io/badge/Security-Scanned-blue)](https://github.com/Dashtid/portfolio-site/actions)

## 🚀 Live Site

**Production**: [https://dashti.se](https://dashti.se)

## 📋 About

This portfolio website showcases my professional experience as a QA/RA & Security Specialist at Hermes Medical Solutions, focusing on:

- **Cybersecurity Governance** for medical software systems
- **Regulatory Compliance** (NIS2, ISO 27001, AI Act preparation)
- **Medical Device Software** quality assurance and validation
- **Interactive Development Portfolio** with GitHub integration

## 🛠️ Technology Stack

- **Frontend**: Vanilla HTML5, CSS3, JavaScript (ES6+)
- **Styling**: Bootstrap 5.3.0 + Custom CSS with Dark/Light themes
- **Build Tools**: Custom Node.js scripts with npm
- **Testing**: Jest (unit) + Playwright (E2E)
- **CI/CD**: GitHub Actions with quality gates
- **Hosting**: Azure Static Web Apps
- **Performance**: Lighthouse CI monitoring
- **Security**: SRI hashes, OWASP ZAP scanning
- **PWA**: Service worker, offline capability

## 🏗️ Project Structure

```
portfolio-site/
├── config/                    # Configuration files
├── site/                      # Website content
│   ├── static/               # Assets (CSS, JS, images)
│   └── *.html               # Pages
├── scripts/                   # Build and utility scripts
├── tests/                     # Test suite
├── build/                     # Development tools
└── README.md                 # This file
```

## 🚦 Getting Started

### Prerequisites

- Node.js 18+ and npm
- Git

### Installation

```bash
# Clone the repository
git clone https://github.com/Dashtid/portfolio-site.git
cd portfolio-site

# Install dependencies
npm install

# Start development server
npm run dev
```

### Development Commands

```bash
# Development
npm run dev              # Start dev server at http://localhost:3000
npm run dev:open         # Start dev server and open browser

# Building
npm run build            # Build and optimize all assets
npm run optimize:images  # Optimize images and generate WebP
npm run minify:css       # Minify CSS files
npm run minify:js        # Bundle and minify JavaScript

# Quality Assurance
npm run lint             # Run all linting (JS, HTML, CSS)
npm run format           # Format code with Prettier
npm run format:check     # Check code formatting

# Testing
npm test                 # Run all tests
npm run test:unit        # Run Jest unit tests
npm run test:e2e         # Run Playwright E2E tests
npm run lighthouse       # Run Lighthouse performance audit

# Security
npm run security:audit   # Security vulnerability audit
```

## 🧪 Testing

### Unit Tests (Jest)
```bash
npm run test:unit
npm run test:unit:watch     # Watch mode
npm run test:unit:coverage  # With coverage report
```

### E2E Tests (Playwright)
```bash
npm run test:e2e
npm run test:e2e:headed     # Headed mode
npm run test:e2e:debug      # Debug mode
npm run test:report         # View test report
```

## 📊 Performance & Quality

### Lighthouse CI
- **Performance**: Automated monitoring of Core Web Vitals
- **Accessibility**: WCAG compliance testing
- **SEO**: Search engine optimization validation
- **Best Practices**: Security and modern web standards

### Code Quality
- **ESLint**: JavaScript linting with Standard config
- **Prettier**: Consistent code formatting
- **Stylelint**: CSS linting and best practices
- **HTML Validation**: W3C compliance checking

### Security
- **SRI Hashes**: Subresource Integrity for CDN resources
- **OWASP ZAP**: Automated security vulnerability scanning
- **Dependency Audit**: Regular npm security auditing
- **CSP Headers**: Content Security Policy implementation

## 🌟 Features

### Core Website
- **Responsive Design**: Mobile-first approach with Bootstrap
- **Dark/Light Theme**: User preference with system detection
- **PWA Support**: Offline capability and installable
- **SEO Optimized**: Meta tags, structured data, sitemap


### Performance Optimizations
- **Image Optimization**: Automatic WebP conversion and responsive variants
- **Asset Minification**: CSS and JavaScript compression
- **Lazy Loading**: Efficient resource loading
- **Caching Strategy**: Optimized for fast load times

## 🔧 Configuration

Configuration files are organized in the `/config` directory:

- **ESLint**: JavaScript linting rules and Prettier integration
- **Prettier**: Code formatting standards
- **Jest**: Unit testing configuration
- **Playwright**: E2E testing setup
- **Lighthouse**: Performance testing parameters

## 🚀 Deployment

### Automatic Deployment
- **Production**: Deploys automatically on push to `master`
- **Staging**: Deploys automatically on pull requests
- **Quality Gates**: All tests and quality checks must pass

### Manual Deployment
```bash
npm run build           # Build optimized assets
# Deploy to your hosting provider
```

## 📈 Monitoring

### Continuous Integration
- **GitHub Actions**: Automated testing and quality checks
- **Quality Gates**: Linting, testing, security, performance
- **Artifact Storage**: Test results and performance reports

### Performance Monitoring
- **Lighthouse CI**: Automated performance auditing
- **Core Web Vitals**: LCP, FID, CLS tracking
- **Bundle Analysis**: JavaScript and CSS optimization

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📧 Contact

**David Dashti**
- LinkedIn: [David Dashti](https://linkedin.com/in/daviddashti)
- Email: [contact@dashti.se](mailto:contact@dashti.se)
- Website: [https://dashti.se](https://dashti.se)

---

*Built with ❤️ and modern web technologies*