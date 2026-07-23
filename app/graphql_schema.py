"""GraphQL schema (Strawberry) sharing the service layer with the REST API.

Conventions:
- Enum values follow the GraphQL convention (HIGH, OPEN, ...) while the REST
  API uses lowercase strings; both map to the same Python enums.
- Mutations require the X-API-Key header when INCIDENT_API_KEY is set.
"""
from datetime import datetime
from typing import List, Optional

import strawberry
from fastapi import Depends, Request
from pydantic import ValidationError
from sqlalchemy.orm import Session
from strawberry.fastapi import GraphQLRouter
from strawberry.types import Info

from app import crud, models, schemas
from app.database import get_db
from app.security import check_request_api_key

Severity = strawberry.enum(models.Severity, name="Severity")
Status = strawberry.enum(models.Status, name="Status")


@strawberry.type
class Incident:
    id: int
    title: str
    description: str
    severity: Severity
    status: Status
    reporter_email: str
    resolution_notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_model(cls, m: models.Incident) -> "Incident":
        return cls(
            id=m.id,
            title=m.title,
            description=m.description,
            severity=m.severity,
            status=m.status,
            reporter_email=m.reporter_email,
            resolution_notes=m.resolution_notes,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )


@strawberry.type
class Query:
    @strawberry.field(description="Fetch a single incident by id.")
    def incident(self, info: Info, id: int) -> Optional[Incident]:
        db: Session = info.context["db"]
        m = crud.get_incident(db, id)
        return Incident.from_model(m) if m else None

    @strawberry.field(description="List incidents, optionally filtered by status/severity.")
    def incidents(
        self,
        info: Info,
        status: Optional[Status] = None,
        severity: Optional[Severity] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Incident]:
        db: Session = info.context["db"]
        rows = crud.list_incidents(db, status=status, severity=severity, limit=limit, offset=offset)
        return [Incident.from_model(m) for m in rows]


@strawberry.type
class Mutation:
    @strawberry.mutation(description="Report a new incident. Requires X-API-Key.")
    def create_incident(
        self,
        info: Info,
        title: str,
        description: str,
        severity: Severity,
        reporter_email: str,
    ) -> Incident:
        check_request_api_key(info.context["request"])
        try:
            data = schemas.IncidentCreate(
                title=title,
                description=description,
                severity=severity,
                reporter_email=reporter_email,
            )
        except ValidationError as exc:
            first = exc.errors()[0]
            raise ValueError(f"Validation failed on '{first['loc'][0]}': {first['msg']}") from exc
        db: Session = info.context["db"]
        return Incident.from_model(crud.create_incident(db, data))

    @strawberry.mutation(description="Update an incident's status. Requires X-API-Key.")
    def update_incident_status(
        self,
        info: Info,
        id: int,
        status: Status,
        resolution_notes: Optional[str] = None,
    ) -> Incident:
        check_request_api_key(info.context["request"])
        db: Session = info.context["db"]
        m = crud.get_incident(db, id)
        if m is None:
            raise ValueError(f"Incident {id} not found")
        data = schemas.IncidentUpdate(status=status, resolution_notes=resolution_notes)
        return Incident.from_model(crud.update_incident(db, m, data))


def get_context(request: Request, db: Session = Depends(get_db)) -> dict:
    return {"request": request, "db": db}


schema = strawberry.Schema(query=Query, mutation=Mutation)
graphql_router = GraphQLRouter(schema, context_getter=get_context)
