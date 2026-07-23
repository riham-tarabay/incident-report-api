"""GraphQL endpoint tests: queries, mutations, validation, and auth."""

CREATE_MUTATION = """
mutation CreateIncident($title: String!, $description: String!, $severity: Severity!, $email: String!) {
  createIncident(title: $title, description: $description, severity: $severity, reporterEmail: $email) {
    id
    title
    status
    severity
    reporterEmail
    resolutionNotes
  }
}
"""

UPDATE_MUTATION = """
mutation UpdateStatus($id: Int!, $status: Status!, $notes: String) {
  updateIncidentStatus(id: $id, status: $status, resolutionNotes: $notes) {
    id
    status
    resolutionNotes
  }
}
"""

LIST_QUERY = """
query ListIncidents($severity: Severity) {
  incidents(severity: $severity) {
    id
    title
    severity
  }
}
"""

GET_QUERY = """
query GetIncident($id: Int!) {
  incident(id: $id) {
    id
    title
  }
}
"""

VALID_VARS = {
    "title": "Search returns stale results",
    "description": "The /search endpoint serves cached results for 24 hours even after reindexing completes.",
    "severity": "HIGH",
    "email": "qa@example.com",
}


def gql(client, query, variables=None, headers=None):
    resp = client.post(
        "/graphql",
        json={"query": query, "variables": variables or {}},
        headers=headers or {},
    )
    assert resp.status_code == 200
    return resp.json()


def test_create_incident_mutation(client, auth_headers):
    body = gql(client, CREATE_MUTATION, VALID_VARS, headers=auth_headers)
    assert "errors" not in body
    data = body["data"]["createIncident"]
    assert data["title"] == VALID_VARS["title"]
    assert data["severity"] == "HIGH"
    assert data["status"] == "OPEN"
    assert data["reporterEmail"] == "qa@example.com"
    assert data["resolutionNotes"] is None


def test_create_incident_mutation_requires_api_key(client):
    body = gql(client, CREATE_MUTATION, VALID_VARS)
    assert body["errors"]


def test_create_incident_mutation_rejects_invalid_email(client, auth_headers):
    variables = {**VALID_VARS, "email": "not-an-email"}
    body = gql(client, CREATE_MUTATION, variables, headers=auth_headers)
    assert body["errors"]
    assert "Validation failed" in body["errors"][0]["message"]


def test_get_incident_query_returns_null_for_missing_id(client):
    body = gql(client, GET_QUERY, {"id": 999})
    assert "errors" not in body
    assert body["data"]["incident"] is None


def test_update_incident_status_mutation(client, auth_headers):
    created = gql(client, CREATE_MUTATION, VALID_VARS, headers=auth_headers)["data"]["createIncident"]
    body = gql(
        client,
        UPDATE_MUTATION,
        {"id": created["id"], "status": "RESOLVED", "notes": "Cache TTL reduced to 5 minutes."},
        headers=auth_headers,
    )
    assert "errors" not in body
    data = body["data"]["updateIncidentStatus"]
    assert data["status"] == "RESOLVED"
    assert data["resolutionNotes"] == "Cache TTL reduced to 5 minutes."


def test_update_missing_incident_returns_error(client, auth_headers):
    body = gql(client, UPDATE_MUTATION, {"id": 999, "status": "RESOLVED", "notes": None}, headers=auth_headers)
    assert body["errors"]
    assert "not found" in body["errors"][0]["message"]


def test_list_incidents_query_filters_by_severity(client, auth_headers):
    gql(client, CREATE_MUTATION, VALID_VARS, headers=auth_headers)
    low_vars = {**VALID_VARS, "title": "Minor typo on settings page", "severity": "LOW"}
    gql(client, CREATE_MUTATION, low_vars, headers=auth_headers)

    body = gql(client, LIST_QUERY, {"severity": "LOW"})
    incidents = body["data"]["incidents"]
    assert len(incidents) == 1
    assert incidents[0]["severity"] == "LOW"

    all_body = gql(client, LIST_QUERY, {})
    assert len(all_body["data"]["incidents"]) == 2
