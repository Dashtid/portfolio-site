"""Persistence layer for the admin OSS contribution dashboard.

Every row is a single PR or Issue across the 8 tracked upstream repos
(see ``app.services.oss_queries.TRACKED_REPOS``), tagged with the
bucket the classifier assigned at last refresh time. The dashboard's
GET endpoint groups rows by bucket; the POST endpoint triggers a
fresh GraphQL pull, classifies each node, and upserts the rows.

Rows are addressed by ``github_node_id`` (the GraphQL Global Node ID,
stable across renames and even repo transfers). The classifier only
ever assigns one of NOW / WAITING / WATCHING / DONE here — LATER
entries are hardcoded in code and merged into the GET response at
serve time, never persisted.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.database import Base


class OssContribution(Base):
    """One row per tracked PR or Issue.

    Replaced wholesale on each refresh: ``oss_sync.refresh()`` opens a
    transaction, deletes every row, inserts the latest classification,
    and commits. The table is small (<50 rows steady-state), so the
    delete+insert pattern is simpler than per-row upsert + tombstone.
    """

    __tablename__ = "oss_contributions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # GraphQL Global Node ID — stable across renames and repo transfers.
    # Unique so a future delta-tracking step (v1.3) can address rows by
    # source identity without depending on repo-name string equality.
    github_node_id: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)

    # "pr" or "issue". Kept short for index density.
    kind: Mapped[str] = mapped_column(String(16), nullable=False)

    # e.g. "anchore/syft". Indexed because the UI groups within bucket
    # by repository.
    repo_name_with_owner: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)

    # Source state from GitHub: OPEN / CLOSED / MERGED.
    state: Mapped[str] = mapped_column(String(16), nullable=False)
    is_draft: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="0"
    )

    # Author login. NULL only when GitHub returns a deleted/ghost user
    # (rare but possible on very old threads).
    author_login: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Classifier output. Indexed because the GET endpoint groups by it.
    bucket: Mapped[str] = mapped_column(String(16), nullable=False, index=True)

    # GitHub timestamps. ``created_at`` is the contribution birth; the
    # dashboard renders "X days since" from ``last_activity_at``.
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_activity_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    merged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Our row's last refresh. Stamped at INSERT by the server_default, and
    # explicitly re-stamped by oss_sync.refresh() when it updates a
    # preserved merged row in place (the replace-with-history path). Do NOT
    # copy this field off a freshly built, unflushed row — the
    # server_default has not materialized there yet and it reads None.
    synced_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        # Composite index for the GET endpoint's primary query:
        # ORDER BY bucket, repo_name_with_owner, last_activity_at DESC.
        Index(
            "ix_oss_contributions_bucket_repo_activity",
            "bucket",
            "repo_name_with_owner",
            "last_activity_at",
        ),
    )
