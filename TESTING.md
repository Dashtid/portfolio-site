# Testing Documentation

Comprehensive testing guide for the portfolio website project covering unit tests, integration tests, E2E tests, and accessibility testing.

## Table of Contents

- [Overview](#overview)
- [Testing Stack](#testing-stack)
- [Frontend Testing](#frontend-testing)
- [Backend Testing](#backend-testing)
- [E2E Testing](#e2e-testing)
- [Accessibility Testing](#accessibility-testing)
- [Running Tests](#running-tests)
- [Writing Tests](#writing-tests)
- [Coverage Goals](#coverage-goals)
- [CI/CD Integration](#cicd-integration)
- [Troubleshooting](#troubleshooting)

## Overview

This project implements a multi-layered testing strategy:

- **Frontend Unit Tests** - Component and composable testing with Vitest
- **Backend Unit Tests** - API endpoint testing with pytest
- **E2E Tests** - Cross-browser integration testing with Playwright
- **Accessibility Tests** - WCAG 2.1 AA compliance testing with axe-core

### Coverage Thresholds

All test suites maintain minimum 80% coverage for:
- Lines
- Functions
- Branches
- Statements

## Testing Stack

### Frontend
- **Vitest** - Fast, ESM-native test runner for Vue 3
- **@vue/test-utils** - Official Vue component testing library
- **happy-dom** - Lightweight DOM implementation
- **@vitest/ui** - Web-based test UI

### Backend
- **pytest** - Python testing framework
- **pytest-asyncio** - Async support for FastAPI
- **pytest-cov** - Coverage reporting
- **TestClient** - FastAPI test client

### E2E
- **Playwright** - Cross-browser testing framework
- **@axe-core/playwright** - Accessibility testing integration

### CI/CD
- **GitHub Actions** - Automated test execution
- **CodeCov** - Coverage tracking and reporting

## Frontend Testing

### Setup

Frontend tests are located in `frontend/tests/`:
```
frontend/tests/
├── setup.js              # Global test setup
├── unit/
│   ├── components/       # Component tests
│   │   ├── ThemeToggle.spec.js
│   │   ├── BackToTop.spec.js
│   │   └── NavBar.spec.js
│   └── composables/      # Composable tests
│       └── useTheme.spec.js
```

### Configuration

**`frontend/vitest.config.js`:**
- Environment: happy-dom (faster than jsdom)
- Coverage provider: v8
- Global test utilities enabled
- Setup file: `tests/setup.js`

### Global Mocks

**`frontend/tests/setup.js`** provides:
- `window.matchMedia` - For theme preference detection
- `IntersectionObserver` - For scroll animations
- `localStorage` - For persistent storage
- `requestAnimationFrame` - For animations

### Component Testing Pattern

Example from `ThemeToggle.spec.js`:

```javascript
import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import ThemeToggle from '@/components/ThemeToggle.vue'

describe('ThemeToggle', () => {
  let wrapper

  beforeEach(() => {
    localStorage.clear()
    document.documentElement.removeAttribute('data-theme')
  })

  it('toggles theme on click', async () => {
    wrapper = mount(ThemeToggle)
    await wrapper.find('button').trigger('click')
    expect(localStorage.getItem('portfolio-theme')).toBeTruthy()
  })

  it('applies theme to html element', async () => {
    wrapper = mount(ThemeToggle)
    await wrapper.find('button').trigger('click')
    const htmlElement = document.documentElement
    expect(htmlElement.hasAttribute('data-theme')).toBe(true)
  })
})
```

### Composable Testing Pattern

Example from `useTheme.spec.js`:

```javascript
import { describe, it, expect, beforeEach } from 'vitest'
import { useTheme } from '@/composables/useTheme'

describe('useTheme', () => {
  beforeEach(() => {
    localStorage.clear()
    document.documentElement.removeAttribute('data-theme')
  })

  it('sets theme to dark', () => {
    const { isDark, setTheme } = useTheme()
    setTheme('dark')
    expect(isDark.value).toBe(true)
  })

  it('respects system preference when no stored theme', () => {
    window.matchMedia = vi.fn().mockImplementation(query => ({
      matches: query === '(prefers-color-scheme: dark)'
    }))
    const { isDark } = useTheme()
    expect(isDark.value).toBe(true)
  })
})
```

### Running Frontend Tests

```bash
# Run all tests
cd frontend
npm test

# Run with UI
npm run test:ui

# Run with coverage
npm run coverage

# Watch mode
npm test -- --watch

# Run specific test file
npm test -- ThemeToggle.spec.js
```

## Backend Testing

### Setup

Backend tests are located in `backend/tests/`:
```
backend/tests/
├── conftest.py           # Pytest fixtures
├── test_health.py        # Health check endpoints
├── test_github.py        # GitHub API integration
└── test_auth.py          # Authentication (existing)
```

### Configuration

**`backend/tests/conftest.py`** provides:
- In-memory SQLite test database (`:memory:`)
- Test client with dependency overrides
- Auth token fixtures
- Database session fixtures

### Test Database Pattern

```python
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.testclient import TestClient

@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provides isolated test database session."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with TestSessionLocal() as session:
        yield session
        await session.rollback()

@pytest.fixture(scope="function")
def client(db_session: AsyncSession) -> TestClient:
    """Provides test client with overridden dependencies."""
    async def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
```

### Endpoint Testing Pattern

Example from `test_health.py`:

```python
def test_basic_health_check(client: TestClient):
    """Test basic health endpoint."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data

def test_readiness_check(client: TestClient):
    """Test readiness check with database."""
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["checks"]["database"] == "connected"
```

### Mocking External APIs

Example from `test_github.py`:

```python
from unittest.mock import patch, MagicMock

@patch("app.api.v1.github.httpx.AsyncClient")
def test_get_github_stats_success(mock_client, client: TestClient):
    """Test GitHub stats with mocked API."""
    mock_user_response = MagicMock()
    mock_user_response.status_code = 200
    mock_user_response.json.return_value = {
        "public_repos": 25,
        "followers": 50
    }

    mock_client_instance = MagicMock()
    mock_client_instance.get.return_value = mock_user_response
    mock_client.return_value.__aenter__.return_value = mock_client_instance

    response = client.get("/api/v1/github/stats/testuser")
    assert response.status_code == 200
    assert "public_repos" in response.json()
```

### Running Backend Tests

```bash
# Run all tests
cd backend
pytest

# Run with coverage
pytest --cov=app --cov-report=html --cov-report=term

# Run specific test file
pytest tests/test_health.py

# Run with verbose output
pytest -v

# Run specific test
pytest tests/test_health.py::test_basic_health_check
```

## E2E Testing

### Setup

E2E tests are located in `tests/e2e/` (project root):
```
tests/e2e/
├── homepage.spec.js      # Homepage functionality
├── navigation.spec.js    # Navigation flows
├── theme.spec.js         # Theme switching
└── accessibility.spec.js # WCAG 2.1 AA compliance
```

### Configuration

**`playwright.config.js`** (project root):
- 5 browser configurations (Desktop Chrome, Firefox, Safari, Mobile Chrome, Mobile Safari)
- Built-in web server for frontend dev server
- Automatic screenshot/video on failure
- Parallel test execution
- Retry on failure in CI (2 retries)

### Browser Projects

```javascript
projects: [
  { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
  { name: 'webkit', use: { ...devices['Desktop Safari'] } },
  { name: 'Mobile Chrome', use: { ...devices['Pixel 5'] } },
  { name: 'Mobile Safari', use: { ...devices['iPhone 12'] } }
]
```

### E2E Testing Patterns

**Page Navigation:**
```javascript
test('displays all main sections', async ({ page }) => {
  await page.goto('/')
  await expect(page.locator('#hero')).toBeVisible()
  await expect(page.locator('#experience')).toBeVisible()
  await expect(page.locator('#education')).toBeVisible()
  await expect(page.locator('#projects')).toBeVisible()
})
```

**User Interactions:**
```javascript
test('theme toggle works', async ({ page }) => {
  await page.goto('/')
  const themeToggle = page.locator('.theme-toggle')

  await themeToggle.click()
  await page.waitForTimeout(300)

  const theme = await page.evaluate(() =>
    document.documentElement.getAttribute('data-theme')
  )
  expect(theme).toBeTruthy()
})
```

**State Persistence:**
```javascript
test('theme persists after reload', async ({ page }) => {
  await page.goto('/')
  await page.locator('.theme-toggle').click()

  const initialTheme = await page.evaluate(() =>
    document.documentElement.getAttribute('data-theme')
  )

  await page.reload()

  const reloadedTheme = await page.evaluate(() =>
    document.documentElement.getAttribute('data-theme')
  )

  expect(reloadedTheme).toBe(initialTheme)
})
```

### Running E2E Tests

```bash
# Run all E2E tests
npm run test:e2e

# Run in UI mode (interactive)
npm run test:e2e:ui

# Run in debug mode
npm run test:e2e:debug

# Run headed (see browser)
npm run test:e2e:headed

# Run specific browser
npx playwright test --project=chromium

# Run specific test file
npx playwright test homepage.spec.js

# Show test report
npm run test:e2e:report
```

## Accessibility Testing

### WCAG 2.1 Level AA Compliance

Our accessibility tests ensure compliance with WCAG 2.1 Level AA standards, which is the ADA Title II requirement (effective April 2024).

### Test Coverage

**`tests/e2e/accessibility.spec.js`** includes:

1. **Automated Scans** (57% detection rate)
   - Homepage violations
   - Section-specific violations
   - Navigation violations
   - Color contrast violations
   - ARIA misuse violations

2. **Manual Tests** (Required for full compliance)
   - Keyboard navigation
   - Image alt text
   - Link discernible text
   - Form labels
   - Heading hierarchy
   - Theme toggle accessibility
   - Back-to-top button accessibility
   - Skip navigation links
   - Language attributes
   - Landmark regions

### axe-core Integration

```javascript
import AxeBuilder from '@axe-core/playwright'

test('homepage should not have accessibility issues', async ({ page }) => {
  const accessibilityScanResults = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
    .analyze()

  expect(accessibilityScanResults.violations).toEqual([])
})
```

### Keyboard Navigation Testing

```javascript
test('keyboard navigation works for interactive elements', async ({ page }) => {
  await page.goto('/')

  // Tab to first element
  await page.keyboard.press('Tab')
  let focusedElement = await page.evaluate(() =>
    document.activeElement.tagName
  )
  expect(focusedElement).toBeTruthy()

  // Navigate to nav links
  let tabCount = 0
  let navLinkFocused = false

  while (tabCount < 20 && !navLinkFocused) {
    await page.keyboard.press('Tab')
    tabCount++

    const className = await page.evaluate(() =>
      document.activeElement.className
    )
    if (className && className.includes('nav-link')) {
      navLinkFocused = true
    }
  }

  expect(navLinkFocused).toBeTruthy()
})
```

### Color Contrast Testing

```javascript
test('color contrast meets WCAG AA standards', async ({ page }) => {
  const contrastResults = await new AxeBuilder({ page })
    .withTags(['wcag2aa'])
    .include('body')
    .analyze()

  const contrastViolations = contrastResults.violations.filter(v =>
    v.id === 'color-contrast'
  )

  expect(contrastViolations).toEqual([])
})
```

## Running Tests

### Local Development

```bash
# Frontend unit tests
cd frontend
npm test

# Backend unit tests
cd backend
pytest

# E2E tests (from root)
npm run test:e2e

# All tests (from root)
npm run test:e2e && cd frontend && npm test && cd ../backend && pytest
```

### Watch Mode (Development)

```bash
# Frontend unit tests
cd frontend
npm test -- --watch

# Backend unit tests
cd backend
pytest-watch
# or
ptw
```

### Coverage Reports

```bash
# Frontend coverage
cd frontend
npm run coverage
open coverage/index.html

# Backend coverage
cd backend
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

## Writing Tests

### Frontend Component Test Template

```javascript
import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { mount } from '@vue/test-utils'
import ComponentName from '@/components/ComponentName.vue'

describe('ComponentName', () => {
  let wrapper

  beforeEach(() => {
    // Setup before each test
    localStorage.clear()
  })

  afterEach(() => {
    // Cleanup after each test
    if (wrapper) {
      wrapper.unmount()
    }
  })

  it('renders correctly', () => {
    wrapper = mount(ComponentName)
    expect(wrapper.exists()).toBe(true)
  })

  it('handles user interaction', async () => {
    wrapper = mount(ComponentName)
    await wrapper.find('button').trigger('click')
    expect(wrapper.emitted()).toHaveProperty('event-name')
  })

  it('updates reactive state', async () => {
    wrapper = mount(ComponentName, {
      props: { initialValue: 'test' }
    })
    await wrapper.vm.$nextTick()
    expect(wrapper.vm.someValue).toBe('expected')
  })
})
```

### Backend Endpoint Test Template

```python
import pytest
from fastapi.testclient import TestClient

def test_endpoint_success(client: TestClient):
    """Test successful endpoint response."""
    response = client.get("/api/v1/endpoint")
    assert response.status_code == 200
    data = response.json()
    assert "expected_field" in data

def test_endpoint_validation(client: TestClient):
    """Test input validation."""
    response = client.post("/api/v1/endpoint", json={})
    assert response.status_code == 422  # Validation error

def test_endpoint_error_handling(client: TestClient):
    """Test error handling."""
    response = client.get("/api/v1/endpoint/invalid")
    assert response.status_code in [404, 400]
```

### E2E Test Template

```javascript
import { test, expect } from '@playwright/test'

test.describe('Feature Name', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('user can complete flow', async ({ page }) => {
    // Arrange
    const element = page.locator('[data-testid="element"]')

    // Act
    await element.click()
    await page.waitForTimeout(300)

    // Assert
    await expect(page.locator('.result')).toBeVisible()
  })

  test('handles error state', async ({ page }) => {
    // Test error scenarios
    await page.route('**/api/**', route => route.abort())
    await expect(page.locator('.error')).toBeVisible()
  })
})
```

## Coverage Goals

### Current Thresholds (80%)

All test suites maintain minimum 80% coverage:

**Frontend (`vitest.config.js`):**
```javascript
coverage: {
  thresholds: {
    lines: 80,
    functions: 80,
    branches: 80,
    statements: 80
  }
}
```

**Backend (`pytest`):**
```bash
pytest --cov=app --cov-fail-under=80
```

### Coverage Best Practices

1. **Test User Flows** - Focus on real user interactions
2. **Edge Cases** - Test error states and boundaries
3. **Accessibility** - Ensure keyboard navigation and ARIA
4. **State Management** - Test state changes and persistence
5. **API Integration** - Mock external dependencies
6. **Performance** - Test loading states and timeouts

### Ignoring Coverage

**Frontend - Exclude from coverage:**
```javascript
// vitest.config.js
coverage: {
  exclude: [
    'node_modules/',
    'tests/',
    '*.config.js',
    'dist/'
  ]
}
```

**Backend - Exclude from coverage:**
```python
# .coveragerc or pyproject.toml
[tool.coverage.run]
omit = [
    "*/tests/*",
    "*/migrations/*",
    "*/config.py"
]
```

## CI/CD Integration

### GitHub Actions Workflow

**`.github/workflows/ci-cd.yml`** includes:

1. **Frontend Quality Job**
   - Lint code
   - Run unit tests with coverage
   - Upload coverage to CodeCov
   - Build production bundle

2. **Backend Quality Job**
   - Lint with flake8
   - Run pytest with coverage
   - Upload coverage to CodeCov

3. **E2E Tests Job**
   - Install Playwright browsers
   - Build frontend
   - Run E2E tests across all browsers
   - Upload test reports and videos on failure

4. **Dependencies**
   - Docker build waits for all tests to pass
   - Deployment waits for all tests + security scan

### Test Failure Handling

- **Pull Requests** - Tests must pass before merge
- **Main Branch** - Failed tests block deployment
- **Artifacts** - Test reports and videos uploaded on failure
- **Retries** - E2E tests retry twice in CI environment

### CodeCov Integration

Coverage reports are automatically uploaded to CodeCov:
- Frontend: `frontend/coverage/lcov.info`
- Backend: `backend/coverage.xml`

Configure thresholds in `codecov.yml`:
```yaml
coverage:
  status:
    project:
      default:
        target: 80%
        threshold: 2%
```

## Troubleshooting

### Common Issues

#### Frontend Tests

**Issue: "window.matchMedia is not a function"**
- **Solution:** Ensure `tests/setup.js` is loaded in `vitest.config.js`

**Issue: "localStorage is not defined"**
- **Solution:** Use happy-dom environment in `vitest.config.js`

**Issue: "Component not updating after trigger"**
- **Solution:** Use `await wrapper.vm.$nextTick()` after state changes

#### Backend Tests

**Issue: "Database connection error"**
- **Solution:** Check `conftest.py` test database configuration

**Issue: "Fixture not found"**
- **Solution:** Ensure pytest discovers `conftest.py` in tests directory

**Issue: "Async test hanging"**
- **Solution:** Use `@pytest.mark.asyncio` decorator for async tests

#### E2E Tests

**Issue: "Timeout waiting for element"**
- **Solution:** Increase timeout or use `waitForLoadState('networkidle')`

**Issue: "Browser not installed"**
- **Solution:** Run `npx playwright install --with-deps`

**Issue: "Test flaky in CI"**
- **Solution:** Add explicit waits, use `page.waitForTimeout()` carefully

### Debug Mode

**Frontend:**
```bash
cd frontend
npm test -- --reporter=verbose
```

**Backend:**
```bash
cd backend
pytest -vv --log-cli-level=DEBUG
```

**E2E:**
```bash
npm run test:e2e:debug
# or
PWDEBUG=1 npx playwright test
```

### Performance Tips

1. **Run in parallel** - Playwright runs tests in parallel by default
2. **Use beforeEach sparingly** - Expensive setup can slow tests
3. **Mock external APIs** - Avoid real HTTP calls in tests
4. **Use test.only** - Focus on single test during development
5. **Clean up resources** - Unmount components, close connections

## Resources

### Documentation
- [Vitest](https://vitest.dev/)
- [Vue Test Utils](https://test-utils.vuejs.org/)
- [Playwright](https://playwright.dev/)
- [pytest](https://docs.pytest.org/)
- [axe-core](https://github.com/dequelabs/axe-core)
- [WCAG 2.1](https://www.w3.org/WAI/WCAG21/quickref/)

### Best Practices
- [Testing Library Guiding Principles](https://testing-library.com/docs/guiding-principles/)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Accessibility Testing Guide](https://www.a11yproject.com/)

---

**Last Updated:** 2025-10-22
**Maintained By:** David Dashti
**Questions?** Open an issue on GitHub
