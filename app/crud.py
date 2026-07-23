"""Service layer: all database operations, shared by the REST and GraphQL APIs."""
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app import models, schemas

MAX_PAGE_SIZE = 100


def create_incident(db: Session, data: schemas.IncidentCreate) -> models.Incident:
    incident = models.Incident(**data.model_dump())
    db.add(incident)
    db.commit()
    db.refresh(incident)
    return incident


def get_incident(db: Session, incident_id: int) -> Optional[models.Incident]:
    return db.get(models.Incident, incident_id)


def list_incidents(
    db: Session,
    status: Optional[models.Status] = None,
    severity: Optional[models.Severity] = None,
    limit: int = 50,
    offset: int = 0,
) -> Sequence[models.Incident]:
    stmt = select(models.Incident).order_by(models.Incident.id.desc())
    if status is not None:
        stmt = stmt.where(models.Incident.status == status)
    if severity is not None:
        stmt = stmt.where(models.Incident.severity == severity)
    stmt = stmt.limit(min(max(limit, 1), MAX_PAGE_SIZE)).offset(max(offset, 0))
    return db.scalars(stmt).all()


def update_incident(
    db: Session, incident: models.Incident, data: schemas.IncidentUpdate
) -> models.Incident:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(incident, field, value)
    db.commit()
    db.refresh(incident)
    return incident


def delete_incident(db: Session, incident: models.Incident) -> None:
    db.delete(incident)
    db.commit()
