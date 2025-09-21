# Portfolio Site - Claude Code Guidelines

## Project Overview

This is David Dashti's professional portfolio website showcasing his expertise in cybersecurity and regulatory compliance for medical software and AI systems. The site is built with modern web technologies and follows best practices for performance, accessibility, and SEO.

## Development Environment

**Operating System**: Windows 11
**Shell**: Git Bash / PowerShell / Command Prompt
**Important**: Always use Windows-compatible commands:
- Use `dir` instead of `ls` for Command Prompt
- Use PowerShell commands when appropriate
- File paths use backslashes (`\`) in Windows
- Use `python -m http.server` for local development server
- Git Bash provides Unix-like commands but context should be Windows-aware

## Development Guidelines

### 1. Content Standards
- Keep all content professional and accurate
- Ensure all technical skills and experience descriptions are up-to-date
- Maintain consistency in terminology and formatting
- Follow accessibility guidelines for all content

### 2. Code Quality
- Use semantic HTML5 elements
- Ensure responsive design across all devices
- Optimize images and assets for web performance
- Maintain clean, readable CSS and JavaScript

### 3. SEO and Performance
- Keep page load times under 3 seconds
- Maintain proper meta tags and structured data
- Use appropriate heading hierarchy (h1, h2, h3, etc.)
- Optimize for Core Web Vitals

### 4. Security
- No sensitive information in the codebase
- Use HTTPS for all external resources
- Implement proper Content Security Policy
- Regular dependency updates

## Key Sections to Maintain

### Profile Information
- Current role: QA/RA & Security Specialist at Hermes Medical Solutions
- Focus areas: Cybersecurity governance, NIS2/ISO 27001 compliance, AI Act preparation
- Technical skills: Windows Server, Docker, PowerShell, Python, Git

### Experience Updates
- Keep work experience current and accurate
- Update project descriptions as needed
- Maintain links to relevant documentation and certificates

### Skills Section
- Technical skills should reflect current competencies
- Update skill levels based on experience growth
- Add new technologies and frameworks as learned

## Testing & Quality Assurance

### E2E Testing with Playwright
**IMPORTANT**: E2E tests are configured to auto-start the dev server. Do NOT start it manually.

**Commands:**
- `npm run test:e2e` - Run all E2E tests (auto-starts dev server)
- `npm run test:e2e:headed` - Run tests with browser UI visible
- `npm run test:e2e:debug` - Run tests in debug mode
- `npm run test:report` - Open HTML test report

**Test Configuration:**
- **Main config**: `config/playwright.config.js` (used by npm scripts)
- **E2E directory config**: `tests/e2e/playwright.config.js` (alternative config)
- **Test files**: Located in `tests/e2e/` (*.spec.js)

**Running Tests:**
1. **From project root**: `npm run test:e2e` (recommended)
2. **From e2e directory**: `cd tests/e2e && npx playwright test`

**Debugging Failed Tests:**
- Failed tests create screenshots in `test-results/`
- Use `npm run test:report` to view detailed HTML reports
- Run `npm run test:e2e:debug` for step-by-step debugging

**Windows-Specific Notes:**
- Playwright may need additional browser installations: `npx playwright install`
- Test timeouts may need adjustment on slower Windows systems

### Other Testing
- Unit tests: `npm run test:unit`
- Linting: `npm run lint`
- Format check: `npm run format:check`

## Build and Deployment
- Test all changes locally before deployment
- Run E2E tests to ensure functionality: `npm run test:e2e`
- Run accessibility and performance audits
- Validate HTML and CSS
- Check responsive design on multiple devices

## Contact Information
- Ensure all contact links are functional
- Keep LinkedIn and GitHub profiles up-to-date
- Verify email addresses are current

## Learning and Communication
- Always explain coding actions and decisions to help the user learn
- Describe why specific approaches or technologies are chosen
- Explain the purpose and functionality of code changes
- Provide context about best practices and coding patterns used
- Provide detailed explanations in the console when performing tasks, as many concepts may be new to the user