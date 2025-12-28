"""
Pydantic schemas for frontend error logging
"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

# Allowed error types - strict validation to prevent abuse
ErrorType = Literal["error", "unhandledRejection", "vueError", "manual"]


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
    context: dict | None = Field(None, description="Additional context (max 10 keys)")

    @classmethod
    def model_validate(cls, obj, **kwargs):
        """Validate context dict size to prevent DoS"""
        if isinstance(obj, dict) and "context" in obj and obj["context"]:
            ctx = obj["context"]
            if isinstance(ctx, dict) and len(ctx) > 10:
                obj = {**obj, "context": dict(list(ctx.items())[:10])}
        return super().model_validate(obj, **kwargs)


class FrontendErrorResponse(BaseModel):
    """Response after logging an error"""

    id: str
    received_at: datetime
    message: str = "Error logged successfully"
