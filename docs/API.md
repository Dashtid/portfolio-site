# API Reference

**Interactive docs**: [dashti-portfolio-backend.fly.dev/docs](https://dashti-portfolio-backend.fly.dev/docs)

## Endpoints

| Resource | Methods | Auth |
|----------|---------|------|
| `/api/v1/companies` | GET, POST, PUT, DELETE | Admin (write) |
| `/api/v1/education` | GET, POST, PUT, DELETE | Admin (write) |
| `/api/v1/projects` | GET, POST, PUT, DELETE | Admin (write) |
| `/api/v1/skills` | GET, POST, PUT, DELETE | Admin (write) |
| `/api/v1/documents` | GET | Public |
| `/api/v1/github/stats/{user}` | GET | Public |
| `/api/v1/auth/github` | GET | Public (initiates OAuth) |
| `/api/v1/auth/me` | GET | Required |
| `/api/v1/auth/refresh` | POST | Refresh token |
| `/health` | GET | Public |

## Authentication

- **OAuth**: GitHub via `/api/v1/auth/github`
- **Tokens**: JWT in HTTP-only cookies (primary) or Bearer header (fallback)
- **Refresh**: Automatic via `/api/v1/auth/refresh`

## Rate Limits

- General: 100 requests/minute
- Auth endpoints: 10 requests/minute
- Health checks: Unlimited
