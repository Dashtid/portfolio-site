# Monitoring & Observability Guide

Comprehensive monitoring, logging, error tracking, and analytics documentation for the portfolio website.

## Table of Contents

- [Overview](#overview)
- [Logging](#logging)
- [Error Tracking](#error-tracking)
- [Performance Monitoring](#performance-monitoring)
- [Analytics](#analytics)
- [Metrics Endpoint](#metrics-endpoint)
- [Configuration](#configuration)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)

## Overview

This project implements a comprehensive observability stack:

**Backend (FastAPI):**
- Structured JSON logging with request tracking
- Error tracking with stack traces
- Performance monitoring with response time tracking
- Prometheus-compatible metrics endpoint
- Gzip compression and caching middleware

**Frontend (Vue 3):**
- Privacy-compliant analytics (Plausible/Umami)
- Client-side error tracking
- Core Web Vitals monitoring (LCP, FID, CLS, TTFB)
- Resource timing API integration

**Infrastructure:**
- Nginx with enhanced caching and compression
- Rate limiting for API protection
- Security headers

## Logging

### Backend Logging

**Structured JSON Logging:**

All backend logs are output in JSON format for easy parsing and analysis.

**Log Format:**
```json
{
  "timestamp": "2025-10-22T12:00:00.000Z",
  "level": "INFO",
  "logger": "app.middleware.logging",
  "message": "Request completed",
  "request_id": "123e4567-e89b-12d3-a456-426614174000",
  "method": "GET",
  "path": "/api/v1/companies",
  "status_code": 200,
  "duration_ms": 45.23
}
```

**Log Levels:**

| Level | Usage | Example |
|-------|-------|---------|
| DEBUG | Development debugging | Variable values, state changes |
| INFO | Normal operations | Request/response, startup/shutdown |
| WARNING | Potential issues | Slow requests (>1s), deprecated usage |
| ERROR | Recoverable errors | Failed API calls, validation errors |
| CRITICAL | Unhandled exceptions | Application crashes, data corruption |

**Configuration:**

Set log level in `.env`:
```bash
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

**Sensitive Data Masking:**

The logger automatically masks sensitive fields:
- password
- token
- api_key
- secret
- authorization
- access_token
- refresh_token
- jwt

Example:
```json
{
  "user": {
    "username": "admin",
    "password": "***REDACTED***",
    "api_key": "***REDACTED***"
  }
}
```

**Viewing Logs:**

```bash
# Backend logs (JSON format)
docker-compose logs -f backend

# Filter by level
docker-compose logs backend | grep '"level":"ERROR"'

# Follow specific request
docker-compose logs backend | grep '"request_id":"abc123"'
```

### Frontend Logging

**Development:**
- Console logs enabled
- Vue warnings displayed
- Performance metrics logged

**Production:**
- Console logs removed (terser configuration)
- Only errors tracked
- Performance metrics sent to backend

## Error Tracking

### Backend Error Tracking

**Automatic Capture:**

The `ErrorTrackingMiddleware` automatically captures:
- HTTP exceptions (4xx, 5xx)
- Unhandled Python exceptions
- Stack traces with context

**Error Log Format:**
```json
{
  "timestamp": "2025-10-22T12:00:00.000Z",
  "level": "CRITICAL",
  "message": "Unhandled exception: ValueError: Invalid input",
  "request_id": "abc123",
  "error_type": "ValueError",
  "error_message": "Invalid input",
  "stack_trace": "Traceback (most recent call last)...",
  "method": "POST",
  "path": "/api/v1/companies",
  "client_ip": "192.168.1.1",
  "user_agent": "Mozilla/5.0..."
}
```

**Manual Error Tracking:**

```python
from app.middleware.error_tracking import track_error

try:
    risky_operation()
except Exception as error:
    track_error(error, context={
        "user_id": user.id,
        "operation": "data_import"
    })
```

**Configuration:**

```bash
ERROR_TRACKING_ENABLED=true
ERROR_TRACKING_DSN=  # Optional Sentry DSN
```

### Frontend Error Tracking

**Automatic Capture:**

The error tracker captures:
- Uncaught JavaScript errors
- Unhandled promise rejections
- Vue component errors

**Error Data:**
```javascript
{
  type: 'error',
  message: 'Cannot read property of undefined',
  filename: 'HomeView.vue',
  lineno: 42,
  colno: 10,
  stack: '...',
  timestamp: '2025-10-22T12:00:00.000Z',
  url: 'https://dashti.se/home',
  userAgent: 'Mozilla/5.0...'
}
```

**Manual Error Tracking:**

```javascript
import { trackError } from '@/utils/errorTracking'

try {
  await fetchData()
} catch (error) {
  trackError(error, {
    component: 'CompanyList',
    action: 'fetch_companies'
  })
}
```

**Configuration:**

```bash
VITE_ERROR_TRACKING_ENABLED=true
VITE_API_URL=http://localhost:8000
```

## Performance Monitoring

### Backend Performance

**Automatic Tracking:**

The `PerformanceMiddleware` tracks:
- Request count per endpoint
- Response times (avg, min, max)
- Status code distribution
- Error counts per endpoint

**Slow Request Logging:**

Requests taking >1 second are logged as warnings:
```json
{
  "level": "WARNING",
  "message": "Slow request detected: 1234.56ms",
  "request_id": "abc123",
  "method": "GET",
  "path": "/api/v1/github/stats/username",
  "duration_ms": 1234.56
}
```

**Performance Headers:**

Every response includes:
```
X-Request-ID: 123e4567-e89b-12d3-a456-426614174000
X-Response-Time: 45.23ms
```

### Frontend Performance

**Core Web Vitals:**

Automatically tracked:
- **LCP** (Largest Contentful Paint): Target <2.5s
- **FID** (First Input Delay): Target <100ms
- **CLS** (Cumulative Layout Shift): Target <0.1
- **TTFB** (Time to First Byte): Target <600ms

**Navigation Timing:**

Tracked metrics:
- DNS lookup time
- TCP connection time
- Request/response time
- DOM processing time
- Total load time

**Resource Timing:**

Tracked for:
- Images (average load time)
- Scripts (average load time)
- Stylesheets (average load time)

**Manual Performance Marks:**

```javascript
import { performanceMonitor } from '@/utils/performance'

// Mark start
performanceMonitor.mark('data-fetch-start')

// ... perform operation ...

// Mark end and measure
performanceMonitor.mark('data-fetch-end')
performanceMonitor.measure('data-fetch', 'data-fetch-start', 'data-fetch-end')
```

**Configuration:**

```bash
VITE_METRICS_ENABLED=true
VITE_API_URL=http://localhost:8000
```

## Analytics

### Privacy-Compliant Tracking

**Supported Providers:**
- **Plausible Analytics** (recommended) - EU-hosted, GDPR-compliant
- **Umami** - Open-source, self-hostable

**Features:**
- Cookie-less tracking (no consent banner required)
- No personally identifiable information (PII) collected
- GDPR, CCPA, PECR compliant out-of-the-box
- EU data residency

**Configuration:**

```bash
# .env
VITE_ANALYTICS_ENABLED=true
VITE_ANALYTICS_PROVIDER=plausible  # or 'umami'
VITE_ANALYTICS_SITE_ID=dashti.se
VITE_ANALYTICS_URL=https://plausible.io/js/script.js
```

**Tracked Events:**

Automatic:
- Page views (SPA-aware)
- Navigation

Manual tracking available:
```javascript
import { useAnalytics } from '@/composables/useAnalytics'

const { trackEvent, trackNavigation, trackThemeToggle } = useAnalytics()

// Track custom event
trackEvent('Button Click', { button: 'Contact', location: 'Hero' })

// Track navigation
trackNavigation('About')

// Track theme toggle
trackThemeToggle('dark')
```

**Available Tracking Methods:**

| Method | Usage |
|--------|-------|
| `track(name, props)` | Generic event tracking |
| `trackNavigation(section)` | Section navigation clicks |
| `trackThemeToggle(theme)` | Dark/light mode toggle |
| `trackButtonClick(name, location)` | Button interactions |
| `trackExternalLink(url, label)` | Outbound link clicks |
| `trackContact(method)` | Contact interactions |
| `trackProject(action, name)` | Project card interactions |
| `trackScroll(section)` | Scroll tracking |
| `trackGitHubStats(username)` | GitHub stats viewed |
| `trackBackToTop()` | Back-to-top button |

**Analytics Dashboard:**

Access your analytics:
- **Plausible**: https://plausible.io/dashti.se
- **Umami**: Your self-hosted URL

## Metrics Endpoint

### Accessing Metrics

**Endpoint:** `GET /api/v1/metrics`

**Response Format:**
```json
{
  "total_requests": 1234,
  "endpoints": {
    "GET /api/v1/companies": {
      "count": 456,
      "avg_response_time_ms": 45.23,
      "min_response_time_ms": 12.34,
      "max_response_time_ms": 234.56,
      "errors": 0
    },
    "POST /api/v1/companies": {
      "count": 10,
      "avg_response_time_ms": 123.45,
      "min_response_time_ms": 98.76,
      "max_response_time_ms": 156.78,
      "errors": 2
    }
  },
  "status_codes": {
    "200": 1100,
    "400": 12,
    "404": 8,
    "500": 2
  }
}
```

**Reset Metrics:** `POST /api/v1/metrics/reset`

**Health Check:** `GET /api/v1/metrics/health`

### Prometheus Integration (Optional)

The metrics endpoint returns JSON format. For Prometheus integration, you can:

1. Use a JSON exporter
2. Or create a custom exporter:

```python
# Example Prometheus format converter
from prometheus_client import generate_latest, REGISTRY, Counter, Histogram

# Add to metrics.py
request_count = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration')

@router.get("/prometheus")
async def prometheus_metrics():
    return Response(generate_latest(REGISTRY), media_type="text/plain")
```

## Configuration

### Environment Variables

**Backend (.env):**
```bash
# Logging
LOG_LEVEL=INFO

# Analytics
ANALYTICS_ENABLED=true
ANALYTICS_SITE_ID=
ANALYTICS_URL=

# Error Tracking
ERROR_TRACKING_ENABLED=true
ERROR_TRACKING_DSN=  # Optional Sentry DSN

# Metrics
METRICS_ENABLED=true
```

**Frontend (.env):**
```bash
# Analytics
VITE_ANALYTICS_ENABLED=true
VITE_ANALYTICS_PROVIDER=plausible
VITE_ANALYTICS_SITE_ID=dashti.se
VITE_ANALYTICS_URL=https://plausible.io/js/script.js

# Error Tracking
VITE_ERROR_TRACKING_ENABLED=true

# Performance Monitoring
VITE_METRICS_ENABLED=true

# API URL
VITE_API_URL=http://localhost:8000
```

### Disabling Monitoring

To disable specific monitoring features:

**Disable All Monitoring:**
```bash
# Backend
ERROR_TRACKING_ENABLED=false
METRICS_ENABLED=false
ANALYTICS_ENABLED=false

# Frontend
VITE_ANALYTICS_ENABLED=false
VITE_ERROR_TRACKING_ENABLED=false
VITE_METRICS_ENABLED=false
```

**Disable Specific Middleware:**

Edit `backend/app/main.py`:
```python
# Comment out middleware you don't want
# app.add_middleware(PerformanceMiddleware)
# app.add_middleware(ErrorTrackingMiddleware)
# app.add_middleware(LoggingMiddleware)
```

## Best Practices

### Logging Best Practices

1. **Use Appropriate Log Levels**
   - DEBUG: Only in development
   - INFO: Normal operations
   - WARNING: Potential issues
   - ERROR: Recoverable errors
   - CRITICAL: Unhandled exceptions

2. **Include Context**
   ```python
   logger.info(
       "User action completed",
       extra={
           "user_id": user.id,
           "action": "create_company",
           "duration_ms": 123.45
       }
   )
   ```

3. **Never Log Sensitive Data**
   - The sensitive data filter helps, but be explicit
   - Don't log: passwords, tokens, credit cards, PII

4. **Use Structured Logging**
   - Always use `extra` parameter for additional data
   - Keep log messages consistent

### Error Tracking Best Practices

1. **Add Context to Errors**
   ```javascript
   trackError(error, {
       component: 'CompanyList',
       user_action: 'delete_company',
       company_id: companyId
   })
   ```

2. **Don't Catch and Silence Errors**
   - Always log or track caught errors
   - Don't use empty catch blocks

3. **Set Error Boundaries**
   - Use Vue error boundaries
   - Graceful degradation

### Performance Monitoring Best Practices

1. **Set Performance Budgets**
   - LCP < 2.5s
   - FID < 100ms
   - CLS < 0.1

2. **Monitor Slow Requests**
   - Check logs for warnings
   - Investigate requests >1s

3. **Optimize Based on Data**
   - Use metrics to identify bottlenecks
   - Focus on high-traffic endpoints

### Analytics Best Practices

1. **Respect User Privacy**
   - Use privacy-friendly analytics
   - No PII collection
   - Provide opt-out

2. **Track Meaningful Events**
   - User interactions
   - Feature usage
   - Conversion goals

3. **Don't Over-Track**
   - Only track what you'll use
   - Avoid tracking every click

## Troubleshooting

### Logs Not Appearing

**Issue:** No logs in console/files

**Solutions:**
1. Check `LOG_LEVEL` is set correctly
2. Verify middleware is added in `main.py`
3. Check Docker logs: `docker-compose logs backend`

### Metrics Endpoint Returns Empty

**Issue:** `/api/v1/metrics` shows no data

**Solutions:**
1. Verify `METRICS_ENABLED=true`
2. Make some requests to generate data
3. Check `PerformanceMiddleware` is active

### Analytics Not Tracking

**Issue:** No page views in analytics dashboard

**Solutions:**
1. Verify `VITE_ANALYTICS_ENABLED=true`
2. Check `VITE_ANALYTICS_SITE_ID` is correct
3. Check browser console for errors
4. Verify analytics script is loaded (Network tab)
5. Check ad blocker isn't blocking analytics

### Error Tracking Not Working

**Issue:** Errors not being logged/sent

**Solutions:**
1. Verify `ERROR_TRACKING_ENABLED=true` (backend)
2. Verify `VITE_ERROR_TRACKING_ENABLED=true` (frontend)
3. Check network tab for failed POST requests
4. Verify error tracking middleware is active

### Performance Issues

**Issue:** High response times

**Solutions:**
1. Check `/api/v1/metrics` for slow endpoints
2. Review logs for warnings about slow requests
3. Enable database query logging
4. Check for N+1 queries
5. Add database indexes
6. Implement caching

## Resources

### Documentation
- [Plausible Analytics](https://plausible.io/docs)
- [Umami Analytics](https://umami.is/docs)
- [FastAPI Logging](https://fastapi.tiangolo.com/tutorial/logging/)
- [Web Vitals](https://web.dev/vitals/)
- [GDPR Compliance](https://gdpr.eu/)

### Tools
- [Lighthouse](https://developers.google.com/web/tools/lighthouse) - Performance auditing
- [WebPageTest](https://www.webpagetest.org/) - Detailed performance analysis
- [Chrome DevTools](https://developer.chrome.com/docs/devtools/) - Browser debugging

---

**Last Updated:** 2025-10-22
**Maintained By:** David Dashti
