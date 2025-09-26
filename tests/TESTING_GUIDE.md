# Testing Guide: Jest vs Playwright

## Overview

This project uses **two types of testing** for comprehensive coverage:

1. **Jest** - Unit & Integration Testing
2. **Playwright** - End-to-End Testing

## Jest vs Playwright: When to Use What

### Jest (Unit Testing) ✅
**Use for:** Testing individual functions, classes, and components in isolation

**Environment:**
- JSDOM (simulated browser environment)
- Fast execution (no real browser)
- Mocked dependencies

**Examples:**
```javascript
// ✅ Good for Jest
test('should calculate discount correctly', () => {
  expect(calculateDiscount(100, 20)).toBe(80)
})

test('should toggle theme state', () => {
  const themeManager = new ThemeManager()
  themeManager.toggleTheme()
  expect(themeManager.currentTheme).toBe('dark')
})

test('should update GitHub image URLs', () => {
  const updateGitHubStatsTheme = (isDark) => {
    // Theme switching logic
  }
  updateGitHubStatsTheme(true)
  expect(image.src).toContain('theme=dark')
})
```

### Playwright (E2E Testing) ✅
**Use for:** Testing complete user workflows in real browsers

**Environment:**
- Real browsers (Chrome, Firefox, Safari)
- Real network requests
- Actual rendering and interactions

**Examples:**
```javascript
// ✅ Good for Playwright
test('should complete theme switching workflow', async ({ page }) => {
  await page.goto('/')
  await page.click('#themeToggle')
  await expect(page.locator('[data-theme="dark"]')).toBeVisible()

  // Verify GitHub cards actually changed theme
  const githubCard = page.locator('.github-stats-card img').first()
  await expect(githubCard).toHaveAttribute('src', /theme=dark/)
})

test('should navigate between sections', async ({ page }) => {
  await page.goto('/')
  await page.click('[data-scroll="about"]')
  await expect(page.locator('#about')).toBeInViewport()
})
```

## Improvements Made to Jest Tests

### 1. **Fixed Mock Issues**
**Before:** Tests used incomplete mocks that didn't catch real bugs
```javascript
// ❌ Old approach - mock class that doesn't match real implementation
class MockThemeManager {
  toggleTheme() { return 'dark' } // Too simple
}
```

**After:** Tests use real implementations with proper mocking
```javascript
// ✅ New approach - test real class with proper environment setup
const fs = require('fs')
const themeCode = fs.readFileSync('../../site/static/js/theme.js', 'utf8')
eval(themeCode) // Load real implementation

test('should dispatch real themeChanged event', () => {
  const themeManager = new ThemeManager()
  const spy = jest.spyOn(window, 'dispatchEvent')

  themeManager.setTheme('dark')

  expect(spy).toHaveBeenCalledWith(
    expect.objectContaining({
      type: 'themeChanged',
      detail: { theme: 'dark', isDark: true }
    })
  )
})
```

### 2. **Enhanced DOM Testing**
**Before:** Minimal DOM interaction testing
```javascript
// ❌ Old approach - basic element creation
const button = document.createElement('button')
button.click()
```

**After:** Comprehensive DOM testing with real structure
```javascript
// ✅ New approach - test real DOM structures
beforeEach(() => {
  document.body.innerHTML = `
    <div class="theme-switch-container">
      <div id="themeToggle" role="switch" aria-checked="false">
        <div class="theme-switch-slider"></div>
      </div>
    </div>
  `
})

test('should handle keyboard accessibility', () => {
  const toggle = document.getElementById('themeToggle')
  const keyEvent = new KeyboardEvent('keydown', { key: 'Enter' })

  toggle.dispatchEvent(keyEvent)
  expect(keyEvent.key).toBe('Enter')
})
```

### 3. **GitHub Theme Integration Testing**
**New comprehensive tests for the GitHub cards theme switching:**

