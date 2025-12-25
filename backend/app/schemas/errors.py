"""
Pydantic schemas for frontend error logging
"""

from datetime import datetime

from pydantic import BaseModel, Field


class FrontendErrorCreate(BaseModel):
    """Schema for receiving frontend errors"""

    model_config = {"populate_by_name": True}

    type: str = Field(
        ...,
        max_length=50,
        description="Error type: error, unhandledRejection, vueError, manual",
    )
    message: str = Field(..., max_length=2000)
    filename: str | None = Field(None, max_length=500)
    lineno: int | None = Field(None, ge=0, le=1000000)
    colno: int | None = Field(None, ge=0, le=10000)
    stack: str | None = Field(None, max_length=10000)
    component_name: str | None = Field(None, max_length=100, alias="componentName")
    error_info: str | None = Field(None, max_length=500, alias="errorInfo")
    timestamp: str = Field(..., max_length=50)
    url: str = Field(..., max_length=2000)
    user_agent: str = Field(..., max_length=500, alias="userAgent")
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
