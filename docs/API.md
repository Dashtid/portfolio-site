# API Reference

The API is consumed exclusively by the same-origin frontend on
[dashti.se](https://dashti.se). Swagger UI (`/api/docs`) and ReDoc
(`/api/redoc`) are exposed in development only — disabled in production
since there are no third-party API consumers.

## Endpoints

| Resource                                                 | Methods                | Auth                                                                                                                                          |
| -------------------------------------------------------- | ---------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| `/api/v1/companies`                                      | GET, POST, PUT, DELETE | Public read, admin write                                                                                                                      |
| `/api/v1/education`                                      | GET, POST, PUT, DELETE | Public read, admin write                                                                                                                      |
| `/api/v1/projects`                                       | GET, POST, PUT, DELETE | Public read, admin write                                                                                                                      |
| `/api/v1/skills`                                         | GET, POST, PUT, DELETE | Public read, admin write                                                                                                                      |
| `/api/v1/documents`                                      | GET                    | Public                                                                                                                                        |
| `/api/v1/documents/upload`                               | POST                   | Admin (26 MB cap gated on valid JWT)                                                                                                          |
| `/api/v1/github/stats/{user}`                            | GET                    | Public                                                                                                                                        |
| `/api/v1/oss/contributions`                              | GET                    | Public (the homepage OSS contributions strip)                                                                                                 |
| `/api/v1/analytics/track/pageview`                       | POST                   | Public (rate-limited; also carries synthetic `/event/*` paths for outbound-click events, which the stats summary filters out of page metrics) |
| `/api/v1/analytics/stats/*`                              | GET                    | Admin (summary, visitors)                                                                                                                     |
| `/api/v1/auth/github`                                    | GET                    | Public (OAuth initiation)                                                                                                                     |
| `/api/v1/auth/me`                                        | GET                    | Required                                                                                                                                      |
| `/api/v1/auth/refresh`                                   | POST                   | Refresh-token cookie                                                                                                                          |
| `/api/v1/auth/logout`                                    | POST                   | Clears auth cookies                                                                                                                           |
| `/api/v1/admin/*`                                        | GET                    | Admin (dashboard summary, Sentry panel)                                                                                                       |
| `/api/v1/admin/cv/profile`, `/api/v1/admin/cv/export`    | GET, PUT / GET         | Admin (CV profile + JSON Resume export)                                                                                                       |
| `/api/v1/admin/oss/*`                                    | GET, POST              | Admin (OSS contribution dashboard + refresh)                                                                                                  |
| `/api/v1/metrics/*`                                      | GET                    | Admin (performance counters)                                                                                                                  |
| `/api/v1/errors`                                         | POST                   | Public (frontend error reports, rate-limited)                                                                                                 |
| `/api/v1/health`, `/api/v1/health/{ready,live,detailed}` | GET                    | Public (`ready` probes the DB)                                                                                                                |

## Authentication

- **Login**: GitHub OAuth via `/api/v1/auth/github` (CSRF state is single-use, IP-bound, 5-minute TTL)
- **Sessions**: JWT access + refresh tokens issued as HTTP-only, `secure`, `samesite=lax` cookies. The frontend never touches tokens directly.
- **Refresh**: `/api/v1/auth/refresh` rotates the cookies and returns `{"refreshed": true}` — the response body is intentionally token-free so an XSS payload calling the endpoint cannot extract credentials. Replaying an already-used refresh token is treated as theft (RFC 6819) and revokes every session for the account, with a short grace window so two tabs renewing simultaneously are not mistaken for an attack.
- **Bearer header fallback**: still accepted by `/api/v1/auth/me` and other protected endpoints for non-browser API clients (curl, test suites). The frontend itself uses cookies only.

## Rate Limits

Configured in `app/config.py` (slowapi):

- Default: 100 requests/minute per IP
- Auth endpoints (`/api/v1/auth/*`): 5 requests/minute per IP
- General API tier: 60/minute; public read-only tier: 120/minute
- Health checks: unlimited

## Analytics & Privacy

Page views are pseudonymised before storage: the client IP is hashed with
HMAC-SHA256 keyed off the application secret (see `app/utils/ip_hash.py`)
and only the truncated digest is persisted. Country is resolved via
ipapi.co off the request path (the lookup no longer blocks the tracking
response). Outbound-click tracking rides the same pageview
endpoint under synthetic `/event/*` paths; the admin stats summary
excludes those from page-view metrics and surfaces them as their own
counter instead.
