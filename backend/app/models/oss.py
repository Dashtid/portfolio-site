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

from sqlalchemy import Boolean, Column, DateTime, Index, Integer, String
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

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # GraphQL Global Node ID — stable across renames and repo transfers.
    # Unique so a future delta-tracking step (v1.3) can address rows by
    # source identity without depending on repo-name string equality.
    github_node_id = Column(String(64), nullable=False, unique=True, index=True)

    # "pr" or "issue". Kept short for index density.
    kind = Column(String(16), nullable=False)

    # e.g. "anchore/syft". Indexed because the UI groups within bucket
    # by repository.
    repo_name_with_owner = Column(String(255), nullable=False, index=True)

    number = Column(Integer, nullable=False)
    title = Column(String(500), nullable=False)
    url = Column(String(500), nullable=False)

    # Source state from GitHub: OPEN / CLOSED / MERGED.
    state = Column(String(16), nullable=False)
    is_draft = Column(Boolean, nullable=False, default=False, server_default="0")

    # Author login. NULL only when GitHub returns a deleted/ghost user
    # (rare but possible on very old threads).
    author_login = Column(String(255), nullable=True)

    # Classifier output. Indexed because the GET endpoint groups by it.
    bucket = Column(String(16), nullable=False, index=True)

    # GitHub timestamps. ``created_at`` is the contribution birth; the
    # dashboard renders "X days since" from ``last_activity_at``.
    created_at = Column(DateTime(timezone=True), nullable=False)
    last_activity_at = Column(DateTime(timezone=True), nullable=False)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    merged_at = Column(DateTime(timezone=True), nullable=True)

    # Our row's last refresh. Only ever stamped at INSERT (via server_default)
    # because oss_sync.refresh() is delete-all + insert-all; no UPDATE path
    # exists, so onupdate=... would be dead code.
    synced_at = Column(
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
