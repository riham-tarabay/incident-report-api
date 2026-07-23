import os

# Configure the environment BEFORE importing the app so the engine, API key,
# and rate limiter all bind to test values.
os.environ["DATABASE_URL"] = "sqlite:///./test_incidents.db"
os.environ["INCIDENT_API_KEY"] = "test-key"
os.environ["RATE_LIMIT_MAX"] = "100000"

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402


@pytest.fixture(autouse=True)
def clean_database():
    """Give every test a fresh schema."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def auth_headers():
    return {"X-API-Key": "test-key"}
