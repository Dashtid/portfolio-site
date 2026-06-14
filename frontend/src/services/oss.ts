/**
 * Admin OSS contribution dashboard service.
 *
 * Mirrors the Pydantic response shape from
 * backend/app/schemas/oss.py (OssDashboardView, OssContributionRow,
 * OssRefreshResult). The backend emits camelCase via
 * ``serialization_alias=...`` so the TS interfaces stay snake-free.
 *
 * Both routes are admin-only on the backend; the apiClient already
 * attaches the auth cookie via ``withCredentials: true``. Service
 * methods return ``null`` on failure so the view can render an empty
 * state instead of crashing.
 */
import apiClient from '../api/client'
import { adminLogger } from '../utils/logger'

const ENDPOINT = '/api/v1/admin/oss'

export type Bucket = 'NOW' | 'WAITING' | 'WATCHING' | 'LATER' | 'DONE'

export const BUCKET_ORDER: Bucket[] = ['NOW', 'WAITING', 'WATCHING', 'LATER', 'DONE']

export const BUCKET_LABEL: Record<Bucket, string> = {
  NOW: 'NOW — your move',
  WAITING: 'WAITING — maintainer',
  WATCHING: 'WATCHING — open threads',
  LATER: 'LATER — queued',
  DONE: 'DONE — recent (30d)'
}

export const BUCKET_DESCRIPTION: Record<Bucket, string> = {
  NOW: 'Open PRs awaiting your action: CI red, changes requested, rebase needed, or draft.',
  WAITING: 'Open PRs awaiting maintainer action: review pending or approved-not-merged.',
  WATCHING: 'Issues you authored or substantively commented on.',
  LATER: 'Hardcoded queued future work (not yet on GitHub).',
  DONE: 'Merged PRs, closed issues, and substantive comments on threads closed within 30 days.'
}

/**
 * Empty-state copy per bucket. Encoded as a Record so adding a new
 * Bucket member triggers a compile error here — preferred over a switch
 * statement that would silently fall through and render an empty string.
 */
export const BUCKET_EMPTY_MESSAGE: Record<Bucket, string> = {
  NOW: 'Nothing in your court right now — keep it that way.',
  WAITING: 'No PRs awaiting maintainer review.',
  WATCHING: 'No issues or threads being tracked.',
  LATER: 'No queued future work. Add entries to LATER_ITEMS in oss_queries.py.',
  DONE: 'No recently completed work in the 30-day window.'
}

export interface OssContributionRow {
  id: string
  kind: 'pr' | 'issue' | 'later'
  repoNameWithOwner: string
  number: number
  title: string
  url: string
  state: string
  isDraft: boolean
  authorLogin: string | null
  bucket: Bucket
  createdAt: string
  lastActivityAt: string
  closedAt: string | null
  mergedAt: string | null
}

export interface OssDashboardView {
  buckets: Record<Bucket, OssContributionRow[]>
  lastRefreshAt: string | null
  trackedRepos: string[]
  refreshInProgress: boolean
}

export interface OssRefreshResult {
  contributionsCount: number
  rateLimitCost: number
  rateLimitRemaining: number
  finishedAt: string
}

class OssService {
  /**
   * Fetch the cached bucketed contribution view.
   *
   * Returns null on failure so the admin view can render an empty state
   * instead of throwing. The component logs the failure via adminLogger
   * for debugging.
   */
  async getOssDashboard(): Promise<OssDashboardView | null> {
    try {
      const response = await apiClient.get<OssDashboardView>(ENDPOINT)
      return response.data
    } catch (error) {
      adminLogger.error('Failed to get OSS dashboard:', error)
      return null
    }
  }

  /**
   * Trigger a fresh GraphQL pull from GitHub and replace the cached rows.
   *
   * Rate-limited at the backend (5/minute by default) — the UI should
   * disable the refresh button while ``refreshInProgress`` is true to
   * keep the lockout less surprising.
   *
   * Returns null on 502/503 (PAT-missing or upstream failure). Callers
   * read the surfaced error from the apiClient interceptor; the service
   * never throws.
   */
  async refreshOssDashboard(): Promise<OssRefreshResult | null> {
    try {
      const response = await apiClient.post<OssRefreshResult>(`${ENDPOINT}/refresh`)
      return response.data
    } catch (error) {
      adminLogger.error('Failed to refresh OSS dashboard:', error)
      return null
    }
  }
}

export default new OssService()
