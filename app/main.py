"""FastAPI application: REST endpoints, GraphQL router, middleware, error handling."""
import logging
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app import crud, models, schemas
from app.database import get_db
from app.graphql_schema import graphql_router
from app.rate_limit import limiter_from_env
from app.security import require_api_key

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("incident-api")

app = FastAPI(
    title="Incident Report API",
    description=(
        "Incident tracking backend exposing the same service layer through "
        "REST and GraphQL. Demonstrates validation, API-key auth, rate "
        "limiting, structured error handling, and Alembic migrations."
    ),
    version="1.0.0",
)

_rate_limiter = limiter_from_env()


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if request.url.path != "/health":
        client_ip = request.client.host if request.client else "unknown"
        if not _rate_limiter.allow(client_ip):
            logger.warning("Rate limit exceeded for %s on %s", client_ip, request.url.path)
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Try again later."},
            )
    return await call_next(request)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    # Never leak internals; log the traceback, return a stable error shape.
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


app.include_router(graphql_router, prefix="/graphql", tags=["graphql"])


@app.get("/health", tags=["meta"])
def health() -> dict:
    return {"status": "ok"}


@app.post(
    "/incidents",
    response_model=schemas.IncidentOut,
    status_code=201,
    dependencies=[Depends(require_api_key)],
    tags=["incidents"],
)
def create_incident(payload: schemas.IncidentCreate, db: Session = Depends(get_db)):
    incident = crud.create_incident(db, payload)
    logger.info("Created incident %s (severity=%s)", incident.id, incident.severity.value)
    return incident


@app.get("/incidents", response_model=List[schemas.IncidentOut], tags=["incidents"])
def list_incidents(
    status: Optional[models.Status] = None,
    severity: Optional[models.Severity] = None,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    return crud.list_incidents(db, status=status, severity=severity, limit=limit, offset=offset)


@app.get("/incidents/{incident_id}", response_model=schemas.IncidentOut, tags=["incidents"])
def get_incident(incident_id: int, db: Session = Depends(get_db)):
    incident = crud.get_incident(db, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    return incident


@app.patch(
    "/incidents/{incident_id}",
    response_model=schemas.IncidentOut,
    dependencies=[Depends(require_api_key)],
    tags=["incidents"],
)
def update_incident(incident_id: int, payload: schemas.IncidentUpdate, db: Session = Depends(get_db)):
    incident = crud.get_incident(db, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    return crud.update_incident(db, incident, payload)


@app.delete(
    "/incidents/{incident_id}",
    status_code=204,
    dependencies=[Depends(require_api_key)],
    tags=["incidents"],
)
def delete_incident(incident_id: int, db: Session = Depends(get_db)):
    incident = crud.get_incident(db, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail=f"Incident {incident_id} not found")
    crud.delete_incident(db, incident)
    return None
