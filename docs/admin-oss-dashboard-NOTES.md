# Admin OSS Dashboard — Scoping Notes

**Status:** Scoped 2026-06-12; queued behind DefectDojo PR #14878 (Q3 OWASP KPI hit)
**ETA:** ~1.5 days (12 working hours) for MVP after start
**Owner:** David Dashti (this repo)

## Why this exists

Personal OSS contribution activity is spread across 8 upstream repos (anchore/{syft,grype,stereoscope}, fo-dicom, pydicom, DefectDojo, dependency-track, microsoft/presidio) plus reviews on others' threads. Cognitive load is real when 6+ PRs are awaiting maintainer signals and 7+ issues are silent. The oss-contributions tracker repo at github.com/Dashtid/oss-contributions has a 5-bucket markdown dashboard (NOW / WAITING / WATCHING / LATER / DONE), but visual feedback would scale better.

The dashboard lives at `dashti.se/admin/oss`, behind the existing GitHub OAuth admin gate. It is NOT a portfolio piece — it is an operational tool for ONE user.

## Decisions baked in (workflow research, 2026-06-12)

| Decision | Choice | Why |
|---|---|---|
| Source of truth | Live GitHub GraphQL v4 via githubkit | Fresher than parsing tracker markdown; SQLite caches results so a stale-cache fallback is cheap |
| Refresh cadence | 6h via APScheduler in-process for v1 | Fly.io scheduled machine later if needed; daily would also be fine |
| Read or read-write | **Read-only for v1** | Write-back (drag-to-reclassify) is v1.4; halves MVP scope |
| Scope of v1 | The 8 named upstream repos, hard-coded list | Auto-discover via `author:Dashtid` is v1.3; avoids drive-by contribution noise |
| Charts in v1 | None — Bootstrap card grid only | ApexCharts PR-aging bar is v1.2 |
| github.com/pulls deep link | Yes, day-one | 5-min add, free baseline regardless |
| Auth | Existing GitHub OAuth admin gate | Zero new auth surface |
| Hosting | Vercel (Vue SSG) + Fly.io (FastAPI + SQLite) | Same as today; no new infra |
| Data SDK | **githubkit** (NOT PyGithub) | Async, typed Pydantic v2, GraphQL-native; matches FastAPI async-first posture |
| Backend storage | New SQLAlchemy model `OssContribution` + Alembic migration | Mirrors existing model pattern |
| Frontend pattern | New `AdminOss.vue` copying `AdminAnalytics.vue` shell + Pinia store | No new design system |

## Open questions for v1.x (not blockers for MVP)

- Refresh cadence after MVP: should the 6h APScheduler move to a Fly.io scheduled machine, or stay in-process?
- Status-diff tracking: store last-seen-state per PR and flag "new maintainer comment since last visit" as a NOW-bucket promotion signal. v1.3.
- Write-back: let user reclassify a PR's bucket from UI; persist to SQLite; optional PR back to the oss-contributions README via a GitHub Actions workflow. v1.4.
- Issues + reviews on others' PRs: covered by the GraphQL query already, just needs UI. v2.

## Bucket classifier rules (mirror the oss-contributions README)

| Bucket | Rule |
|---|---|
| NOW | Open PR by Dashtid that is awaiting his action (CI red, requested-changes review, rebase needed). For v1, this is rare — only DefectDojo work-in-progress qualifies. |
| WAITING | Open PR by Dashtid that is awaiting maintainer action (review pending, approved-not-merged, no review yet). Most common bucket. |
| WATCHING | Open issue by Dashtid (no PR), OR open issue Dashtid commented on substantively. Silent-but-tracked. |
| LATER | Explicitly queued future work — these don't exist on GitHub yet; pulled from a hard-coded array in the classifier OR a `queued/` folder in oss-contributions repo. |
| DONE | Merged PR, closed issue, OR posted review/triage comment on someone else's thread. |

