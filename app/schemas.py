"""Pydantic schemas: request validation and response serialization."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import Severity, Status


class IncidentCreate(BaseModel):
    """Payload to report a new incident."""

    title: str = Field(min_length=3, max_length=200, description="Short, specific summary")
    description: str = Field(min_length=10, description="What happened, where, and how to reproduce")
    severity: Severity
    reporter_email: EmailStr


class IncidentUpdate(BaseModel):
    """Partial update; only provided fields are changed."""

    status: Optional[Status] = None
    severity: Optional[Severity] = None
    resolution_notes: Optional[str] = Field(default=None, max_length=5000)


class IncidentOut(BaseModel):
    """Incident as returned by the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    severity: Severity
    status: Status
    reporter_email: EmailStr
    resolution_notes: Optional[str]
    created_at: datetime
    updated_at: datetime
