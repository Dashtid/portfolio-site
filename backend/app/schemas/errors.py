"""
Pydantic schemas for frontend error logging
"""

import json
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

# Allowed error types - strict validation to prevent abuse
ErrorType = Literal["error", "unhandledRejection", "vueError", "manual"]

# The endpoint is unauthenticated (rate-limited 30/min), and context lands
# verbatim in the structured logs — both caps exist to bound attacker-
# controlled log volume. 5000 bytes mirrors the stack field's budget;
# legitimate context is small ad-hoc objects from trackError().
MAX_CONTEXT_KEYS = 10
MAX_CONTEXT_SERIALIZED_BYTES = 5000


class FrontendErrorCreate(BaseModel):
    """Schema for receiving frontend errors"""

    model_config = {"populate_by_name": True}

    type: ErrorType = Field(
        ...,
        description="Error type: error, unhandledRejection, vueError, manual",
    )
    message: str = Field(..., min_length=1, max_length=1000)
    filename: str | None = Field(None, max_length=300, pattern=r"^[a-zA-Z0-9./_:\-@]+$")
    lineno: int | None = Field(None, ge=0, le=100000)
    colno: int | None = Field(None, ge=0, le=10000)
    stack: str | None = Field(None, max_length=5000)
    component_name: str | None = Field(
        None, max_length=100, pattern=r"^[a-zA-Z][a-zA-Z0-9_-]*$", alias="componentName"
    )
    error_info: str | None = Field(None, max_length=500, alias="errorInfo")
    timestamp: str = Field(..., max_length=50, pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")
    url: str = Field(..., max_length=1000, pattern=r"^https?://")
    user_agent: str = Field(..., max_length=300, alias="userAgent")
    context: dict | None = Field(
        None,
        description="Additional context (max 10 keys, 5000 serialized bytes)",
    )

    @field_validator("context")
    @classmethod
    def bound_context(cls, v: dict | None) -> dict | None:
        """Reject oversized context instead of logging it.

        A field_validator runs inside pydantic-core's body validation —
        unlike the previous model_validate override, which FastAPI never
        invoked (and which only trimmed key COUNT, so a single key could
        still carry megabytes into the logs).
        """
        if v is None:
            return v
        if len(v) > MAX_CONTEXT_KEYS:
            raise ValueError(f"context must have at most {MAX_CONTEXT_KEYS} keys")
        try:
            serialized = json.dumps(v, ensure_ascii=False)
        except (TypeError, ValueError) as exc:
            raise ValueError("context must be JSON-serializable") from exc
        if len(serialized.encode("utf-8")) > MAX_CONTEXT_SERIALIZED_BYTES:
            raise ValueError(
                f"context must serialize to at most {MAX_CONTEXT_SERIALIZED_BYTES} bytes"
            )
        return v


class FrontendErrorResponse(BaseModel):
    """Response after logging an error"""

    id: str
    received_at: datetime
    message: str = "Error logged successfully"
