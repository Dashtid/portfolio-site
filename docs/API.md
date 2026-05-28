# API Reference

The API is consumed exclusively by the same-origin frontend on
[dashti.se](https://dashti.se). Swagger UI (`/api/docs`) and ReDoc
(`/api/redoc`) are exposed in development only — disabled in production
since there are no third-party API consumers.

## Endpoints

| Resource | Methods | Auth |
|----------|---------|------|
| `/api/v1/companies` | GET, POST, PUT, DELETE | Public read, admin write |
| `/api/v1/education` | GET, POST, PUT, DELETE | Public read, admin write |
| `/api/v1/projects` | GET, POST, PUT, DELETE | Public read, admin write |
| `/api/v1/skills` | GET, POST, PUT, DELETE | Public read, admin write |
| `/api/v1/documents` | GET | Public |
| `/api/v1/github/stats/{user}` | GET | Public |
| `/api/v1/analytics/track/pageview` | POST | Public (rate-limited) |
| `/api/v1/analytics/stats/*` | GET | Admin |
| `/api/v1/auth/github` | GET | Public (OAuth initiation) |
| `/api/v1/auth/me` | GET | Required |
| `/api/v1/auth/refresh` | POST | Refresh-token cookie |
| `/api/v1/auth/logout` | POST | Clears auth cookies |
| `/api/v1/health` | GET | Public |
| `/api/v1/health/{ready,live,detailed}` | GET | Public |

## Authentication

- **Login**: GitHub OAuth via `/api/v1/auth/github` (CSRF state is single-use, IP-bound, 5-minute TTL)
- **Sessions**: JWT access + refresh tokens issued as HTTP-only, `secure`, `samesite=lax` cookies. The frontend never touches tokens directly.
- **Refresh**: `/api/v1/auth/refresh` rotates the cookies and returns `{"refreshed": true}` — the response body is intentionally token-free so an XSS payload calling the endpoint cannot extract credentials.
- **Bearer header fallback**: still accepted by `/api/v1/auth/me` and other protected endpoints for non-browser API clients (curl, test suites). The frontend itself uses cookies only.

## Rate Limits

- General public endpoints: 100 requests/minute per IP
- Auth endpoints (`/api/v1/auth/*`): 10 requests/minute per IP
- Health checks: unlimited

## Analytics & Privacy

Page views are pseudonymised before storage: the client IP is hashed with
HMAC-SHA256 keyed off the application secret (see `app/utils/ip_hash.py`)
and only the 64-bit truncated digest is persisted. Country is resolved
via ipapi.co at write time and cached for 24h.
