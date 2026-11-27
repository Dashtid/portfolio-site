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
| `/api/v1/github/stats/{user}`                            | GET                    | Public (the site owner's account only; other names get 404)                                                                                   |
| `/api/v1/oss/contributions`                              | GET                    | Public (the homepage OSS contributions strip)                                                                                                 |
| `/api/v1/analytics/track/pageview`                       | POST                   | Public (rate-limited, answers 204; synthetic `/event/*` paths carry outbound clicks, which the stats summary keeps out of page metrics)       |
| `/api/v1/analytics/stats/*`                              | GET                    | Admin (summary, visitors)                                                                                                                     |
| `/api/v1/auth/github`                                    | GET                    | Public (OAuth initiation)                                                                                                                     |
| `/api/v1/auth/me`                                        | GET                    | Required                                                                                                                                      |
| `/api/v1/auth/refresh`                                   | POST                   | Refresh-token cookie                                                                                                                          |
| `/api/v1/auth/logout`                                    | POST                   | Clears auth cookies                                                                                                                           |
| `/api/v1/admin/*`                                        | GET                    | Admin (dashboard summary, Sentry panel)                                                                                                       |
| `/api/v1/admin/cv/profile`, `/api/v1/admin/cv/export`    | GET, PUT / GET         | Admin (CV profile + JSON Resume export)                                                                                                       |
| `/api/v1/admin/oss/*`                                    | GET, POST              | Admin (OSS contribution dashboard + refresh)                                                                                                  |
| `/api/v1/metrics/*`                                      | GET                    | Admin (performance counters)                                                                                                                  |
| `/api/v1/health`, `/api/v1/health/{ready,live,detailed}` | GET                    | Public (`ready` probes the DB)                                                                                                                |

## Authentication

- **Login**: GitHub OAuth via `/api/v1/auth/github` with PKCE (CSRF state is single-use with a 5-minute TTL, and bound to the browser by an HttpOnly cookie that also holds the PKCE code verifier)
- **Sessions**: JWT access + refresh tokens issued as HTTP-only, `secure`, `samesite=lax` cookies. The frontend never touches tokens directly.
- **Refresh**: `/api/v1/auth/refresh` rotates the cookies and returns `{"refreshed": true}` — the response body is intentionally token-free so an XSS payload calling the endpoint cannot extract credentials. Replaying an already-used refresh token is treated as theft (RFC 6819) and revokes every refresh token for the account; access tokens already issued are not tracked server-side and stay valid until they expire (`ACCESS_TOKEN_EXPIRE_MINUTES`, 30). A short grace window keeps two tabs renewing simultaneously from being mistaken for an attack.
- **Bearer header fallback**: still accepted by `/api/v1/auth/me` and other protected endpoints for non-browser API clients (curl, test suites). The frontend itself uses cookies only.

## Rate Limits

Configured in `app/config.py` (slowapi):

- Default: 100 requests/minute per IP
- Auth endpoints (`/api/v1/auth/*`): 5 requests/minute per IP
- General API tier: 60/minute; public read-only tier: 120/minute
- Health checks: unlimited
- "Per IP" is per address for IPv4 and per /64 for IPv6, taken from Fly's `Fly-Client-IP` header

## Analytics & Privacy

`POST /api/v1/analytics/track/pageview` takes a JSON body with `page_path`
(required) and `referrer` (optional), each at most 2048 characters, and
answers `204 No Content` with no body. Fields it does not declare, such as
the `page_title` and `visitor_id` that older frontend bundles send, are
ignored. A request with `Sec-GPC: 1` or `DNT: 1` gets the same 204 and
stores nothing.

A stored page view holds the path (cut to 500 characters), the referrer's
lowercased host only (none for `dashti.se`, `www.dashti.se` or a host that
is an IP address), the country, the time and a daily visitor key: `v_` and
the first 16 hex characters of an HMAC-SHA256 of the client address and
User-Agent under a 32-byte random salt that exists only in the API
process's memory and is replaced when the UTC date changes
(`app/utils/visitor_key.py`). The row holds neither the address nor the
User-Agent, and once the day's salt is replaced the key cannot be turned
back into either. A restart starts a new salt, so a visitor seen before
and after it counts twice that day. Country is resolved via ipapi.co after
the response, from the address with its host part zeroed (IPv4 /24,
IPv6 /48); the answer for that network stays in memory until the end of
the UTC day. Outbound-click tracking rides the same endpoint under
synthetic `/event/*` paths; the admin stats summary excludes those from
page-view metrics and surfaces them as their own counter instead.

Request log lines name no client. The rate-limit refusal line and the
security events (each step of a sign-in) name one by a keyed digest
instead: an HMAC-SHA256 of the address keyed off the application secret,
truncated (`client_ip_hash`, see `app/utils/ip_hash.py`), the same for one
address on every day; the security events also keep at most the first 64
characters of the User-Agent. The page-view beacon is logged only when it
fails. uvicorn's own access log, which would print the address, is off.
