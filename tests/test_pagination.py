"""REST pagination tests: limit/offset behavior and bounds validation."""

BASE = {
    "description": "Reproducible issue used to verify pagination behavior on the incidents list endpoint.",
    "severity": "medium",
    "reporter_email": "qa@example.com",
}


def _create(client, auth_headers, title):
    resp = client.post("/incidents", json={**BASE, "title": title}, headers=auth_headers)
    assert resp.status_code == 201
    return resp.json()["id"]


def test_list_returns_newest_first(client, auth_headers):
    ids = [_create(client, auth_headers, f"Pagination incident {i}") for i in range(3)]
    items = client.get("/incidents").json()
    assert [item["id"] for item in items] == sorted(ids, reverse=True)


def test_limit_and_offset_slice_the_result_set(client, auth_headers):
    ids = [_create(client, auth_headers, f"Pagination incident {i}") for i in range(3)]
    newest_first = sorted(ids, reverse=True)

    page = client.get("/incidents", params={"limit": 2, "offset": 1}).json()
    assert [item["id"] for item in page] == newest_first[1:3]

    last_page = client.get("/incidents", params={"limit": 2, "offset": 2}).json()
    assert [item["id"] for item in last_page] == newest_first[2:]


def test_pagination_bounds_are_validated(client):
    assert client.get("/incidents", params={"limit": 0}).status_code == 422
    assert client.get("/incidents", params={"limit": 101}).status_code == 422
    assert client.get("/incidents", params={"offset": -1}).status_code == 422