Classifier is testable in isolation with fixture GraphQL responses; aim for ~95% coverage on classifier logic specifically.

### Bucket-rule edge cases (locked Phase 2)

- **Draft PRs → NOW.** A draft PR is the author's call to promote or abandon; the maintainer literally cannot act until it leaves draft state. Surfacing them as NOW keeps "things requiring my decision" visible.
- **`mergeStateStatus=BLOCKED` alone → WAITING.** BLOCKED typically means branch-protection waiting on a maintainer review or required CI check. If the author actually broke CI, `statusCheckRollup.state in (FAILURE, ERROR)` catches it first and routes to NOW.
- **Dedup ordering: authored wins over commented.** The classifier iterates AUTHORED_OPEN_PRS → AUTHORED_OPEN_ISSUES → AUTHORED_CLOSED → COMMENTED_OPEN → COMMENTED_CLOSED. A node that collides on `github_node_id` (shouldn't happen today — `-author:{username}` excludes self in commented_*) keeps its authored row because that carries the richer NOW/WAITING signal set.
- **Substantive-comment heuristic = 80 chars after `strip()`.** Whitespace doesn't game it; the COMMENT_BOT_ALLOWLIST is consulted as defense-in-depth (Dashtid isn't a bot, but a future relaxation of the author check would otherwise let dependabot comments promote threads).

## Architecture sketch

### Data flow
```
GitHub GraphQL v4 (githubkit, async)
    -> app/services/oss_sync.py (wraps SDK calls)
    -> app/services/bucket_classifier.py (state -> bucket logic)
    -> SQLAlchemy upsert into oss_contribution table
    -> FastAPI router app/api/v1/oss.py (admin-gated GET endpoint)
    -> Vue 3 view src/views/admin/AdminOss.vue
    -> Pinia store src/stores/oss.ts
    -> axios call from view
    -> Bootstrap 5.3 card grid grouped by bucket
```

### Reuse map (copy from these existing files)

| New file | Copy / pattern from |
|---|---|
| `backend/app/api/v1/oss.py` | `backend/app/api/v1/endpoints/admin_panel.py` (admin auth pattern) |
| `backend/app/services/oss_sync.py` | `backend/app/services/github_service.py` (service-layer pattern) |
| `backend/app/schemas/oss.py` | `backend/app/schemas/github.py` (Pydantic v2 schema pattern) |
| `backend/app/models/oss.py` | existing models in `backend/app/models/` |
| `backend/alembic/versions/XXX_add_oss_contribution.py` | existing migrations in `backend/alembic/versions/` |
| `frontend/src/views/admin/AdminOss.vue` | `frontend/src/views/AdminAnalytics.vue` (most relevant shell) |
| `frontend/src/stores/oss.ts` | existing Pinia stores |
| `frontend/src/router/` entry | existing `authGuard.ts` pattern |

### Auth + secrets

- Reuse existing GitHub OAuth admin gate (HTTP-only cookies, no localStorage).
- GitHub PAT for the GraphQL queries: `public_repo` scope (all 8 upstream repos are public). Store in Fly.io secrets as `GITHUB_OSS_DASHBOARD_PAT`. **PAT rotation requires a Fly Machine restart** — Pydantic Settings is module-level and not hot-reloadable; the service reads the PAT into the githubkit client on every refresh, but only from process-start memory.
- **PAT must never leak via logs or Sentry.** githubkit/httpx exceptions can include `Authorization` header dumps. The fetch path catches every exception, runs the message through `_sanitize_pat()` (literal substring redaction), and re-raises via `raise ... from None` so the original traceback (which may contain the unredacted token) is dropped from the chain.
- Rate limit: GraphQL primary rate limit is 5000 points/hr per user (120,000 points/day). The Phase 1 query uses 5 aliased `search()` calls + nested connections, measured at ~7-8 points per refresh. 6h refresh = 4 queries/day ≈ 32 points/day. ~3,750x headroom. The earlier ~50-points estimate assumed per-repo `repository(owner, name) { pullRequests issues }` blocks — switched to search-based aliases for the actual implementation.

