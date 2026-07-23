"""API-key authentication for write operations.

If the INCIDENT_API_KEY environment variable is unset, auth is disabled
(convenient for local exploration). When set, every write request must send
the key in the X-API-Key header.
"""
import hmac
import os
from typing import Optional

from fastapi import Header, HTTPException, Request


def _expected_key() -> Optional[str]:
    return os.environ.get("INCIDENT_API_KEY") or None


def _key_matches(provided: Optional[str], expected: str) -> bool:
    # Constant-time comparison to avoid timing side channels.
    return provided is not None and hmac.compare_digest(provided, expected)


def require_api_key(x_api_key: Optional[str] = Header(default=None)) -> None:
    """FastAPI dependency enforcing X-API-Key on REST write endpoints."""
    expected = _expected_key()
    if expected is None:
        return
    if not _key_matches(x_api_key, expected):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


def check_request_api_key(request: Request) -> None:
    """Same check for GraphQL mutations; raises into the GraphQL errors array."""
    expected = _expected_key()
    if expected is None:
        return
    if not _key_matches(request.headers.get("x-api-key"), expected):
        raise PermissionError("Invalid or missing API key")
