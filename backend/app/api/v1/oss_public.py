"""Public read-only OSS contributions endpoint (D3-FEAT-01).

``GET /api/v1/oss/contributions`` returns merged upstream pull requests
only — the third-party-verifiable subset of the admin OSS dashboard.
Everything in-flight (open PRs, drafts, issues, watch/wait buckets) and
every person-derived field (maintainer logins) stays behind the admin
surface in ``oss.py``; this endpoint discloses nothing that isn't
already public on the upstream PR page itself.
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.oss import OssContribution
from app.schemas.oss import PublicOssContribution
from app.services.oss_queries import GITHUB_USERNAME

router = APIRouter()

DbSession = Annotated[AsyncSession, Depends(get_db)]


@router.get("/contributions", response_model=list[PublicOssContribution])
async def get_public_contributions(session: DbSession) -> list[PublicOssContribution]:
    """Return merged upstream PRs, newest merge first.

    Filter is server-side and structural: SELF-AUTHORED (the commented-*
    GraphQL searches also persist other people's merged PRs that Dashtid
    reviewed — presenting those as his contributions would be
    misattribution), kind ``pr``, state ``MERGED``, non-draft, with a
    real ``merged_at``. A row can't leak into the public list by bucket
    misclassification alone.
    """

    stmt = (
        select(OssContribution)
        .where(
            OssContribution.author_login == GITHUB_USERNAME,
            OssContribution.kind == "pr",
            OssContribution.state == "MERGED",
            OssContribution.is_draft.is_(False),
            OssContribution.merged_at.is_not(None),
        )
        .order_by(OssContribution.merged_at.desc())
    )
    result = await session.execute(stmt)
    return [PublicOssContribution.model_validate(row) for row in result.scalars().all()]