## MVP build sequence (12 hours)

1. **Hour 0-2 — Data query.** Write the GraphQL query covering the 8 upstream repos: PRs authored by Dashtid (`search` with `author:Dashtid is:pr`), issues authored by Dashtid, PRs Dashtid has commented on (reviews / triage). Build Pydantic v2 schemas matching response shape. Validate against the live API once.
2. **Hour 2-5 — Backend.** Create FastAPI router `app/api/v1/oss.py` mirroring `admin_panel.py` auth pattern. Add `OssContribution` model + Alembic migration. Manual-refresh POST endpoint that triggers `oss_sync.refresh()` and returns updated rows. GET endpoint returns rows grouped by bucket.
3. **Hour 5-8 — Frontend.** Create `AdminOss.vue` by copying `AdminAnalytics.vue` shell. Bootstrap 5.3 card grid: one column per bucket, one card per row, showing repo + #number + title + days-since-last-activity + link out. Pinia store + axios fetch. Add deep link to `github.com/pulls` in a corner widget (the 5-min baseline).
4. **Hour 8-10 — Classifier + tests.** Pure-function bucket classifier; pytest with fixture GraphQL responses; hit 83% repo-wide coverage floor (95%+ on classifier itself).
5. **Hour 10-12 — Deploy + smoke.** Fly.io PAT secret, Alembic migration on deploy, Vercel push, smoke-test behind admin gate. Confirm no third-party API consumer warnings.

First useful version (just GraphQL fetch + table behind manual refresh, no cron, no classifier) is **under 8 hours**.

## Follow-up roadmap

| Version | Adds | When |
|---|---|---|
| v1.0 | MVP per above | first build session |
| v1.1 | Fly.io scheduled machine for 6h auto-refresh (or APScheduler in-process) | next weekend |
| v1.2 | ApexCharts horizontal PR-aging bar chart | when active threads exceed ~15 |
| v1.3 | Status diff — flag "new maintainer comment since last visit" | when polling cadence is stable |
| v1.4 | Write-back — drag-to-reclassify bucket, persist to SQLite, optional PR back to oss-contributions README | when read-only UI feels limiting |
| v2.0 | Auto-discover upstream repos via `author:Dashtid` search; per-repo swimlane view if threads > 30 | when fixed 8-repo list becomes restrictive |

## Sequencing reminder

This is queued behind DefectDojo PR #14878 (Garak parser). That Q3 KPI ships first; this is a 1-2 weekend project after. Do NOT start until the DefectDojo work is in maintainer hands.

## Reference: workflow research result

Full ranked recommendation from the 2026-06-12 workflow run is in the session transcript. Top pick rationale (verbatim from the synthesis agent):

> Extend portfolio-site with a new /admin/oss route backed by a FastAPI ingester. This is the highest-fit option because every primitive already exists on dashti.se — GitHub OAuth admin gate, httpx-based GitHubService in app/api/v1/github.py, SQLAlchemy + Alembic, 9 admin views as copy-paste templates, Pinia stores, Sentry, strict CSP, SHA-pinned CI. No off-the-shelf tool matches the 'one identity, many upstreams, behind my own gate, with bucket semantics tied to the oss-contributions repo' shape as cleanly.

Declined options (don't reconsider unless circumstances change): Octobox (notification inbox, not status), AKharytonchyk/git-pull-request-dashboard (React + repo-centric), NihalJain/opensource-contributions-tracker (markdown reports, not live dashboard), OSSInsight Lite (dead upstream), PyGithub (sync-only, wrong for FastAPI), vue3-calendar-heatmap (unmaintained, volume not status), PrimeVue (collides with Bootstrap), Cloudflare Access (duplicates existing auth), K3s lab server (over-engineered for this), Vercel Password Protection ($170/mo for less auth than already exists).
