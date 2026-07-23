# Incident Report API

![CI](https://github.com/riham-tarabay/incident-report-api/actions/workflows/ci.yml/badge.svg)

An incident/bug-report tracking backend that exposes **the same service layer through both REST and GraphQL APIs**. Built to demonstrate production backend fundamentals end to end: input validation, API-key authentication, rate limiting, structured error handling, **versioned database migrations (Alembic)**, and a CI-verified test suite.

## Tech stack

| Layer | Technology |
|---|---|
| REST API | FastAPI |
| GraphQL API | Strawberry (`strawberry-graphql`) |
| ORM | SQLAlchemy 2.0 (typed `Mapped` models) |
| Migrations | Alembic (upgrade + downgrade tested in CI) |
| Validation | Pydantic v2 (`EmailStr`, field constraints) |
| Tests | pytest + FastAPI TestClient |
| CI | GitHub Actions |

## Architecture

```
            +-----------+     +---------------+
  clients ->|  REST     |     |  GraphQL      |
            |  (FastAPI)|     |  (Strawberry) |
            +-----+-----+     +-------+-------+
                  |                   |
                  +---------+---------+
                            v
                    app/crud.py  (service layer)
                            v
                 SQLAlchemy ORM  ->  SQLite / PostgreSQL
                            ^
                    Alembic migrations
```

Both APIs share one service layer (`app/crud.py`), so business logic is written once and tested once. Cross-cutting concerns live in middleware/dependencies:

- **Validation** — Pydantic schemas reject bad payloads (short titles, invalid emails, unknown enum values) with structured 422 responses; GraphQL mutations reuse the same schemas and surface failures in the `errors` array.
- **API security** — write operations (REST and GraphQL) require an `X-API-Key` header when `INCIDENT_API_KEY` is set, compared in constant time to avoid timing side channels.
- **Rate limiting** — a dependency-free sliding-window limiter keyed by client IP returns `429` when saturated.
- **Error handling** — a global exception handler logs full tracebacks server-side and returns a stable, non-leaking error shape.

## Getting started

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Create the schema via migrations (not create_all):
alembic upgrade head

# Run the API:
export INCIDENT_API_KEY=dev-secret   # optional; omit to disable auth locally
uvicorn app.main:app --reload
```

- REST docs (Swagger UI): http://127.0.0.1:8000/docs
- GraphQL explorer (GraphiQL): http://127.0.0.1:8000/graphql

## REST examples

```bash
# Report an incident
curl -X POST http://127.0.0.1:8000/incidents \
  -H 'Content-Type: application/json' -H 'X-API-Key: dev-secret' \
  -d '{
    "title": "Checkout API returns 500 on empty cart",
    "description": "POST /checkout returns HTTP 500 when the cart is empty instead of a 422.",
    "severity": "high",
    "reporter_email": "qa@example.com"
  }'

# List open high-severity incidents
curl 'http://127.0.0.1:8000/incidents?status=open&severity=high'

# Resolve an incident
curl -X PATCH http://127.0.0.1:8000/incidents/1 \
  -H 'Content-Type: application/json' -H 'X-API-Key: dev-secret' \
  -d '{"status": "resolved", "resolution_notes": "Validation added to the cart handler."}'
```

## GraphQL examples

```graphql
mutation {
  createIncident(
    title: "Search returns stale results"
    description: "The /search endpoint serves cached results for 24 hours after reindexing."
    severity: HIGH
    reporterEmail: "qa@example.com"
  ) {
    id
    status
  }
}

query {
  incidents(severity: HIGH, limit: 10) {
    id
    title
    status
    createdAt
  }
}
```

(REST uses lowercase enum strings; GraphQL follows the uppercase enum convention. Both map to the same Python enums.)

## Database migrations

Schema changes are versioned in `alembic/versions/`:

1. `0001` — create `incidents` table with severity/status enums and indexes.
2. `0002` — add `resolution_notes` column (with a batch-mode downgrade so `DROP COLUMN` also works on SQLite).

```bash
alembic upgrade head        # apply all migrations
alembic downgrade -1        # roll back one revision
alembic revision --autogenerate -m "describe the change"
```

Migrations are exercised three ways in CI: `upgrade head`, full `downgrade base`, and re-upgrade — plus dedicated pytest cases that assert the schema before and after each revision.

## Testing

```bash
pytest -v
```

The suite covers:

- REST: creation, filtering, 404s, auth (missing/wrong key), validation failures (email, title length, unknown enum), update, delete.
- GraphQL: queries, mutations, auth errors, validation errors, filtering.
- Rate limiter: limit enforcement, key isolation, window expiry.
- Migrations: full upgrade/downgrade/re-upgrade cycle against a temporary database via the real `alembic` CLI.

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./incidents.db` | SQLAlchemy database URL (PostgreSQL supported) |
| `INCIDENT_API_KEY` | *(unset = auth disabled)* | API key required on write operations |
| `RATE_LIMIT_MAX` | `120` | Max requests per window per client IP |
| `RATE_LIMIT_WINDOW_SECONDS` | `60` | Rate-limit window size |

## AI-assisted development

This project was built with an AI-assisted workflow (AI pair-programmer for scaffolding and iteration), with every change human-reviewed and verified by the automated test suite and CI before publication. The repository doubles as a testbed for evaluating how AI coding tools handle multi-file backend changes — schema migrations, API contracts, and test maintenance.

## License

MIT — see [LICENSE](LICENSE).
