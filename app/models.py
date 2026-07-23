"""SQLAlchemy ORM models."""
import enum
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Severity(str, enum.Enum):
    """How badly the incident impacts users."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Status(str, enum.Enum):
    """Lifecycle state of an incident."""

    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _enum_values(enum_cls):
    return [member.value for member in enum_cls]


class Incident(Base):
    """A reported incident (bug, outage, or degradation)."""

    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    severity: Mapped[Severity] = mapped_column(
        Enum(Severity, name="severity", values_callable=_enum_values, native_enum=False),
        nullable=False,
        index=True,
    )
    status: Mapped[Status] = mapped_column(
        Enum(Status, name="status", values_callable=_enum_values, native_enum=False),
        nullable=False,
        default=Status.OPEN,
        index=True,
    )
    reporter_email: Mapped[str] = mapped_column(String(320), nullable=False)
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    def __repr__(self) -> str:  # pragma: no cover
        return f"<Incident id={self.id} severity={self.severity.value} status={self.status.value}>"
