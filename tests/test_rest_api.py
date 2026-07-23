"""REST endpoint tests: happy paths, validation, auth, and error handling."""

VALID_PAYLOAD = {
    "title": "Checkout API returns 500 on empty cart",
    "description": "POST /checkout returns HTTP 500 when the cart is empty instead of a 422 validation response.",
    "severity": "high",
    "reporter_email": "qa@example.com",
}


def test_health_check(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_create_incident(client, auth_headers):
    resp = client.post("/incidents", json=VALID_PAYLOAD, headers=auth_headers)
    assert resp.status_code == 201
    body = resp.json()
    assert body["id"] > 0
    assert body["title"] == VALID_PAYLOAD["title"]
    assert body["severity"] == "high"
    assert body["status"] == "open"
    assert body["resolution_notes"] is None
    assert body["created_at"]


def test_create_incident_requires_api_key(client):
    resp = client.post("/incidents", json=VALID_PAYLOAD)
    assert resp.status_code == 401


def test_create_incident_rejects_wrong_api_key(client):
    resp = client.post("/incidents", json=VALID_PAYLOAD, headers={"X-API-Key": "wrong"})
    assert resp.status_code == 401


def test_create_incident_rejects_invalid_email(client, auth_headers):
    payload = {**VALID_PAYLOAD, "reporter_email": "not-an-email"}
    resp = client.post("/incidents", json=payload, headers=auth_headers)
    assert resp.status_code == 422


def test_create_incident_rejects_short_title(client, auth_headers):
    payload = {**VALID_PAYLOAD, "title": "ab"}
    resp = client.post("/incidents", json=payload, headers=auth_headers)
    assert resp.status_code == 422


def test_create_incident_rejects_unknown_severity(client, auth_headers):
    payload = {**VALID_PAYLOAD, "severity": "catastrophic"}
    resp = client.post("/incidents", json=payload, headers=auth_headers)
    assert resp.status_code == 422


def test_list_incidents_filters_by_severity(client, auth_headers):
    client.post("/incidents", json=VALID_PAYLOAD, headers=auth_headers)
    low = {**VALID_PAYLOAD, "title": "Tooltip text overflows container", "severity": "low"}
    client.post("/incidents", json=low, headers=auth_headers)

    resp = client.get("/incidents", params={"severity": "low"})
    assert resp.status_code == 200
    items = resp.json()
    assert len(items) == 1
    assert items[0]["severity"] == "low"

    assert len(client.get("/incidents").json()) == 2


def test_get_incident_not_found_returns_404(client):
    resp = client.get("/incidents/999")
    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"]


def test_update_incident_status(client, auth_headers):
    created = client.post("/incidents", json=VALID_PAYLOAD, headers=auth_headers).json()
    resp = client.patch(
        f"/incidents/{created['id']}",
        json={"status": "resolved", "resolution_notes": "Validation added to the cart handler."},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "resolved"
    assert body["resolution_notes"] == "Validation added to the cart handler."


def test_delete_incident(client, auth_headers):
    created = client.post("/incidents", json=VALID_PAYLOAD, headers=auth_headers).json()
    resp = client.delete(f"/incidents/{created['id']}", headers=auth_headers)
    assert resp.status_code == 204
    assert client.get(f"/incidents/{created['id']}").status_code == 404
