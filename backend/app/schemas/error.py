"""Pydantic schemas for standardized API error responses.

Conforms to Section 6 of 05_API_SPECIFICATION.md:
{
  "error": {
    "code": "INVALID_QUERY",
    "message": "The limit parameter must be within the allowed range."
  }
}
"""

from __future__ import annotations
from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Error payload containing code and human-readable message."""

    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Actionable explanation of error")


class ErrorResponse(BaseModel):
    """Envelope conforming to Phase 4 error contract."""

    error: ErrorDetail