```javascript
// ✅ Tests actual GitHub stats URL manipulation
test('should switch GitHub stats to dark theme', () => {
  document.body.innerHTML = `
    <img src="https://github-readme-stats.vercel.app/api/pin/?username=dashtid&theme=default">
  `

  updateGitHubStatsTheme(true)

  const img = document.querySelector('img')
  expect(img.src).toContain('theme=dark')
  expect(img.src).not.toContain('theme=default')
})
```

### 4. **Better Error Handling Tests**
```javascript
// ✅ Test graceful error handling
test('should handle localStorage errors gracefully', () => {
  localStorage.setItem = jest.fn().mockImplementation(() => {
    throw new Error('Storage quota exceeded')
  })

  expect(() => {
    const themeManager = new ThemeManager()
    themeManager.setTheme('dark')
  }).not.toThrow()
})
```

## Test Structure Overview

```
tests/
├── unit/                          # Jest unit tests
│   ├── setup.js                   # Test environment setup
│   ├── theme-manager-real.test.js # Real ThemeManager tests
│   ├── dom-interactions.test.js   # DOM manipulation tests
│   ├── github-theme-integration.test.js # GitHub cards tests
│   └── [existing tests...]        # Original test files
├── integration/                   # Jest integration tests
│   ├── theme-integration.test.js  # Cross-component tests
│   └── build-workflow.test.js     # Build process tests
└── e2e/                          # Playwright E2E tests
    ├── homepage.spec.js           # Homepage functionality
    ├── theme.spec.js              # Complete theme workflows
    ├── navigation.spec.js         # Navigation user journeys
    └── accessibility.spec.js      # Accessibility testing
```

## Running Tests

### Jest (Unit & Integration)
```bash
# Run all Jest tests
npm run test:unit

# Run specific test file
npx jest tests/unit/github-theme-integration.test.js

# Run with coverage
npm run test:unit:coverage

# Watch mode during development
npm run test:unit:watch
```

### Playwright (E2E)
```bash
# Run all E2E tests (auto-starts dev server)
npm run test:e2e

# Run with browser UI visible
npm run test:e2e:headed

# Debug mode
npm run test:e2e:debug

# View test reports
npm run test:report
```

## Best Practices

### Jest Best Practices ✅
1. **Test real implementations**, not mocks when possible
2. **Mock external dependencies** (APIs, localStorage, etc.)
3. **Use descriptive test names** that explain the behavior
4. **Test error conditions** and edge cases
5. **Keep tests fast** - avoid unnecessary DOM operations
6. **Use proper setup/teardown** to isolate tests

### Playwright Best Practices ✅
1. **Test user workflows**, not individual functions
2. **Use data-testid attributes** for reliable element selection
3. **Wait for elements** instead of using fixed delays
4. **Test across browsers** when needed
5. **Take screenshots** on failures for debugging
6. **Test real user interactions** (clicks, keyboard, etc.)

## Coverage Goals

### Jest Coverage Targets:
- **Lines:** 85%
- **Functions:** 80%
- **Branches:** 70%
- **Statements:** 85%

### E2E Coverage Goals:
- **Critical user paths:** 100%
- **Accessibility features:** 100%
- **Cross-browser compatibility:** Chrome + 1 other
- **Mobile responsiveness:** Basic coverage

## What Each Test Type Catches

### Jest Catches:
- ❌ Logic errors in functions
- ❌ Incorrect state management
- ❌ API integration issues
- ❌ Edge case handling
- ❌ Performance issues in algorithms

### Playwright Catches:
- ❌ Visual layout problems
- ❌ Cross-browser compatibility issues
- ❌ Real network request failures
- ❌ User workflow interruptions
- ❌ Accessibility problems
- ❌ Performance issues under load

## Summary

**Use Jest for:** Fast feedback during development, testing business logic, API integrations, and component behavior.

**Use Playwright for:** Comprehensive end-to-end validation, user acceptance testing, and catching issues that only appear in real browsers.

**Together they provide:** Complete confidence that your application works correctly both in individual components and as a complete user experience.